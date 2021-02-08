# !/usr/bin/python

# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from pprint import pformat

from jinja2 import Template, StrictUndefined

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
import ast
import operator
import more_itertools as mit
from asteval import Interpreter
from pathlib import PurePath
from box import Box
import textwrap
import copy
import ast
import functools
import boltons.iterutils
import glob
import os
import logging
import jinja2

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('lgblkb')

a = Interpreter(usersyms=dict(string=string, it=it, mit=mit, copy=copy, ast=ast, boltons=boltons, bool=bool,
                              Path=PurePath, Box=Box, functools=functools, glob=glob))


def run_module():
    module_args = dict(
        input=dict(type='raw', required=True),
        env_name=dict(type='str'),
        env_names=dict(type='list'),
        # merge=dict(type='raw', required=False, default={}),
        set_to=dict(type='str', required=True)
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=False)

    result = evaluate(Box(module.params))

    # if module.check_mode: module.exit_json(**result)
    module.exit_json(**result)


def boxify(obj, **kwargs):
    if type(obj) is str:
        if not os.path.exists(obj):
            raise FileNotFoundError(obj)
        out = Box.from_yaml(filename=obj)
    elif isinstance(obj, dict):
        out = obj
    else:
        raise ValueError('Wrong type provided.', dict(input_type=type(obj), obj=obj))
    out = Box(**out, **kwargs)
    return out


# def fmt(a_string, *payloads, **kwargs):
#     return a_string.format(**functools.reduce(operator.add, list(map(Box, [*payloads, kwargs]))))
#
#
# def eval(expression, **kwargs):
#     a = Interpreter(usersyms=dict(string=string, it=it, mit=mit, copy=copy, ast=ast, boltons=boltons, bool=bool,
#                                   Path=PurePath, Box=Box, functools=functools, glob=glob))
#     a.symtable.update(kwargs)
#     result = a(textwrap.dedent(expression))
#     if not result:
#         if not 'out' in a.symtable:
#             raise RuntimeError('Eval errored.', dict(error_msg=a.error_msg))
#         result = a.symtable['out']
#     return result


def evaluate(params: Box):
    input_data = boxify(params.input, default_box=True)
    result = Box(changed=False)
    if params.get('env_names'):
        env_names = params.env_names or set(input_data.keys()) - {'default'}

        env_data = Box()
        for env_name in env_names:
            env_data[env_name] = input_data.default + input_data[env_name]
        result.ansible_facts = {params.set_to: env_data}
    else:
        env_datum = input_data.default + input_data[params.env_name]
        result.ansible_facts = {params.set_to: env_datum}
    return result.to_dict()


def test():
    box_1 = Box(cast={'Scooby-Doo': True, 'Velma': True, 'Shaggy': True},
                props={'Mystery Machine': True})
    box_2 = Box(props={'Mystery Machine': False}, set='Desert')

    res = box_1 + box_2
    logger.info("res: %s", res)


def main():
    # test()
    run_module()


if __name__ == '__main__':
    main()
