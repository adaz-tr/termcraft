import shutil
import sys
from typing import Dict, List, Any
from termcraft.i18n import get_current_language

# tavsiye edilen modern CLI araclari. binaries listesi birden fazla cunku
# ayni arac dagitima gore farkli isimle kuruluyor (bat/batcat, fd/fdfind, eza/exa)
RECOMMENDED_TOOLS = [
    {
        "id": "starship",
        "name": "Starship",
        "category": "Prompt Engine",
        "desc_en": "The minimal, blazing-fast, and customizable prompt for any shell",
        "desc_tr": "Her kabuk için ultra hızlı ve özelleştirilebilir modern prompt motoru",
        "binaries": ["starship"],
        "install": {
            "windows": "winget install Starship.Starship",
            "darwin": "brew install starship",
            "linux": "curl -sS https://starship.rs/install.sh | sh"
        }
    },
    {
        "id": "oh-my-posh",
        "name": "Oh-My-Posh",
        "category": "Prompt Engine",
        "desc_en": "A prompt theme engine for any shell with rich glyphs and powerline segments",
        "desc_tr": "Zengin ikon ve segment destekli popüler prompt tema motoru",
        "binaries": ["oh-my-posh"],
        "install": {
            "windows": "winget install JanDeDobbeleer.OhMyPosh",
            "darwin": "brew install jandedobbeleer/oh-my-posh/oh-my-posh",
            "linux": "curl -s https://ohmyposh.dev/install.sh | bash -s"
        }
    },
    {
        "id": "eza",
        "name": "eza (ex-exa)",
        "category": "File Listing",
        "desc_en": "A modern replacement for ls with colors, icons, and git status",
        "desc_tr": "Renkli, ikonlu ve git durumlu modern ls alternatifi",
        "binaries": ["eza", "exa"],
        "install": {
            "windows": "winget install eza-community.eza",
            "darwin": "brew install eza",
            "linux": "sudo apt install eza || cargo install eza"
        }
    },
    {
        "id": "bat",
        "name": "bat",
        "category": "File Viewing",
        "desc_en": "A cat clone with syntax highlighting and Git integration",
        "desc_tr": "Renkli sözdizimi vurgusu ve git destekli modern cat alternatifi",
        "binaries": ["bat", "batcat"],
        "install": {
            "windows": "winget install sharkdp.bat",
            "darwin": "brew install bat",
            "linux": "sudo apt install bat || cargo install bat"
        }
    },
    {
        "id": "zoxide",
        "name": "zoxide",
        "category": "Navigation",
        "desc_en": "A smarter cd command that remembers your most used directories",
        "desc_tr": "En çok kullanılan dizinleri hatırlayan akıllı cd aracı",
        "binaries": ["zoxide"],
        "install": {
            "windows": "winget install ajeetdsouza.zoxide",
            "darwin": "brew install zoxide",
            "linux": "curl -sS https://raw.githubusercontent.com/ajeetdsouza/zoxide/main/install.sh | bash"
        }
    },
    {
        "id": "ripgrep",
        "name": "ripgrep (rg)",
        "category": "Search",
        "desc_en": "Blazing fast line-oriented search tool for regex patterns",
        "desc_tr": "Kod tabanında ultra hızlı regex metin arama aracı",
        "binaries": ["rg"],
        "install": {
            "windows": "winget install BurntSushi.ripgrep.MSVC",
            "darwin": "brew install ripgrep",
            "linux": "sudo apt install ripgrep || cargo install ripgrep"
        }
    },
    {
        "id": "fzf",
        "name": "fzf",
        "category": "Fuzzy Finder",
        "desc_en": "Interactive fuzzy finder for files, history and git",
        "desc_tr": "Dosya, geçmiş ve git için interaktif bulanık arama aracı",
        "binaries": ["fzf"],
        "install": {
            "windows": "winget install junegunn.fzf",
            "darwin": "brew install fzf",
            "linux": "sudo apt install fzf"
        }
    },
    {
        "id": "fastfetch",
        "name": "fastfetch",
        "category": "System Info",
        "desc_en": "Blazing fast system info fetcher written in C",
        "desc_tr": "C ile yazılmış yüksek performanslı sistem bilgi görüntüleyici",
        "binaries": ["fastfetch"],
        "install": {
            "windows": "winget install Fastfetch-cli.Fastfetch",
            "darwin": "brew install fastfetch",
            "linux": "sudo apt install fastfetch"
        }
    },
    {
        "id": "lazygit",
        "name": "lazygit",
        "category": "Git UI",
        "desc_en": "Simple terminal UI for effortless git commands",
        "desc_tr": "Terminal içinde görsel ve pratik Git yönetim arayüzü",
        "binaries": ["lazygit"],
        "install": {
            "windows": "winget install JesseDuffield.lazygit",
            "darwin": "brew install lazygit",
            "linux": "sudo apt install lazygit || go install github.com/jesseduffield/lazygit@latest"
        }
    },
    {
        "id": "fd",
        "name": "fd",
        "category": "Search",
        "desc_en": "Simple, fast and user-friendly alternative to find",
        "desc_tr": "Klasik find komutuna hızlı ve kullanıcı dostu alternatif",
        "binaries": ["fd", "fdfind"],
        "install": {
            "windows": "winget install sharkdp.fd",
            "darwin": "brew install fd",
            "linux": "sudo apt install fd-find"
        }
    }
]

# not: bilincli olarak sadece TESPIT ediyoruz, kurulumu kendimiz calistirmiyoruz.
# winget/brew/curl|sh gibi komutlari kullanicinin haberi olmadan calistirmak
# istemiyoruz - komutu gosterip karari ona birakiyoruz
class ToolHub:
    def get_tool_status(self) -> List[Dict[str, Any]]:
        # PATH'te ilk bulunan varyant kazaniyor, kurulu sayiyoruz
        os_key = "windows" if sys.platform == "win32" else ("darwin" if sys.platform == "darwin" else "linux")
        is_tr = get_current_language() == "tr"
        status_list = []
        for t in RECOMMENDED_TOOLS:
            found_path = None
            for b in t["binaries"]:
                p = shutil.which(b)
                if p:
                    found_path = p
                    break
            desc = t["desc_tr"] if is_tr else t["desc_en"]
            status_list.append({
                "id": t["id"],
                "name": t["name"],
                "category": t["category"],
                "description": desc,
                "installed": found_path is not None,
                "binary_path": found_path,
                "install_command": t["install"].get(os_key, "")
            })
        return status_list
