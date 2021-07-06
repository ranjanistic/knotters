import os
from manage import ENVPATH

filepath = ENVPATH
readpath = 'main\.env.example'
print(f"Sample from: {readpath}")

if str(input(f'This will create/overwrite {filepath}. Continue? (y/N) ')) == 'y':
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
                if not subkeys[1]: del subkeys[1]
            val = ''
            if len(subkeys) > 1:
                val = str(input(f"{subkeys[0]} (default:{subkeys[1]}) ="))
                if not val:
                    val = subkeys[1]
            else: val = str(input(f"{subkeys[0]}="))
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
    print(f'Created {filepath}.')
    if str(input(f'GPG encrypt {filepath}? (y/N) ')) == 'y':
        email = str(input(f'email: '))
        os.system(f'gpg -e -r {email} {filepath}')
        os.remove(f'{filepath}')