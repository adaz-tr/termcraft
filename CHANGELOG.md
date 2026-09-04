# Changelog

All notable changes to this project are documented here.
Format loosely follows [Keep a Changelog](https://keepachangelog.com/),
and versions follow [Semantic Versioning](https://semver.org/).

## [1.0.0] — 2026-09-04

First release.

### Themes

- 23 built-in palettes, including 8 with 24-bit RGB gradients.
- One command applies a theme to Windows Terminal, Alacritty, WezTerm and Kitty **and** to your
  shell tools (`bat` syntax theme, `fzf` colors) at the same time.
- Custom themes: drop a JSON or YAML file into `~/.termcraft/themes/` and it shows up in
  `termcraft theme list`.
- Live preview in both the CLI (`theme preview`) and the studio.

### Prompts

- Starship and Oh-My-Posh presets, written straight to the right config path.
- The engine is derived from the preset, so a misspelled `--engine` cannot apply the wrong one.

### Aliases

- Define once, synchronize to PowerShell, Bash, Zsh, Fish and NuShell, each with correct quoting
  for that shell.
- Bundled packs for Git, Docker and dev tooling, plus an opt-in `modern-replacements` pack.
- Aliases can declare the binary they need (`--requires`); if the tool is not installed the alias
  is skipped rather than shadowing a core command with something that does not exist.
- Alias names are validated before they reach a shell profile.

### Studio (TUI)

- Full-screen Textual dashboard: themes, prompts, aliases, doctor, benchmark, tools, backups,
  language.
- The studio recolors itself to match the selected theme, so you see a palette in place before
  applying it. Accent colors are shifted until they clear a WCAG contrast threshold against the
  panel behind them, so light palettes stay readable.
- Diagnostics, tool scans, benchmarks and theme application run on background workers, so the UI
  does not freeze.

### Diagnostics & tooling

- `termcraft doctor` checks TrueColor support, Nerd Fonts, broken and duplicate `PATH` entries,
  UTF-8 readiness, alias shadowing, and missing alias requirements.
- `termcraft benchmark` measures shell startup latency with a warm-up pass, and reports timeouts
  distinctly from "not installed".
- `termcraft tools list` detects `eza`, `bat`, `zoxide`, `ripgrep`, `fzf`, `fastfetch`, `lazygit`,
  `fd`, Starship and Oh-My-Posh, and prints the install command for your OS.

### Safety

Everything TermCraft writes to a config file was built around not breaking what is already there:

- All shell edits live between `# >>> termcraft initialize >>>` markers; your own lines are never
  touched, and `termcraft uninstall` removes the block cleanly.
- `auto_backup` snapshots your shell, terminal and prompt configs before any theme or prompt is
  applied, and `backup restore` snapshots the current state before overwriting it.
- WezTerm colors go to a sidecar `termcraft_colors.lua` and the hook is inserted *before* the
  file's final `return`, because Lua requires `return` to be the last statement in a block.
- Alacritty color tables are replaced rather than appended, because TOML rejects a duplicate
  `[colors.*]` table.
- An unreadable `config.yaml` is quarantined to `config.broken-<timestamp>.yaml` instead of being
  silently replaced with defaults.
- Changing PowerShell's ExecutionPolicy is opt-in and prompted for, never silent.

### i18n

- Full Türkçe and English across the CLI, diagnostics and studio, with a test enforcing key parity
  between the two.

### Notes

- Not published to PyPI. Install from the standalone binaries attached to each release, or from
  source.
