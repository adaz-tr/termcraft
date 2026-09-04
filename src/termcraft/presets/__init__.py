# preset paketinin toplu re-export'u
from termcraft.presets.themes import BUILTIN_THEMES
from termcraft.presets.prompts import STARSHIP_PRESETS, OH_MY_POSH_PRESETS
from termcraft.presets.aliases import BUNDLES_DATA, get_alias_bundle, list_bundle_names

__all__ = [
    "BUILTIN_THEMES",
    "STARSHIP_PRESETS",
    "OH_MY_POSH_PRESETS",
    "BUNDLES_DATA",
    "get_alias_bundle",
    "list_bundle_names",
]
