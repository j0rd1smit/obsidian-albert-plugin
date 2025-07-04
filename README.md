# Obsidian-albert-plugin

![Screenshot](example.png)

A simple plugin that makes it possible to search your [Obsidian](https://obsidian.md/) vault.

## Features

- Search your Obsidian vault based on paths of your note
- Use fuzzy search for easier searchability
- UTF-8 support for searches
- Add custom command using built-in URIs or the Advanced URIs plugin
- Ability to define arbitrary external commands

## Setup

This plugin requires `fd` (`fd-find` on Debian distributions) and `fzf` to be installed.

Before installing the plugin, make sure that the Albert Python plugin is enabled.

### Download code

```bash
git clone https://github.com/masasin/obsidian-albert-plugin.git ~/.local/share/albert/python/plugins/obsidian

```

### Enable plugin

Start up Albert and go to the settings page. On the settings page, go to “Extensions > Python > Obsidian” and enable the Obsidian plugin.

### Configure

An example configuration file should appear at `~/.config/albert/python.obsidian/config.json` after you have enabled the plugin. In this configuration file, you **must** specify the following:
- **vault_name**: This is the name of your Obsidian folder.
- **path_to_vault**: The absolute path to your vault.

Optionally, you can also add additional commands under `commands`. These commands call specific obsidian URI that preform certain action in your vault. For more information about the available URI in obsidian, see [uing obsidian URI(https://help.obsidian.md/Advanced+topics/Using+obsidian+URI) and [advanced Obsidian URI plugin](https://github.com/Vinzent03/obsidian-advanced-uri).

Here is an example configuration file for reference

```json
{
    "vault_name": "notes",
    "path_to_vault": "/path/to/notes",
    "commands": [
        {
            "name": "nn",
            "description": "Add a new note to the vault",
            "uri": "obsidian://new?vault={vault_name}&name={q}"
        },
        {
            "name": "l",
            "description": "Log to daily note",
            "uri": "obsidian://advanced-uri?vault={vault_name}&daily=true&data=-%20{q}&mode=append&heading=Log"
        },
        {
            "name": "c",
            "description": "Append clipboard to daily note",
            "uri": "obsidian://advanced-uri?vault={vault_name}&daily=true&data=-%20{{xclip -o}}&mode=append&heading=Notes"
        }
    ]
}
```

# Credit

The original plugin was created by J0rd1smit. It was modified to Alfred's new API by Jean Nassar, and improved with various new features.
