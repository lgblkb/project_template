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
        container_info=dict(type='dict', required=True),
        container_vars=dict(type='dict', required=True),
        set_to=dict(type='str', required=False),
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=False)

    result = evaluate(Box(module.params))

    # if module.check_mode: module.exit_json(**result)
    module.exit_json(changed=False, **result)


def evaluate(params: Box):
    container_info = Box(params.container_info)
    if 'command' not in container_info:
        worker_options = Box(params.container_vars.celery_worker, default_box=True)
        worker_options.app = worker_options.get('app', 'app')
        worker_options.concurrency = worker_options.get('concurrency', 1)
        worker_options.loglevel = worker_options.get('loglevel', 'INFO')
        worker_options.hostname = worker_options.get('hostname', container_info.name)
        worker_options.events = worker_options.get('events', True)
        worker_options.prefetch_multiplier = worker_options.get('prefetch_multiplier', 1)

        if params.container_vars.get('name_prefix', False):
            default_base_name = container_info.name.replace(f"{params.container_vars.name_prefix}_", '')
            worker_options.queues = ['.'.join([params.container_vars.name_prefix, queue])
                                     for queue in worker_options.get('queues', [default_base_name])]
        if not worker_options.queues:
            worker_options.queues = [container_info.name]
        worker_options.queues = ",".join(worker_options.queues)

        command_parts = list()
        command_parts.append('celery --app {app} worker -O fair')
        command_parts.append('--loglevel={loglevel}')
        command_parts.append('--concurrency={concurrency}')
        command_parts.append('--hostname={hostname}')
        command_parts.append('--queues={queues}')
        command_parts.append('--prefetch-multiplier={prefetch_multiplier}')
        if worker_options.events:
            command_parts.append('--events')
        if worker_options.autoscale:
            command_parts.append('--autoscale={autoscale}')

        container_info.command = " ".join(command_parts).format(**worker_options)

    out = Box(container_info=container_info)
    if 'set_to' in params:
        out.ansible_facts = {params.set_to: container_info}
    return out.to_dict()


def test():
    path = r'/home/lgblkb/PycharmProjects/project_template/provision/deploy_switches/service.yaml'
    res = evaluate(Box(switch=Box.from_yaml(filename=path).default))
    logger.info("res:\n%s", pformat(res))


def main():
    # test()
    run_module()


if __name__ == '__main__':
    main()
