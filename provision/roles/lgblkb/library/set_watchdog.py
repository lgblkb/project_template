# !/usr/bin/python

# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from pathlib import Path
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
import os

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('lgblkb')


def run_module():
    module_args = dict(
        container_info=dict(type='dict', required=True),
        watchdog=dict(type='raw', required=True),
        watch_dir=dict(type='str', required=True),
        set_to=dict(type='str', required=False),
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=False)

    result = evaluate(Box(module.params))

    # if module.check_mode: module.exit_json(**result)
    module.exit_json(changed=False, **result)


def create_watch_file(watch_dir, name):
    watched_filepath = Path(watch_dir).joinpath(f'watch_{name}.txt')
    if not os.path.exists(watched_filepath): watched_filepath.touch()
    return watched_filepath


def get_watchdogged_command(watch_dir, filepaths, original_cmd):
    command_parts = list()
    command_parts.append('watchmedo auto-restart')
    command_parts.append('--pattern=' + ";".join([f"**/*{x.with_suffix('').name}*" for x in filepaths]))
    command_parts.append(f'--directory={watch_dir}')
    command_parts.append('--')
    command_parts.append(original_cmd)
    new_command = " ".join(command_parts)
    return new_command


def evaluate(params: Box):
    container_info = Box(params.container_info)
    os.makedirs(params.watch_dir, exist_ok=True)
    if isinstance(params.watchdog, dict):
        filepaths = set([create_watch_file(params.watch_dir, k)
                         for k, v in params.watchdog.items() if v] \
                        + [create_watch_file(params.watch_dir, container_info.name)])
        container_info.command = get_watchdogged_command(params.watch_dir, filepaths, container_info.command)
    else:
        if params.watchdog:
            filepath = create_watch_file(params.watch_dir, container_info.name)
            container_info.command = get_watchdogged_command(params.watch_dir, [filepath], container_info.command)
    out = Box(container_info=container_info)
    if 'set_to' in params:
        out.ansible_facts = {params.set_to: container_info}
    return out.to_dict()


def test():
    path = r'/provision_old/deploy_switches/service.yaml'
    res = evaluate(Box(switch=Box.from_yaml(filename=path).default))
    logger.info("res:\n%s", pformat(res))


def main():
    # test()
    run_module()


if __name__ == '__main__':
    main()
