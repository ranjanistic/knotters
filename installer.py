import os
file = "requirements.txt"

print(f"This is a custom requirements installer. It reads dependencies from {file} one by one, and installs them in orderly fashion.")
print(f"This is only recommended in emergency situations.\n")

if(str(input('You sure this is the only option you\'re left with? (y/N): ')).lower().strip()=='y'):
    f = open(file, "r")

    content = f.read()

    deps = content.split("\n")


    for dep in deps:
        print(dep)
        if dep:
            os.system(f"pip install {dep}")

    print("Done maybe?")