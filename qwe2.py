from asteval import Interpreter
import string
import itertools as it
import more_itertools as mit


def main():
    aeval = Interpreter(usersyms=dict(string=string, it=it, mit=mit))
    aeval.symtable['qwe'] = """
qweqweqwe
    """
    res = aeval('qwe.strip()')
    print(res)

    pass


if __name__ == '__main__':
    main()
