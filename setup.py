import os
from manage import ENVPATH, ENVSAMPLEPATH, ENVTESTPATH
from random import SystemRandom

if str(input('This will override previously done setup, if any. Continue? (y/n) : ')) == 'y':

    try:
        os.mkdir('_logs_')
        print('Created _logs_/')
    except:
        pass

    fd = open(ENVSAMPLEPATH, "r")
    envcontent = fd.read()
    fd.close()

    envf = open(ENVPATH, 'w')
    envf.write(envcontent)
    envf.close()
    print(f'Created {ENVPATH}')

    tenvf = open(ENVTESTPATH, 'w')
    envcontent = envcontent.replace('development', 'testing').replace(
        'HOSTS=127.0.0.1', 'HOSTS=127.0.0.1,testserver').replace('main/.env', 'main/.env.testing')
    tenvf.write(envcontent)
    tenvf.close()
    print(f'Created {ENVTESTPATH}\n')
    
    filepath = ENVPATH
    testfilepath = ENVTESTPATH
    readpath = ENVSAMPLEPATH

    print(f"Setting up {ENVPATH}")
    print(f"Sample from: {readpath}")
    print('NOTE: Some keys could have default values, empty press Enter to accept them if you\'re ok with them.\n')
    fd = open(readpath, "r")
    contents = fd.read()
    fd.close()

    keys = contents.split('\n')
    data = {}
    for key in keys:
        if str(key).strip():
            subkeys = key.split('=')
            if len(subkeys) > 1:
                if not subkeys[1]:
                    del subkeys[1]
            val = ''
            if len(subkeys) > 1:
                if subkeys[0] == 'PROJECTKEY':
                    val = str(input(f"{subkeys[0]} (default:{''.join([SystemRandom().choice('abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)') for _ in range(50)])}) ="))
                else:
                    val = str(input(f"{subkeys[0]} (default:{subkeys[1]}) ="))
                if not val:
                    val = subkeys[1]
            else:
                if subkeys[0] == 'PROJECTKEY':
                    pkey = ''.join([SystemRandom().choice('abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)') for _ in range(50)])
                    val = str(input(f"{subkeys[0]} (default:{pkey}) ="))
                    if not val:
                        val = pkey
                else:
                    val = str(input(f"{subkeys[0]}="))
            data[subkeys[0]] = val

    f = open(filepath, "w")
    content = ''
    for key in data:
        if content:
            content = f"{content}\n{key}={data[key]}"
        else:
            content = f"{key}={data[key]}"
    f.write(content)
    f.close()
    print(f'\nSetup {filepath} compete.')
    content = content.replace('development', 'testing').replace(
        'HOSTS=127.0.0.1', 'HOSTS=127.0.0.1,testserver').replace('main/.env', 'main/.env.testing')
    f = open(testfilepath, "w")
    f.write(content)
    f.close()
    print(f'Setup {testfilepath} compete.\nCheck this manually as well.\n')

    print('Environment setup complete.')
    print('You may now proceed with the next steps in README.md')
