import shutil
import pytest

# ONEMLI: bu suit gercekten dosya yaziyor - kabuk profilleri, ~/.termcraft,
# starship.toml, terminal config'leri. HOME'u izole etmezsek `pytest` calistiran
# herkesin kendi .bashrc / $PROFILE dosyasi degisiyor.
# asagidaki autouse fixture HOME'u tmp_path'e cevirip her testi kendi kumunda
# calistiriyor. bunu kaldirmayin.


@pytest.fixture(autouse=True)
def isolated_home(tmp_path, monkeypatch):
    fake_home = tmp_path / "home"
    fake_home.mkdir(parents=True, exist_ok=True)

    # pathlib.Path.home() platforma gore farkli degiskene bakiyor,
    # hepsini birden ayarliyoruz
    for var in ("HOME", "USERPROFILE"):
        monkeypatch.setenv(var, str(fake_home))
    monkeypatch.setenv("APPDATA", str(fake_home / "AppData" / "Roaming"))
    monkeypatch.setenv("LOCALAPPDATA", str(fake_home / "AppData" / "Local"))
    monkeypatch.delenv("STARSHIP_CONFIG", raising=False)
    # windows'ta HOMEDRIVE/HOMEPATH birlesimi USERPROFILE'i ezebiliyor
    monkeypatch.delenv("HOMEDRIVE", raising=False)
    monkeypatch.delenv("HOMEPATH", raising=False)
    monkeypatch.setattr("pathlib.Path.home", classmethod(lambda cls: fake_home))

    # ConfigManager singleton'i onceki testin HOME'unu tutuyor olabilir
    from termcraft.core.config_manager import ConfigManager
    ConfigManager.reset_instance()

    yield fake_home

    ConfigManager.reset_instance()


@pytest.fixture(autouse=True)
def no_subprocess_side_effects(monkeypatch, request):
    """Testler gercek kabuk baslatmasin / ExecutionPolicy degistirmesin.

    `allow_subprocess` marker'i olan testler bunun disinda tutuluyor.
    """
    if request.node.get_closest_marker("allow_subprocess"):
        return

    import subprocess

    class _FakeCompleted:
        returncode = 0
        stdout = ""
        stderr = ""

    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: _FakeCompleted())


@pytest.fixture
def no_shells(monkeypatch):
    """Hicbir kabuk/arac kurulu degilmis gibi davranir."""
    monkeypatch.setattr(shutil, "which", lambda name: None)


def pytest_configure(config):
    config.addinivalue_line("markers", "allow_subprocess: gercek subprocess calistirmasina izin ver")
