# %% Imports
import logging
import os
import functools

from datetime import datetime as dt


# %% Misc helpers
def getRelativeFp(fileDunder: str, pathToAppend: str, upOneLevel: bool = True) -> str:
    """Takes a __file__ and a relative path and returns an absolute path.
    If path navigates to a folder that does not yet exists, creates the folder.

    Args:

        fileDunder (str) -- easiest to pass just __file__

        pathToAppend (str) -- relative path to append. Handles goinf up levels with ../

        upOneLevel (bool) -- Go up one level initially. Defaults to True.
        Change to false if passing file path and not an actual file.

    Returns

        str -- absolute path to folder
    """

    import os
    import pathlib

    if upOneLevel:
        fileParentPath = pathlib.Path(fileDunder).parent.absolute()
    else:
        fileParentPath = fileDunder

    newFilePath = os.path.join(fileParentPath, pathToAppend)
    fpParent = pathlib.Path(newFilePath).parent.absolute()
    if not os.path.exists(fpParent):
        os.makedirs(fpParent)
        print(f"Created directory {fpParent}")
    return newFilePath


# Add imagepath as a constant
IMAGEPATH = "/Users/ryanofarrell/projects/public/docs/assets/images/"


# %% Logger
class logger:
    "Logger class"

    def __init__(self, fp, fileLevel, consoleLevel, removeOldFile=False, name="myCustomLogger"):
        format = "%(asctime)s | %(levelname)s | %(message)s"
        if consoleLevel < fileLevel:
            print("Min level set in fileLevel; console will not go lower!")

        if removeOldFile:
            try:
                os.remove(fp)
            except FileNotFoundError:
                # If file exists, do nothing
                pass

        # File logging
        logging.basicConfig(filename=fp, level=fileLevel, format=format)

        # Console Printing
        console = logging.StreamHandler()
        console.setLevel(consoleLevel)
        console.setFormatter(logging.Formatter(format))
        logging.getLogger().addHandler(console)

    def debug(self, message):
        logging.debug(message)

    def info(self, message):
        logging.info(message)

    def warning(self, message):
        logging.warning(message)

    def error(self, message):
        logging.error(message)

    def critical(self, message):
        logging.critical(message)

    def timeFuncInfo(self, fn):
        @functools.wraps(fn)
        def decorated(*args, **kwargs):
            try:
                now = dt.now()
                logging.info(f"Fn | {fn.__name__} | Begin")
                result = fn(*args, **kwargs)
                logging.info(f"Fn | {fn.__name__} | Complete | {dt.now() - now}")
                return result
            except Exception as ex:
                logging.critical(f"Exception {ex}")
                raise ex

        return decorated
