#!/usr/bin/python
import itertools as it
import string
from pathlib import PurePath

import more_itertools as mit
from asteval import Interpreter
from box import Box
import textwrap

a = Interpreter(usersyms=dict(string=string, it=it, mit=mit, textwrap=textwrap,
                              Path=PurePath, Box=Box))


class FilterModule(object):
    def filters(self):
        return dict(eval=self.eval)

    def eval(self, expression, out=None, **kwargs):
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
        a.symtable.update(kwargs)
        result = a(expression)
        if out: result = a.symtable[out]
        return result
