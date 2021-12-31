from django.core.management.base import BaseCommand, CommandError
from django.template.loader import render_to_string
from django.conf import settings
from os import listdir, remove,  symlink, mkdir
from os.path import isdir, isfile, join
from pathlib import Path
import shutil
from datetime import datetime
from main.env import VERSION
from main.methods import renderData
from main.context_processors import GlobalContextData

class Command(BaseCommand):
    """
    
    """
    help = 'Remove previous version static folders and generate error pages.'

    def add_arguments(self, parser):
        parser.add_argument('errors_dir', nargs='+', type=str)
        

    def decrease_version(self, version, by=2):
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

    def handle(self, *args, **options):
        __STATIC_ROOT_VERSION = list(
            filter(lambda x: x != "", settings.STATIC_ROOT.split("/")))[-1]

        __SUCCESS = False

        if __STATIC_ROOT_VERSION != VERSION:
            print("VERSION:", VERSION)
            print("STATIC_ROOT_VERSION:", __STATIC_ROOT_VERSION)
            print("STATIC_ROOT:", settings.STATIC_ROOT)
            raise Exception("Mismatch STATIC_ROOT & VERSION")
        else:
            print("\nCLEARING OBSOLETE STATICS (VERSION < 2)\n")
            if not (Path(settings.STATIC_ROOT).exists() and Path(settings.STATIC_ROOT).is_dir()):
                raise Exception(f"PANIC: STATIC_ROOT doesn't exist! : {settings.STATIC_ROOT}")
            __MORE_OLD = True
            __OLD_STATIC_ROOT_VERSION = self.decrease_version(__STATIC_ROOT_VERSION, by=2)
            __OLD_STATIC_ROOT = settings.STATIC_ROOT.replace(
                __STATIC_ROOT_VERSION, __OLD_STATIC_ROOT_VERSION)
            while __MORE_OLD:
                print("OLD_STATIC_VERSION:", __OLD_STATIC_ROOT_VERSION)
                print("OLD STATIC_ROOT:", __OLD_STATIC_ROOT)
                __OLD_STATIC_ROOT_PATH = Path(__OLD_STATIC_ROOT)
                if __OLD_STATIC_ROOT_PATH.exists() and __OLD_STATIC_ROOT_PATH.is_dir() and __OLD_STATIC_ROOT_PATH != settings.STATIC_ROOT:
                    print("OLD STATIC_ROOT REMOVING: ", __OLD_STATIC_ROOT_PATH)
                    shutil.rmtree(__OLD_STATIC_ROOT_PATH)
                    print("OLD STATIC_ROOT REMOVED: ", __OLD_STATIC_ROOT_PATH)
                    __N_OLD_STATIC_ROOT_VERSION = self.decrease_version(
                        __OLD_STATIC_ROOT_VERSION, by=1)
                    __OLD_STATIC_ROOT = __OLD_STATIC_ROOT.replace(
                        __OLD_STATIC_ROOT_VERSION, __N_OLD_STATIC_ROOT_VERSION)
                    __OLD_STATIC_ROOT_VERSION = __N_OLD_STATIC_ROOT_VERSION
                else:
                    __MORE_OLD = False
                    print("STATIC_ROOT STOPPED: ", __OLD_STATIC_ROOT_PATH)
                    __LAST_STATIC_ROOT = settings.STATIC_ROOT.replace(__STATIC_ROOT_VERSION,  self.decrease_version(__STATIC_ROOT_VERSION, by=1))
                    if not (Path(__LAST_STATIC_ROOT).exists() and Path(__LAST_STATIC_ROOT).is_dir()):
                        print(f"WARNING: LAST_STATIC_ROOT doesn't exist : {__LAST_STATIC_ROOT}")
                    else: print("LAST_STATIC_ROOT RETAINED: ", __LAST_STATIC_ROOT)
                    print("STATIC_ROOT RETAINED: ", settings.STATIC_ROOT)
                    __SUCCESS = True

        print("\nLINKING EMAIL ASSETS WITH LATEST STATIC VERSION\n")
        if __SUCCESS and Path(settings.STATIC_ROOT).exists() and Path(settings.STATIC_ROOT).is_dir():
            __STATIC_EMAIL_LNROOT = settings.STATIC_ROOT.replace(__STATIC_ROOT_VERSION, 'email')
            __STATIC_EMAIL_LN_TARGET = join(settings.STATIC_ROOT, 'graphics/email/')
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

        print("\nGENERATING STATIC ERROR PAGES\n")
        err_dir = Path(options['errors_dir'][0])
        if not err_dir.exists():
            mkdir(err_dir)
        print("ERR DIR: ", err_dir)
        notfoundstr = render_to_string('404.html', renderData(dict(**GlobalContextData,csrf_token=" ")))
        notfoundpath = join(err_dir,'40x.html')
        print("404 PATH: ", notfoundpath)
        with open(notfoundpath,'w+') as file:
            file.write(notfoundstr)
        print("404 PATH DONE: ", notfoundpath)
        servererrorstr = render_to_string('50x.html', renderData(dict(**GlobalContextData,csrf_token=" ")))
        servererrpath = join(err_dir,'50x.html')
        print("500 PATH: ", servererrpath)
        with open(servererrpath,'w+') as file:
            file.write(servererrorstr)
        print("500 PATH DONE: ", servererrpath)
        
        print("\nDONE", __SUCCESS and Path(settings.STATIC_ROOT).exists() and Path(settings.STATIC_ROOT).is_dir())
