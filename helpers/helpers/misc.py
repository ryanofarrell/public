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

# %%
