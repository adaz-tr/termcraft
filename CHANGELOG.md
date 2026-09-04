# Changelog

All notable changes to this project are documented here.
Format loosely follows [Keep a Changelog](https://keepachangelog.com/).

## [1.0.0] — 2026-09-04

First public release. This entry also records the hardening pass done before publishing.

### Fixed — config-destroying bugs

- **`doctor --fix` wiped your setup.** `auto_fix()` called `inject_block()` with an env-only
  script, and since that method replaces the whole marked block, every alias and the prompt hook
  were deleted. It now goes through `sync_all_shells(extra_env=...)`, which regenerates the block
  in full.
- **WezTerm configs were left unparseable.** The theme block was appended after the file's final
  `return config`, which is a Lua syntax error. Colors now live in a sidecar
  `termcraft_colors.lua` and the hook is inserted *before* the last top-level `return`.
- **Alacritty configs were left unparseable.** Appending `[colors.primary]` to a file that already
  had one produced a TOML "duplicate table" error. Existing `[colors.*]` tables are now stripped
  before the block is written, and `.yml` configs are no longer targeted with TOML content.
- **`ls`, `cat`, `cd`, `grep` and `find` could break your shell.** The `modern-replacements` bundle
  was seeded by default and installed regardless of whether `eza`/`bat`/`zoxide`/`rg`/`fd` existed.
  It is now opt-in, each alias declares the binary it `requires`, and aliases whose tool is missing
  are skipped during sync.
- **No backups were taken.** The `auto_backup` setting existed but was never read. Theme and prompt
  application now snapshot shell, terminal and prompt configs first, and `backup restore` takes a
  `pre-restore` snapshot before overwriting anything.
- **A single YAML typo deleted your config.** A malformed `config.yaml` was silently overwritten
  with defaults. It is now copied to `config.broken-<timestamp>.yaml` and the CLI says where.

### Fixed — behaviour

- `backup restore` printed a stray empty `Error:` line on failure (`typer.Exit` subclasses
  `RuntimeError` and was caught by the surrounding `except Exception`).
- Theme names were stored unnormalized, so `theme apply "Tokyo Night"` later fell back to default
  colors on the next sync. Names now resolve to a canonical key before being saved.
- The NuShell prompt hook re-ran `starship init nu | save -f` on **every** shell start. It is now
  guarded so it only generates the autoload file once.
- `benchmark` reported an installed shell as "Not Found" if the first iteration timed out. It now
  keeps going and reports `timeout` separately. A warm-up pass was added so the first run no longer
  skews the average.
- `rival-gradient` was a byte-for-byte duplicate of `cyber-gradient`, down to the display name. It
  now has its own magenta→teal palette and is registered in the gradient and `bat` maps.
- Every built-in theme now has a `bat` theme mapping; previously 7 of them silently fell back to
  `ansi`.
- Alias names are validated — a name with spaces or shell metacharacters is rejected instead of
  being written into `.bashrc` verbatim.
- Doctor now warns about aliases that shadow core commands. The previous check explicitly excluded
  exactly the dangerous ones.
- `prompt apply` picks the engine from the preset instead of trusting a possibly-misspelled
  `--engine`; `prompt preview` exits non-zero for an unknown preset.
- Windows Terminal: a theme without a `name` key no longer raises `KeyError`.
- `psutil.cpu_percent()` is called with an interval, so the banner no longer always shows 0%.
- Snapshots sort by their manifest timestamp instead of directory name (which sorted by tag first).
- Output is no longer forced to ANSI when stdout is a pipe.
- Unix font scanning recurses into subdirectories.

### Added

- `termcraft uninstall` — removes the TermCraft block from every shell profile.
- `--requires` flag on `alias add`.
- `--exec-policy` flag on `doctor --fix`; changing PowerShell's ExecutionPolicy is now opt-in and
  prompted for instead of happening silently.
- Confirmation prompts before restoring a snapshot (CLI and TUI).
- `tests/conftest.py` isolates `HOME` for every test and stubs `subprocess.run` — running `pytest`
  no longer rewrites the developer's own shell profiles.
- Regression tests for each of the config-destroying bugs above.
- Ruff lint config and a CI lint job; CI also runs a packaged-CLI smoke test.
- Comments throughout the codebase.

### Changed

- TUI diagnostics, tool scan, benchmark and theme/prompt apply run on background workers, so the
  interface no longer freezes. Added `q` (quit) and `r` (refresh) bindings.
- All remaining hardcoded UI strings moved into the i18n table; a test enforces `tr`/`en` parity.
- `bat` theme mapping and fzf color generation live in one place instead of being duplicated
  between `sync.py` and `theme_engine.py`.
- Version is read from a single source (`src/termcraft/__init__.py`) via `hatch.version`.
- Release workflow: per-platform artifact names (all three builds previously produced the same
  filename and overwrote each other), `contents: write` permission, `--collect-all textual`, a
  binary smoke test, and wheel/sdist upload.
- `git commit -m` shortcut renamed `gc` → `gcm`, `gp` → `gpush`, `gpl` → `gpull` to avoid colliding
  with PowerShell's built-in `gc` (Get-Content) and `gp` (Get-ItemProperty) aliases.
- Added `src/termcraft/utils/__init__.py`, which was missing.
