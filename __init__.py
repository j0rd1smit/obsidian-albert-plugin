# -*- coding: utf-8 -*-
# Albert Obsidian Plugin
#
# Requires fd and fzf for search.
# 
# > ob <file>
# 
# Configuration in ~/.config/albert/python.obsidian/config.json
#

import json
import re
import shlex
import subprocess
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import quote

from albert import *

md_iid = "3.0"
md_version = "0.5.1"
md_name = "Obsidian"
md_description = "Search your Obsidian vault and execute commands"
md_license = "MIT"
md_url = "https://github.com/albertlauncher/albert"
md_authors = ["J0rd1smit", "Jean Nassar"]

@dataclass
class Command:
    """Represents a single, simplified command from the configuration."""
    name: str
    description: str
    uri: str

    @classmethod
    def from_dict(cls, data: Dict) -> "Command":
        """Creates a Command instance from a dictionary with safe defaults."""
        return cls(
            name=data.get("name", "Unknown Command"),
            description=data.get("description", "No description provided."),
            uri=data.get("uri", ""),
        )

class ConfigManager:
    """Handles loading, validation, and access to the plugin's configuration."""

    def __init__(self, config_path: Path):
        self.config_path = config_path
        self._config_data: Optional[Dict] = None
        self._ensure_default_config_exists()

    def _ensure_default_config_exists(self):
        """Creates a default configuration file if one does not exist."""
        if self.config_path.exists():
            return
        default_config = {
            "vault_name": "obsidian",
            "path_to_vault": str(Path.home() / "obsidian"),
            "commands": [
                {
                    "name": "nn",
                    "description": "Create a new note in the vault",
                    "uri": "obsidian://new?vault={vault_name}&name={q}",
                },
                {
                    "name": "c",
                    "description": "Append clipboard to daily note",
                    "uri": "obsidian://advanced-uri?vault={vault_name}&daily=true&data=-%20{{xclip -o -selection clipboard}}&mode=append&heading=Notes",
                },
            ],
        }
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with self.config_path.open("w", encoding="utf-8") as f:
                json.dump(default_config, f, indent=4)
        except (IOError, OSError) as e:
            critical(f"Failed to create default config at {self.config_path}: {e}")

    def _load_config(self) -> Dict:
        """Loads configuration from the JSON file, with error handling."""
        if self._config_data is None:
            try:
                with self.config_path.open("r", encoding="utf-8") as f:
                    self._config_data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError, OSError) as e:
                critical(f"Obsidian plugin configuration error: {e}")
                self._config_data = {}
        return self._config_data

    @property
    def vault_name(self) -> str:
        return self._load_config().get("vault_name", "")

    @property
    def vault_path(self) -> Path:
        return Path(self._load_config().get("path_to_vault", ""))

    @property
    def commands(self) -> List[Command]:
        command_list = self._load_config().get("commands", [])
        return [Command.from_dict(c) for c in command_list]


class Plugin(PluginInstance, TriggerQueryHandler):
    def __init__(self):
        PluginInstance.__init__(self)
        TriggerQueryHandler.__init__(self)

        self.icon_path = f"file:{Path(__file__).parent}/obsidian.png"
        self.config = ConfigManager(self.configLocation() / "config.json")

    def defaultTrigger(self) -> str:
        return "ob "

    def handleTriggerQuery(self, query: Query):
        """Main handler for all queries, dispatching to sub-handlers."""
        vault_path = self.config.vault_path
        if not vault_path.is_dir():
            query.add(
                self._create_error_item(
                    "Vault Path Not Found",
                    f"Check config: '{vault_path}' does not exist or is not a directory.",
                )
            )
            return

        query_string_norm = unicodedata.normalize('NFC', query.string.strip()).casefold()

        if not query_string_norm:
            query.add([self._create_command_item(cmd) for cmd in self.config.commands])
            return

        if command_item := self._handle_command_query(query_string_norm, query.string.strip()):
            query.add(command_item)
            return

        results = self._handle_search_query(query_string_norm, vault_path)
        if results:
            query.add(results)
            return
            
        search_url = f"obsidian://search?vault={quote(self.config.vault_name)}&query={quote(query.string.strip())}"
        fallback_item = StandardItem(
            id=self.id(),
            text=f"Search for '{query.string.strip()}' in Obsidian",
            subtext="No local file path matches found. Press Enter to search.",
            iconUrls=[self.icon_path],
            actions=[Action("search", "Search", lambda u=search_url: openUrl(u))],
        )
        query.add(fallback_item)

    def _handle_command_query(self, query_norm: str, query_raw: str) -> Optional[Item]:
        """Check if the query matches a command and return the appropriate item."""
        for command in self.config.commands:
            cmd_name_norm = unicodedata.normalize('NFC', command.name).casefold()
            if query_norm == cmd_name_norm or query_norm.startswith(f"{cmd_name_norm} "):
                argument = query_raw[len(command.name):].strip()
                return self._create_command_item(command, argument)
        return None

    def _handle_search_query(self, query_norm: str, vault_path: Path) -> List[Item]:
        """Performs a fuzzy search by piping the output of `fd` into `fzf`."""
        if not query_norm:
            return []
        try:
            fd_command = ['fd', '--extension', 'md', '.', str(vault_path)]
            p_fd = subprocess.Popen(fd_command, stdout=subprocess.PIPE, cwd=str(vault_path))
            fzf_command = ['fzf', '--filter', query_norm]
            p_fzf = subprocess.Popen(
                fzf_command, stdin=p_fd.stdout, stdout=subprocess.PIPE, text=True, encoding='utf-8'
            )
            if p_fd.stdout:
                p_fd.stdout.close()
            stdout, _ = p_fzf.communicate()
            if p_fzf.returncode > 1:
                raise subprocess.CalledProcessError(p_fzf.returncode, fzf_command, stdout)
            results = []
            for rel_path_str in stdout.splitlines():
                full_path_obj = vault_path / Path(rel_path_str)
                results.append(self._create_note_item(full_path_obj, vault_path))
            return results
        except FileNotFoundError as e:
            tool_name = "'fd'" if e.filename == "fd" else "'fzf'"
            return [self._create_error_item(f"{tool_name} Not Found", "Please install it to use this plugin.")]
        except subprocess.CalledProcessError as e:
            warning(f"Fuzzy search command failed: {e}")
            return []

    def _process_uri(self, uri_template: str, argument: Optional[str]) -> str:
        """Builds the final URI by substituting placeholders and executing shell commands."""
        uri = uri_template.replace("{vault_name}", quote(self.config.vault_name))
        if argument is not None:
            uri = uri.replace("{q}", quote(argument.encode('utf-8')))

        def execute_placeholder(match: re.Match) -> str:
            command_str = match.group(1)
            try:
                # Use shlex for robust command parsing
                command_to_run = shlex.split(command_str)
                result = subprocess.run(
                    command_to_run, capture_output=True, check=True, text=True, encoding='utf-8'
                )
                return quote(result.stdout.strip())
            except FileNotFoundError:
                warning(f"Shell command '{command_str}' not found in URI template.")
                return ""
            except subprocess.CalledProcessError as e:
                warning(f"Shell command '{command_str}' failed: {e.stderr}")
                return ""
            except ValueError:
                warning(f"Shell command '{command_str}' has unclosed quotes.")
                return ""

        # Use new `{{command}}` syntax
        return re.sub(r'{{(.*?)}}', execute_placeholder, uri)

    def _create_note_item(self, file_path: Path, vault_path: Path) -> Item:
        """Builds a StandardItem for a note search result."""
        rel_path = file_path.relative_to(vault_path)
        encoded_file_path = quote(str(rel_path).encode('utf-8'), safe='/')
        url = f"obsidian://open?vault={quote(self.config.vault_name)}&file={encoded_file_path}"
        return StandardItem(
            id=str(file_path),
            text=file_path.stem,
            subtext=str(rel_path.parent) if str(rel_path.parent) != '.' else 'Vault Root',
            iconUrls=[self.icon_path],
            actions=[Action("open-note", "Open Note", lambda u=url: openUrl(u))]
        )

    def _create_command_item(self, command: Command, argument: Optional[str] = None) -> Item:
        """Builds an item for a command, either as a prompt or an executable action."""
        needs_argument = "{q}" in command.uri
        if needs_argument and not argument:
            return StandardItem(
                id=f"prompt_{command.name}",
                text=command.name,
                subtext=command.description,
                iconUrls=[self.icon_path],
                inputActionText=f"{command.name} ",
            )
        
        final_uri = self._process_uri(command.uri, argument)
        item_text = f"{command.name}: {argument}" if argument else command.name
        return StandardItem(
            id=f"cmd_{command.name}",
            text=item_text,
            subtext=command.description,
            iconUrls=[self.icon_path],
            actions=[Action("run-command", f"Execute: {command.name}", lambda u=final_uri: openUrl(u))],
        )

    def _create_error_item(self, title: str, subtitle: str) -> Item:
        """Builds a StandardItem for displaying an error message."""
        return StandardItem(
            id="error", 
            text=title, 
            subtext=subtitle, 
            iconUrls=[self.icon_path], 
            actions=[Action("config", "Open Config File", lambda p=self.config.config_path: openFile(str(p)))]
        )

    def configWidget(self):
        return [{'type': 'label', 'text': f"<p>Obsidian Plugin v{md_version}</p>"}]
