# !/usr/bin/python

# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
import operator
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
import copy
import ast
import functools
import boltons.iterutils
import glob


def merge(obj1, obj2):
    """
    run me with nosetests --with-doctest file.py

    >>> a = { 'first' : { 'all_rows' : { 'pass' : 'dog', 'number' : '1' } } }
    >>> b = { 'first' : { 'all_rows' : { 'fail' : 'cat', 'number' : '5' } } }
    >>> merge(a, b) == { 'first' : { 'all_rows' : { 'pass' : 'dog', 'fail' : 'cat', 'number' : '5' } } }
    True
    """
    for key, value in obj2.items():
        if isinstance(value, dict):
            # get node or create one
            node = obj1.setdefault(key, {})
            merge(node, value)
        else:
            obj1[key] = value

    return obj1


a = Interpreter(usersyms=dict(string=string, it=it, mit=mit, copy=copy, ast=ast, boltons=boltons, bool=bool,
                              Path=PurePath, Box=Box, merge=merge, functools=functools, glob=glob,
                              operator=operator))


def run_module():
    module_args = dict(
        expression=dict(type='str', required=True),
        out=dict(type='raw', required=False, default=None),
        data=dict(type='dict', required=False, default={}),
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True, )

    outs = evaluate(**module.params)

    # if module.check_mode: module.exit_json(**result)
    module.exit_json(changed=False, **outs)


def evaluate(data, expression, out=None):
    a.symtable.update(data)
    eval_out = a(textwrap.dedent(expression))
    outs = dict()
    if out:
        if type(out) is str:
            target_outs = [out]
        elif isinstance(out, list):
            target_outs = out
        else:
            raise NotImplementedError(str(type(out)))
        for out in target_outs:
            outs[out] = a.symtable[out]
    else:
        outs['out'] = eval_out
    return outs


def test():
    result = evaluate({}, "set([1,2,3])-set([1])")
    print(result)


def main():
    # test()
    run_module()


if __name__ == '__main__':
    main()
