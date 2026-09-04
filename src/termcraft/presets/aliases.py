from typing import Dict, List
from termcraft.config import AliasDefinition
from termcraft.i18n import get_current_language

# hazir alias paketleri. aciklamalar iki dilde tutuluyor, AliasDefinition'a
# cevrilirken aktif dile gore secimi yapiliyor.
# "requires" alani dolu olan alias'lar ilgili binary PATH'te yoksa kabuk
# profiline hic yazilmiyor -> `ls` / `cd` gibi temel komutlar bozulmuyor
BUNDLES_DATA: Dict[str, List[dict]] = {
    "git": [
        {"name": "gs", "command": "git status", "desc_en": "Git status shorthand", "desc_tr": "Git durumunu göster"},
        {"name": "ga", "command": "git add .", "desc_en": "Git add all changes", "desc_tr": "Tüm değişiklikleri git'e ekle"},
        {"name": "gcm", "command": "git commit -m", "desc_en": "Git commit with message", "desc_tr": "Mesaj ile commit oluştur"},
        {"name": "gco", "command": "git checkout", "desc_en": "Git checkout branch", "desc_tr": "Dala (branch) geçiş yap"},
        {"name": "gcb", "command": "git checkout -b", "desc_en": "Git checkout new branch", "desc_tr": "Yeni dal oluştur ve geç"},
        {"name": "gpush", "command": "git push", "desc_en": "Git push to remote", "desc_tr": "Değişiklikleri uzak sunucuya gönder"},
        {"name": "gpull", "command": "git pull", "desc_en": "Git pull from remote", "desc_tr": "Uzak sunucudan değişiklikleri çek"},
        {"name": "glog", "command": "git log --oneline --graph --decorate", "desc_en": "Git visual graph log", "desc_tr": "Görsel git commit geçmişi"},
        {"name": "gdiff", "command": "git diff", "desc_en": "Git diff comparison", "desc_tr": "Değişiklik farklarını göster"},
    ],
    "docker": [
        {"name": "dps", "command": "docker ps --format 'table {{.ID}}\t{{.Names}}\t{{.Status}}\t{{.Ports}}'", "desc_en": "Docker ps pretty table", "desc_tr": "Çalışan konteynerleri listele", "requires": "docker"},
        {"name": "dpa", "command": "docker ps -a", "desc_en": "Docker list all containers", "desc_tr": "Tüm konteynerleri listele", "requires": "docker"},
        {"name": "dstop", "command": "docker stop", "desc_en": "Stop container", "desc_tr": "Konteyneri durdur", "requires": "docker"},
        {"name": "dstart", "command": "docker start", "desc_en": "Start container", "desc_tr": "Konteyneri başlat", "requires": "docker"},
        {"name": "dcomp", "command": "docker compose", "desc_en": "Docker compose shorthand", "desc_tr": "Docker compose kısayolu", "requires": "docker"},
        {"name": "dcup", "command": "docker compose up -d", "desc_en": "Docker compose detached start", "desc_tr": "Arka planda compose başlat", "requires": "docker"},
        {"name": "dcdown", "command": "docker compose down", "desc_en": "Docker compose stop and tear down", "desc_tr": "Compose konteynerlerini kapat", "requires": "docker"},
        {"name": "dclogs", "command": "docker compose logs -f", "desc_en": "Docker compose follow logs", "desc_tr": "Konteyner loglarını canlı izle", "requires": "docker"},
    ],
    "dev": [
        {"name": "pipr", "command": "pip install -r requirements.txt", "desc_en": "Install python requirements", "desc_tr": "Python paketlerini yükle", "requires": "pip"},
        {"name": "nrd", "command": "npm run dev", "desc_en": "NPM Run Dev", "desc_tr": "NPM geliştirme sunucusu", "requires": "npm"},
        {"name": "nrb", "command": "npm run build", "desc_en": "NPM Run Build", "desc_tr": "NPM projeyi derle", "requires": "npm"},
        {"name": "nrt", "command": "npm run test", "desc_en": "NPM Run Test", "desc_tr": "NPM testleri çalıştır", "requires": "npm"},
        {"name": "pnd", "command": "pnpm dev", "desc_en": "PNPM dev server", "desc_tr": "PNPM geliştirme sunucusu", "requires": "pnpm"},
        {"name": "pnb", "command": "pnpm build", "desc_en": "PNPM build", "desc_tr": "PNPM projeyi derle", "requires": "pnpm"},
    ],
    # DIKKAT: bu paket ls/cat/cd/grep/find gibi temel komutlarin uzerine yaziyor.
    # o yuzden varsayilan olarak YUKLENMIYOR (bkz. ConfigManager.get_aliases) ve
    # her alias kendi aracina "requires" ile bagli. arac kurulu degilse yazilmiyor
    "modern-replacements": [
        {"name": "ls", "command": "eza --icons --group-directories-first", "desc_en": "Modern colorful ls with eza", "desc_tr": "Renkli ve ikonlu modern ls", "requires": "eza"},
        {"name": "ll", "command": "eza -la --icons --group-directories-first --git", "desc_en": "Long list with icons & git info", "desc_tr": "Detaylı liste, ikonlar ve git bilgisi", "requires": "eza"},
        {"name": "cat", "command": "bat --paging=never", "desc_en": "Syntax highlighted cat with bat", "desc_tr": "Renkli kod vurgulu dosya okuyucu", "requires": "bat"},
        {"name": "cd", "command": "z", "desc_en": "Smart directory jumping with zoxide", "desc_tr": "Akıllı hızlı dizin geçişi", "requires": "zoxide"},
        {"name": "grep", "command": "rg", "desc_en": "Blazing fast ripgrep", "desc_tr": "Ultra hızlı metin arama", "requires": "rg"},
        {"name": "find", "command": "fd", "desc_en": "Intuitive fast find with fd", "desc_tr": "Hızlı ve kolay dosya bulucu", "requires": "fd"},
    ]
}

# temel kabuk komutlarini golgeleyen alias'lar. doctor bunlari ayrica uyariyor
SHADOWING_ALIAS_NAMES = {"ls", "ll", "cat", "cd", "grep", "find", "rm", "cp", "mv", "gc", "gp", "gl", "gm"}

def list_bundle_names() -> List[str]:
    return list(BUNDLES_DATA.keys())

def get_alias_bundle(bundle_name: str) -> List[AliasDefinition]:
    raw_list = BUNDLES_DATA.get(bundle_name, [])
    lang = get_current_language()
    result = []
    for item in raw_list:
        desc = item["desc_tr"] if lang == "tr" else item["desc_en"]
        result.append(AliasDefinition(
            name=item["name"],
            command=item["command"],
            description=desc,
            shells=["powershell", "bash", "zsh", "fish", "nushell"],
            requires=item.get("requires")
        ))
    return result
