from typing import Dict, Any

# preset icerikleri ham metin olarak tutuluyor (toml/json). ayri dosyalarda
# tutmak paketleme sirasinda package-data derdi cikardigi icin gomulu birakildi.
# ikonlar nerd font ister, yoksa kutucuk gorunur
STARSHIP_PRESETS: Dict[str, Dict[str, Any]] = {
    "modern-cyber": {
        "name": "Modern Cyber",
        "description": "Sleek multi-segment prompt with git status, runtime info, and duration",
        "config_toml": 'format = """$os$username$hostname$directory$git_branch$git_status$nodejs$rust$golang$python$docker_context$package$time$cmd_duration$character"""\n\n[character]\nsuccess_symbol = "[➜](bold #00ffcc)"\nerror_symbol = "[✗](bold #ff0055)"\n\n[directory]\nstyle = "bold #7aa2f7"\nread_only = " 🔒"\ntruncation_length = 4\ntruncate_to_repo = true\n\n[git_branch]\nsymbol = " "\nstyle = "bold #bb9af7"\n\n[git_status]\nstyle = "bold #f7768e"\nahead = "⇡${count}"\ndiverged = "⇕⇡${ahead_count}⇣${behind_count}"\nbehind = "⇣${count}"\n\n[python]\nsymbol = " "\nstyle = "bold #e0af68"\n\n[nodejs]\nsymbol = " "\nstyle = "bold #9ece6a"\n\n[rust]\nsymbol = " "\nstyle = "bold #ff9e64"\n\n[golang]\nsymbol = " "\nstyle = "bold #7dcfff"\n\n[cmd_duration]\nmin_time = 2_000\nstyle = "bold #e0af68"\nformat = "took [$duration]($style) "\n\n[time]\ndisabled = false\ntime_format = "%R"\nstyle = "dim #565f89"\nformat = "[$time]($style) "\n'
    },
    "minimal-pure": {
        "name": "Minimal Pure",
        "description": "Super clean and ultra-fast minimalist prompt",
        "config_toml": 'format = """$directory$git_branch$character"""\n\n[directory]\nstyle = "bold cyan"\ntruncation_length = 3\n\n[git_branch]\nsymbol = "git:"\nstyle = "bold yellow"\n\n[character]\nsuccess_symbol = "[❯](bold green)"\nerror_symbol = "[❯](bold red)"\n'
    },
    "powerline-gradient": {
        "name": "Powerline Catppuccin",
        "description": "Rich powerline-styled rounded glyph prompt",
        "config_toml": 'format = """[](#89b4fa)$os[](bg:#fab387 fg:#89b4fa)$directory[](bg:#a6e3a1 fg:#fab387)$git_branch$git_status[](fg:#a6e3a1)$character"""\n\n[directory]\nstyle = "bg:#fab387 fg:#11111b bold"\nformat = "[ $path ]($style)"\n\n[git_branch]\nstyle = "bg:#a6e3a1 fg:#11111b bold"\nformat = "[ $symbol$branch ]($style)"\nsymbol = " "\n\n[character]\nsuccess_symbol = "[ ➜ ](bold #a6e3a1)"\nerror_symbol = "[ ✗ ](bold #f38ba8)"\n'
    }
}

# TODO: sadece tek oh-my-posh preset'i var, listeyi genisletmek lazim
OH_MY_POSH_PRESETS: Dict[str, Dict[str, Any]] = {
    "catppuccin-clean": {
        "name": "Catppuccin Clean",
        "description": "High performance Oh-My-Posh theme based on Catppuccin palette",
        "config_json": '{\n  "$schema": "https://raw.githubusercontent.com/JanDeDobbeleer/oh-my-posh/main/themes/schema.json",\n  "blocks": [\n    {\n      "alignment": "left",\n      "segments": [\n        {\n          "background": "#89b4fa",\n          "foreground": "#11111b",\n          "powerline_symbol": "",\n          "style": "powerline",\n          "type": "path",\n          "properties": {\n            "style": "folder"\n          }\n        },\n        {\n          "background": "#a6e3a1",\n          "foreground": "#11111b",\n          "powerline_symbol": "",\n          "style": "powerline",\n          "type": "git"\n        },\n        {\n          "background": "#f9e2af",\n          "foreground": "#11111b",\n          "powerline_symbol": "",\n          "style": "powerline",\n          "type": "node"\n        },\n        {\n          "background": "#fab387",\n          "foreground": "#11111b",\n          "powerline_symbol": "",\n          "style": "powerline",\n          "type": "python"\n        }\n      ],\n      "type": "prompt"\n    },\n    {\n      "alignment": "left",\n      "newline": true,\n      "segments": [\n        {\n          "foreground": "#89b4fa",\n          "style": "plain",\n          "template": "❯ ",\n          "type": "text"\n        }\n      ],\n      "type": "prompt"\n    }\n  ],\n  "version": 3\n}'
    }
}
