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
import itertools as it
import string

import more_itertools as mit
from asteval import Interpreter
from pathlib import PurePath
from box import Box
import textwrap

a = Interpreter(usersyms=dict(string=string, it=it, mit=mit,
                              Path=PurePath, Box=Box))


def run_module():
    module_args = dict(
        expression=dict(type='str', required=True),
        out=dict(type='str', required=False, default=''),
        data=dict(type='dict', required=False, default={}),
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True, )

    result = evaluate(module.params)

    if module.check_mode: module.exit_json(**result)
    module.exit_json(**result)


def evaluate(params: dict):
    params = Box(params)
    a.symtable.update(params.data)
    out = a(textwrap.dedent(params.expression))
    if params.out: out = a.symtable[params.out]

    result = params.copy()
    result.update(changed=False, **{(params.out or 'out'): out})
    return result.to_dict()


def test():
    params = Box(default_box=True)
    params.data.info.image = 'proj_1-development'
    params.expression = """
    out = Box(info)
    
    def update(key, info_default=None, kwargs=None):
        if kwargs:
            out.update({key: kwargs})
            out.update(info.get(key, info_default))
        elif (key in info) or info_default:
            out.update({key: info.get(key, info_default)})
    
    out.image = info['image']
    update('name', out.image)
    update('hostname', out.name)
    
    env = Box()
    env.ENV_FOR_DYNACONF = "{{env_name}}"
    env.TZ = 'Asia/Almaty'
    update('env', {}, env)
    update('comparisons', {}, {'*': 'strict'})
    update('volumes', [])
    out = out.to_dict()"""

    params.out = 'out'
    result = evaluate(params)
    print(pformat(result))


def main():
    # test()
    run_module()


if __name__ == '__main__':
    main()
