# %% Imports
from collections import defaultdict
import json
import os
import re
import yaml
from helpers import getRelativeFp

# %% Constants
nChar = 50  # Number of characters in snippet before and after
PATH = "/Users/ryanofarrell/projects/public/docs/_mindmap/"
MINDMAPPATTERN = re.compile("\{\% ?include mindmap-link .*? ?\%\}")

# Create blank file
def getBlankFile(title):
    out = f"""---
title: {title}
layout: mindmap-concept
---
"""

    return out


# %% Parse files
concepts = [f for f in os.listdir(PATH) if f[-3:] == ".md"]

print(concepts)

p = re.compile("---([\s\S]*)---([\s\S]*)\Z")
data = {}
for f in concepts:
    with open(PATH + f) as file:
        fileData = file.read()
        front = yaml.load(p.match(fileData).group(1), Loader=yaml.Loader)
        contents = p.match(fileData).group(2)
        data[front["title"]] = {"front": front, "contents": contents, "url": f[:-3]}


def replaceAllLinksWithText(s: str, bolded: bool = False) -> str:
    "Replaces the mindmap link patters with the text from that pattern, optionally <b></b>"

    textP = re.compile("text=[\x27\x22](.*)[\x27\x22]", flags=re.U)
    newS = s

    for link in MINDMAPPATTERN.finditer(s):
        newText = "[[" + textP.findall(link.group())[0] + "]]"
        if bolded:
            newText = f"<b>{newText}</b>"

        newS = newS.replace(link.group(), newText)
    return newS


# %% parse through data
mindmap = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

for fromTitle, details in data.items():
    fromUrl = f"/mindmap/{details['url']}"

    for link in MINDMAPPATTERN.finditer(details["contents"]):
        # Find newlines before and after the link,
        preChars = details["contents"][: link.start()].rfind("\n") + 1
        postChars = details["contents"][link.end() :].find("\n")
        if postChars == -1:
            postChars = len(details["contents"])

        # Replace pre-link, link (bolded), and post-link with text from link
        preLink = details["contents"][preChars : link.start()]
        postLink = details["contents"][link.end() : link.end() + postChars]
        snippet = replaceAllLinksWithText(preLink)
        snippet += replaceAllLinksWithText(link.group(), bolded=True)
        snippet += replaceAllLinksWithText(postLink)

        # Get the toFile
        toFile = None
        urlP = re.compile("url=[\x27\x22](.*?)[\x27\x22]", flags=re.U)
        foundUrls = urlP.findall(link.group())
        if len(foundUrls) != 0:
            toFile = foundUrls[0][9:]

        conceptP = re.compile("concept=[\x27\x22](.*?)[\x27\x22]", flags=re.U)
        foundConcepts = conceptP.findall(link.group())
        if len(foundConcepts) != 0:
            toFile = foundConcepts[0]
        if toFile == None:
            raise ValueError(f"No file found in match: {link.group()}!")

        mindmap[toFile][fromTitle]["fromUrl"] = fromUrl
        mindmap[toFile][fromTitle]["snippets"].append(snippet)

        # If toFile does not exist, create placeholder
        if f"{toFile}.md" not in concepts:
            print(f"New concept: {toFile}, creating file!")
            with open(f"{PATH}{toFile}.md", "w") as outfile:
                outfile.write(getBlankFile(toFile))


# %% jsonify
with open(getRelativeFp(PATH, "../_data/mindmap.json", False), "w") as outfile:
    json.dump(mindmap, outfile)
# %%
