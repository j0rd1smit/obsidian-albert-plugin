# -*- coding: utf-8 -*-

"""This is a simple python template extension.

This extension should show the API in a comprehensible way. Use the module docstring to provide a \
description of the extension. The docstring should have three paragraphs: A brief description in \
the first line, an optional elaborate description of the plugin, and finally the synopsis of the \
extension.

Synopsis: <trigger> [delay|throw] <query>"""

from albert import *
import os
from time import sleep
from pathlib import Path
import sys
import Levenshtein as lev


__title__ = "Obsidian"
__version__ = "0.0.0"
__triggers__ = "ob "
__authors__ = "J0rd1smit"
__exec_deps__ = []
__py_deps__ = []

iconPath = iconLookup("albert")

vault_path = Path("/home/jordi/Dropbox/obsidian")
vault_name = "obsidian"


# Can be omitted
def initialize():
    pass


# Can be omitted
def finalize():
    pass


def handleQuery(query):
    if not query.isTriggered:
        return
    
    query_text = query.string.lower()
    items = []
    max_n_matches = 0

    for path in vault_path.rglob("*.md"):
        n_matches = _n_matches(path, query_text)

        path_rel_to_value = str(path).replace(str(vault_path), "")
        action = UrlAction(
            text="UrlAction",
            url=f"obsidian://open?vault={vault_name}&file={path_rel_to_value.replace(' ', '%20')}",
        )
        item = Item(id=__title__,
            icon=os.path.dirname(__file__)+"/plugin.png",
            text=path.name,
            subtext=path_rel_to_value,
            actions=[action],
        )
        items.append((item, n_matches))
        max_n_matches = max(max_n_matches, n_matches)



    n_matches = _n_matches("quick add", query_text)
    action = UrlAction(
        text="UrlAction",
        url=f"obsidian://advanced-uri?commandname=QuickAdd%3A%20Run%20QuickAdd",
    )
    item = Item(id=__title__,
        icon=os.path.dirname(__file__)+"/plugin.png",
        text="Quick Add",
        subtext="",
        actions=[action],
    )
    items.append((item, n_matches))
    max_n_matches = max(max_n_matches, n_matches)

           


    return [i[0] for i in items if i[1] == max_n_matches]

def _n_matches(path, query):
    matches = 0
    for search_key in query.split(" "):
        if search_key in str(path).lower():
            matches += 1

    return matches