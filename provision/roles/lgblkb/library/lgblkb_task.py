import copy
import json
import logging
import os
import os.path
import sys
import textwrap
from pathlib import Path
from typing import Union

import boltons.iterutils
from ansible.module_utils.basic import AnsibleModule
from asteval import Interpreter
from boltons.iterutils import remap, research
from box import Box
from omegaconf import OmegaConf

logging.basicConfig(filename='logs.log', level=logging.DEBUG, filemode='w')
logger = logging.getLogger('lgblkb')

as_path = lambda path: Path(os.path.abspath(path))

box_sum = lambda boxes: sum(boxes, Box())


def find_file(filename):
    path = Path(os.path.abspath(os.curdir))
    for parent in path.parents:
        file = parent.joinpath(filename)
        if file.exists(): return file
    raise FileNotFoundError(filename)


def is_obj_json_serializable(obj):
    try:
        json.JSONEncoder().encode(obj)
        return True
    except TypeError:
        return False


__show = lambda self: OmegaConf.to_yaml(OmegaConf.create(self.to_dict()))
Box.show = __show


def solve_envy_data(data: Box, default_key='', target_keys=()):
    if isinstance(target_keys, str): target_keys = (target_keys,)
    data = Box(data, default_box=True)
    default_data = data[default_key] if default_key else Box()
    if not target_keys: target_keys = (data - {default_key: 1}).keys() if default_key else data.keys()
    return Box({target_key: default_data + data[target_key] for target_key in target_keys})


def make_path(path, value):
    out = Box(default_box=True)
    data = out
    for step in path[:-1]:
        data = data[step]
    data[path[-1]] = value
    return out


class Base(AnsibleModule):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.results = Box(changed=False, box_dots=True)
        # self.ansible_vars = Box()

    def add_facts(self, *facts, **other_facts):
        self.results += dict(ansible_facts=box_sum(list(facts)) + other_facts)

    def add_results(self, *results, **other_results):
        self.results += box_sum(list(results)) + other_results

    def resolve(self, data, **base_data):
        reference_data = self.results + base_data

        def resolve_pre_post(p, k, v):
            if k in ['pre_', 'post_']:
                return k, self.resolve(dict(data=v)).data
            return True

        data = remap(data, resolve_pre_post)
        config = OmegaConf.create((reference_data + data).to_dict())
        return Box(OmegaConf.to_container(config, resolve=True)) - {k: 1 for k in reference_data if k not in data}

    def envise_data(self, file_data: Box, name: Union[bool, str], add=True, **other_base_data) -> Box:
        _other_envs = Box({k: 1 for k in self.results.project_envs}) + dict(default=1)
        env_data = solve_envy_data(file_data, 'default', self.results.env_name)[self.results.env_name]

        base_data = self.resolve(file_data - _other_envs + other_base_data)
        env_data = self.resolve(env_data, **base_data)

        env_data = remap(env_data,
                         lambda p, k, v: (k, solve_envy_data(v, '*')) if (isinstance(v, dict) and '*' in v) else True)

        def merge_pre_post(p, k, v: Box):
            if not (isinstance(v, dict) and ('pre_' in v or 'post_' in v)): return
            pre_data = v.pop('pre_', Box())
            post_data = v.pop('post_', Box())
            other_data = v - pre_data - post_data
            v.update(pre_data + other_data + post_data)

        research(env_data, merge_pre_post)
        if name:
            data = Box(OmegaConf.to_object(OmegaConf.from_dotlist([name])))
            # logger.debug("data1: %s", data.show())
            data = remap(data, lambda p, k, v: (k, v) if v else (k, env_data))
            # logger.debug("data2: %s", data.show())
            # data[name] = env_data
        else:
            data = env_data
            # logger.debug("env_data:\n%s", env_data.show())
        if add: self.add_results(data)

        return Box(name=name, data=env_data)

    def envise(self, yaml_file: Union[str, Path], name: Union[bool, str] = '', add=True) -> Box:
        yaml_file = as_path(yaml_file)
        # logger.debug("yaml_file: %s", yaml_file)
        if name is not False:
            name = name or ".".join(yaml_file
                                    .relative_to(self.results.project_folder, 'provision', )
                                    .with_suffix('').parts)
        file_data = Box.from_yaml(filename=yaml_file, default_box=True)
        return self.envise_data(file_data, name=name, add=add)


class ExtractProjectInfo(Base):

    def extract_project_info(self, env_name):
        toml_file = find_file('pyproject.toml')
        toml_data = Box.from_toml(filename=toml_file)
        info = toml_data.project
        project_name = info.name
        image_name = f"{project_name}-{env_name}"
        image_tag = 'latest'
        image_fullname = f"{image_name}:{image_tag}"
        self.add_results(project_name=project_name, image_name=image_name, image_tag=image_tag,
                         image_fullname=image_fullname, env_name=env_name, project_folder=str(toml_file.parent),
                         project_envs=os.listdir(toml_file.parent.joinpath('provision', 'envs')))

    def _merge_targets(self, p, k, v: Box, base_dir: Path):
        if not (isinstance(v, dict) and 'merge' in v and 'targets' in v): return
        targets = Box({k: self.envise(base_dir.joinpath(v), k).data for k, v in v.targets.items()})
        self.add_results({k: box_sum([targets[key] for key in v]) for k, v in v.merge.items()})

    def read_settings_switch(self, yaml_file: Union[str, Path]):
        switch_data = self.envise(yaml_file, add=False, name=False).data

        def walker(p, k, v):
            if not isinstance(v, dict): return True
            if 'eval_' in v:
                return k, self.resolve_eval(v.eval_)
            if 'read_' in v:
                return k, self.resolve_read(v.read_)
            return True

        for step_key, step_data in switch_data.items():
            def stepper(p, k, v):
                if not isinstance(v, str): return True
                result_data = make_path(p, Box({k: v}))
                result_data = remap(result_data, walker)
                self.add_results(result_data)
                return True

            remap(step_data, stepper)

    def generate_commands(self):
        commands = self.envise(Path(self.results.project_folder)
                               .joinpath('provision/commands/templated.yaml'), 'commands', add=False).data
        for name, cmd in commands.items():
            Path(self.results.project_folder).joinpath('provision/commands', name + '.sh') \
                .write_text(cmd.replace('--', '\\\n\t--'))


class Resolvers(Base):
    file_format_reader = {'.json': Box.from_json,
                          '.yaml': Box.from_yaml,
                          '.yml': Box.from_yaml,
                          '.toml': Box.from_toml}

    def _fetch_data(self, data):
        if isinstance(data, str):
            data = self.results[data]
        return data

    def resolve_fmt(self, string_to_format: str, *datas):
        merged_data = box_sum([self._fetch_data(data) for data in datas])
        return string_to_format.format(**merged_data)

    def resolve_eval(self, expression: str, data=None):
        data = data or {}
        if isinstance(data, str):
            if data in self.results:
                data = self.results[data]
            else:
                k, v = str(data).split('=', maxsplit=1)
                data = {k: self.resolve_eval(v)}
        if not isinstance(data, dict):
            logger.critical(f"Resolve volumes: data should be of type dict!", data)
        asteval_interp = Interpreter()
        asteval_interp.symtable.update(self.results + data)
        # logger.debug("expression: %s", expression)
        eval_res = asteval_interp(textwrap.dedent(expression))
        return asteval_interp.symtable['out'] if eval_res is None else eval_res

    def resolve_read(self, filepath: str, accessor=''):
        data = self.envise(filepath, name=False, add=False).data

        if accessor:
            data = self.resolve_eval(accessor, data)
        return data
        # file_content = self.file_format_reader[filepath.suffix](filepath.read_text())


class Deploy(Base):
    def read_deploy_settings(self, deploy_settings: list):
        for deploy_setting in deploy_settings:
            self.envise(deploy_setting)


class Module(Resolvers, ExtractProjectInfo, Deploy):
    pass


module = Module(dict(env_name=dict(type='str', required=True),
                     settings_switch=dict(type='str', required=True),
                     vars=dict(type='dict', required=True),
                     deploy_settings=dict(type='list', required=True),
                     ))

OmegaConf.register_new_resolver('fmt', module.resolve_fmt)
OmegaConf.register_new_resolver('eval', module.resolve_eval)
OmegaConf.register_new_resolver('read', module.resolve_read)


def main():
    params = Box(module.params)
    module.results.update(params.vars)
    module.extract_project_info(env_name=params.env_name)
    module.read_settings_switch(yaml_file=params.settings_switch)
    module.generate_commands()
    module.read_deploy_settings(params.deploy_settings)
    module.results.to_yaml(filename=Path(module.results.project_folder).joinpath('settings.yaml'))
    # module.add_facts(deploy_settings=[v for k, v in module.results.compose.items()])
    module.exit_json(**module.results.to_dict())


if __name__ == '__main__':
    main()
