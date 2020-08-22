from pprint import pformat

from asteval import Interpreter
import string
import itertools as it
import more_itertools as mit
from box import Box


def main():
    #     aeval = Interpreter(usersyms=dict(string=string, it=it, mit=mit))
    #     aeval.symtable['qwe'] = """
    # qweqweqwe
    #     """
    #     res = aeval('qwe.strip()')
    #     print(res)
    # filepath = r'/home/lgblkb/PycharmProjects/proj_1/provision/library/eval.py'
    info = dict(image='some_image')
    out = Box(info)

    def update(key, info_default=None, kwargs=None):
        if kwargs:
            out.update({key: kwargs})
            out.update(info.get(key, info_default))
        else:
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
    out = out.to_dict()
    print(pformat(out))

    pass


if __name__ == '__main__':
    main()
