#!/usr/bin/env python3
import logging
import os
import shutil
from functools import partial, wraps
from pathlib import Path

import fire
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('lgblkb')

project_folder = Path(__file__).parent
provision_folder = project_folder.joinpath('provision')
scripts_folder = provision_folder.joinpath('scripts')
commands_folder = provision_folder.joinpath('commands')
secret_filepath = provision_folder.joinpath('roles/lgblkb/files/.secret')

vault_parts = ['--vault-password-file', secret_filepath]


def compose(filename, target, vault=False, **options):
    parts = ['ansible-playbook', scripts_folder.joinpath(f'{filename}.yaml')]
    parts += ['--inventory', provision_folder.joinpath('envs', target)]

    for k, v in options.items():
        if type(v) is bool and v:
            if len(k) == 1:
                parts.append(f'-{k}')
            else:
                parts.append(f'--{k}')
        else:
            parts.append(f'--{k}={v}')
    if vault:
        parts += vault_parts
    cmd = """ """.join(map(str, parts))
    # logger.debug("cmd: %s", cmd)
    return cmd


default_target = 'development'
default_filename = 'init'


def add_method(cls, name=''):
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            return func(self, *args, **kwargs)

        setattr(cls, name or func.__name__, wrapper)
        # Note we are not binding func, but wrapper which accepts self but does exactly the same as func
        return func  # returning func means func can still be used normally

    return decorator


class Play(object):
    def __init__(self, filename=default_filename, target=default_target):
        self._target = target
        self._filename = filename
        self._tasks = list()

    def play(self):
        for task in self._tasks:
            os.system(task(target=self._target))

    def check(self):
        for idx, task in enumerate(self._tasks):
            logger.debug("task %s: %s", idx, task)

    def on(self, target):
        if target == 'dev': target = 'development'
        self._target = target
        return self

    def __str__(self):
        self.play()
        return "Done."


class Runner(object):
    @staticmethod
    def build(complete=False):
        poetry_cache_folder = project_folder.joinpath('provision/roles/lgblkb/files/poetry_cache')
        poetry_cache_folder.mkdir(exist_ok=True)
        copy_lock = lambda: shutil.copyfile(
            *[x.joinpath('poetry.lock') for x in [project_folder, poetry_cache_folder]])
        copy_toml = lambda: shutil.copyfile(
            *[x.joinpath('pyproject.toml') for x in [project_folder, poetry_cache_folder]])
        if complete:
            os.remove(poetry_cache_folder.joinpath('pyproject.toml'))
            os.remove(poetry_cache_folder.joinpath('poetry.lock'))
            copy_toml()
            copy_lock()
        else:
            if not poetry_cache_folder.joinpath('poetry.lock').exists():
                copy_lock()
            if not poetry_cache_folder.joinpath('pyproject.toml').exists():
                copy_toml()

        _run_cmd_parts = [str(commands_folder.joinpath('docker_build')) + ".sh"]
        full_cmd = " ".join(_run_cmd_parts)
        os.system(full_cmd)

    @staticmethod
    def run(key='docker_run', rm=True, it=True, display=False, gpus=False, root=False, cmd='bash'):
        _run_cmd_parts = [str(commands_folder.joinpath(key)) + ".sh"]
        if rm:
            _run_cmd_parts.append('--rm')
        if it:
            _run_cmd_parts.append('-it')
        if display:
            os.system('xhost +')
            _run_cmd_parts.append('--volume="/tmp/.X11-unix:/tmp/.X11-unix:rw"')
            _run_cmd_parts.append('--env="DISPLAY"')
        if root:
            _run_cmd_parts.append('--user root')
        if gpus:
            _run_cmd_parts.append('--gpus all')

        # project_name = project_folder.absolute().name.upper()
        image_fullname = os.getenv('IMAGE_FULLNAME')
        _run_cmd_parts.append(image_fullname)
        _run_cmd_parts.append(cmd)
        full_cmd = " ".join(_run_cmd_parts)
        logger.debug("full_cmd: %s", full_cmd)
        os.system(full_cmd)


class Entry(Runner):
    def __init__(self):
        for filename in [x.with_suffix('').name for x in scripts_folder.glob('*.y*ml')]:
            # noinspection PyTypeChecker
            add_method(Play, filename)(partial(create_task, filename=filename))
        self.play = Play()


def create_task(self, filename, **kwargs):
    self._tasks.append(partial(compose, filename=filename, target=self._target, **kwargs))
    return self


def main():
    fire.Fire(Entry)


if __name__ == '__main__':
    main()
