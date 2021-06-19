import os
filepath = "main/.env"
readpath = 'main/.env.example'
print(f"Reading from {readpath}")

if str(input(f'This will overwrite {filepath}. Continue (y/n)? ')) == 'y':
    fd = open(readpath, "r")
    contents = fd.read()
    fd.close()

    keys = contents.split('\n')
    data = {}
    for key in keys:
        if str(key).strip():
            subkeys = key.split('=')
            data[subkeys[0]] = str(input(f"{subkeys[0]}="))
        
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
    if str(input(f'GPG encrypt {filepath}? (y/n)? ')) == 'y':
        email = str(input(f'email: '))
        os.system(f'gpg -e -r {email} {filepath}')
        os.remove(f'{filepath}')