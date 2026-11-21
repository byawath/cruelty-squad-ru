#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
05_build_pck_pure_python.py
--------------------------------------------------------------------------------
Lead Localization Engineering & Reverse-Engineering Tool for Cruelty Squad (Godot 3.x)
Task 5: Pure Python Binary .PCK Builder & Packager (No External Tools Required)
--------------------------------------------------------------------------------
"""

import os
import sys
import struct
import json
import hashlib
import re
import shutil
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional, Set

# Reconfigure console output to UTF-8
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Constants for Godot 3.x PCK Format v1
PCK_MAGIC = b"GDPC"
PCK_FORMAT_VERSION = 1
PCK_HEADER_SIZE = 88
FILE_ALIGNMENT = 16  # 16-byte alignment standard for Godot 3.x PCK data

STRING_LITERAL_REGEX = re.compile(r'("(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\')')
ALLOWED_TSCN_PROPS = {
    "text", "bbcode_text", "hint_tooltip",
    "dialogue", "lines", "dyn_lines", "dialog_text", "message",
    "npc_name", "implant_name", "override_name", "line", "line2", "value"
}

# Assets to import from ru_2021.pck
FONTS_TO_IMPORT = [
    "res://Fonts/MingLiU-ExtB-01.ttf",
    "res://Fonts/gamefont(1).ttf",
    "res://Fonts/gamefont.ttf",
]

STEX_TO_IMPORT = [
    "res://.import/Misery_Achieved.png-c258c1f600a358f228fcb3cee8a3b4d9.stex",
    "res://.import/Soul_Rended.png-f59fc37014a0d66d7570cbe8018df385.stex",
    "res://.import/ending2face.png-0a76daf9337823202a1f7b99bfe2981e.s3tc.stex",
    "res://.import/ending2face.png-0cba63e81c5b558cca967bb717ba984e.s3tc.stex",
    "res://.import/gorbino.png-2a2ee8205345cb3889d9ae67826ce45a.s3tc.stex",
    "res://.import/store_punishment.png-3c139239c2f9b91de9121602fb5d6bb3.s3tc.stex",
    "res://.import/title1.png-a1bb4ee083219025e0ecce91a09c21ba.stex",
    "res://.import/title11.png-21e54c121bd05711c72e3e99d7ca5ed3.stex",
]


class PckBuilder:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.db_path = base_dir / "localization_db.json"
        self.vanilla_dir = base_dir / "vanilla_new"
        self.patched_dir = base_dir / "_patched_files"
        self.pck_dir = base_dir / "_source_pcks"
        self.vanilla_pck_path = self.pck_dir / "vanilla_steam.pck"
        self.ru_pck_path = self.pck_dir / "ru_2021.pck"
        self.output_pck_path = base_dir / "crueltysquad_ru_v2.pck"

    # ==========================================================================
    # STEP 1: Generate Patched Files into ./_patched_files/
    # ==========================================================================
    def generate_patched_files(self) -> int:
        print("\n" + "=" * 80)
        print(" [STEP 1/5] GENERATING PATCHED FILES INTO ./_patched_files/")
        print("=" * 80)

        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")

        with open(self.db_path, "r", encoding="utf-8") as f:
            db = json.load(f)

        if self.patched_dir.exists():
            shutil.rmtree(self.patched_dir)
        self.patched_dir.mkdir(parents=True, exist_ok=True)

        # Group entries by file_path
        db_by_file: Dict[str, List[Dict[str, Any]]] = {}
        for entry in db:
            db_by_file.setdefault(entry["file_path"], []).append(entry)

        print(f"[*] Total files to patch from localization database: {len(db_by_file)}")

        gd_files = [f for f in db_by_file if f.endswith(".gd")]
        tscn_files = [f for f in db_by_file if f.endswith(".tscn")]
        print(f"    - GDScript files: {len(gd_files)}")
        print(f"    - TSCN scene files: {len(tscn_files)}")

        # 1. Patch GDScript files
        for fpath_str in gd_files:
            entries = db_by_file[fpath_str]
            line_map: Dict[Tuple[int, int], str] = {}
            for e in entries:
                sub_i = int(e["id"].split(":")[-1])
                line_map[(e["line_num"], sub_i)] = e["ru_final"]

            src_p = self.vanilla_dir / fpath_str
            if not src_p.exists():
                raise FileNotFoundError(f"Source file not found: {src_p}")

            with open(src_p, "r", encoding="utf-8", errors="ignore") as fp:
                lines = fp.readlines()

            for lno in range(1, len(lines) + 1):
                line = lines[lno - 1]
                matches = list(STRING_LITERAL_REGEX.finditer(line))
                repls = []
                for s_idx, m in enumerate(matches):
                    if (lno, s_idx) in line_map:
                        repls.append((m.start(), m.end(), line_map[(lno, s_idx)]))

                if repls:
                    repls.sort(key=lambda x: x[0], reverse=True)
                    new_line = line
                    for start, end, ru_text in repls:
                        new_token = f'"{ru_text}"'
                        new_line = new_line[:start] + new_token + new_line[end:]
                    lines[lno - 1] = new_line

            out_p = self.patched_dir / fpath_str
            out_p.parent.mkdir(parents=True, exist_ok=True)
            with open(out_p, "w", encoding="utf-8", newline="\n") as out_f:
                out_f.writelines(lines)

        # 2. Patch TSCN files
        for fpath_str in tscn_files:
            entries = db_by_file[fpath_str]
            entry_map = {e["id"]: e["ru_final"] for e in entries}

            src_p = self.vanilla_dir / fpath_str
            if not src_p.exists():
                raise FileNotFoundError(f"Source file not found: {src_p}")

            with open(src_p, "r", encoding="utf-8", errors="ignore") as fp:
                lines = fp.readlines()

            in_node = False
            idx = 0
            total_lines = len(lines)

            while idx < total_lines:
                line_num = idx + 1
                line = lines[idx]
                stripped = line.strip()

                if stripped.startswith("["):
                    in_node = stripped.startswith("[node")
                    idx += 1
                    continue

                if not in_node:
                    idx += 1
                    continue

                pm = re.match(r"^([a-zA-Z0-9_]+)\s*=\s*(.*)$", stripped)
                if pm:
                    prop_name = pm.group(1)
                    prop_val = pm.group(2)

                    if prop_name.lower() in ALLOWED_TSCN_PROPS:
                        start_idx = idx
                        full_val = prop_val
                        if full_val.startswith('"') and (not full_val.endswith('"') or full_val == '"'):
                            while idx + 1 < total_lines:
                                idx += 1
                                full_val += "\n" + lines[idx].rstrip("\r\n")
                                if lines[idx].rstrip("\r\n").endswith('"'):
                                    break
                        elif full_val.startswith("[") and not full_val.endswith("]"):
                            while idx + 1 < total_lines:
                                idx += 1
                                full_val += " " + lines[idx].strip()
                                if lines[idx].strip().endswith("]"):
                                    break

                        end_idx = idx
                        matches = list(STRING_LITERAL_REGEX.finditer(full_val))
                        repls = []
                        for s_idx, m in enumerate(matches):
                            eid = f"{fpath_str}:{line_num}:{s_idx}"
                            if eid in entry_map:
                                repls.append((m.start(), m.end(), entry_map[eid]))

                        if repls:
                            repls.sort(key=lambda x: x[0], reverse=True)
                            new_val = full_val
                            for start, end, ru_text in repls:
                                new_val = new_val[:start] + f'"{ru_text}"' + new_val[end:]

                            prefix = lines[start_idx][:lines[start_idx].index("=") + 1] + " "
                            lines[start_idx] = prefix + new_val + "\n"
                            for del_idx in range(start_idx + 1, end_idx + 1):
                                lines[del_idx] = ""

                idx += 1

            out_p = self.patched_dir / fpath_str
            out_p.parent.mkdir(parents=True, exist_ok=True)
            with open(out_p, "w", encoding="utf-8", newline="\n") as out_f:
                out_f.writelines(l for l in lines if l != "")

        total_patched = len(list(self.patched_dir.rglob("*.*")))
        print(f"[+] Successfully wrote {total_patched} patched files with Unix newlines (LF) and UTF-8 encoding.")
        return total_patched

    # ==========================================================================
    # STEP 2: Syntax and Quotation Integrity Validation
    # ==========================================================================
    def validate_patched_syntax(self):
        print("\n" + "=" * 80)
        print(" [STEP 2/5] PARSING & VALIDATING SYNTAX OF PATCHED FILES")
        print("=" * 80)

        errors = []
        checked_count = 0

        for p in self.patched_dir.rglob("*"):
            if not p.is_file():
                continue

            checked_count += 1
            rel_path = p.relative_to(self.patched_dir).as_posix()
            content = open(p, "r", encoding="utf-8").read()

            if p.suffix == ".gd":
                lines = content.split("\n")
                for lno, line in enumerate(lines, 1):
                    stripped = line.strip()
                    if stripped.startswith("#"):
                        continue

                    # Check for unclosed quotes on single line
                    in_q = False
                    q_char = ""
                    i = 0
                    while i < len(line):
                        ch = line[i]
                        if ch == "\\" and in_q:
                            i += 2
                            continue
                        if not in_q:
                            if ch in ('"', "'"):
                                in_q = True
                                q_char = ch
                            elif ch == "#":
                                break
                        else:
                            if ch == q_char:
                                in_q = False
                                q_char = ""
                        i += 1

                    if in_q:
                        errors.append((rel_path, lno, f"Unclosed string quote on line: {line.strip()[:60]}"))

            elif p.suffix == ".tscn":
                raw_no_escaped = re.sub(r'\\"', '', content)
                quote_count = raw_no_escaped.count('"')
                if quote_count % 2 != 0:
                    errors.append((rel_path, 0, f"Odd number of quotes ({quote_count}) in .tscn file"))

        print(f"[*] Validated {checked_count} patched files for quotation balance and syntax.")
        if errors:
            print(f"[!] Syntax errors detected ({len(errors)}):")
            for rel, lno, msg in errors[:10]:
                print(f"    - {rel}:{lno} -> {msg}")
            raise SyntaxError("Patched files contain syntax or quote balance errors!")
        else:
            print("[+] 100% of patched files passed syntax and quote balance checks!")

    # ==========================================================================
    # STEP 3 & 4: Virtual Table Formation & Pure Python Binary PCK Writer
    # ==========================================================================
    def read_pck_index(self, pck_path: Path) -> Tuple[Dict[str, Any], Dict[str, Dict[str, Any]]]:
        if not pck_path.exists():
            raise FileNotFoundError(f"PCK not found: {pck_path}")

        with open(pck_path, "rb") as f:
            hdr_bytes = f.read(PCK_HEADER_SIZE)
            magic, pack_ver, v_maj, v_min, v_rev, file_count = struct.unpack(
                "<4sIIII64xI", hdr_bytes
            )
            if magic != PCK_MAGIC:
                raise ValueError(f"Invalid magic: {magic}")

            header = {
                "magic": magic,
                "pack_ver": pack_ver,
                "v_maj": v_maj,
                "v_min": v_min,
                "v_rev": v_rev,
                "file_count": file_count,
                "raw_header": hdr_bytes,
            }

            files = {}
            for _ in range(file_count):
                (plen,) = struct.unpack("<I", f.read(4))
                raw_path = f.read(plen)
                clean_path = raw_path.rstrip(b"\x00").decode("utf-8", errors="replace")
                offset, size, md5_raw = struct.unpack("<QQ16s", f.read(32))
                files[clean_path] = {
                    "offset": offset,
                    "size": size,
                    "md5": md5_raw,
                }
        return header, files

    def build_pck(self):
        print("\n" + "=" * 80)
        print(" [STEP 3 & 4] FORMING VIRTUAL TABLE & WRITING crueltysquad_ru_v2.pck")
        print("=" * 80)

        t0 = time.time()
        v_hdr, vanilla_files = self.read_pck_index(self.vanilla_pck_path)
        ru_hdr, ru_files = self.read_pck_index(self.ru_pck_path)

        print(f"[*] Vanilla PCK File Count:  {len(vanilla_files):,}")
        print(f"[*] RU (2021) PCK File Count: {len(ru_files):,}")

        # Construct Virtual Files Table: path -> entry info
        # entry info: { "source_type": ..., "path": ..., "size": ..., "md5": ... }
        virtual_table: Dict[str, Dict[str, Any]] = {}

        # 1. Base: all vanilla files
        for p, meta in vanilla_files.items():
            virtual_table[p] = {
                "type": "vanilla",
                "offset": meta["offset"],
                "size": meta["size"],
                "md5": meta["md5"],
            }

        # 2. Fonts replacement from ru_2021.pck
        fonts_replaced = 0
        for font_path in FONTS_TO_IMPORT:
            if font_path in ru_files:
                virtual_table[font_path] = {
                    "type": "ru_pck",
                    "offset": ru_files[font_path]["offset"],
                    "size": ru_files[font_path]["size"],
                    "md5": ru_files[font_path]["md5"],
                }
                fonts_replaced += 1
            else:
                print(f"[!] Warning: Font {font_path} not found in ru_2021.pck")
        print(f"[+] Replaced {fonts_replaced} fonts from ru_2021.pck")

        # 3. STEX UI textures replacement from ru_2021.pck
        stex_replaced = 0
        for stex_path in STEX_TO_IMPORT:
            if stex_path in ru_files:
                virtual_table[stex_path] = {
                    "type": "ru_pck",
                    "offset": ru_files[stex_path]["offset"],
                    "size": ru_files[stex_path]["size"],
                    "md5": ru_files[stex_path]["md5"],
                }
                stex_replaced += 1
            else:
                print(f"[!] Warning: STEX {stex_path} not found in ru_2021.pck")
        print(f"[+] Replaced {stex_replaced} STEX textures from ru_2021.pck")

        # 4. Patched scenes (.tscn) from _patched_files/
        patched_tscn_files = list(self.patched_dir.rglob("*.tscn"))
        for p in patched_tscn_files:
            rel = p.relative_to(self.patched_dir).as_posix()
            res_path = f"res://{rel}"
            data = p.read_bytes()
            virtual_table[res_path] = {
                "type": "disk",
                "disk_path": p,
                "size": len(data),
                "md5": hashlib.md5(data).digest(),
            }
        print(f"[+] Integrated {len(patched_tscn_files)} patched .tscn scenes")

        # 5. Patched GDScript files (.gd instead of .gdc + removal of .remap)
        patched_gd_files = list(self.patched_dir.rglob("*.gd"))
        gdc_removed = 0
        remap_removed = 0
        for p in patched_gd_files:
            rel = p.relative_to(self.patched_dir).as_posix()
            res_gd = f"res://{rel}"
            res_gdc = f"res://{rel[:-3]}.gdc"
            res_remap = f"res://{rel}.remap"

            if res_gdc in virtual_table:
                del virtual_table[res_gdc]
                gdc_removed += 1
            if res_remap in virtual_table:
                del virtual_table[res_remap]
                remap_removed += 1

            data = p.read_bytes()
            virtual_table[res_gd] = {
                "type": "disk",
                "disk_path": p,
                "size": len(data),
                "md5": hashlib.md5(data).digest(),
            }
        print(f"[+] Integrated {len(patched_gd_files)} patched .gd scripts (removed {gdc_removed} .gdc and {remap_removed} .remap)")

        new_file_count = len(virtual_table)
        print(f"[*] Final Virtual Table File Count: {new_file_count:,}")

        # Calculate TOC size and assign file offsets with 16-byte alignment
        # Header = 88 bytes
        # Each entry: 4 (path_len) + path_len + 8 (offset) + 8 (size) + 16 (md5) = 36 + path_len
        sorted_paths = sorted(virtual_table.keys())

        toc_bytes_len = 88
        path_info: Dict[str, Tuple[int, bytes]] = {}
        for p in sorted_paths:
            p_bytes = p.encode("utf-8")
            raw_len = len(p_bytes)
            padded_len = (raw_len + 3) & ~3 if (raw_len % 4 != 0) else raw_len
            padded_bytes = p_bytes.ljust(padded_len, b"\x00")
            path_info[p] = (padded_len, padded_bytes)
            toc_bytes_len += 4 + padded_len + 32

        # Data starts at 16-byte boundary after TOC
        data_start_offset = (toc_bytes_len + (FILE_ALIGNMENT - 1)) & ~(FILE_ALIGNMENT - 1)
        toc_padding = data_start_offset - toc_bytes_len

        print(f"[*] TOC unaligned size: {toc_bytes_len:,} bytes")
        print(f"[*] Data start offset (16-byte aligned): {data_start_offset:,} bytes")

        # Assign offsets to all files
        current_offset = data_start_offset
        file_offsets: Dict[str, int] = {}
        for p in sorted_paths:
            entry = virtual_table[p]
            file_offsets[p] = current_offset
            size = entry["size"]
            aligned_size = (size + (FILE_ALIGNMENT - 1)) & ~(FILE_ALIGNMENT - 1)
            current_offset += aligned_size

        total_expected_pck_size = current_offset
        print(f"[*] Projected PCK size: {total_expected_pck_size:,} bytes ({total_expected_pck_size / 1024 / 1024:.2f} MB)")

        # BINARY WRITING
        print(f"[*] Writing binary PCK to {self.output_pck_path.name}...")

        with open(self.vanilla_pck_path, "rb") as f_vanilla, \
             open(self.ru_pck_path, "rb") as f_ru, \
             open(self.output_pck_path, "wb") as f_out:

            # 1. Header (88 bytes)
            # magic (4s), pack_version (I), engine ver (III), 64x zeroes, file_count (I)
            hdr_pack = struct.pack(
                "<4sIIII64xI",
                PCK_MAGIC,
                PCK_FORMAT_VERSION,
                v_hdr["v_maj"],
                v_hdr["v_min"],
                v_hdr["v_rev"],
                new_file_count
            )
            f_out.write(hdr_pack)

            # 2. Table of Contents
            for p in sorted_paths:
                plen, pbytes = path_info[p]
                entry = virtual_table[p]
                f_out.write(struct.pack("<I", plen))
                f_out.write(pbytes)
                f_out.write(struct.pack("<QQ16s", file_offsets[p], entry["size"], entry["md5"]))

            # 3. TOC padding to 16 bytes
            if toc_padding > 0:
                f_out.write(b"\x00" * toc_padding)

            # 4. File Data
            chunk_size = 1024 * 1024  # 1 MB chunk
            for idx, p in enumerate(sorted_paths, 1):
                entry = virtual_table[p]
                expected_offset = file_offsets[p]
                actual_pos = f_out.tell()
                if actual_pos != expected_offset:
                    raise IOError(f"Offset alignment mismatch at file #{idx} ({p}): expected {expected_offset}, got {actual_pos}")

                etype = entry["type"]
                size = entry["size"]

                if etype == "disk":
                    disk_p: Path = entry["disk_path"]
                    f_out.write(disk_p.read_bytes())
                elif etype == "ru_pck":
                    f_ru.seek(entry["offset"])
                    bytes_remaining = size
                    while bytes_remaining > 0:
                        to_read = min(bytes_remaining, chunk_size)
                        buf = f_ru.read(to_read)
                        f_out.write(buf)
                        bytes_remaining -= len(buf)
                elif etype == "vanilla":
                    f_vanilla.seek(entry["offset"])
                    bytes_remaining = size
                    while bytes_remaining > 0:
                        to_read = min(bytes_remaining, chunk_size)
                        buf = f_vanilla.read(to_read)
                        f_out.write(buf)
                        bytes_remaining -= len(buf)
                else:
                    raise ValueError(f"Unknown entry type: {etype}")

                # 16-byte alignment padding after file body
                pad_len = (FILE_ALIGNMENT - (size % FILE_ALIGNMENT)) % FILE_ALIGNMENT
                if pad_len > 0:
                    f_out.write(b"\x00" * pad_len)

                if idx % 500 == 0 or idx == new_file_count:
                    print(f"    - Written {idx:,}/{new_file_count:,} files ({(idx / new_file_count) * 100:.1f}%)...")

        t1 = time.time()
        final_size = self.output_pck_path.stat().st_size
        print(f"[+] PCK packaging completed in {t1 - t0:.2f} seconds!")
        print(f"[+] File written: {self.output_pck_path.resolve()} ({final_size:,} bytes)")

    # ==========================================================================
    # STEP 5: Verification of the Created .PCK
    # ==========================================================================
    def verify_pck(self):
        print("\n" + "=" * 80)
        print(" [STEP 5/5] VERIFYING crueltysquad_ru_v2.pck INTEGRITY & INVARIANTS")
        print("=" * 80)

        pck_path = self.output_pck_path
        if not pck_path.exists():
            raise FileNotFoundError(f"Created PCK not found: {pck_path}")

        file_size = pck_path.stat().st_size
        print(f"[*] Reading and auditing: {pck_path.resolve()} ({file_size:,} bytes)")

        header, files = self.read_pck_index(pck_path)

        print(f"[*] Verification details:")
        print(f"    - Magic:           {header['magic'].decode('ascii')}")
        print(f"    - Pack Version:    {header['pack_ver']}")
        print(f"    - Engine Version:  {header['v_maj']}.{header['v_min']}.{header['v_rev']}")
        print(f"    - File Count:      {header['file_count']:,}")

        # 1. Check all offsets and path alignment
        misaligned_offsets = []
        md5_mismatches = []
        last_offset_end = 0

        with open(pck_path, "rb") as f:
            for p, meta in files.items():
                offset = meta["offset"]
                size = meta["size"]
                expected_md5 = meta["md5"]

                if offset % 16 != 0:
                    misaligned_offsets.append((p, offset))

                # Verify actual MD5
                f.seek(offset)
                data = f.read(size)
                actual_md5 = hashlib.md5(data).digest()
                if actual_md5 != expected_md5:
                    md5_mismatches.append((p, expected_md5.hex(), actual_md5.hex()))

                end_pos = (offset + size + 15) & ~15
                if end_pos > last_offset_end:
                    last_offset_end = end_pos

        print(f"    - Offset Alignment Errors (16-byte): {len(misaligned_offsets)}")
        print(f"    - MD5 Digest Mismatches:             {len(md5_mismatches)}")
        print(f"    - Last Data End Position:            {last_offset_end:,}")
        print(f"    - File Size on Disk:                 {file_size:,}")

        if last_offset_end != file_size:
            raise IOError(f"PCK size mismatch: last data end {last_offset_end} != file size {file_size}")

        if misaligned_offsets:
            raise ValueError(f"Found {len(misaligned_offsets)} misaligned file offsets!")

        if md5_mismatches:
            raise ValueError(f"Found {len(md5_mismatches)} MD5 mismatches!")

        # 2. Check localized assets existence
        # Check fonts
        for font in FONTS_TO_IMPORT:
            if font not in files:
                raise ValueError(f"Required font missing: {font}")
        print(f"    - Russian Fonts Present:             YES (3/3)")

        # Check STEX
        for stex in STEX_TO_IMPORT:
            if stex not in files:
                raise ValueError(f"Required STEX missing: {stex}")
        print(f"    - Russian STEX UI Textures Present:  YES (8/8)")

        # Check GD scripts and verify absence of GDC/REMAP
        patched_gd = [p.relative_to(self.patched_dir).as_posix() for p in self.patched_dir.rglob("*.gd")]
        for rel in patched_gd:
            gd_path = f"res://{rel}"
            gdc_path = f"res://{rel[:-3]}.gdc"
            remap_path = f"res://{rel}.remap"

            if gd_path not in files:
                raise ValueError(f"Patched .gd script missing: {gd_path}")
            if gdc_path in files:
                raise ValueError(f"Old bytecode .gdc was NOT removed: {gdc_path}")
            if remap_path in files:
                raise ValueError(f"Old .remap file was NOT removed: {remap_path}")

        print(f"    - Patched GDScripts Present:         YES ({len(patched_gd)} scripts)")
        print(f"    - Old .gdc/.remap Safely Stripped:   YES (0 lingering)")

        # Check TSCN scenes
        patched_tscn = [p.relative_to(self.patched_dir).as_posix() for p in self.patched_dir.rglob("*.tscn")]
        for rel in patched_tscn:
            tscn_path = f"res://{rel}"
            if tscn_path not in files:
                raise ValueError(f"Patched .tscn scene missing: {tscn_path}")
        print(f"    - Patched TSCN Scenes Present:       YES ({len(patched_tscn)} scenes)")

        print("\n" + "=" * 80)
        print(" VERIFICATION STATUS: [SUCCESS] ARCHIVE IS 100% HEALTHY AND VALID")
        print("=" * 80)


def main():
    script_dir = Path(__file__).resolve().parent
    if (script_dir / "_source_pcks" / "vanilla_steam.pck").exists():
        base_dir = script_dir
    elif (script_dir / "cs_loc" / "_source_pcks" / "vanilla_steam.pck").exists():
        base_dir = script_dir / "cs_loc"
    elif (Path.cwd() / "_source_pcks" / "vanilla_steam.pck").exists():
        base_dir = Path.cwd()
    elif (Path.cwd() / "cs_loc" / "_source_pcks" / "vanilla_steam.pck").exists():
        base_dir = Path.cwd() / "cs_loc"
    else:
        base_dir = script_dir

    builder = PckBuilder(base_dir)
    builder.generate_patched_files()
    builder.validate_patched_syntax()
    builder.build_pck()
    builder.verify_pck()


if __name__ == "__main__":
    main()
