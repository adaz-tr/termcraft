from typing import List, Type
from termcraft.adapters.terminals.base import BaseTerminalAdapter
from termcraft.adapters.terminals.windows_terminal import WindowsTerminalAdapter
from termcraft.adapters.terminals.alacritty import AlacrittyAdapter
from termcraft.adapters.terminals.wezterm import WezTermAdapter
from termcraft.adapters.terminals.kitty import KittyAdapter

ALL_TERMINAL_ADAPTERS: List[Type[BaseTerminalAdapter]] = [
    WindowsTerminalAdapter,
    AlacrittyAdapter,
    WezTermAdapter,
    KittyAdapter
]

def get_available_terminal_adapters() -> List[BaseTerminalAdapter]:
    # kabuklardan farkli olarak burada 'available' = config dosyasi gercekten var.
    # olmayan bir terminal icin bos config uretip kullaniciyi sasirtmak istemiyoruz
    adapters = []
    for cls in ALL_TERMINAL_ADAPTERS:
        inst = cls()
        if inst.is_available():
            adapters.append(inst)
    return adapters
