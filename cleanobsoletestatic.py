"""
Remove previous version static folders
"""
from os import listdir, remove, environ, symlink
from os.path import isdir, isfile, join
from pathlib import Path
import shutil
from datetime import datetime
from manage import ENVPATH

environ.setdefault('ENVPATH', ENVPATH)
from main.env import STATIC_ROOT
from main.__version__ import VERSION


def __decrease_version(version, by=2):
    """
    Decrease version
    """
    if by == 0:
        raise Exception("DECREASE VERSION BY: 0")
    version = "".join(version.split('.'))
    oldversion = str(int(version) - by)
    if(len(oldversion)) > 3:
        startpart = oldversion[0:len(oldversion)-2]
        lastpr = oldversion[len(oldversion)-2:]
        oldversion = startpart + "." + ".".join([lastpr[0], lastpr[1]])
    else:
        oldversion = ".".join([oldversion[0], oldversion[1], oldversion[2]])
    return oldversion


__STATIC_ROOT_VERSION = list(
    filter(lambda x: x != "", STATIC_ROOT.split("/")))[-1]

__SUCCESS = False

if __STATIC_ROOT_VERSION != VERSION:
    print("VERSION:", VERSION)
    print("STATIC_ROOT_VERSION:", __STATIC_ROOT_VERSION)
    print("STATIC_ROOT:", STATIC_ROOT)
    raise Exception("Mismatch STATIC_ROOT & VERSION")
else:
    if not (Path(STATIC_ROOT).exists() and Path(STATIC_ROOT).is_dir()):
        raise Exception(f"PANIC: STATIC_ROOT doesn't exist! : {STATIC_ROOT}")
    __MORE_OLD = True
    __OLD_STATIC_ROOT_VERSION = __decrease_version(__STATIC_ROOT_VERSION, by=2)
    __OLD_STATIC_ROOT = STATIC_ROOT.replace(
        __STATIC_ROOT_VERSION, __OLD_STATIC_ROOT_VERSION)
    while __MORE_OLD:
        print("OLD_STATIC_VERSION:", __OLD_STATIC_ROOT_VERSION)
        print("OLD STATIC_ROOT:", __OLD_STATIC_ROOT)
        __OLD_STATIC_ROOT_PATH = Path(__OLD_STATIC_ROOT)
        if __OLD_STATIC_ROOT_PATH.exists() and __OLD_STATIC_ROOT_PATH.is_dir() and __OLD_STATIC_ROOT_PATH != STATIC_ROOT:
            print("OLD STATIC_ROOT REMOVING: ", __OLD_STATIC_ROOT_PATH)
            shutil.rmtree(__OLD_STATIC_ROOT_PATH)
            print("OLD STATIC_ROOT REMOVED: ", __OLD_STATIC_ROOT_PATH)
            __N_OLD_STATIC_ROOT_VERSION = __decrease_version(
                __OLD_STATIC_ROOT_VERSION, by=1)
            __OLD_STATIC_ROOT = __OLD_STATIC_ROOT.replace(
                __OLD_STATIC_ROOT_VERSION, __N_OLD_STATIC_ROOT_VERSION)
            __OLD_STATIC_ROOT_VERSION = __N_OLD_STATIC_ROOT_VERSION
        else:
            __MORE_OLD = False
            print("STATIC_ROOT STOPPED: ", __OLD_STATIC_ROOT_PATH)
            __LAST_STATIC_ROOT = STATIC_ROOT.replace(__STATIC_ROOT_VERSION,  __decrease_version(__STATIC_ROOT_VERSION, by=1))
            if not (Path(__LAST_STATIC_ROOT).exists() and Path(__LAST_STATIC_ROOT).is_dir()):
                print(f"WARNING: LAST_STATIC_ROOT doesn't exist : {__LAST_STATIC_ROOT}")
            else: print("LAST_STATIC_ROOT RETAINED: ", __LAST_STATIC_ROOT)
            print("\nSTATIC_ROOT RETAINED: ", STATIC_ROOT)
            __SUCCESS = True

# Linking email graphics to new static graphics
if __SUCCESS and Path(STATIC_ROOT).exists() and Path(STATIC_ROOT).is_dir():
    __STATIC_EMAIL_LNROOT = STATIC_ROOT.replace(__STATIC_ROOT_VERSION, 'email')
    __STATIC_EMAIL_LN_TARGET = join(STATIC_ROOT, 'graphics/email/')
    print("EMAIL STATIC LNROOT: ", __STATIC_EMAIL_LNROOT)

    if not (Path(__STATIC_EMAIL_LN_TARGET).exists() and Path(__STATIC_EMAIL_LN_TARGET).is_dir()):
        print("NEW EMAIL STATIC TARGET EMPTY: ", __STATIC_EMAIL_LN_TARGET)
        print("RETAINING LN OLD EMAIL STATIC TARGET")
    else:
        print("LINKING NEW EMAIL STATIC TARGET: ", __STATIC_EMAIL_LN_TARGET)
        
        __STATIC_EMAIL_LNROOT_PATH = Path(__STATIC_EMAIL_LNROOT)
        if __STATIC_EMAIL_LNROOT_PATH.exists() and __STATIC_EMAIL_LNROOT_PATH.is_dir():
            try:
                print("REMOVING OLD STATIC LNROOT: ", __STATIC_EMAIL_LNROOT_PATH)
                remove(__STATIC_EMAIL_LNROOT_PATH)
                print("REMOVED OLD STATIC LNROOT")
            except Exception as e:
                print("REMOVE OLD STATIC LNROOT ERR: ", __STATIC_EMAIL_LNROOT_PATH)
                print(e)
                print("PROCEEDING EMAIL STATIC LINK W: ", __STATIC_EMAIL_LN_TARGET)
                pass
        else:
            try:
                print("REMOVING OLD STATIC LNROOT (INEXISTENT|NONDIR): ", __STATIC_EMAIL_LNROOT_PATH)
                remove(__STATIC_EMAIL_LNROOT_PATH)
                print("REMOVED OLD STATIC LNROOT (INEXISTENT|NONDIR)")
            except Exception as e:
                print("REMOVE OLD STATIC LNROOT ERR (INEXISTENT|NONDIR): ", __STATIC_EMAIL_LNROOT_PATH)
                print(e)
                print("PROCEEDING EMAIL STATIC LINK W: ", __STATIC_EMAIL_LN_TARGET)
                pass
        try:
            print("LINKING NEW STATIC LNROOT")
            symlink(__STATIC_EMAIL_LN_TARGET,__STATIC_EMAIL_LNROOT_PATH)
            print("DONE LINKING NEW STATIC LNROOT: ", __STATIC_EMAIL_LN_TARGET)
        except Exception as e:
            print("LINKING NEW STATIC LNROOT ERR: ", __STATIC_EMAIL_LNROOT_PATH)
            print(e)

        if __STATIC_EMAIL_LNROOT_PATH.exists() and __STATIC_EMAIL_LNROOT_PATH.is_dir():
            print("EMAIL STATIC LNROOT EXISTS: ", __STATIC_EMAIL_LNROOT_PATH)
        else:
            print("PANIC: EMAIL STATIC LNROOT NOT EXIST: ", __STATIC_EMAIL_LNROOT_PATH)

print("DONE", __SUCCESS and Path(STATIC_ROOT).exists() and Path(STATIC_ROOT).is_dir())

