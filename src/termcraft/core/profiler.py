import time
import shutil
import subprocess
from typing import Dict, Any, List

# kabuk acilis suresi olcumu. surec baslatma maliyeti de olcume dahil oluyor,
# yani mutlak deger degil kabuklar arasi karsilastirma icin anlamli
class ShellProfiler:
    TIMEOUT_SECONDS = 15

    def benchmark_shell(self, shell_cmd: List[str], iterations: int = 5) -> Dict[str, Any]:
        # ilk calistirma disk cache'ini isitiyor ve ortalamayi ciddi sekilde
        # bozuyordu. bir warmup turu atip sonuclarina bakmiyoruz
        warmup_ok = self._run_once(shell_cmd) is not None

        durations: List[float] = []
        timed_out = False
        for _ in range(iterations):
            elapsed = self._run_once(shell_cmd)
            if elapsed is None:
                # tek bir tur patlarsa hemen pes etme, kalanlari dene.
                # eskiden burada break vardi ve kabuk kurulu olmasina ragmen
                # tabloda "bulunamadi" gorunuyordu
                timed_out = True
                continue
            durations.append(elapsed)

        if not durations:
            return {
                "available": warmup_ok,
                "timed_out": timed_out,
                "avg_ms": 0, "min_ms": 0, "max_ms": 0, "samples": 0
            }

        durations.sort()
        return {
            "available": True,
            "timed_out": timed_out,
            "avg_ms": round(sum(durations) / len(durations), 2),
            "min_ms": round(durations[0], 2),
            "max_ms": round(durations[-1], 2),
            "samples": len(durations)
        }

    def _run_once(self, shell_cmd: List[str]) -> Any:
        start = time.perf_counter()
        try:
            subprocess.run(shell_cmd, capture_output=True, text=True, timeout=self.TIMEOUT_SECONDS)
        except Exception:
            return None
        return (time.perf_counter() - start) * 1000

    def run_all_benchmarks(self, iterations: int = 3) -> Dict[str, Dict[str, Any]]:
        # bash/zsh'ta -i sart cunku rc dosyalari sadece interaktif modda okunuyor.
        # fish ve nu config'i her halukarda okudugu icin onlarda gerek yok
        shells = {}

        if shutil.which("pwsh"):
            shells["PowerShell 7 (pwsh)"] = ["pwsh", "-NoLogo", "-Command", "exit"]
        if shutil.which("powershell"):
            shells["Windows PowerShell 5.1"] = ["powershell", "-NoLogo", "-Command", "exit"]
        if shutil.which("bash"):
            shells["Bash"] = ["bash", "-i", "-c", "exit"]
        if shutil.which("zsh"):
            shells["Zsh"] = ["zsh", "-i", "-c", "exit"]
        if shutil.which("fish"):
            shells["Fish"] = ["fish", "-c", "exit"]
        if shutil.which("nu"):
            shells["NuShell"] = ["nu", "-c", "exit"]

        return {name: self.benchmark_shell(cmd, iterations=iterations) for name, cmd in shells.items()}
