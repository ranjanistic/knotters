import json
import os
from pathlib import Path
import requests

with open('static.json', 'r') as static:
    statics = json.loads(static.read())
    for key in statics.keys():
        print(key)
        for path in statics[key]:
            filename = path.split("/")[-1]
            finalpath = Path.joinpath(
                Path(os.getcwd()), "static", key, filename)
            print(finalpath)
            response = requests.get(path)
            with open(finalpath, 'w') as f:
                f.write(response.text)
                f.close()
                response.close()
                print("DONE")
