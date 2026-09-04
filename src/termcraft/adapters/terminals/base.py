from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional

# terminal emulatorleri icin ortak arayuz. kabuk adapterlerinden ayri cunku
# burada alias/prompt degil sadece renk semasi yaziyoruz
class BaseTerminalAdapter(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def get_config_path(self) -> Optional[Path]:
        pass

    def get_settings_path(self) -> Optional[Path]:
        return self.get_config_path()

    @abstractmethod
    def is_available(self) -> bool:
        pass

    @abstractmethod
    def apply_theme(self, theme_data: Dict[str, Any]) -> bool:
        pass
