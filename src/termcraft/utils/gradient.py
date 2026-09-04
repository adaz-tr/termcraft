import os
import sys
from typing import List, Tuple
from rich.text import Text

if sys.platform == "win32":
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)
        mode = ctypes.c_ulong()
        kernel32.GetConsoleMode(handle, ctypes.byref(mode))
        kernel32.SetConsoleMode(handle, mode.value | 0x0004 | 0x0001 | 0x0002)
    except Exception:
        pass

# 24-bit gradient motoru. rich'in kendi gradient'i yok, renk aralarini
# elle interpolate edip her karaktere ayri stil basiyoruz
def hex_to_rgb(hex_code: str) -> Tuple[int, int, int]:
    hex_clean = hex_code.lstrip("#")
    # #abc kisa yazimini #aabbcc'ye ac
    if len(hex_clean) == 3:
        hex_clean = "".join(c * 2 for c in hex_clean)
    return int(hex_clean[0:2], 16), int(hex_clean[2:4], 16), int(hex_clean[4:6], 16)

def rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{r:02x}{g:02x}{b:02x}"

def interpolate_color(color1: Tuple[int, int, int], color2: Tuple[int, int, int], factor: float) -> Tuple[int, int, int]:
    r = int(color1[0] + (color2[0] - color1[0]) * factor)
    g = int(color1[1] + (color2[1] - color1[1]) * factor)
    b = int(color1[2] + (color2[2] - color1[2]) * factor)
    return max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b))

def relative_luminance(hex_code: str) -> float:
    """0.0 (siyah) - 1.0 (beyaz). Bir rengin uzerine siyah mi beyaz mi yazacagimiza karar veriyor."""
    r, g, b = hex_to_rgb(hex_code)
    # WCAG'in basitlestirilmis hali, gamma duzeltmesi olmadan da karar icin yeterli
    return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0


def is_dark(hex_code: str) -> bool:
    return relative_luminance(hex_code) < 0.5


def mix_hex(base: str, other: str, factor: float) -> str:
    """base rengini other'a dogru factor kadar (0..1) karistirir."""
    factor = max(0.0, min(1.0, factor))
    return rgb_to_hex(*interpolate_color(hex_to_rgb(base), hex_to_rgb(other), factor))


def readable_on(background: str) -> str:
    """Verilen zemin uzerinde okunur bir metin rengi (siyah ya da beyaz)."""
    return "#000000" if not is_dark(background) else "#ffffff"


def _linear_channel(value: int) -> float:
    c = value / 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def wcag_luminance(hex_code: str) -> float:
    """WCAG'in gamma duzeltilmis bagil parlakligi. contrast_ratio icin gerekli."""
    r, g, b = (_linear_channel(v) for v in hex_to_rgb(hex_code))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(a: str, b: str) -> float:
    """1.0 (ayni renk) - 21.0 (siyah/beyaz) arasi WCAG kontrast orani."""
    la, lb = wcag_luminance(a), wcag_luminance(b)
    lighter, darker = max(la, lb), min(la, lb)
    return (lighter + 0.05) / (darker + 0.05)


def ensure_contrast(color: str, background: str, min_ratio: float = 4.5) -> str:
    """Rengi zeminden yeterince ayrilana kadar koyulastirir ya da aydinlatir.

    Tema paletleri bizim UI zeminlerimiz dusunulerek yapilmiyor; acik temalarda
    (catppuccin-latte) aksan rengi panel uzerinde okunmuyordu. Rengin tonunu
    koruyup sadece parlakligini kaydiriyoruz.
    """
    if contrast_ratio(color, background) >= min_ratio:
        return color
    # zemin acikse rengi siyaha, koyuysa beyaza dogru kaydir
    target = "#000000" if wcag_luminance(background) > 0.5 else "#ffffff"
    best = color
    for step in range(1, 21):
        candidate = mix_hex(color, target, step * 0.05)
        best = candidate
        if contrast_ratio(candidate, background) >= min_ratio:
            break
    return best


def get_gradient_palette(color_stops: List[str], steps: int) -> List[str]:
    # n tane renk durağindan steps kadar ara renk uret.
    # t'yi segmentlere bolup her segment icinde 0..1 arasina yeniden olcekliyoruz
    if steps <= 1:
        return [color_stops[0]] if color_stops else ["#ffffff"]
    if len(color_stops) == 1:
        return [color_stops[0]] * steps
    
    rgb_stops = [hex_to_rgb(c) for c in color_stops]
    result = []
    num_segments = len(rgb_stops) - 1
    
    for i in range(steps):
        t = i / (steps - 1)
        segment = min(int(t * num_segments), num_segments - 1)
        segment_t = (t - (segment / num_segments)) * num_segments
        c = interpolate_color(rgb_stops[segment], rgb_stops[segment + 1], segment_t)
        result.append(rgb_to_hex(*c))
    return result

def is_truecolor_supported() -> bool:
    # tam guvenilir bir yontem yok, terminaller kendini duzgun tanitmiyor.
    # o yuzden bilinen env degiskenlerini sirayla yokluyoruz. son care olarak
    # win10 1607+ ise zaten VT destegi var kabul ediyoruz
    if os.environ.get("COLORTERM", "").lower() in ("truecolor", "24bit"):
        return True
    if os.environ.get("WT_SESSION") is not None:
        return True
    if os.environ.get("WEZTERM_EXECUTABLE") is not None or os.environ.get("WEZTERM_PANE") is not None:
        return True
    if os.environ.get("ALACRITTY_LOG") is not None or os.environ.get("ALACRITTY_WINDOW_ID") is not None:
        return True
    if os.environ.get("KITTY_WINDOW_ID") is not None:
        return True
    term_prog = os.environ.get("TERM_PROGRAM", "").lower()
    if term_prog in ("iterm.app", "vscode", "ghostty", "wezterm", "alacritty", "kitty"):
        return True
    term = os.environ.get("TERM", "").lower()
    if "256color" in term or "xterm" in term:
        return True
    if sys.platform == "win32":
        try:
            ver = sys.getwindowsversion()
            if ver.major >= 10 and ver.build >= 14393:
                return True
        except Exception:
            pass
    return False

# banner ve gradient temalar icin hazir renk duraklari
GRADIENT_PALETTES = {
    "cyber-gradient": ["#00ffff", "#00d4ff", "#0099ff", "#6600ff", "#a800ff", "#ff00cc"],
    "sunset-gradient": ["#ff0055", "#ff5500", "#ff8800", "#ffaa00", "#ffd500"],
    "matrix-gradient": ["#003300", "#008822", "#00cc44", "#00ff66", "#99ffcc"],
    "aurora-gradient": ["#00f0ff", "#5b86e5", "#8a2387", "#e94057", "#f27121"],
    "synthwave-gradient": ["#ff007f", "#ff00cc", "#9900ff", "#00ccff", "#00ffff"],
    "fire-ice-gradient": ["#00f5d4", "#00bbf9", "#fee440", "#f15bb5", "#9b5de5"],
    "deep-space-gradient": ["#0b0c10", "#1f2833", "#45a29e", "#66fcf1", "#c5c6c7"],
    "rival-gradient": ["#ff2d95", "#ff5fa2", "#c04dff", "#7b5cff", "#3ba9ff", "#28e0d4"]
}

def render_gradient_text(raw_text: str, palette_key: str = "cyber-gradient", mode: str = "2d") -> Text:
    # mode sadece "vertical" mi degil mi diye bakiliyor, geri kalan her sey 2d.
    # 2d'de renk indeksi char+line oldugu icin capraz bir gecis olusuyor
    stops = GRADIENT_PALETTES.get(palette_key, GRADIENT_PALETTES["cyber-gradient"])
    result = Text()
    lines = raw_text.splitlines()
    if not lines:
        return result
    
    max_len = max(len(line) for line in lines) if lines else 1
    num_lines = len(lines)
    
    if mode == "vertical":
        line_colors = get_gradient_palette(stops, max(2, num_lines))
        for idx, line in enumerate(lines):
            c = line_colors[min(idx, len(line_colors)-1)]
            result.append(line, style=f"bold {c}")
            if idx < num_lines - 1:
                result.append("\n")
        return result
        
    palette = get_gradient_palette(stops, max(4, max_len + num_lines))
    for line_idx, line in enumerate(lines):
        for char_idx, ch in enumerate(line):
            color_idx = min(char_idx + line_idx, len(palette) - 1)
            result.append(ch, style=f"bold {palette[color_idx]}")
        if line_idx < num_lines - 1:
            result.append("\n")
    return result

def render_gradient_divider(title: str = "", width: int = 70, palette_key: str = "cyber-gradient") -> Text:
    # ortada baslik olan renk gecisli ayirac. baslik cok uzunsa side_len 2'ye
    # sabitleniyor ve cizgi width'i asiyor, ama palet buna gore uretildigi icin
    # index hatasi cikmiyor
    stops = GRADIENT_PALETTES.get(palette_key, GRADIENT_PALETTES["cyber-gradient"])
    if not title:
        palette = get_gradient_palette(stops, max(2, width))
        res = Text()
        for idx in range(width):
            res.append("━", style=f"bold {palette[idx]}")
        return res

    center_text = f" ◆ {title} ◆ "
    side_len = max(2, (width - len(center_text)) // 2)
    total_len = side_len * 2 + len(center_text)
    palette = get_gradient_palette(stops, max(2, total_len))

    res = Text()
    for idx in range(side_len):
        res.append("━", style=f"bold {palette[idx]}")
    for idx, ch in enumerate(center_text):
        res.append(ch, style=f"bold {palette[side_len + idx]}")
    for idx in range(side_len):
        res.append("━", style=f"bold {palette[side_len + len(center_text) + idx]}")
    return res
