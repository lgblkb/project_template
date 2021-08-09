#!/usr/bin/python
import ast
import copy
import functools
import glob
import itertools as it
import operator
import string
import textwrap
from pathlib import PurePath

import boltons
import more_itertools as mit
from asteval import Interpreter
from boltons.iterutils import remap
from box import Box


def merge(obj1, obj2):
    """
    run me with nosetests --with-doctest file.py

    >>> a = { 'first' : { 'all_rows' : { 'pass' : 'dog', 'number' : '1' } } }
    >>> b = { 'first' : { 'all_rows' : { 'fail' : 'cat', 'number' : '5' } } }
    >>> merge(a, b) == { 'first' : { 'all_rows' : { 'pass' : 'dog', 'fail' : 'cat', 'number' : '5' } } }
    True
    """
    obj1 = obj1.copy()
    for key, value in obj2.items():
        if isinstance(value, dict):
            # get node or create one
            node = obj1.setdefault(key, {})
            merge(node, value)
        else:
            obj1[key] = value

    return obj1


#
# a = Interpreter(usersyms=dict(string=string, it=it, mit=mit, copy=copy, ast=ast, boltons=boltons, bool=bool,
#                               Path=PurePath, Box=Box, merge=merge, functools=functools, glob=glob))

import re


def filler(m, p, k, v):
    if type(v) is str:
        for mk, mv in m.items():
            v = re.sub(rf"{{meta\.{mk}}}", str(mv), v)
        return k, v
    else:
        return k, v


def str_format(params):
    out = remap(params['content'], functools.partial(filler, Box(params['payload'])))
    return out


def fmt(a_string, *payloads, **kwargs):
    return a_string.format(**functools.reduce(operator.add, list(map(Box, [*payloads, kwargs]))))


def eval(expression, **kwargs):
    a = Interpreter(usersyms=dict(string=string, it=it, mit=mit, copy=copy, ast=ast, boltons=boltons, bool=bool,
                                  Path=PurePath, Box=Box, merge=merge, functools=functools, glob=glob,
                                  operator=operator))
    a.symtable.update(kwargs)
    result = a(textwrap.dedent(expression))
    if not result:
        if 'out' not in a.symtable:
            raise RuntimeError(dict(error=a.error_msg))
        result = a.symtable['out']
    return result


class FilterModule(object):
    def filters(self):
        return dict(eval=self.eval, fmt=self.fmt)

    def eval(self, expression, **kwargs):
        """
        - name: test evaluator
          set_fact:
            x: |
             {{"count=10
             a=list(range(count))
             b=[string.ascii_letters[:i+3] for i in a]
             out=dict([(k,v) for k,v in zip(a,b)])
             "|eval('out')}}
        - debug: "msg={{x}}"

        :returns:
            "msg": {
                    "0": "abc",
                    "1": "abcd",
                    "2": "abcde",
                    "3": "abcdef",
                    "4": "abcdefg",
                    "5": "abcdefgh",
                    "6": "abcdefghi",
                    "7": "abcdefghij",
                    "8": "abcdefghijk",
                    "9": "abcdefghijkl"
                }

        :param expression:
        :type expression: str
        :param out:
        :type out: str
        :return: Result of evaluating the expression.
        """
        return eval(expression, **kwargs)

    def fmt(self, a_string, *payloads, **kwargs):
        return fmt(a_string, *payloads, **kwargs)
