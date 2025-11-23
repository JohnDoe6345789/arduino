from __future__ import annotations

import platform
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import (
    Dict,
    Iterable,
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
    TYPE_CHECKING,
)


# =========================
# Procedural ASCII font
# =========================

FONT: Dict[str, List[int]] = {
    "A": [0b01110, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001],
    "B": [0b11110, 0b10001, 0b10001, 0b11110, 0b10001, 0b10001, 0b11110],
    "C": [0b01110, 0b10001, 0b10000, 0b10000, 0b10000, 0b10001, 0b01110],
    "D": [0b11110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b11110],
    "E": [0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b11111],
    "F": [0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b10000],
    "G": [0b01110, 0b10001, 0b10000, 0b10111, 0b10001, 0b10001, 0b01110],
    "H": [0b10001, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001],
    "I": [0b11111, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b11111],
    "J": [0b00111, 0b00010, 0b00010, 0b00010, 0b10010, 0b10010, 0b01100],
    "K": [0b10001, 0b10010, 0b10100, 0b11000, 0b10100, 0b10010, 0b10001],
    "L": [0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b11111],
    "M": [0b10001, 0b11011, 0b10101, 0b10101, 0b10001, 0b10001, 0b10001],
    "N": [0b10001, 0b11001, 0b10101, 0b10101, 0b10011, 0b10001, 0b10001],
    "O": [0b01110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110],
    "P": [0b11110, 0b10001, 0b10001, 0b11110, 0b10000, 0b10000, 0b10000],
    "Q": [0b01110, 0b10001, 0b10001, 0b10001, 0b10101, 0b10010, 0b01101],
    "R": [0b11110, 0b10001, 0b10001, 0b11110, 0b10100, 0b10010, 0b10001],
    "S": [0b01111, 0b10000, 0b10000, 0b01110, 0b00001, 0b00001, 0b11110],
    "T": [0b11111, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100],
    "U": [0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110],
    "V": [0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01010, 0b00100],
    "W": [0b10001, 0b10001, 0b10001, 0b10101, 0b10101, 0b10101, 0b01010],
    "X": [0b10001, 0b10001, 0b01010, 0b00100, 0b01010, 0b10001, 0b10001],
    "Y": [0b10001, 0b10001, 0b01010, 0b00100, 0b00100, 0b00100, 0b00100],
    "Z": [0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b10000, 0b11111],
    "0": [0b01110, 0b10001, 0b10011, 0b10101, 0b11001, 0b10001, 0b01110],
    "1": [0b00100, 0b01100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110],
    "2": [0b01110, 0b10001, 0b00001, 0b00010, 0b00100, 0b01000, 0b11111],
    "3": [0b11110, 0b00001, 0b00001, 0b00110, 0b00001, 0b00001, 0b11110],
    "4": [0b00010, 0b00110, 0b01010, 0b10010, 0b11111, 0b00010, 0b00010],
    "5": [0b11111, 0b10000, 0b11110, 0b00001, 0b00001, 0b10001, 0b01110],
    "6": [0b00110, 0b01000, 0b10000, 0b11110, 0b10001, 0b10001, 0b01110],
    "7": [0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b01000, 0b01000],
    "8": [0b01110, 0b10001, 0b10001, 0b01110, 0b10001, 0b10001, 0b01110],
    "9": [0b01110, 0b10001, 0b10001, 0b01111, 0b00001, 0b00010, 0b01100],
    " ": [0b00000] * 7,
    "-": [0b00000, 0b00000, 0b00000, 0b11111, 0b00000, 0b00000, 0b00000],
    "_": [0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b11111],
}


def render_big_text(
    text: str,
    on: str = "#",
    off: str = " ",
    spacing: int = 1,
    scale: int = 1,
) -> str:
    text = text.upper()
    rows: List[str] = []

    for row in range(7):
        line_chunks: List[str] = []
        for char in text:
            glyph = FONT.get(char, FONT[" "])
            bits = glyph[row]
            pixels: List[str] = []

            for col in range(4, -1, -1):
                filled = bool(bits & (1 << col))
                pixels.append(on if filled else off)

            scaled = "".join(ch * scale for ch in pixels)
            line_chunks.append(scaled)

        line = (" " * spacing).join(line_chunks)

        for _ in range(scale):
            rows.append(line)

    return "\n".join(rows)


def print_ascii_logo(title: str) -> None:
    art = render_big_text(title, on="#", off=" ", spacing=1, scale=1)
    print(art)
    print("-" * max(len(line) for line in art.splitlines()))
    print()


# =========================
# Data models
# =========================

@dataclass(frozen=True)
class CoreInfo:
    arduino_h: Path
    include_dir: Path


@dataclass(frozen=True)
class ToolchainInfo:
    stdlib_h: Path
    include_dir: Path


@dataclass(frozen=True)
class BSPInfo:
    bsp_api_h: Path
    include_dir: Path


@dataclass(frozen=True)
class FSPCommonInfo:
    fsp_common_api_h: Path
    include_dir: Path


@dataclass(frozen=True)
class ComPortInfo:
    device: str
    description: str
    hwid: str
    vid: Optional[int]
    pid: Optional[int]
    manufacturer: Optional[str]
    product: Optional[str]


if TYPE_CHECKING:
    from serial.tools import list_ports_common  # type: ignore[import]


# =========================
# pyserial handling
# =========================

def ensure_pyserial() -> Optional[object]:
    try:
        from serial.tools import list_ports  # type: ignore[import]
        print("[pyserial] Already installed.")
        return list_ports
    except Exception:
        print("[pyserial] Not installed, attempting to install with pip...")

    cmd = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--user",
        "pyserial",
    ]

    print(f"[pyserial] Running: {' '.join(cmd)}")

    try:
        proc = subprocess.run(
            cmd,
            text=True,
            capture_output=True,
        )
    except Exception as exc:
        print(f"[pyserial] pip invocation failed: {exc}")
        return None

    print(f"[pyserial] pip exit code: {proc.returncode}")
    if proc.stdout.strip():
        print("[pyserial] pip stdout:")
        print(proc.stdout.strip())
    if proc.stderr.strip():
        print("[pyserial] pip stderr:")
        print(proc.stderr.strip())

    if proc.returncode != 0:
        print("[pyserial] Install failed; COM port scanning will be disabled.")
        return None

    try:
        from serial.tools import list_ports  # type: ignore[import]
        print("[pyserial] Import after install succeeded.")
        return list_ports
    except Exception as exc:
        print(f"[pyserial] Import still failing after install: {exc}")
        return None


LIST_PORTS = ensure_pyserial()


# =========================
# Utility helpers
# =========================

def resolve_base_dir(argv: Sequence[str]) -> Path:
    if len(argv) > 1:
        return Path(argv[1]).expanduser().resolve()
    return Path(r"C:\Users\richa\Documents\ArduinoData").resolve()


def path_contains_any(path: Path, tokens: Sequence[str]) -> bool:
    lower = str(path).lower()
    return any(t in lower for t in tokens)


# =========================
# Arduino core discovery
# =========================

def find_arduino_headers(base_dir: Path) -> List[CoreInfo]:
    results: List[CoreInfo] = []

    for header in base_dir.rglob("Arduino.h"):
        parts = [p.lower() for p in header.parts]
        if "cores" not in parts:
            continue
        results.append(CoreInfo(arduino_h=header, include_dir=header.parent))

    return _dedupe_cores(results)


def _dedupe_cores(cores: Iterable[CoreInfo]) -> List[CoreInfo]:
    seen: Set[Path] = set()
    unique: List[CoreInfo] = []

    for core in sorted(cores, key=lambda c: str(c.include_dir)):
        if core.include_dir in seen:
            continue
        seen.add(core.include_dir)
        unique.append(core)

    return unique


# =========================
# Toolchain discovery
# =========================

_TOOLCHAIN_TOKENS: Sequence[str] = (
    "gcc",
    "arm-none-eabi",
    "avr",
    "rx-elf",
    "xtensa",
    "riscv",
)


def find_stdlib_headers(base_dir: Path) -> List[ToolchainInfo]:
    results: List[ToolchainInfo] = []

    for header in base_dir.rglob("stdlib.h"):
        if not header.is_file():
            continue
        if header.parent.name != "include":
            continue
        if not path_contains_any(header, _TOOLCHAIN_TOKENS):
            continue
        results.append(ToolchainInfo(stdlib_h=header, include_dir=header.parent))

    return _dedupe_toolchains(results)


def _dedupe_toolchains(
    toolchains: Iterable[ToolchainInfo],
) -> List[ToolchainInfo]:
    seen: Set[Path] = set()
    unique: List[ToolchainInfo] = []

    for tc in sorted(toolchains, key=lambda t: str(t.include_dir)):
        if tc.include_dir in seen:
            continue
        seen.add(tc.include_dir)
        unique.append(tc)

    return unique


# =========================
# BSP API discovery
# =========================

def find_bsp_api_headers(base_dir: Path) -> List[BSPInfo]:
    results: List[BSPInfo] = []

    for header in base_dir.rglob("bsp_api.h"):
        if not header.is_file():
            continue
        results.append(BSPInfo(bsp_api_h=header, include_dir=header.parent))

    return _dedupe_bsp(results)


def _dedupe_bsp(bsp_list: Iterable[BSPInfo]) -> List[BSPInfo]:
    seen: Set[Path] = set()
    unique: List[BSPInfo] = []

    for bsp in sorted(bsp_list, key=lambda b: str(b.include_dir)):
        if bsp.include_dir in seen:
            continue
        seen.add(bsp.include_dir)
        unique.append(bsp)

    return unique


def find_fsp_common_api_headers(base_dir: Path) -> List[FSPCommonInfo]:
    results: List[FSPCommonInfo] = []

    for header in base_dir.rglob("fsp_common_api.h"):
        if not header.is_file():
            continue
        results.append(FSPCommonInfo(fsp_common_api_h=header, include_dir=header.parent))

    return _dedupe_fsp_common(results)


def _dedupe_fsp_common(fsp_list: Iterable[FSPCommonInfo]) -> List[FSPCommonInfo]:
    seen: Set[Path] = set()
    unique: List[FSPCommonInfo] = []

    for fsp in sorted(fsp_list, key=lambda f: str(f.include_dir)):
        if fsp.include_dir in seen:
            continue
        seen.add(fsp.include_dir)
        unique.append(fsp)

    return unique


def find_matching_bsp(
    bsp_list: Sequence[BSPInfo],
    ports: Sequence[ComPortInfo],
) -> Tuple[Optional[BSPInfo], List[BSPInfo]]:
    if not ports or not bsp_list:
        return None, list(bsp_list)

    detected_port = None
    for p in ports:
        if p.vid in (0x2341, 0x2A03):
            detected_port = p
            break
    
    if detected_port is None:
        detected_port = ports[0] if ports else None

    if detected_port is None:
        return None, list(bsp_list)

    board_short = short_board_name(detected_port.vid, detected_port.pid)
    variant_names = _BOARD_TO_VARIANT.get(board_short)

    if variant_names is None:
        return None, list(bsp_list)

    if not isinstance(variant_names, list):
        variant_names = [variant_names]

    for variant_name in variant_names:
        for bsp in bsp_list:
            bsp_path_lower = str(bsp.bsp_api_h).lower()
            if variant_name.lower() in bsp_path_lower:
                remaining = [b for b in bsp_list if b != bsp]
                return bsp, remaining

    return None, list(bsp_list)


def find_matching_fsp_common(
    fsp_list: Sequence[FSPCommonInfo],
    ports: Sequence[ComPortInfo],
) -> Tuple[Optional[FSPCommonInfo], List[FSPCommonInfo]]:
    if not ports or not fsp_list:
        return None, list(fsp_list)

    detected_port = None
    for p in ports:
        if p.vid in (0x2341, 0x2A03):
            detected_port = p
            break
    
    if detected_port is None:
        detected_port = ports[0] if ports else None

    if detected_port is None:
        return None, list(fsp_list)

    board_short = short_board_name(detected_port.vid, detected_port.pid)
    variant_names = _BOARD_TO_VARIANT.get(board_short)

    if variant_names is None:
        return None, list(fsp_list)

    if not isinstance(variant_names, list):
        variant_names = [variant_names]

    for variant_name in variant_names:
        for fsp in fsp_list:
            fsp_path_lower = str(fsp.fsp_common_api_h).lower()
            if variant_name.lower() in fsp_path_lower:
                remaining = [f for f in fsp_list if f != fsp]
                return fsp, remaining

    return None, list(fsp_list)


# =========================
# Header "friends" with fallback search
# =========================

_CORE_FRIENDS: Sequence[str] = (
    "WString.h",
    "HardwareSerial.h",
    "Print.h",
    "Stream.h",
)

_CLIB_FRIENDS: Sequence[str] = (
    "stdlib.h",
    "stdio.h",
    "string.h",
    "stdint.h",
    "stdbool.h",
    "math.h",
    "ctype.h",
    "time.h",
    "limits.h",
    "float.h",
    "errno.h",
    "stddef.h",
    "signal.h",
)


def friends_status(
    include_dir: Path,
    friends: Sequence[str],
    search_root: Optional[Path],
) -> List[Tuple[str, List[Path]]]:
    """
    For each friend header, return (name, [paths]).
    paths:
      - empty => genuinely missing
      - contains include_dir/name => present in primary include dir
      - one other entry => found elsewhere under search_root
    """
    statuses: List[Tuple[str, List[Path]]] = []

    for name in sorted(friends):
        primary = include_dir / name
        found: List[Path] = []

        if primary.is_file():
            found.append(primary)

        if not found and search_root is not None and search_root.is_dir():
            for p in search_root.rglob(name):
                if not p.is_file():
                    continue
                if p == primary:
                    continue
                found.append(p)
                # only keep a single alternative to avoid spam / duplicates
                break

        statuses.append((name, found))

    return statuses


# =========================
# COM port detection + board guessing
# =========================

_BOARD_MAP: Dict[Tuple[int, int], str] = {
    (0x2341, 0x0043): "Arduino Uno (ATmega16U2)",
    (0x2341, 0x0001): "Arduino Uno (old bootloader)",
    (0x2341, 0x0010): "Arduino Mega 2560",
    (0x2341, 0x8036): "Arduino Leonardo / Micro",
    (0x2341, 0x805A): "Arduino UNO R4 (family, best guess)",
    (0x2341, 0x0074): "Arduino R4 Family (UNO R4 WiFi/Minima or NANO R4)",
    (0x2A03, 0x0043): "Arduino Uno (2A03 VID)",
    (0x1A86, 0x7523): "CH340/CH341 USB–Serial (clone/adapter)",
    (0x10C4, 0xEA60): "Silicon Labs CP2102 USB–Serial",
}


def guess_board(vid: Optional[int], pid: Optional[int]) -> str:
    if vid is None or pid is None:
        return "Unknown device (no VID/PID)"

    key = (vid, pid)
    if key in _BOARD_MAP:
        return _BOARD_MAP[key]

    if vid == 0x2341 or vid == 0x2A03:
        return "Arduino (exact model unknown)"
    if vid == 0x1A86:
        return "CH340-based Arduino/adapter"
    if vid == 0x10C4:
        return "CP210x-based Arduino/adapter"

    return "Unknown device (unmapped VID/PID)"


_BOARD_TO_VARIANT: Dict[str, List[str]] = {
    "UNO": ["UNOWIFIR4"],
    "UNO R4": ["UNOWIFIR4"],
    "NANO": ["NANOR4"],
    "NANO R4": ["NANOR4"],
    "MINIMA": ["MINIMA"],
    "R4 FAMILY": ["NANOR4", "UNOWIFIR4", "MINIMA"],
}


def short_board_name(vid: Optional[int], pid: Optional[int]) -> str:
    if vid is None or pid is None:
        return "SCAN"

    key = (vid, pid)

    if key in {
        (0x2341, 0x0043),
        (0x2341, 0x0001),
        (0x2A03, 0x0043),
    }:
        return "UNO"

    if key == (0x2341, 0x0010):
        return "MEGA"

    if key == (0x2341, 0x8036):
        return "LEONARDO"

    if key == (0x2341, 0x805A):
        return "UNO R4"

    if key == (0x2341, 0x0074):
        return "R4 FAMILY"

    if vid == 0x1A86:
        return "CH340"

    if vid == 0x10C4:
        return "CP210X"

    if vid in {0x2341, 0x2A03}:
        return "ARDUINO"

    return "SCAN"


def scan_com_ports() -> List[ComPortInfo]:
    if LIST_PORTS is None:
        return []

    ports = LIST_PORTS.comports()  # type: ignore[attr-defined]
    results: List[ComPortInfo] = []

    for p in ports:
        vid = getattr(p, "vid", None)
        pid = getattr(p, "pid", None)
        manufacturer = getattr(p, "manufacturer", None)
        product = getattr(p, "product", None)

        results.append(
            ComPortInfo(
                device=str(p.device),
                description=str(p.description),
                hwid=str(p.hwid),
                vid=vid,
                pid=pid,
                manufacturer=manufacturer,
                product=product,
            )
        )

    return results


def derive_banner_title(ports: Sequence[ComPortInfo]) -> str:
    if not ports:
        return "ARDUINO SCAN"

    arduino_ports: List[ComPortInfo] = []
    other_ports: List[ComPortInfo] = []

    for p in ports:
        if p.vid in (0x2341, 0x2A03):
            arduino_ports.append(p)
        else:
            other_ports.append(p)

    if arduino_ports:
        target = arduino_ports[0]
    else:
        target = other_ports[0] if other_ports else None

    if target is None:
        return "ARDUINO SCAN"

    short = short_board_name(target.vid, target.pid)
    return f"ARDUINO {short}"


# =========================
# Pretty printing helpers
# =========================

def print_rule(char: str = "─", width: int = 72) -> None:
    print(char * width)


def print_section(title: str) -> None:
    print_rule("=")
    print(title)
    print_rule("=")


def indent(text: str, prefix: str = "  ") -> str:
    return "\n".join(prefix + line for line in text.splitlines())


# =========================
# Neofetch-style printing
# =========================

def print_system_neofetch(base_dir: Path) -> None:
    print_section("Arduino Neofetch")
    print(f"User        : {Path.home().name}")
    print(f"OS          : {platform.system()} {platform.release()}")
    print(f"Python      : {platform.python_version()}")
    print(f"Arch        : {platform.machine()}")
    print(f"ArduinoDir  : {base_dir}")
    print(f"PythonExe   : {sys.executable}")
    print()


def print_cores(
    cores: Sequence[CoreInfo],
    extra_core_includes: Set[Path],
) -> None:
    print_section("Arduino cores (Arduino.h and friends)")
    print(f"Discovered cores: {len(cores)}\n")

    if not cores:
        print("No Arduino cores (Arduino.h) found.\n")
        return

    for idx, core in enumerate(cores, start=1):
        print(f"[Core #{idx}]")
        print("  Arduino.h full path:")
        print(indent(str(core.arduino_h), "    "))
        print("  Include directory (-I):")
        print(indent(str(core.include_dir), "    "))

        parents = list(core.include_dir.parents)
        hw_root = parents[2] if len(parents) > 2 else core.include_dir

        status_list = friends_status(core.include_dir, _CORE_FRIENDS, hw_root)
        print("  Core header friends (present / elsewhere / missing):")
        for name, paths in status_list:
            primary = core.include_dir / name
            if not paths:
                print(f"    [MISS] {name} (not found under {hw_root})")
                continue
            for p in paths:
                label = "[OK]" if p == primary else "[ALT]"
                print(f"    {label}  {name} -> {p}")
                if p.parent != core.include_dir:
                    extra_core_includes.add(p.parent)

        print()


def print_toolchains(
    toolchains: Sequence[ToolchainInfo],
    extra_tc_includes: Set[Path],
) -> None:
    print_section("Toolchain C library (stdlib.h and friends)")
    print(f"Discovered toolchains: {len(toolchains)}\n")

    if not toolchains:
        print("No toolchain C library headers (stdlib.h) found.\n")
        return

    for idx, tc in enumerate(toolchains, start=1):
        print(f"[Toolchain #{idx}]")
        print("  stdlib.h full path:")
        print(indent(str(tc.stdlib_h), "    "))
        print("  Include directory (-I):")
        print(indent(str(tc.include_dir), "    "))

        parents = list(tc.include_dir.parents)
        if len(parents) > 1:
            tc_root = parents[1]
        else:
            tc_root = tc.include_dir

        status_list = friends_status(tc.include_dir, _CLIB_FRIENDS, tc_root)
        print("  C library header friends (present / elsewhere / missing):")
        for name, paths in status_list:
            primary = tc.include_dir / name
            if not paths:
                print(f"    [MISS] {name} (not found under {tc_root})")
                continue
            for p in paths:
                label = "[OK]" if p == primary else "[ALT]"
                print(f"    {label}  {name} -> {p}")
                if p.parent != tc.include_dir:
                    extra_tc_includes.add(p.parent)

        print()

    print("Best-guess default toolchain include dir (-I):")
    print(indent(str(toolchains[0].include_dir), "  "))
    print()


def print_bsp(bsp_list: Sequence[BSPInfo], ports: Sequence[ComPortInfo]) -> None:
    print_section("BSP API (bsp_api.h)")
    print(f"Discovered BSP headers: {len(bsp_list)}\n")

    if not bsp_list:
        print("No BSP API headers (bsp_api.h) found.\n")
        return

    matched_bsp, remaining = find_matching_bsp(bsp_list, ports)

    if matched_bsp is not None:
        print("[BSP #1] [MATCHED TO DETECTED BOARD]")
        print("  bsp_api.h full path:")
        print(indent(str(matched_bsp.bsp_api_h), "    "))
        print("  Include directory (-I):")
        print(indent(str(matched_bsp.include_dir), "    "))
        print()

        for idx, bsp in enumerate(remaining, start=2):
            print(f"[BSP #{idx}]")
            print("  bsp_api.h full path:")
            print(indent(str(bsp.bsp_api_h), "    "))
            print("  Include directory (-I):")
            print(indent(str(bsp.include_dir), "    "))
            print()
    else:
        for idx, bsp in enumerate(bsp_list, start=1):
            print(f"[BSP #{idx}]")
            print("  bsp_api.h full path:")
            print(indent(str(bsp.bsp_api_h), "    "))
            print("  Include directory (-I):")
            print(indent(str(bsp.include_dir), "    "))
            print()


def print_fsp_common(fsp_list: Sequence[FSPCommonInfo], ports: Sequence[ComPortInfo]) -> None:
    print_section("FSP Common API (fsp_common_api.h)")
    print(f"Discovered FSP common headers: {len(fsp_list)}\n")

    if not fsp_list:
        print("No FSP common API headers (fsp_common_api.h) found.\n")
        return

    matched_fsp, remaining = find_matching_fsp_common(fsp_list, ports)

    if matched_fsp is not None:
        print("[FSP #1] [MATCHED TO DETECTED BOARD]")
        print("  fsp_common_api.h full path:")
        print(indent(str(matched_fsp.fsp_common_api_h), "    "))
        print("  Include directory (-I):")
        print(indent(str(matched_fsp.include_dir), "    "))
        print()

        for idx, fsp in enumerate(remaining, start=2):
            print(f"[FSP #{idx}]")
            print("  fsp_common_api.h full path:")
            print(indent(str(fsp.fsp_common_api_h), "    "))
            print("  Include directory (-I):")
            print(indent(str(fsp.include_dir), "    "))
            print()
    else:
        for idx, fsp in enumerate(fsp_list, start=1):
            print(f"[FSP #{idx}]")
            print("  fsp_common_api.h full path:")
            print(indent(str(fsp.fsp_common_api_h), "    "))
            print("  Include directory (-I):")
            print(indent(str(fsp.include_dir), "    "))
            print()


def print_com_ports(ports: Sequence[ComPortInfo]) -> None:
    print_section("Serial / COM ports")

    if LIST_PORTS is None:
        print("pyserial is not available; COM port scan disabled.\n")
        return

    print(f"Detected COM ports: {len(ports)}\n")

    if not ports:
        print("No COM ports found.\n")
        return

    for idx, port in enumerate(ports, start=1):
        board_guess = guess_board(port.vid, port.pid)

        print(f"[Port #{idx}] {port.device}")
        print(f"  Description : {port.description}")
        print(f"  HWID        : {port.hwid}")

        if port.vid is not None and port.pid is not None:
            print(f"  VID/PID     : 0x{port.vid:04X} / 0x{port.pid:04X}")
        else:
            print("  VID/PID     : (not available)")

        if port.manufacturer or port.product:
            print("  USB strings :")
            if port.manufacturer:
                print(f"    Manufacturer : {port.manufacturer}")
            if port.product:
                print(f"    Product      : {port.product}")

        print(f"  Board guess : {board_guess}")
        print()


def print_suggested_flags(
    cores: Sequence[CoreInfo],
    toolchains: Sequence[ToolchainInfo],
    bsp_headers: Sequence[BSPInfo],
    extra_core_includes: Set[Path],
    extra_tc_includes: Set[Path],
    fsp_headers: Sequence[FSPCommonInfo] = None,
) -> None:
    if fsp_headers is None:
        fsp_headers = []

    print_section("Suggested -I include flags")

    print("Arduino core include paths:")
    if cores:
        for c in cores:
            print(f'  -I"{c.include_dir}"')
    else:
        print("  (none found)")

    if extra_core_includes:
        print("\nExtra Arduino core friend include paths:")
        for p in sorted(extra_core_includes, key=str):
            print(f'  -I"{p}"')

    print()

    print("Toolchain C library include paths:")
    if toolchains:
        for t in toolchains:
            print(f'  -I"{t.include_dir}"')
    else:
        print("  (none found)")

    if extra_tc_includes:
        print("\nExtra toolchain friend include paths:")
        for p in sorted(extra_tc_includes, key=str):
            print(f'  -I"{p}"')

    print()

    print("BSP API include paths:")
    if bsp_headers:
        for b in bsp_headers:
            print(f'  -I"{b.include_dir}"')
    else:
        print("  (none found)")

    print()

    print("FSP Common API include paths:")
    if fsp_headers:
        for f in fsp_headers:
            print(f'  -I"{f.include_dir}"')
    else:
        print("  (none found)")

    print()


# =========================
# Main
# =========================

def main(argv: Sequence[str]) -> None:
    base_dir = resolve_base_dir(argv)

    if not base_dir.is_dir():
        print(f"[error] Base directory does not exist: {base_dir}", file=sys.stderr)
        sys.exit(1)

    ports = scan_com_ports()
    banner_title = derive_banner_title(ports)
    print_ascii_logo(banner_title)

    print_system_neofetch(base_dir)

    cores = find_arduino_headers(base_dir)
    toolchains = find_stdlib_headers(base_dir)
    bsp_headers = find_bsp_api_headers(base_dir)
    fsp_common_headers = find_fsp_common_api_headers(base_dir)

    extra_core_includes: Set[Path] = set()
    extra_tc_includes: Set[Path] = set()

    print_cores(cores, extra_core_includes)
    print_toolchains(toolchains, extra_tc_includes)
    print_bsp(bsp_headers, ports)
    print_fsp_common(fsp_common_headers, ports)
    print_com_ports(ports)
    
    matched_bsp, _ = find_matching_bsp(bsp_headers, ports)
    suggested_bsp = [matched_bsp] if matched_bsp else bsp_headers
    matched_fsp, _ = find_matching_fsp_common(fsp_common_headers, ports)
    suggested_fsp = [matched_fsp] if matched_fsp else fsp_common_headers
    print_suggested_flags(cores, toolchains, suggested_bsp, extra_core_includes, extra_tc_includes, suggested_fsp)


if __name__ == "__main__":
    main(sys.argv)
