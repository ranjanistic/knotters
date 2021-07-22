import os
from manage import ENVPATH, ENVSAMPLEPATH

if str(input('This will override previously done setup, if any. Continue? (y/n) : ')) == 'y':

    os.mkdir('_logs_')
    f = open('_logs_/error.txt', 'w')
    f.write('Exception logs will also remain here.')
    f.close()

    fd = open(ENVSAMPLEPATH, "r")
    envcontent = fd.read()
    fd.close()

    envf = open(ENVPATH, 'w')
    envf.write(envcontent)
    envf.close()

    print('Setup complete.')
