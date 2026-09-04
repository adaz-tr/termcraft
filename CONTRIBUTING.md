# Contributing to TermCraft

Thanks for wanting to help out.

## Development setup

```bash
git clone https://github.com/adaz-tr/termcraft.git
cd termcraft

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -e ".[dev]"
```

## Running checks

```bash
pytest                  # test suite
pytest -v               # verbose
ruff check src tests    # lint
```

### ⚠️ About the test suite

TermCraft writes to real config files (`~/.bashrc`, `$PROFILE`, `~/.termcraft`, `starship.toml`,
terminal emulator configs). `tests/conftest.py` has an **autouse fixture that redirects `HOME` to a
temp directory** for every test, plus one that stubs out `subprocess.run`.

Do not remove those fixtures, and do not add a test that bypasses them. Without the isolation,
running `pytest` silently rewrites the shell profile of whoever ran it.

If a test genuinely needs to spawn a process, mark it:

```python
@pytest.mark.allow_subprocess
def test_something_real():
    ...
```

## Project layout

```
src/termcraft/
├── cli.py              # Typer commands — thin, all logic lives in core/
├── config.py           # pydantic schema for ~/.termcraft/config.yaml
├── i18n.py             # translation strings (tr / en)
├── adapters/           # shell adapters (bash, zsh, fish, nushell, powershell)
│   └── terminals/      # terminal emulator adapters (WT, alacritty, wezterm, kitty)
├── core/               # engines: theme, prompt, alias, sync, doctor, profiler, backup
├── presets/            # built-in themes, prompt presets, alias bundles
├── tui/                # Textual studio
└── utils/              # paths, gradients, banner, font detection
```

**The one rule that matters:** everything TermCraft writes into a shell profile goes through
`sync_all_shells()`, which regenerates the whole marked block. `inject_block()` replaces the block
entirely, so calling it with a partial script wipes the rest. If you need to add something to the
block, add it to `sync_all_shells` (there is an `extra_env` parameter for exactly this).

## Screenshots

README images are generated, not hand-captured:

```bash
python scripts/make_screenshots.py
```

It writes SVGs to `docs/images/` using Textual's own export, driving the app in a temp `HOME`
so your real config is untouched. Regenerate them whenever the TUI layout changes.

## Adding a theme

Add an entry to `BUILTIN_THEMES` in `src/termcraft/presets/themes.py` with the standard keys
(`background`, `foreground`, `cursor`, `selection`, the 8 ANSI colors and their `bright*` variants).
Then add a matching entry to `BAT_THEME_MAP` in the same file — there is a test that fails if a
theme has no `bat` mapping.

The studio recolors itself to match the selected theme, so a new palette also has to stay
readable as UI chrome. `test_studio_ui_is_readable_for_every_builtin_theme` checks the WCAG
contrast of the header, footer, body text and button labels for every built-in theme. Accent
colors are auto-corrected by `ensure_contrast()` when they are too close to the panel behind
them, but a palette with, say, near-identical `background` and `foreground` will still fail.

Gradient themes also need `is_gradient: True`, a `gradient_stops` list, and an entry in
`GRADIENT_PALETTES` in `src/termcraft/utils/gradient.py` if you want the preview to use its own colors.

## Adding a shell or terminal adapter

- Shell adapters inherit `BaseShellAdapter` (`src/termcraft/adapters/base.py`) and register in
  `ALL_SHELL_ADAPTERS`.
- Terminal adapters inherit `BaseTerminalAdapter` (`src/termcraft/adapters/terminals/base.py`) and
  register in `ALL_TERMINAL_ADAPTERS`.

When writing into a config file, **never blindly append**. Two adapters have already been bitten by
this: WezTerm (Lua requires `return` to be the last statement) and Alacritty (TOML rejects duplicate
tables). Write a test that applies the theme twice over a realistic existing config and asserts the
result is still valid.

## Adding a translation string

Add the key to **both** `en` and `tr` in `src/termcraft/i18n.py`.
`test_i18n_all_languages_have_same_keys` fails otherwise.

## Adding a language

Add a new top-level key to `STRINGS` in `i18n.py` with every key from `en`, then add it to the
`lang` choices in the TUI selector.

## Pull requests

1. Branch off `main` with a descriptive name (`feature/kitty-font-sync`, `fix/wezterm-return`).
2. Add tests for new behaviour — especially regression tests for anything that writes to disk.
3. Make sure `pytest` and `ruff check src tests` pass.
4. Keep comments in the existing style: short, lowercase, explaining *why* rather than *what*.
5. Open the PR against `main`.
