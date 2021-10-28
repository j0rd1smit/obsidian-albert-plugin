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
import json

__title__ = "Obsidian"
__version__ = "0.0.1"
__triggers__ = "ob "
__authors__ = "J0rd1smit"
__exec_deps__ = []
__py_deps__ = []

PATH_TO_CONFIG_FOLDER = Path.home() / ".config/albert/obsidian-plugin"
PATH_TO_CONFIG_DATA = PATH_TO_CONFIG_FOLDER / "config.json"
PATH_TO_ICON = os.path.dirname(__file__) + "/plugin.png"

iconPath = iconLookup("albert")


def initialize():
    PATH_TO_CONFIG_FOLDER.mkdir(parents=True, exist_ok=True)

    if not PATH_TO_CONFIG_DATA.exists():
        _create_default_config()

            
def _create_default_config():
    with open(PATH_TO_CONFIG_DATA, "w") as f:
        data = {
            "vault_name": "obsidian",
            "path_to_vault": str(Path.home() / "obsidian"),
            "commands": [
                {
                    "name": "New note",
                    "subtext": "Add a new note to the vault",
                    "uri": "obsidian://new?vault=REPLACE_WITH_VAULT_NAME&name={{q}}"
                }
            ],
        }
        json.dump(data, f, indent=4)


def handleQuery(query):
    if not query.isTriggered:
        return
    
    query_text = query.string.lower()

    with open(PATH_TO_CONFIG_DATA) as f:
        config = json.load(f)

    vault_name = config["vault_name"]
    path_to_vault = Path(config["path_to_vault"])
    commands = config["commands"]

    item_ranking_pairs = []
    max_ranking = 0

    for path in path_to_vault.rglob("*.md"):
        item, ranking = create_open_note_item(vault_name, path_to_vault, path, query_text)

        max_ranking = max(max_ranking, ranking)
        item_ranking_pairs.append((item, ranking))


    for command in commands:
        item, ranking = create_uri_item(query_text, command)
        max_ranking = max(max_ranking, ranking)
        item_ranking_pairs.append((item, ranking))

    return [item for (item, ranking) in item_ranking_pairs if ranking == max_ranking]

def create_open_note_item(
        vault_name,
        path_to_vault, 
        path_to_file,
        query,
    ):
    path_rel_to_vault = str(path_to_file).replace(str(path_to_vault), "")
    path_rel_to_vault_encoded = to_uri_encoding(path_rel_to_vault)

    action = UrlAction(
        text="UrlAction",
        url=f"obsidian://open?vault={vault_name}&file={path_rel_to_vault_encoded}",
    )
    item = Item(
        id=__title__,
        icon=PATH_TO_ICON,
        text=path_to_file.name,
        subtext=path_rel_to_vault,
        actions=[action],
    )

    return item, _n_matches(path_rel_to_vault, query)

def to_uri_encoding(s):
    return s.replace(' ', '%20').replace("/", "%2F")


def _n_matches(key, query):
    key = key.lower()
    matches = 0
    for search_key in query.split(" "):
        if search_key in key:
            matches += 1

    return matches


def create_uri_item(
        query,
        uri_config,
    ):
    
    name = uri_config["name"]
    subtext = uri_config["subtext"]
    uri_template = uri_config["uri_template"]

    q = query.lower()
    for i in name.lower().split():
        q = q.replace(i, "")


    action = UrlAction(
        text="UrlAction",
        url=uri_template.replace("{{q}}", to_uri_encoding(q)),
    )
    item = Item(id=__title__,
        icon=PATH_TO_ICON,
        text=name,
        subtext=subtext,
        actions=[action],
    )
    key = name
    if len(subtext) > 0:
        key = " " + subtext

    return item, _n_matches(key, query)

