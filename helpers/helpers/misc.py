# %% Misc helpers
def getRelativeFp(fileDunder: str, pathToAppend: str) -> str:
    """Takes a __file__ and a relative path and returns an absolute path.
    If path navigates to a folder that does not yet exists, creates the folder.

    Args:

        fileDunder (str) -- easiest to pass just __file__

        pathToAppend (str) -- relative path to append. Handles goinf up levels with ../

    Returns

        str -- absolute path to folder
    """

    import os
    import pathlib

    fileParentPath = pathlib.Path(fileDunder).parent.absolute()
    newFilePath = os.path.join(fileParentPath, pathToAppend)
    fpParent = pathlib.Path(newFilePath).parent.absolute()
    if not os.path.exists(fpParent):
        os.makedirs(fpParent)
        print(f"Created directory {fpParent}")
    return newFilePath
