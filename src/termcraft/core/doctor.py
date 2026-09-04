import os
import sys
import subprocess
from pathlib import Path
from typing import List, Dict, Any
from termcraft.adapters import get_available_adapters
from termcraft.adapters.terminals import get_available_terminal_adapters
from termcraft.utils.font_detector import detect_nerd_fonts
from termcraft.utils.gradient import is_truecolor_supported
from termcraft.core.tool_hub import ToolHub
from termcraft.core.alias_manager import AliasManager
from termcraft.i18n import t

# ortam saglik kontrolu. her kontrol tek bir dict satiri uretiyor,
# CLI ve TUI ayni rapordan kendi tablosunu ciziyor
class DoctorReport:
    def __init__(self):
        self.checks: List[Dict[str, Any]] = []

    def add(self, title: str, status: str, message: str, fix_suggestion: str = ""):
        self.checks.append({
            "title": title,
            "status": status,
            "message": message,
            "fix_suggestion": fix_suggestion
        })


class TerminalDoctor:
    def run_diagnostics(self) -> DoctorReport:
        # hicbir kontrol dosyaya yazmiyor, sadece okuma yapiyor.
        # (test_doctor_diagnostics_no_side_effects tam da bunu koruyor)
        report = DoctorReport()

        shells = get_available_adapters()
        if shells:
            names = ", ".join([s.name for s in shells])
            report.add(t("shell_detection"), "pass", t("found_shells", shells=names))
        else:
            report.add(t("shell_detection"), "warn", t("no_shells_found"), t("init_shell_hint"))

        terminals = get_available_terminal_adapters()
        if terminals:
            tnames = ", ".join([term.name for term in terminals])
            report.add("Terminal Emulators", "pass", t("terminals_detected", terms=tnames))
        else:
            report.add("Terminal Emulators", "warn", t("no_terminals_found"))

        if is_truecolor_supported():
            report.add(t("truecolor_support"), "pass", t("truecolor_ok"))
        else:
            report.add(t("truecolor_support"), "warn", t("truecolor_warn"), t("truecolor_hint"))

        fonts = detect_nerd_fonts()
        installed_nfs = [name for name, present in fonts.items() if present]
        if installed_nfs:
            report.add("Nerd Font", "pass", t("nerd_font_found", fonts=", ".join(installed_nfs[:3])))
        else:
            report.add("Nerd Font", "warn", t("nerd_font_missing"), t("nerd_font_hint"))

        # olmayan dizinler ve tekrar eden kayitlar PATH aramasini yavaslatiyor
        path_entries = os.environ.get("PATH", "").split(os.pathsep)
        clean_paths = [p for p in path_entries if p.strip()]
        missing_paths = [p for p in clean_paths if not Path(p).exists()]
        duplicate_paths = {p for p in clean_paths if clean_paths.count(p) > 1}

        if not missing_paths and not duplicate_paths:
            report.add("PATH Environment", "pass", t("path_ok", count=len(clean_paths)))
        else:
            issues = []
            if missing_paths:
                issues.append(f"{len(missing_paths)} invalid paths")
            if duplicate_paths:
                issues.append(f"{len(duplicate_paths)} duplicates")
            report.add("PATH Environment", "warn", t("path_issues", issues=", ".join(issues)), t("path_hint"))

        alias_mgr = AliasManager()
        shadowing = alias_mgr.check_shadowing()
        conflicts = alias_mgr.check_conflicts()
        missing_reqs = alias_mgr.check_missing_requirements()

        if shadowing:
            desc = ", ".join([f"{name} -> {cmd}" for name, cmd in shadowing[:3]])
            report.add("Alias Shadowing", "warn", t("alias_shadowing", aliases=desc), t("alias_shadowing_hint"))
        if missing_reqs:
            desc = ", ".join([f"{name} ({req})" for name, req in missing_reqs[:3]])
            report.add("Alias Requirements", "warn", t("alias_missing_tool", aliases=desc), t("tools_hint"))
        if conflicts:
            c_desc = ", ".join([f"{name} ({path})" for name, path in conflicts[:2]])
            report.add("Alias System", "warn", f"Binary overlap detected: {c_desc}", "Review alias overrides in termcraft alias list")
        if not shadowing and not conflicts and not missing_reqs:
            report.add("Alias System", "pass", t("alias_ok"))

        hub = ToolHub()
        tool_status = hub.get_tool_status()
        installed_tools = [t_item["name"] for t_item in tool_status if t_item["installed"]]
        missing_tools = [t_item["name"] for t_item in tool_status if not t_item["installed"]]

        if installed_tools:
            report.add("Modern CLI Suite", "pass", t("tools_installed", tools=", ".join(installed_tools)))
        if missing_tools:
            report.add("CLI Recommendations", "info", t("tools_missing", tools=", ".join(missing_tools)), t("tools_hint"))

        # utf-8 degilse nerd font ikonlari kutucuk olarak cikiyor
        encoding = getattr(sys.stdout, "encoding", None) or sys.getdefaultencoding() or "utf-8"
        if "utf" in encoding.lower():
            report.add("Encoding / Unicode", "pass", t("encoding_active", encoding=encoding))
        else:
            report.add("Encoding / Unicode", "warn", t("encoding_warn", encoding=encoding))

        return report

    def auto_fix(self, set_execution_policy: bool = False) -> List[str]:
        """Onerilen ortam duzeltmelerini uygular.

        ONEMLI: burada dogrudan inject_block CAGIRILMAZ. Eskiden oyleydi ve
        base.inject_block termcraft blogunu komple degistirdigi icin daha once
        yazilmis tum alias'lar ve prompt hook'u siliniyordu. Artik blogu butun
        halinde yeniden ureten sync_all_shells'i extra_env ile cagiriyoruz.

        Set-ExecutionPolicy sistem ayari degistirdigi icin varsayilan olarak
        KAPALI. CLI kullaniciya sorup bu bayragi aciyor.
        """
        fixed: List[str] = []

        if set_execution_policy and sys.platform == "win32":
            try:
                proc = subprocess.run(
                    ["powershell.exe", "-NoProfile", "-Command",
                     "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force"],
                    capture_output=True,
                    timeout=20
                )
                if proc.returncode == 0:
                    fixed.append("PowerShell ExecutionPolicy set to RemoteSigned (CurrentUser)")
            except Exception:
                pass

        # blogu bastan ureterek yaz. env'e ekstra degerleri gecirmek yeterli,
        # alias + prompt kismini sync kendisi tekrar koyuyor
        from termcraft.core.sync import sync_all_shells
        extra_env = {"TERMCRAFT_INIT": "1", "COLORTERM": "truecolor"}
        for shell_name, ok in sync_all_shells(extra_env=extra_env).items():
            if ok:
                fixed.append(f"Refreshed TermCraft block for {shell_name}")

        return fixed
