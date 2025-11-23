from __future__ import annotations

import argparse
import platform
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Mapping,
    Optional,
    Protocol,
    Sequence,
    Set,
    Tuple,
    TypeVar,
    TypedDict,
    cast,
)


# =========================
# User-facing strings
# =========================

STRINGS: Dict[str, str] = {
    # CLI / description / errors
    "app_description": "Scan Arduino core, toolchain, and FSP/BSP headers.",
    "arg_base_dir_help": (
        "Base directory to scan (defaults to common Arduino data locations)."
    ),
    "err_base_dir_missing": "Base directory does not exist: {path}",

    # pyserial
    "pyserial_already": "[pyserial] Already installed.",
    "pyserial_not_installed": "[pyserial] Not installed, attempting to install with pip...",
    "pyserial_running_cmd": "[pyserial] Running: {cmd}",
    "pyserial_pip_failed": "[pyserial] pip invocation failed: {exc}",
    "pyserial_pip_exit": "[pyserial] pip exit code: {code}",
    "pyserial_pip_stdout_header": "[pyserial] pip stdout:",
    "pyserial_pip_stderr_header": "[pyserial] pip stderr:",
    "pyserial_install_failed": "[pyserial] Install failed; COM port scanning will be disabled.",
    "pyserial_import_after_install_ok": "[pyserial] Import after install succeeded.",
    "pyserial_import_after_install_failed": (
        "[pyserial] Import still failing after install: {exc}"
    ),

    # Neofetch section
    "section_neofetch_title": "Arduino Neofetch",
    "neofetch_user_label": "User        : {value}",
    "neofetch_os_label": "OS          : {value}",
    "neofetch_python_label": "Python      : {value}",
    "neofetch_arch_label": "Arch        : {value}",
    "neofetch_arduino_dir_label": "ArduinoDir  : {value}",
    "neofetch_python_exe_label": "PythonExe   : {value}",

    # Core section
    "section_cores_title": "Arduino cores (Arduino.h and friends)",
    "section_cores_discovered": "Discovered cores: {count}",
    "section_cores_none": "No Arduino cores (Arduino.h) found.",
    "section_core_header": "[Core #{index}]",
    "section_core_arduino_path": "  Arduino.h full path:",
    "section_core_include_dir": "  Include directory (-I):",

    # Toolchain section
    "section_toolchains_title": "Toolchain C library (stdlib.h and friends)",
    "section_toolchains_discovered": "Discovered toolchains: {count}",
    "section_toolchains_none": "No toolchain C library headers (stdlib.h) found.",
    "section_toolchain_header": "[Toolchain #{index}]",
    "section_toolchain_stdlib_path": "  stdlib.h full path:",
    "section_toolchain_include_dir": "  Include directory (-I):",
    "section_toolchain_compiler_path": "  Compiler path:",
    "section_toolchain_best_guess": "Best-guess default toolchain include dir (-I):",

    # Friend headers labels
    "friends_label_core": "Core header friends (present / elsewhere / missing):",
    "friends_label_toolchain": (
        "C library header friends (present / elsewhere / missing):"
    ),
    "friends_label_generic": "{label} (present / elsewhere / missing):",
    "friends_missing": "[MISS] {name} (not found under {root})",
    "friends_ok": "[OK]",
    "friends_alt": "[ALT]",

    # Serial / COM ports section
    "section_com_title": "Serial / COM ports",
    "section_com_pyserial_missing": "pyserial is not available; COM port scan disabled.",
    "section_com_detected": "Detected COM ports: {count}",
    "section_com_none": "No COM ports found.",
    "section_com_port_header": "[Port #{index}] {device}",
    "section_com_description": "  Description : {value}",
    "section_com_hwid": "  HWID        : {value}",
    "section_com_vid_pid": "  VID/PID     : 0x{vid:04X} / 0x{pid:04X}",
    "section_com_vid_pid_missing": "  VID/PID     : (not available)",
    "section_com_usb_strings": "  USB strings :",
    "section_com_manufacturer": "    Manufacturer : {value}",
    "section_com_product": "    Product      : {value}",
    "section_com_board_guess": "  Board guess : {value}",

    # Board descriptions
    "board_arduino_uno_atmega16u2": "Arduino Uno (ATmega16U2)",
    "board_arduino_uno_old": "Arduino Uno (old bootloader)",
    "board_arduino_mega_2560": "Arduino Mega 2560",
    "board_arduino_leonardo_micro": "Arduino Leonardo / Micro",
    "board_arduino_uno_r4_family": "Arduino UNO R4 (family, best guess)",
    "board_arduino_r4_family": "Arduino R4 Family (UNO R4 WiFi/Minima or NANO R4)",
    "board_arduino_uno_2a03": "Arduino Uno (2A03 VID)",
    "board_ch340": "CH340/CH341 USB–Serial (clone/adapter)",
    "board_cp2102": "Silicon Labs CP2102 USB–Serial",
    "board_arduino_exact_unknown": "Arduino (exact model unknown)",
    "board_ch340_based": "CH340-based Arduino/adapter",
    "board_cp210x_based": "CP210x-based Arduino/adapter",
    "board_unknown_no_vid_pid": "Unknown device (no VID/PID)",
    "board_unknown_unmapped": "Unknown device (unmapped VID/PID)",

    # Banner titles
    "banner_default": "ARDUINO SCAN",
    "banner_arduino_prefix": "ARDUINO {short}",

    # Suggested flags section
    "section_flags_title": "Suggested -I include flags",
    "flags_arduino_paths_title": "Arduino core include paths:",
    "flags_toolchain_paths_title": "Toolchain C library include paths:",
    "flags_none_found": "  (none found)",
    "flags_extra_core_paths_title": "Extra Arduino core friend include paths:",
    "flags_extra_toolchain_paths_title": "Extra toolchain friend include paths:",
    "flags_group_label": "{label} include paths:",
    "flags_compiler_label": '  Compiler: "{path}"',

    # Flags group labels
    "flags_group_bsp": "BSP API",
    "flags_group_bsp_cfg": "BSP Configuration",
    "flags_group_hal_data": "HAL Data",
    "flags_group_fsp_common": "FSP Common API",
    "flags_group_cmsis": "CMSIS",
    "flags_group_r_cgc": "R_CGC",
    "flags_group_r_cgc_cfg": "R_CGC Configuration",
    "flags_group_fsp_module_cfg": "FSP Module Configuration",

    # Header generic section text
    "section_header_discovered": "{label}: {count}",
    "section_header_none": "{message}",
    "section_header_item_header": "[{item_label} #{index}]{suffix}",
    "section_header_full_path": "  {desc} full path:",
    "section_header_include_dir": "  Include directory (-I):",
    "section_header_match_suffix": " [MATCHED TO DETECTED BOARD]",

    # Header group specific (titles & messages)
    "section_bsp_title": "BSP API (bsp_api.h)",
    "section_bsp_discovered": "Discovered BSP headers",
    "section_bsp_none": "No BSP API headers (bsp_api.h) found.",

    "section_fsp_common_title": "FSP Common API (fsp_common_api.h)",
    "section_fsp_common_discovered": "Discovered FSP common headers",
    "section_fsp_common_none": "No FSP common API headers (fsp_common_api.h) found.",

    "section_bsp_cfg_title": "BSP Configuration (bsp_cfg.h)",
    "section_bsp_cfg_discovered": "Discovered BSP config headers",
    "section_bsp_cfg_none": "No BSP config headers (bsp_cfg.h) found.",

    "section_hal_data_title": "HAL Data (hal_data.h)",
    "section_hal_data_discovered": "Discovered HAL data headers",
    "section_hal_data_none": "No HAL data headers (hal_data.h) found.",

    "section_cmsis_title": "CMSIS Headers",
    "section_cmsis_discovered": "Discovered CMSIS headers",
    "section_cmsis_none": "No CMSIS headers found.",

    "section_r_cgc_title": "R_CGC Headers",
    "section_r_cgc_discovered": "Discovered R_CGC headers",
    "section_r_cgc_none": "No R_CGC headers (r_cgc.h) found.",

    "section_r_cgc_cfg_title": "R_CGC Configuration (r_cgc_cfg.h)",
    "section_r_cgc_cfg_discovered": "Discovered R_CGC config headers",
    "section_r_cgc_cfg_none": "No R_CGC config headers (r_cgc_cfg.h) found.",

    "section_fsp_module_cfg_title": "FSP Module Configuration (r_*_cfg.h)",
    "section_fsp_module_cfg_discovered": "Discovered FSP module config headers",
    "section_fsp_module_cfg_none": "No FSP module config headers (r_*_cfg.h) found.",
}


def S(key: str) -> str:
    # Strict lookup; if you want softer behavior, change to .get with fallback
    return STRINGS[key]


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


# =========================
# Static configuration (typed)
# =========================

TOOLCHAIN_TOKENS: Tuple[str, ...] = (
    "gcc",
    "arm-none-eabi",
    "avr",
    "rx-elf",
    "xtensa",
    "riscv",
)

CORE_FRIENDS: Tuple[str, ...] = (
    "WString.h",
    "HardwareSerial.h",
    "Print.h",
    "Stream.h",
)

CLIB_FRIENDS: Tuple[str, ...] = (
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


class HeaderGroupConfig(TypedDict):
    section_title_key: str
    discovered_label_key: str
    none_found_key: str
    item_label: str
    header_desc: str
    header_attr: str
    include_attr: str


HEADER_GROUP_ORDER: Tuple[str, ...] = (
    "bsp",
    "fsp_common",
    "bsp_cfg",
    "hal_data",
    "cmsis",
    "r_cgc",
    "r_cgc_cfg",
    "fsp_module_cfg",
)

HEADER_GROUPS: Dict[str, HeaderGroupConfig] = {
    "bsp": {
        "section_title_key": "section_bsp_title",
        "discovered_label_key": "section_bsp_discovered",
        "none_found_key": "section_bsp_none",
        "item_label": "BSP",
        "header_desc": "bsp_api.h",
        "header_attr": "bsp_api_h",
        "include_attr": "include_dir",
    },
    "fsp_common": {
        "section_title_key": "section_fsp_common_title",
        "discovered_label_key": "section_fsp_common_discovered",
        "none_found_key": "section_fsp_common_none",
        "item_label": "FSP",
        "header_desc": "fsp_common_api.h",
        "header_attr": "fsp_common_api_h",
        "include_attr": "include_dir",
    },
    "bsp_cfg": {
        "section_title_key": "section_bsp_cfg_title",
        "discovered_label_key": "section_bsp_cfg_discovered",
        "none_found_key": "section_bsp_cfg_none",
        "item_label": "BSP Config",
        "header_desc": "bsp_cfg.h",
        "header_attr": "bsp_cfg_h",
        "include_attr": "include_dir",
    },
    "hal_data": {
        "section_title_key": "section_hal_data_title",
        "discovered_label_key": "section_hal_data_discovered",
        "none_found_key": "section_hal_data_none",
        "item_label": "HAL Data",
        "header_desc": "hal_data.h",
        "header_attr": "hal_data_h",
        "include_attr": "include_dir",
    },
    "cmsis": {
        "section_title_key": "section_cmsis_title",
        "discovered_label_key": "section_cmsis_discovered",
        "none_found_key": "section_cmsis_none",
        "item_label": "CMSIS",
        "header_desc": "Header",
        "header_attr": "cmsis_h",
        "include_attr": "include_dir",
    },
    "r_cgc": {
        "section_title_key": "section_r_cgc_title",
        "discovered_label_key": "section_r_cgc_discovered",
        "none_found_key": "section_r_cgc_none",
        "item_label": "R_CGC",
        "header_desc": "r_cgc.h",
        "header_attr": "r_cgc_h",
        "include_attr": "include_dir",
    },
    "r_cgc_cfg": {
        "section_title_key": "section_r_cgc_cfg_title",
        "discovered_label_key": "section_r_cgc_cfg_discovered",
        "none_found_key": "section_r_cgc_cfg_none",
        "item_label": "R_CGC Config",
        "header_desc": "r_cgc_cfg.h",
        "header_attr": "r_cgc_cfg_h",
        "include_attr": "include_dir",
    },
    "fsp_module_cfg": {
        "section_title_key": "section_fsp_module_cfg_title",
        "discovered_label_key": "section_fsp_module_cfg_discovered",
        "none_found_key": "section_fsp_module_cfg_none",
        "item_label": "FSP Module Config",
        "header_desc": "Config header",
        "header_attr": "cfg_h",
        "include_attr": "include_dir",
    },
}

FLAGS_GROUP_LABEL_KEYS: Dict[str, str] = {
    "bsp": "flags_group_bsp",
    "bsp_cfg": "flags_group_bsp_cfg",
    "hal_data": "flags_group_hal_data",
    "fsp_common": "flags_group_fsp_common",
    "cmsis": "flags_group_cmsis",
    "r_cgc": "flags_group_r_cgc",
    "r_cgc_cfg": "flags_group_r_cgc_cfg",
    "fsp_module_cfg": "flags_group_fsp_module_cfg",
}

VID_PID_TO_STRING_KEY: Dict[Tuple[int, int], str] = {
    (0x2341, 0x0043): "board_arduino_uno_atmega16u2",
    (0x2341, 0x0001): "board_arduino_uno_old",
    (0x2341, 0x0010): "board_arduino_mega_2560",
    (0x2341, 0x8036): "board_arduino_leonardo_micro",
    (0x2341, 0x805A): "board_arduino_uno_r4_family",
    (0x2341, 0x0074): "board_arduino_r4_family",
    (0x2A03, 0x0043): "board_arduino_uno_2a03",
    (0x1A86, 0x7523): "board_ch340",
    (0x10C4, 0xEA60): "board_cp2102",
}

BOARD_VARIANTS: Dict[str, List[str]] = {
    "UNO": ["UNOWIFIR4"],
    "UNO R4": ["UNOWIFIR4"],
    "NANO": ["NANOR4"],
    "NANO R4": ["NANOR4"],
    "MINIMA": ["MINIMA"],
    "R4 FAMILY": ["NANOR4", "UNOWIFIR4", "MINIMA"],
}

SHORT_NAME_MAP: Dict[Tuple[int, int], str] = {
    (0x2341, 0x0043): "UNO",
    (0x2341, 0x0001): "UNO",
    (0x2A03, 0x0043): "UNO",
    (0x2341, 0x0010): "MEGA",
    (0x2341, 0x8036): "LEONARDO",
    (0x2341, 0x805A): "UNO R4",
    (0x2341, 0x0074): "R4 FAMILY",
}

VENDOR_SHORT_FALLBACK: Dict[int, str] = {
    0x1A86: "CH340",
    0x10C4: "CP210X",
}

ARDUINO_VIDS: Tuple[int, ...] = (0x2341, 0x2A03)

PIPELINE_ORDER: Tuple[str, ...] = (
    "banner",
    "cores",
    "toolchains",
    "header_groups",
    "com_ports",
    "flags",
)


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
    compiler_path: Optional[Path] = None


@dataclass(frozen=True)
class BSPInfo:
    bsp_api_h: Path
    include_dir: Path


@dataclass(frozen=True)
class FSPCommonInfo:
    fsp_common_api_h: Path
    include_dir: Path


@dataclass(frozen=True)
class BSPCfgInfo:
    bsp_cfg_h: Path
    include_dir: Path


@dataclass(frozen=True)
class HALDataInfo:
    hal_data_h: Path
    include_dir: Path


@dataclass(frozen=True)
class CMSISInfo:
    cmsis_h: Path
    include_dir: Path


@dataclass(frozen=True)
class RCGCInfo:
    r_cgc_h: Path
    include_dir: Path


@dataclass(frozen=True)
class RCGCCfgInfo:
    r_cgc_cfg_h: Path
    include_dir: Path


@dataclass(frozen=True)
class FSPModuleCfgInfo:
    cfg_h: Path
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


class HasIncludeDir(Protocol):
    include_dir: Path


TInclude = TypeVar("TInclude", bound=HasIncludeDir)


# =========================
# Generic helpers
# =========================

def _dedupe_by_include_dir(items: Iterable[TInclude]) -> List[TInclude]:
    seen: Set[Path] = set()
    unique: List[TInclude] = []

    for item in sorted(items, key=lambda x: str(x.include_dir)):
        if item.include_dir in seen:
            continue
        seen.add(item.include_dir)
        unique.append(item)

    return unique


def _select_detected_port(
    ports: Sequence[ComPortInfo],
) -> Optional[ComPortInfo]:
    if not ports:
        return None

    for port in ports:
        if port.vid in ARDUINO_VIDS:
            return port

    return ports[0]


def _variant_names_for_ports(
    ports: Sequence[ComPortInfo],
) -> List[str]:
    detected = _select_detected_port(ports)
    if detected is None:
        return []

    board_short = short_board_name(detected.vid, detected.pid)
    variant_names = BOARD_VARIANTS.get(board_short)

    if not variant_names:
        return []

    return list(variant_names)


def _match_header_by_variants(
    items: Sequence[object],
    ports: Sequence[ComPortInfo],
    path_getter: Callable[[object], Path],
) -> Tuple[Optional[object], List[object]]:
    if not items:
        return None, list(items)

    variant_names = _variant_names_for_ports(ports)
    if not variant_names:
        return None, list(items)

    for variant_name in variant_names:
        variant_lower = variant_name.lower()
        for item in items:
            if variant_lower in str(path_getter(item)).lower():
                remaining = [i for i in items if i is not item]
                return item, remaining

    return None, list(items)


def _print_matched_headers(
    section_title: str,
    discovered_label: str,
    none_found_msg: str,
    item_label: str,
    header_desc: str,
    items: Sequence[object],
    ports: Sequence[ComPortInfo],
    header_attr: str,
    include_attr: str,
) -> None:
    print_section(section_title)
    print(
        S("section_header_discovered").format(
            label=discovered_label,
            count=len(items),
        )
    )
    print()

    if not items:
        print(S("section_header_none").format(message=none_found_msg))
        print()
        return

    def _header_path(item: object) -> Path:
        return cast(Path, getattr(item, header_attr))

    def _include_dir(item: object) -> Path:
        return cast(Path, getattr(item, include_attr))

    matched, remaining = _match_header_by_variants(items, ports, _header_path)

    def _print_item(idx: int, item: object, matched_flag: bool) -> None:
        suffix = S("section_header_match_suffix") if matched_flag else ""
        print(
            S("section_header_item_header").format(
                item_label=item_label,
                index=idx,
                suffix=suffix,
            )
        )
        print(S("section_header_full_path").format(desc=header_desc))
        print(indent(str(_header_path(item)), "    "))
        print(S("section_header_include_dir"))
        print(indent(str(_include_dir(item)), "    "))
        print()

    if matched is not None:
        _print_item(1, matched, True)
        for idx, item in enumerate(remaining, start=2):
            _print_item(idx, item, False)
    else:
        for idx, item in enumerate(items, start=1):
            _print_item(idx, item, False)


# =========================
# ASCII logo
# =========================

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
# pyserial handling
# =========================

def ensure_pyserial() -> Optional[Any]:
    try:
        from serial.tools import list_ports  # type: ignore[import]
        print(S("pyserial_already"))
        return list_ports
    except Exception:
        print(S("pyserial_not_installed"))

    cmd_list = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--user",
        "pyserial",
    ]
    cmd_str = " ".join(cmd_list)
    print(S("pyserial_running_cmd").format(cmd=cmd_str))

    try:
        proc = subprocess.run(
            cmd_list,
            text=True,
            capture_output=True,
        )
    except Exception as exc:
        print(S("pyserial_pip_failed").format(exc=exc))
        return None

    print(S("pyserial_pip_exit").format(code=proc.returncode))

    if proc.stdout.strip():
        print(S("pyserial_pip_stdout_header"))
        print(proc.stdout.strip())
    if proc.stderr.strip():
        print(S("pyserial_pip_stderr_header"))
        print(proc.stderr.strip())

    if proc.returncode != 0:
        print(S("pyserial_install_failed"))
        return None

    try:
        from serial.tools import list_ports  # type: ignore[import]
        print(S("pyserial_import_after_install_ok"))
        return list_ports
    except Exception as exc:
        print(S("pyserial_import_after_install_failed").format(exc=exc))
        return None


# =========================
# Utility helpers
# =========================

def resolve_base_dir(cli_base_dir: Optional[str]) -> Path:
    if cli_base_dir:
        return Path(cli_base_dir).expanduser().resolve()

    home = Path.home()
    candidates = [
        home / "Documents" / "ArduinoData",
        home / "AppData" / "Local" / "Arduino15",
    ]

    for candidate in candidates:
        if candidate.is_dir():
            return candidate

    return Path.cwd()


def path_contains_any(path: Path, tokens: Sequence[str]) -> bool:
    lower = str(path).lower()
    return any(token in lower for token in tokens)


# =========================
# Arduino core discovery
# =========================

def find_arduino_headers(base_dir: Path) -> List[CoreInfo]:
    results: List[CoreInfo] = []

    for header in base_dir.rglob("Arduino.h"):
        parts = [part.lower() for part in header.parts]
        if "cores" not in parts:
            continue
        results.append(CoreInfo(arduino_h=header, include_dir=header.parent))

    return _dedupe_by_include_dir(results)


# =========================
# Toolchain discovery
# =========================

def _find_compiler(include_dir: Path) -> Optional[Path]:
    compiler_names = [
        "arm-none-eabi-gcc",
        "arm-none-eabi-g++",
        "gcc",
        "g++",
        "cc",
        "c++",
    ]

    parents = [include_dir.parent] + list(include_dir.parents[:3])

    for parent in parents:
        bin_dir = parent / "bin"
        if not bin_dir.is_dir():
            continue

        for name in compiler_names:
            compiler = (
                bin_dir / f"{name}.exe"
                if platform.system() == "Windows"
                else bin_dir / name
            )
            if compiler.is_file():
                return compiler

    return None


def find_stdlib_headers(base_dir: Path) -> List[ToolchainInfo]:
    results: List[ToolchainInfo] = []

    for header in base_dir.rglob("stdlib.h"):
        if not header.is_file():
            continue
        if header.parent.name != "include":
            continue
        if not path_contains_any(header, TOOLCHAIN_TOKENS):
            continue
        compiler = _find_compiler(header.parent)
        results.append(
            ToolchainInfo(
                stdlib_h=header,
                include_dir=header.parent,
                compiler_path=compiler,
            )
        )

    return _dedupe_by_include_dir(results)


# =========================
# BSP / FSP discovery
# =========================

def find_bsp_api_headers(base_dir: Path) -> List[BSPInfo]:
    results: List[BSPInfo] = []

    for header in base_dir.rglob("bsp_api.h"):
        if not header.is_file():
            continue
        results.append(BSPInfo(bsp_api_h=header, include_dir=header.parent))

    return _dedupe_by_include_dir(results)


def find_fsp_common_api_headers(base_dir: Path) -> List[FSPCommonInfo]:
    results: List[FSPCommonInfo] = []

    for header in base_dir.rglob("fsp_common_api.h"):
        if not header.is_file():
            continue
        results.append(
            FSPCommonInfo(fsp_common_api_h=header, include_dir=header.parent)
        )

    return _dedupe_by_include_dir(results)


def find_bsp_cfg_headers(base_dir: Path) -> List[BSPCfgInfo]:
    results: List[BSPCfgInfo] = []

    for header in base_dir.rglob("bsp_cfg.h"):
        if not header.is_file():
            continue
        results.append(BSPCfgInfo(bsp_cfg_h=header, include_dir=header.parent))

    return _dedupe_by_include_dir(results)


def find_hal_data_headers(base_dir: Path) -> List[HALDataInfo]:
    results: List[HALDataInfo] = []

    for header in base_dir.rglob("hal_data.h"):
        if not header.is_file():
            continue
        results.append(HALDataInfo(hal_data_h=header, include_dir=header.parent))

    return _dedupe_by_include_dir(results)


def find_cmsis_headers(base_dir: Path) -> List[CMSISInfo]:
    results: List[CMSISInfo] = []
    cmsis_patterns = (
        "cmsis_device.h",
        "core_cm0.h",
        "core_cm3.h",
        "core_cm4.h",
        "core_cm7.h",
    )

    for pattern in cmsis_patterns:
        for header in base_dir.rglob(pattern):
            if not header.is_file():
                continue
            results.append(CMSISInfo(cmsis_h=header, include_dir=header.parent))

    return _dedupe_by_include_dir(results)


def find_r_cgc_headers(base_dir: Path) -> List[RCGCInfo]:
    results: List[RCGCInfo] = []

    for header in base_dir.rglob("r_cgc.h"):
        if not header.is_file():
            continue
        results.append(RCGCInfo(r_cgc_h=header, include_dir=header.parent))

    return _dedupe_by_include_dir(results)


def find_r_cgc_cfg_headers(base_dir: Path) -> List[RCGCCfgInfo]:
    results: List[RCGCCfgInfo] = []

    for header in base_dir.rglob("r_cgc_cfg.h"):
        if not header.is_file():
            continue
        results.append(RCGCCfgInfo(r_cgc_cfg_h=header, include_dir=header.parent))

    return _dedupe_by_include_dir(results)


def find_fsp_module_cfg_headers(base_dir: Path) -> List[FSPModuleCfgInfo]:
    results: List[FSPModuleCfgInfo] = []

    for header in base_dir.rglob("r_*_cfg.h"):
        if not header.is_file():
            continue
        if header.name == "r_cgc_cfg.h":
            continue
        results.append(FSPModuleCfgInfo(cfg_h=header, include_dir=header.parent))

    return _dedupe_by_include_dir(results)


# =========================
# Header "friends"
# =========================

def friends_status(
    include_dir: Path,
    friends: Sequence[str],
    search_root: Optional[Path],
) -> List[Tuple[str, List[Path]]]:
    statuses: List[Tuple[str, List[Path]]] = []

    for name in sorted(friends):
        primary = include_dir / name
        found: List[Path] = []

        if primary.is_file():
            found.append(primary)

        if not found and search_root is not None and search_root.is_dir():
            for candidate in search_root.rglob(name):
                if not candidate.is_file():
                    continue
                if candidate == primary:
                    continue
                found.append(candidate)
                break

        statuses.append((name, found))

    return statuses


def _print_friend_headers(
    label: str,
    include_dir: Path,
    friends: Sequence[str],
    search_root: Path,
    extra_includes: Set[Path],
) -> None:
    print(S("friends_label_generic").format(label=label))
    status_list = friends_status(include_dir, friends, search_root)
    for name, paths in status_list:
        primary = include_dir / name
        if not paths:
            print(S("friends_missing").format(name=name, root=search_root))
            continue
        for path in paths:
            tag = S("friends_ok") if path == primary else S("friends_alt")
            print(f"    {tag}  {name} -> {path}")
            if path.parent != include_dir:
                extra_includes.add(path.parent)


# =========================
# COM port detection + board guessing
# =========================

def guess_board(vid: Optional[int], pid: Optional[int]) -> str:
    if vid is None or pid is None:
        return S("board_unknown_no_vid_pid")

    key = (vid, pid)
    string_key = VID_PID_TO_STRING_KEY.get(key)

    if string_key is not None:
        return S(string_key)

    if vid in ARDUINO_VIDS:
        return S("board_arduino_exact_unknown")
    if vid == 0x1A86:
        return S("board_ch340_based")
    if vid == 0x10C4:
        return S("board_cp210x_based")

    return S("board_unknown_unmapped")


def short_board_name(vid: Optional[int], pid: Optional[int]) -> str:
    if vid is None or pid is None:
        return "SCAN"

    key = (vid, pid)

    if key in SHORT_NAME_MAP:
        return SHORT_NAME_MAP[key]

    if vid in VENDOR_SHORT_FALLBACK:
        return VENDOR_SHORT_FALLBACK[vid]

    if vid in ARDUINO_VIDS:
        return "ARDUINO"

    return "SCAN"


def scan_com_ports(list_ports_module: Optional[Any]) -> List[ComPortInfo]:
    if list_ports_module is None:
        return []

    ports = list_ports_module.comports()  # type: ignore[attr-defined]
    results: List[ComPortInfo] = []

    for port in ports:
        vid = getattr(port, "vid", None)
        pid = getattr(port, "pid", None)
        manufacturer = getattr(port, "manufacturer", None)
        product = getattr(port, "product", None)

        results.append(
            ComPortInfo(
                device=str(port.device),
                description=str(port.description),
                hwid=str(port.hwid),
                vid=vid,
                pid=pid,
                manufacturer=manufacturer,
                product=product,
            )
        )

    return results


def derive_banner_title(ports: Sequence[ComPortInfo]) -> str:
    if not ports:
        return S("banner_default")

    arduino_ports: List[ComPortInfo] = []
    other_ports: List[ComPortInfo] = []

    for port in ports:
        if port.vid in ARDUINO_VIDS:
            arduino_ports.append(port)
        else:
            other_ports.append(port)

    if arduino_ports:
        target = arduino_ports[0]
    else:
        target = other_ports[0] if other_ports else None

    if target is None:
        return S("banner_default")

    short = short_board_name(target.vid, target.pid)
    return S("banner_arduino_prefix").format(short=short)


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
    print_section(S("section_neofetch_title"))
    print(S("neofetch_user_label").format(value=Path.home().name))
    print(
        S("neofetch_os_label").format(
            value=f"{platform.system()} {platform.release()}",
        )
    )
    print(S("neofetch_python_label").format(value=platform.python_version()))
    print(S("neofetch_arch_label").format(value=platform.machine()))
    print(S("neofetch_arduino_dir_label").format(value=base_dir))
    print(S("neofetch_python_exe_label").format(value=sys.executable))
    print()


def print_cores(
    cores: Sequence[CoreInfo],
    extra_core_includes: Set[Path],
) -> None:
    print_section(S("section_cores_title"))
    print(S("section_cores_discovered").format(count=len(cores)))
    print()

    if not cores:
        print(S("section_cores_none"))
        print()
        return

    for idx, core in enumerate(cores, start=1):
        print(S("section_core_header").format(index=idx))
        print(S("section_core_arduino_path"))
        print(indent(str(core.arduino_h), "    "))
        print(S("section_core_include_dir"))
        print(indent(str(core.include_dir), "    "))

        parents = list(core.include_dir.parents)
        hw_root = parents[2] if len(parents) > 2 else core.include_dir

        _print_friend_headers(
            label=S("friends_label_core"),
            include_dir=core.include_dir,
            friends=CORE_FRIENDS,
            search_root=hw_root,
            extra_includes=extra_core_includes,
        )

        print()


def print_toolchains(
    toolchains: Sequence[ToolchainInfo],
    extra_tc_includes: Set[Path],
) -> None:
    print_section(S("section_toolchains_title"))
    print(S("section_toolchains_discovered").format(count=len(toolchains)))
    print()

    if not toolchains:
        print(S("section_toolchains_none"))
        print()
        return

    for idx, tc in enumerate(toolchains, start=1):
        print(S("section_toolchain_header").format(index=idx))
        print(S("section_toolchain_stdlib_path"))
        print(indent(str(tc.stdlib_h), "    "))
        print(S("section_toolchain_include_dir"))
        print(indent(str(tc.include_dir), "    "))
        if tc.compiler_path:
            print(S("section_toolchain_compiler_path"))
            print(indent(str(tc.compiler_path), "    "))

        parents = list(tc.include_dir.parents)
        tc_root = parents[1] if len(parents) > 1 else tc.include_dir

        _print_friend_headers(
            label=S("friends_label_toolchain"),
            include_dir=tc.include_dir,
            friends=CLIB_FRIENDS,
            search_root=tc_root,
            extra_includes=extra_tc_includes,
        )

        print()

    print(S("section_toolchain_best_guess"))
    print(indent(str(toolchains[0].include_dir), "  "))
    print()


def print_com_ports(
    ports: Sequence[ComPortInfo],
    pyserial_available: bool,
) -> None:
    print_section(S("section_com_title"))

    if not pyserial_available:
        print(S("section_com_pyserial_missing"))
        print()
        return

    print(S("section_com_detected").format(count=len(ports)))
    print()

    if not ports:
        print(S("section_com_none"))
        print()
        return

    for idx, port in enumerate(ports, start=1):
        board_guess = guess_board(port.vid, port.pid)

        print(S("section_com_port_header").format(index=idx, device=port.device))
        print(S("section_com_description").format(value=port.description))
        print(S("section_com_hwid").format(value=port.hwid))

        if port.vid is not None and port.pid is not None:
            print(S("section_com_vid_pid").format(vid=port.vid, pid=port.pid))
        else:
            print(S("section_com_vid_pid_missing"))

        if port.manufacturer or port.product:
            print(S("section_com_usb_strings"))
            if port.manufacturer:
                print(S("section_com_manufacturer").format(value=port.manufacturer))
            if port.product:
                print(S("section_com_product").format(value=port.product))

        print(S("section_com_board_guess").format(value=board_guess))
        print()


def print_header_groups(
    header_collections: Mapping[str, Sequence[object]],
    ports: Sequence[ComPortInfo],
) -> None:
    for key in HEADER_GROUP_ORDER:
        cfg = HEADER_GROUPS[key]
        items = list(header_collections.get(key, ()))

        section_title = S(cfg["section_title_key"])
        discovered_label = S(cfg["discovered_label_key"])
        none_found_msg = S(cfg["none_found_key"])
        item_label = cfg["item_label"]
        header_desc = cfg["header_desc"]
        header_attr = cfg["header_attr"]
        include_attr = cfg["include_attr"]

        _print_matched_headers(
            section_title=section_title,
            discovered_label=discovered_label,
            none_found_msg=none_found_msg,
            item_label=item_label,
            header_desc=header_desc,
            items=items,
            ports=ports,
            header_attr=header_attr,
            include_attr=include_attr,
        )


def print_suggested_flags(
    header_collections: Mapping[str, Sequence[object]],
    suggested_collections: Mapping[str, Sequence[object]],
    extra_core_includes: Set[Path],
    extra_tc_includes: Set[Path],
) -> None:
    cores = cast(Sequence[CoreInfo], header_collections.get("cores", ()))
    toolchains = cast(Sequence[ToolchainInfo], header_collections.get("toolchains", ()))

    print_section(S("section_flags_title"))

    # Arduino core include paths
    print(S("flags_arduino_paths_title"))
    if cores:
        for core in cores:
            print(f'  -I"{core.include_dir}"')
    else:
        print(S("flags_none_found"))

    if extra_core_includes:
        print()
        print(S("flags_extra_core_paths_title"))
        for path in sorted(extra_core_includes, key=str):
            print(f'  -I"{path}"')

    print()

    # Toolchain include paths
    print(S("flags_toolchain_paths_title"))
    if toolchains:
        for toolchain in toolchains:
            print(f'  -I"{toolchain.include_dir}"')
            if toolchain.compiler_path:
                print(S("flags_compiler_label").format(path=toolchain.compiler_path))
    else:
        print(S("flags_none_found"))

    if extra_tc_includes:
        print()
        print(S("flags_extra_toolchain_paths_title"))
        for path in sorted(extra_tc_includes, key=str):
            print(f'  -I"{path}"')

    print()

    def _print_group(label_key: str, paths: Sequence[Path]) -> None:
        print(S("flags_group_label").format(label=S(label_key)))
        if paths:
            for path in paths:
                print(f'  -I"{path}"')
        else:
            print(S("flags_none_found"))
        print()

    for key, label_key in FLAGS_GROUP_LABEL_KEYS.items():
        items = list(suggested_collections.get(key, ()))
        paths: List[Path] = [
            cast(Path, getattr(item, "include_dir")) for item in items
        ]
        _print_group(label_key, paths)


# =========================
# Scan orchestration (typed)
# =========================

HeaderFinder = Callable[[Path], Sequence[object]]

SCAN_FINDERS: Dict[str, HeaderFinder] = {
    "cores": lambda base: cast(Sequence[object], find_arduino_headers(base)),
    "toolchains": lambda base: cast(Sequence[object], find_stdlib_headers(base)),
    "bsp": lambda base: cast(Sequence[object], find_bsp_api_headers(base)),
    "fsp_common": lambda base: cast(
        Sequence[object],
        find_fsp_common_api_headers(base),
    ),
    "bsp_cfg": lambda base: cast(Sequence[object], find_bsp_cfg_headers(base)),
    "hal_data": lambda base: cast(Sequence[object], find_hal_data_headers(base)),
    "cmsis": lambda base: cast(Sequence[object], find_cmsis_headers(base)),
    "r_cgc": lambda base: cast(Sequence[object], find_r_cgc_headers(base)),
    "r_cgc_cfg": lambda base: cast(Sequence[object], find_r_cgc_cfg_headers(base)),
    "fsp_module_cfg": lambda base: cast(
        Sequence[object],
        find_fsp_module_cfg_headers(base),
    ),
}


def run_scans(base_dir: Path) -> Dict[str, Sequence[object]]:
    collections: Dict[str, Sequence[object]] = {}
    for key, finder in SCAN_FINDERS.items():
        collections[key] = finder(base_dir)
    return collections


def build_suggested_collections(
    header_collections: Mapping[str, Sequence[object]],
    ports: Sequence[ComPortInfo],
) -> Dict[str, Sequence[object]]:
    suggested: Dict[str, Sequence[object]] = {}

    for key, cfg in HEADER_GROUPS.items():
        items = list(header_collections.get(key, ()))
        header_attr = cfg["header_attr"]

        def _header_path(item: object) -> Path:
            return cast(Path, getattr(item, header_attr))

        matched, _ = _match_header_by_variants(items, ports, _header_path)

        if matched is not None:
            suggested[key] = [matched]
        else:
            suggested[key] = items

    return suggested


# =========================
# OO wrapper: ArduinoScanner
# =========================

class ArduinoScanner:
    def __init__(
        self,
        base_dir: Path,
        list_ports_module: Optional[Any],
    ) -> None:
        self.base_dir = base_dir
        self.list_ports_module = list_ports_module
        self.pyserial_available = list_ports_module is not None
        self.ports: List[ComPortInfo] = scan_com_ports(list_ports_module)

        self.header_collections: Dict[str, Sequence[object]] = run_scans(base_dir)

        self.extra_core_includes: Set[Path] = set()
        self.extra_tc_includes: Set[Path] = set()

        self.suggested_collections: Dict[str, Sequence[object]] = (
            build_suggested_collections(
                self.header_collections,
                self.ports,
            )
        )

    def step_banner(self) -> None:
        banner_title = derive_banner_title(self.ports)
        print_ascii_logo(banner_title)
        print_system_neofetch(self.base_dir)

    def step_cores(self) -> None:
        cores = cast(Sequence[CoreInfo], self.header_collections.get("cores", ()))
        print_cores(cores, self.extra_core_includes)

    def step_toolchains(self) -> None:
        toolchains = cast(
            Sequence[ToolchainInfo],
            self.header_collections.get("toolchains", ()),
        )
        print_toolchains(toolchains, self.extra_tc_includes)

    def step_header_groups(self) -> None:
        print_header_groups(self.header_collections, self.ports)

    def step_com_ports(self) -> None:
        print_com_ports(self.ports, self.pyserial_available)

    def step_flags(self) -> None:
        print_suggested_flags(
            self.header_collections,
            self.suggested_collections,
            self.extra_core_includes,
            self.extra_tc_includes,
        )

    def run_pipeline(self) -> None:
        step_map: Dict[str, Callable[[], None]] = {
            "banner": self.step_banner,
            "cores": self.step_cores,
            "toolchains": self.step_toolchains,
            "header_groups": self.step_header_groups,
            "com_ports": self.step_com_ports,
            "flags": self.step_flags,
        }

        for name in PIPELINE_ORDER:
            step = step_map.get(name)
            if step is not None:
                step()


# =========================
# CLI / main
# =========================

def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=S("app_description"))
    parser.add_argument(
        "base_dir",
        nargs="?",
        help=S("arg_base_dir_help"),
    )
    return parser.parse_args(list(argv))


def main(argv: Optional[Sequence[str]] = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    args = parse_args(argv)
    base_dir = resolve_base_dir(args.base_dir)

    if not base_dir.is_dir():
        print(S("err_base_dir_missing").format(path=base_dir), file=sys.stderr)
        return 1

    list_ports_module = ensure_pyserial()
    scanner = ArduinoScanner(base_dir, list_ports_module)
    scanner.run_pipeline()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
