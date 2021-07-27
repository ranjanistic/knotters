import os
from main.strings import Environment
from manage import ENVPATH, ENVSAMPLEPATH
from testmanage import ENVTESTPATH

if str(input('This will override previously done setup, if any. Continue? (y/n) : ')) == 'y':

    print('Creating _logs_/error.txt')
    try:
        os.mkdir('_logs_')
    except: pass
    f = open('_logs_/error.txt', 'w')
    f.write('Exception logs will also remain here.')
    f.close()
    print('Created _logs_/error.txt')

    fd = open(ENVSAMPLEPATH, "r")
    envcontent = fd.read()
    fd.close()

    print(f'Creating {ENVPATH}')
    envf = open(ENVPATH, 'w')
    envf.write(envcontent)
    envf.close()
    print(f'Created {ENVPATH}')

    print(f'Creating {ENVTESTPATH}')
    tenvf = open(ENVTESTPATH, 'w')
    envcontent = envcontent.replace(Environment.DEVELOPMENT,Environment.TESTING)
    tenvf.write(envcontent)
    tenvf.close()
    print(f'Created {ENVTESTPATH}')

    print('Setup complete.')
    print(f'NOTE: Values at {ENVPATH} and {ENVTESTPATH} might still require manual edit.')
