# %% Imports
from collections import defaultdict
import json
import os
import re
from typing import DefaultDict
import yaml
from helpers import getRelativeFp

# %% Constants
nChar = 50  # Number of characters in snippet before and after
# %% Parse files
concepts = [f for f in os.listdir() if f[-3:] == ".md"]

p = re.compile("---([\s\S]*)---([\s\S]*)\Z")
data = {}
for f in concepts:
    with open(f) as file:
        fileData = file.read()
        front = yaml.load(p.match(fileData).group(1), Loader=yaml.Loader)
        contents = p.match(fileData).group(2)
        data[front["title"]] = {"front": front, "contents": contents, "url": f[:-3]}


# %% parse through data
p = re.compile("\{\% include mindmap-link .* \%\}")
outList = []
mindmap = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

for fromTitle, details in data.items():
    fromUrl = f"/mindmap/{details['url']}"

    for link in p.finditer(details["contents"]):
        prevNewline = details["contents"][: link.start()].rfind("\n") + 1
        nextNewLine = link.end() + details["contents"][link.end() :].find("\n")
        if nextNewLine == 0:
            nextNewLine = len(details["contents"])
        snippet = details["contents"][prevNewline:nextNewLine]
        # Get text from match
        textP = re.compile("text=[\x27\x22](.*)[\x27\x22]", flags=re.U)
        replacedSnippet = details["contents"][prevNewline : link.start()]
        replacedSnippet += "<b>" + textP.findall(link.group())[0] + "</b>"
        replacedSnippet += details["contents"][link.end() : nextNewLine]

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

        # mindmap[toFile]["toFile"] = toFile
        print(f"{fromTitle} -> {toFile}: {replacedSnippet}")

        mindmap[toFile][fromTitle]["fromUrl"] = fromUrl
        mindmap[toFile][fromTitle]["snippets"].append(replacedSnippet)

        # mindmap[toTitle][fromTitle]["links"].append(replacedSnippet)

# toTitle:
#   fromTitle:
#       fromLink:
#       links:
#           [snippet, snippet]

# %% jsonify
with open(getRelativeFp(__file__, "../_data/mindmap.json"), "w") as outfile:
    json.dump(mindmap, outfile)
# %%
