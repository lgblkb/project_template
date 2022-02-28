# !/usr/bin/python

# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from pprint import pformat

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: my_test

short_description: This is my test module

version_added: "2.4"

description:
    - "This is my longer description explaining my test module"

options:
    name:
        description:
            - This is the message to send to the test module
        required: true
    new:
        description:
            - Control to demo if the result of this module is changed or not
        required: false

extends_documentation_fragment:
    - azure

author:
    - Your Name (@yourhandle)
'''

EXAMPLES = '''
# Pass in a message
- name: Test with a message
  my_test:
    name: hello world

# pass in a message and have changed true
- name: Test with a message and changed output
  my_test:
    name: hello world
    new: true

# fail the module
- name: Test failure of the module
  my_test:
    name: fail me
'''

RETURN = '''
original_message:
    description: The original name param that was passed in
    type: str
    returned: always
message:
    description: The output message that the test module generates
    type: str
    returned: always
'''

from ansible.module_utils.basic import AnsibleModule
from box import Box
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('lgblkb')


def run_module():
    module_args = dict(
        switch=dict(type='dict', required=True),
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=False)

    target_groups = evaluate(Box(module.params))

    # if module.check_mode: module.exit_json(**result)
    module.exit_json(target_groups=target_groups, changed=False)


var_keys = ['watchdog', 'celery_worker', 'name_prefix']
builtin_keys = set(['pre', 'post', 'target', 'targets', 'vars'] + var_keys)


def set_targets(target_name, target_info):
    if 'target' in target_info:
        if isinstance(target_info.target, dict):
            targets = [target_info.target]
        else:
            targets = [{target_name: target_info.target}]
    elif 'targets' in target_info:
        if isinstance(target_info.targets, (list, tuple)):
            if isinstance(target_info.targets[0], dict):
                targets = target_info.targets
            else:
                raise ValueError('Target items can only be str or dict.',
                                 dict(got_type=str(type(target_info.targets[0]))))
        elif isinstance(target_info.targets, dict):
            targets = [{k: v} for k, v in target_info.targets.items()]
        else:
            raise ValueError('Targets option can only be list, tuple or dict',
                             dict(got_type=str(type(target_info.targets))))
    else:
        targets = [{target_name: ''}]
    return targets


def evaluate(params: Box):
    outs = list()
    sw = Box(params.switch, default_box=True)
    for target_name, target_info in sw.configs.items():
        target_out = Box()
        if isinstance(target_info, Box):
            info_keys = set(target_info.keys())
            present_builtin_keys = builtin_keys - (builtin_keys - info_keys)
            target_info.post = target_info - Box({bk: 1 for bk in present_builtin_keys}) + target_info.post

            target_out.targets = set_targets(target_name, target_info)
            target_out.pre = sw.pre + target_info.pre
            target_out.post = sw.post + target_info.post

            target_out.vars = sw.vars
            for var_key in var_keys:
                if var_key in present_builtin_keys:
                    target_out.vars += {var_key: target_info[var_key]}
            target_out.vars += target_info.vars
        else:
            target_out.targets = [{target_name: target_info}]
            target_out.pre = sw.pre
            target_out.post = sw.post
            target_out.vars = sw.vars
        outs.append(target_out.to_dict())
    return outs


def test():
    path = r'/provision_old/deploy_switches/service.yaml'
    res = evaluate(Box(switch=Box.from_yaml(filename=path).default))
    logger.info("res:\n%s", pformat(res))


def main():
    # test()
    run_module()


if __name__ == '__main__':
    main()
