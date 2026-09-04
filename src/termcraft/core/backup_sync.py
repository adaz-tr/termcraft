import shutil
import datetime
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from termcraft.utils.paths import (
    get_termcraft_dir,
    get_config_file_path,
    get_starship_config_path,
    get_powershell_profile_paths,
)
from termcraft.adapters import get_available_adapters
from termcraft.adapters.terminals import get_available_terminal_adapters

# snapshot = bir klasor icinde config.yaml + tum kabuk/terminal config kopyalari
# + nereden geldiklerini tutan manifest.json. geri yukleme manifest'e bakiyor
class BackupManager:
    def __init__(self):
        self.base_dir = get_termcraft_dir()
        self.backup_dir = self.base_dir / "backups"
        self.profiles_dir = self.base_dir / "profiles"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.profiles_dir.mkdir(parents=True, exist_ok=True)

    def create_snapshot(self, tag: str = "auto") -> Path:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        snapshot_name = f"snapshot_{tag}_{timestamp}"
        target_dir = self.backup_dir / snapshot_name
        target_dir.mkdir(parents=True, exist_ok=True)

        config_path = get_config_file_path()
        if config_path.exists():
            shutil.copy2(config_path, target_dir / "config.yaml")

        manifest: Dict[str, Any] = {
            "timestamp": timestamp,
            "tag": tag,
            "files": []
        }

        for adapter in get_available_adapters():
            if adapter.name == "powershell":
                # powershell'in birden fazla profili olabildigi icin ayri ele aliniyor,
                # dosya adlarina index koyup ustuste yazmalarini engelliyoruz
                for idx, ps_path in enumerate(get_powershell_profile_paths()):
                    if ps_path.exists():
                        dest = target_dir / f"shell_powershell_{idx}_{ps_path.name}"
                        shutil.copy2(ps_path, dest)
                        manifest["files"].append({"type": "shell", "name": "powershell", "origin": str(ps_path), "backup": dest.name})
            else:
                p = adapter.get_config_path()
                if p and p.exists():
                    dest = target_dir / f"shell_{adapter.name}_{p.name}"
                    shutil.copy2(p, dest)
                    manifest["files"].append({"type": "shell", "name": adapter.name, "origin": str(p), "backup": dest.name})

        for term in get_available_terminal_adapters():
            found_path = term.get_config_path()
            if found_path and found_path.exists():
                dest = target_dir / f"term_{term.name}_{found_path.name}"
                shutil.copy2(found_path, dest)
                manifest["files"].append({"type": "terminal", "name": term.name, "origin": str(found_path), "backup": dest.name})

        # prompt tarafi da yedeklenmeli, yoksa `prompt apply` geri alinamiyor
        starship_path = get_starship_config_path()
        if starship_path.exists():
            dest = target_dir / "prompt_starship.toml"
            shutil.copy2(starship_path, dest)
            manifest["files"].append({"type": "prompt", "name": "starship", "origin": str(starship_path), "backup": dest.name})

        for idx, omp_file in enumerate(sorted((self.base_dir / "prompts").glob("*.json"))):
            dest = target_dir / f"prompt_omp_{idx}_{omp_file.name}"
            shutil.copy2(omp_file, dest)
            manifest["files"].append({"type": "prompt", "name": "oh-my-posh", "origin": str(omp_file), "backup": dest.name})

        (target_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return target_dir

    def list_snapshots(self) -> List[Dict[str, Any]]:
        results = []
        for d in self.backup_dir.iterdir():
            if d.is_dir() and (d / "manifest.json").exists():
                try:
                    data = json.loads((d / "manifest.json").read_text(encoding="utf-8"))
                    data["dir_name"] = d.name
                    data["full_path"] = str(d)
                    results.append(data)
                except Exception:
                    pass
        # klasor adi snapshot_<tag>_<tarih> oldugu icin isme gore siralarsak once
        # tag'e gore siralaniyor. gercekten yeniden eskiye istiyorsak timestamp lazim
        results.sort(key=lambda r: r.get("timestamp", ""), reverse=True)
        return results

    def restore_snapshot(self, snapshot_name: str) -> bool:
        target_dir = self.backup_dir / snapshot_name
        if not target_dir.exists() or not (target_dir / "manifest.json").exists():
            # tam isim tutmazsa kismi eslesmeyi de deniyoruz, kullanici uzun
            # klasor adini elle yazmak zorunda kalmasin
            for d in sorted(self.backup_dir.iterdir(), reverse=True):
                if d.is_dir() and snapshot_name in d.name and (d / "manifest.json").exists():
                    target_dir = d
                    break
        if not target_dir.exists() or not (target_dir / "manifest.json").exists():
            return False

        # geri yuklemeden once mevcut durumu da bir kenara al, yanlis snapshot
        # secildiginde geri donebilelim
        try:
            self.create_snapshot(tag="pre-restore")
        except Exception:
            pass

        try:
            manifest = json.loads((target_dir / "manifest.json").read_text(encoding="utf-8"))
            for item in manifest.get("files", []):
                backup_file = target_dir / item["backup"]
                origin_file = Path(item["origin"])
                if backup_file.exists():
                    origin_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(backup_file, origin_file)

            saved_config = target_dir / "config.yaml"
            if saved_config.exists():
                active_cfg = get_config_file_path()
                active_cfg.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(saved_config, active_cfg)

            return True
        except Exception:
            return False


def maybe_snapshot(tag: str = "auto") -> Optional[Path]:
    """config.auto_backup aciksa sessizce bir snapshot alir.

    Tema/prompt uygulamak gibi dosya ustune yazan islemlerden once cagriliyor.
    Yedek alinamazsa asil islemi engellememesi icin hatalari yutuyoruz.
    """
    try:
        from termcraft.core.config_manager import ConfigManager
        if not ConfigManager.get_instance().config.auto_backup:
            return None
        return BackupManager().create_snapshot(tag=tag)
    except Exception:
        return None
