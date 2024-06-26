from django.core.management.base import BaseCommand
from main.strings import Template
from rcssmin import cssmin
from rjsmin import jsmin
from htmlmin.minify import html_minify
from django.template.loader import render_to_string
from django.conf import settings
from json import dumps as jsondumps, loads as jsonloads
from os import remove, symlink, mkdir, walk, path as ospath
from pathlib import Path
from shutil import rmtree
from main.env import SITE, VERSION
from main.methods import renderData
from main.context_processors import GlobalContextData


class Command(BaseCommand):
    """

    """
    help = """
        Remove previous versions of static assets, minify the latest assets, link email assets to latest ones, and generate error pages,
        depending on STATIC_ROOT & VERSION setting.
        Please note that collectstatic command must be run before this command is used.
        """

    def add_arguments(self, parser):
        parser.add_argument('errors_dir', nargs='+', type=str, help="The directory path for static error pages. (E.g. /var/www/knotters/errors/)")

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
            oldversion = ".".join(
                [oldversion[0], oldversion[1], oldversion[2]])
        return oldversion

    def handle(self, *args, **options):
        __STATIC_ROOT_VERSION = list(
            filter(lambda x: x != "", settings.STATIC_ROOT.split("/")))[-1]

        __SUCCESS = False

        if __STATIC_ROOT_VERSION != VERSION:
            print("VERSION:", VERSION)
            print("STATIC_ROOT_VERSION:", __STATIC_ROOT_VERSION)
            print("STATIC_ROOT:", settings.STATIC_ROOT)
            raise Exception("Mismatch STATIC_ROOT VERSION & main VERSION")
        else:
            print("\nCLEARING OBSOLETE STATICS (VERSION < 2)\n")
            if not (Path(settings.STATIC_ROOT).exists() and Path(settings.STATIC_ROOT).is_dir()):
                raise Exception(
                    f"PANIC: STATIC_ROOT doesn't exist! : {settings.STATIC_ROOT}\nForgot to run collectstatic perhaps?")
            __MORE_OLD = True
            __OLD_STATIC_ROOT_VERSION = self.decrease_version(
                __STATIC_ROOT_VERSION, by=2)
            __OLD_STATIC_ROOT = settings.STATIC_ROOT.replace(
                __STATIC_ROOT_VERSION, __OLD_STATIC_ROOT_VERSION)
            while __MORE_OLD:
                print("OLD_STATIC_VERSION:", __OLD_STATIC_ROOT_VERSION)
                print("OLD STATIC_ROOT:", __OLD_STATIC_ROOT)
                __OLD_STATIC_ROOT_PATH = Path(__OLD_STATIC_ROOT)
                if __OLD_STATIC_ROOT_PATH.exists() and __OLD_STATIC_ROOT_PATH.is_dir() and __OLD_STATIC_ROOT_PATH != settings.STATIC_ROOT:
                    print("OLD STATIC_ROOT REMOVING: ", __OLD_STATIC_ROOT_PATH)
                    rmtree(__OLD_STATIC_ROOT_PATH)
                    print("OLD STATIC_ROOT REMOVED: ", __OLD_STATIC_ROOT_PATH)
                    __N_OLD_STATIC_ROOT_VERSION = self.decrease_version(
                        __OLD_STATIC_ROOT_VERSION, by=1)
                    __OLD_STATIC_ROOT = __OLD_STATIC_ROOT.replace(
                        __OLD_STATIC_ROOT_VERSION, __N_OLD_STATIC_ROOT_VERSION)
                    __OLD_STATIC_ROOT_VERSION = __N_OLD_STATIC_ROOT_VERSION
                else:
                    __MORE_OLD = False
                    print("STATIC_ROOT STOPPED: ", __OLD_STATIC_ROOT_PATH)
                    __LAST_STATIC_ROOT = settings.STATIC_ROOT.replace(
                        __STATIC_ROOT_VERSION,  self.decrease_version(__STATIC_ROOT_VERSION, by=1))
                    if not (Path(__LAST_STATIC_ROOT).exists() and Path(__LAST_STATIC_ROOT).is_dir()):
                        print(
                            f"WARNING: LAST_STATIC_ROOT doesn't exist : {__LAST_STATIC_ROOT}")
                    else:
                        print("LAST_STATIC_ROOT RETAINED: ", __LAST_STATIC_ROOT)
                    print("STATIC_ROOT RETAINED: ", settings.STATIC_ROOT)
                    __SUCCESS = True

        if __SUCCESS and Path(settings.STATIC_ROOT).exists() and Path(settings.STATIC_ROOT).is_dir():
            print("\nLINKING EMAIL ASSETS WITH LATEST STATIC VERSION\n")
            __STATIC_EMAIL_LNROOT = settings.STATIC_ROOT.replace(
                __STATIC_ROOT_VERSION, 'email')
            __STATIC_EMAIL_LN_TARGET = ospath.join(
                settings.STATIC_ROOT, 'graphics/email/')
            print("EMAIL STATIC LNROOT: ", __STATIC_EMAIL_LNROOT)

            if not (Path(__STATIC_EMAIL_LN_TARGET).exists() and Path(__STATIC_EMAIL_LN_TARGET).is_dir()):
                print("NEW EMAIL STATIC TARGET EMPTY: ",
                      __STATIC_EMAIL_LN_TARGET)
                print("RETAINING LN OLD EMAIL STATIC TARGET")
            else:
                print("LINKING NEW EMAIL STATIC TARGET: ",
                      __STATIC_EMAIL_LN_TARGET)

                __STATIC_EMAIL_LNROOT_PATH = Path(__STATIC_EMAIL_LNROOT)
                if __STATIC_EMAIL_LNROOT_PATH.exists() and __STATIC_EMAIL_LNROOT_PATH.is_dir():
                    try:
                        print("REMOVING OLD STATIC LNROOT: ",
                              __STATIC_EMAIL_LNROOT_PATH)
                        remove(__STATIC_EMAIL_LNROOT_PATH)
                        print("REMOVED OLD STATIC LNROOT")
                    except Exception as e:
                        print("REMOVE OLD STATIC LNROOT ERR: ",
                              __STATIC_EMAIL_LNROOT_PATH)
                        print(e)
                        print("PROCEEDING EMAIL STATIC LINK W: ",
                              __STATIC_EMAIL_LN_TARGET)
                        pass
                else:
                    try:
                        print("REMOVING OLD STATIC LNROOT (INEXISTENT|NONDIR): ",
                              __STATIC_EMAIL_LNROOT_PATH)
                        remove(__STATIC_EMAIL_LNROOT_PATH)
                        print("REMOVED OLD STATIC LNROOT (INEXISTENT|NONDIR)")
                    except Exception as e:
                        print("REMOVE OLD STATIC LNROOT ERR (INEXISTENT|NONDIR): ",
                              __STATIC_EMAIL_LNROOT_PATH)
                        print(e)
                        print("PROCEEDING EMAIL STATIC LINK W: ",
                              __STATIC_EMAIL_LN_TARGET)
                        pass
                try:
                    print("LINKING NEW STATIC LNROOT")
                    symlink(__STATIC_EMAIL_LN_TARGET,
                            __STATIC_EMAIL_LNROOT_PATH)
                    print("DONE LINKING NEW STATIC LNROOT: ",
                          __STATIC_EMAIL_LN_TARGET)
                except Exception as e:
                    print("LINKING NEW STATIC LNROOT ERR: ",
                          __STATIC_EMAIL_LNROOT_PATH)
                    print(e)

                if __STATIC_EMAIL_LNROOT_PATH.exists() and __STATIC_EMAIL_LNROOT_PATH.is_dir():
                    print("EMAIL STATIC LNROOT EXISTS: ",
                          __STATIC_EMAIL_LNROOT_PATH)
                else:
                    print("PANIC: EMAIL STATIC LNROOT NOT EXIST: ",
                          __STATIC_EMAIL_LNROOT_PATH)

            print("\nLINKING CDN ASSETS WITH LATEST STATIC VERSION\n")
            __STATIC_CDN_LNROOT = settings.STATIC_ROOT.replace(
                __STATIC_ROOT_VERSION, 'cdn')
            __STATIC_CDN_LN_TARGET = ospath.join(settings.STATIC_ROOT)
            print("CDN STATIC LNROOT: ", __STATIC_CDN_LNROOT)

            if not (Path(__STATIC_CDN_LN_TARGET).exists() and Path(__STATIC_CDN_LN_TARGET).is_dir()):
                print("NEW CDN STATIC TARGET EMPTY: ", __STATIC_CDN_LN_TARGET)
                print("RETAINING LN OLD CDN STATIC TARGET")
            else:
                print("LINKING NEW CDN STATIC TARGET: ", __STATIC_CDN_LN_TARGET)

                __STATIC_CDN_LNROOT_PATH = Path(__STATIC_CDN_LNROOT)
                if __STATIC_CDN_LNROOT_PATH.exists() and __STATIC_CDN_LNROOT_PATH.is_dir():
                    try:
                        print("REMOVING OLD STATIC LNROOT: ",
                              __STATIC_CDN_LNROOT_PATH)
                        remove(__STATIC_CDN_LNROOT_PATH)
                        print("REMOVED OLD STATIC LNROOT")
                    except Exception as e:
                        print("REMOVE OLD STATIC LNROOT ERR: ",
                              __STATIC_CDN_LNROOT_PATH)
                        print(e)
                        print("PROCEEDING CDN STATIC LINK W: ",
                              __STATIC_CDN_LN_TARGET)
                        pass
                else:
                    try:
                        print(
                            "REMOVING OLD STATIC LNROOT (INEXISTENT|NONDIR): ", __STATIC_CDN_LNROOT_PATH)
                        remove(__STATIC_CDN_LNROOT_PATH)
                        print("REMOVED OLD STATIC LNROOT (INEXISTENT|NONDIR)")
                    except Exception as e:
                        print(
                            "REMOVE OLD STATIC LNROOT ERR (INEXISTENT|NONDIR): ", __STATIC_CDN_LNROOT_PATH)
                        print(e)
                        print("PROCEEDING CDN STATIC LINK W: ",
                              __STATIC_CDN_LN_TARGET)
                        pass
                try:
                    print("LINKING NEW STATIC LNROOT")
                    symlink(__STATIC_CDN_LN_TARGET, __STATIC_CDN_LNROOT_PATH)
                    print("DONE LINKING NEW STATIC LNROOT: ",
                          __STATIC_CDN_LN_TARGET)
                except Exception as e:
                    print("LINKING NEW STATIC LNROOT ERR: ",
                          __STATIC_CDN_LNROOT_PATH)
                    print(e)

                if __STATIC_CDN_LNROOT_PATH.exists() and __STATIC_CDN_LNROOT_PATH.is_dir():
                    print("CDN STATIC LNROOT EXISTS: ",
                          __STATIC_CDN_LNROOT_PATH)
                else:
                    print("PANIC: CDN STATIC LNROOT NOT EXIST: ",
                          __STATIC_CDN_LNROOT_PATH)
        else:
            print("STATIC ROOT NOT EXIST: ", settings.STATIC_ROOT, __SUCCESS)

        print("\nGENERATING STATIC ERROR PAGES\n")
        err_dir = Path(options['errors_dir'][0])
        if not err_dir.exists():
            mkdir(err_dir)
        print("ERR DIR: ", err_dir)
        notfoundstr = render_to_string('404.html', renderData(
            dict(**GlobalContextData, csrf_token=" ", SCRIPTS=Template.Script.getAllKeys())))
        notfoundstr = html_minify(notfoundstr.replace(
            settings.STATIC_URL, 'https://cdn.knotters.org/').replace('href=\"/', f'href=\"{SITE}/'))
        notfoundpath = ospath.join(err_dir, '40x.html')
        print("404 PATH: ", notfoundpath)
        with open(notfoundpath, 'w+') as file:
            file.write(notfoundstr)
        print("404 PATH DONE: ", notfoundpath)
        servererrorstr = render_to_string('50x.html', renderData(
            dict(**GlobalContextData, csrf_token=" ", SCRIPTS=Template.Script.getAllKeys())))
        servererrorstr = html_minify(servererrorstr.replace(
            settings.STATIC_URL, 'https://cdn.knotters.org/').replace('href=\"/', f'href=\"{SITE}/'))
        servererrpath = ospath.join(err_dir, '50x.html')
        print("500 PATH: ", servererrpath)
        with open(servererrpath, 'w+') as file:
            file.write(servererrorstr.replace('\n', '').strip())
        print("500 PATH DONE: ", servererrpath)

        print("\nDONE", __SUCCESS and Path(settings.STATIC_ROOT).exists()
              and Path(settings.STATIC_ROOT).is_dir())

        print("COMPRESSING: ", settings.STATIC_ROOT)
        if __SUCCESS and Path(settings.STATIC_ROOT).exists() and Path(settings.STATIC_ROOT).is_dir():
            print("COMPRESSING STATIC ROOT: ", settings.STATIC_ROOT)
            try:
                print("COMPRESSING STATIC ROOT: ", settings.STATIC_ROOT)
                compress(settings.STATIC_ROOT)
                print("COMPRESSED STATIC ROOT: ", settings.STATIC_ROOT)
            except Exception as e:
                print("COMPRESS STATIC ROOT ERR: ", settings.STATIC_ROOT)
                print(e)
                pass


def compress(path):
    """
    Compress all files in a directory
    """
    if Path(path).exists() and Path(path).is_dir():
        for root, dirs, files in walk(path):
            for file in files:
                if file.endswith('.css'):
                    filepath = ospath.join(root, file)
                    print("COMPRESSING: ", filepath)
                    try:
                        with open(filepath, "r") as f:
                            fdata = f.read()
                        compressedfdata = cssmin(fdata)
                        with open(filepath, "w") as f:
                            f.write(compressedfdata)
                    except Exception as e:
                        print("COMPRESS CSS ERR: ", filepath)
                        print(e)
                        print("PROCEEDING WITH COMPRESSION")
                        pass
                elif file.endswith('.js'):
                    filepath = ospath.join(root, file)
                    print("COMPRESSING: ", filepath)
                    try:
                        with open(filepath, "r") as f:
                            fdata = f.read()
                        compressedfdata = jsmin(fdata)
                        with open(filepath, "w") as f:
                            f.write(compressedfdata)
                    except Exception as e:
                        print("COMPRESS JS ERR: ", filepath)
                        print(e)
                        print("PROCEEDING WITH COMPRESSION")
                        pass
                elif file.endswith('.json'):
                    filepath = ospath.join(root, file)
                    print("COMPRESSING: ", filepath)
                    try:
                        with open(filepath, "r") as f:
                            fdata = f.read()
                        compressedfdata = jsondumps(
                            jsonloads(fdata), separators=(',', ':'))
                        with open(filepath, "w") as f:
                            f.write(compressedfdata)
                    except Exception as e:
                        print("COMPRESS JSON ERR: ", filepath)
                        print(e)
                        print("PROCEEDING WITH COMPRESSION")
                        pass
                else:
                    print("SKIPPING: ", ospath.join(root, file))
                    pass
    else:
        print("NOT A DIR: ", path)
        pass
