#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
10_wrap_intro_subtitles.py
--------------------------------------------------------------------------------
Lead Localization Engineering & Reverse-Engineering Tool for Cruelty Squad (Godot 3.x)
TASK 10: Safe Line Wrapping (\\n) for Long Intro & Ending Subtitles (Zero-Risk Polish)
--------------------------------------------------------------------------------
Author: Antigravity (Google DeepMind)
Target Game: Cruelty Squad (Godot Engine v3.x)
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
from typing import Dict, Any, List, Tuple, Set, Optional

# Reconfigure console output to UTF-8
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

PCK_MAGIC = b"GDPC"
PCK_FORMAT_VERSION = 1
PCK_HEADER_SIZE = 88
FILE_ALIGNMENT = 16

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

# Exact natural Russian subtitles with newline (\\n) wrapping for Intro
CUTSCENE1_WRAPPED_LINES = [
    "",
    "",
    "",
    # 3 (len 56 -> 10 + 45)
    "Эй, это я.\\nЯ разбудил тебя от твоей депрессивной спячки?",
    # 4 (len 68 -> 29 + 38)
    "Слышал, ты в глубокой заднице\\nпосле увольнения из Отряда Смерти SEC.",
    # 5 (len 89 -> 45 + 43)
    "В конце концов, не так уж много может сделать\\nтакой конченый отшельник-неудачник, как ты.",
    # 6 (len 67 -> 32 + 34)
    "У меня для тебя отличные новости\\nкасательно твоего трудоустройства.",
    # 7 (len 91 -> 50 + 40)
    "Эта работа как раз в твоем вкусе, но тебе придется\\nперестроиться на корпоративное мышление.",
    # 8 (len 75 -> 32 + 42)
    "Я создал тебе аккаунт на MyWork,\\nтак что можешь приступать, когда захочешь.",
    # 9 (len 47 -> 1 line)
    "Полагаю, подходящее снаряжение у тебя уже есть.",
    # 10 (len 104 -> 56 + 47)
    "И последнее: тебе придется логиниться хотя бы на 15 минут\\nв день в приложении психологической адаптации.",
    # 11 (len 58 -> 39 + 18)
    "Нам нужен ясный и подготовленный разум.\\nБез срывов. Понял?",
    # 12 (len 54 -> 22 + 31)
    "На этом, пожалуй, все.\\nУдачи на новой карьерной стезе.",
    "",
    "",
]


class IntroSubtitlesWrapTool:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.vanilla_dir = base_dir / "vanilla_new"
        self.patched_dir = base_dir / "_patched_files"
        self.pck_dir = base_dir / "_source_pcks"
        self.vanilla_pck_path = self.pck_dir / "vanilla_steam.pck"
        self.ru_pck_path = self.pck_dir / "ru_2021.pck"
        self.output_pck_path = base_dir / "crueltysquad_ru_v2.pck"
        self.root_pck_path = Path("C:/dev/crueltysquad_ru_v2.pck")
        self.backup_pck_path = base_dir / "crueltysquad_ru_v2_working_backup.pck"
        self.root_backup_pck_path = Path("C:/dev/crueltysquad_ru_v2_working_backup.pck")

    def run_all(self):
        print("=" * 80)
        print(" CRUELTY SQUAD - TASK 10: ZERO-RISK SUBTITLES WRAPPING & PACK")
        print("=" * 80)

        self.step1_backup_pck()
        self.step2_apply_subtitles_wrapping()
        self.step3_prepack_automated_linter()
        self.step4_binary_pck_rebuild()
        self.step5_verify_and_report()

    # --------------------------------------------------------------------------
    # Step 1: Backup Working PCK
    # --------------------------------------------------------------------------
    def step1_backup_pck(self):
        print("\n[*] [1/5] Ensuring working backup of PCK exists...")
        if self.output_pck_path.exists():
            shutil.copy2(self.output_pck_path, self.backup_pck_path)
            shutil.copy2(self.output_pck_path, self.root_backup_pck_path)
            print(f"[+] Backup created: {self.backup_pck_path} ({self.backup_pck_path.stat().st_size:,} bytes)")
        else:
            raise FileNotFoundError(f"Working PCK not found: {self.output_pck_path}")

    # --------------------------------------------------------------------------
    # Step 2: Apply Subtitles Wrapping to Cutscenes
    # --------------------------------------------------------------------------
    def step2_apply_subtitles_wrapping(self):
        print("\n" + "=" * 80)
        print(" [*] [2/5] FORMATTING SUBTITLES WITH SAFE \\n WRAPPING")
        print("=" * 80)

        # 1. Cutscenes/Cutscene1.tscn (Intro)
        c1_file = self.patched_dir / "Cutscenes" / "Cutscene1.tscn"
        assert c1_file.exists(), f"Missing file: {c1_file}"

        c1_lines = c1_file.read_text(encoding="utf-8").splitlines(keepends=True)

        # Lines 1893 to 1897 in Cutscene1.tscn
        ru_items = [f'"{s}"' for s in CUTSCENE1_WRAPPED_LINES]
        c1_lines[1892] = f'LINES = [ {ru_items[0]}, {ru_items[1]}, {ru_items[2]}, {ru_items[3]},\n'
        c1_lines[1893] = f'{ru_items[4]},\n'
        c1_lines[1894] = f'{ru_items[5]},\n'
        c1_lines[1895] = f'{ru_items[6]}, {ru_items[7]},\n'
        c1_lines[1896] = f'{ru_items[8]}, {ru_items[9]}, {ru_items[10]}, {ru_items[11]}, {ru_items[12]}, {ru_items[13]}, {ru_items[14]} ]\n'

        c1_file.write_text("".join(c1_lines), encoding="utf-8", newline="\n")
        print(f"[+] Updated {c1_file.name} with natural \\n line wrapping on lines 1893-1897.")

        # 2. Cutscenes/CutsceneEnd2.tscn (Ending 2 - wrap CEO mindset quote)
        c2_file = self.patched_dir / "Cutscenes" / "CutsceneEnd2.tscn"
        if c2_file.exists():
            c2_content = c2_file.read_text(encoding="utf-8")
            target_ceo_unwrapped = '"Ставь цели. Имей десятилетний план. Инвестируй. Вставай рано. Мышление СЕО."'
            target_ceo_wrapped = '"Ставь цели. Имей десятилетний план. Инвестируй.\\nВставай рано. Мышление СЕО."'
            if target_ceo_unwrapped in c2_content:
                c2_content = c2_content.replace(target_ceo_unwrapped, target_ceo_wrapped, 1)
                c2_file.write_text(c2_content, encoding="utf-8", newline="\n")
                print(f"[+] Updated {c2_file.name} (wrapped long CEO quote with \\n).")

        # Display full before/after table for Intro
        print("\n" + "=" * 80)
        print(" INTRO SUBTITLES FORMATTING COMPARISON (BEFORE vs AFTER):")
        print("=" * 80)
        unwrapped_phrases = [
            "Эй, это я. Я разбудил тебя от твоей депрессивной спячки?",
            "Слышал, ты в глубокой заднице после увольнения из Отряда Смерти SEC.",
            "В конце концов, не так уж много может сделать такой конченый отшельник-неудачник, как ты.",
            "У меня для тебя отличные новости касательно твоего трудоустройства.",
            "Эта работа как раз в твоем вкусе, но тебе придется перестроиться на корпоративное мышление.",
            "Я создал тебе аккаунт на MyWork, так что можешь приступать, когда захочешь.",
            "Полагаю, подходящее снаряжение у тебя уже есть.",
            "И последнее: тебе придется логиниться хотя бы на 15 минут в день в приложении психологической адаптации.",
            "Нам нужен ясный и подготовленный разум. Без срывов. Понял?",
            "На этом, пожалуй, все. Удачи на новой карьерной стезе.",
        ]
        wrapped_phrases = [
            CUTSCENE1_WRAPPED_LINES[3],
            CUTSCENE1_WRAPPED_LINES[4],
            CUTSCENE1_WRAPPED_LINES[5],
            CUTSCENE1_WRAPPED_LINES[6],
            CUTSCENE1_WRAPPED_LINES[7],
            CUTSCENE1_WRAPPED_LINES[8],
            CUTSCENE1_WRAPPED_LINES[9],
            CUTSCENE1_WRAPPED_LINES[10],
            CUTSCENE1_WRAPPED_LINES[11],
            CUTSCENE1_WRAPPED_LINES[12],
        ]

        for i, (u, w) in enumerate(zip(unwrapped_phrases, wrapped_phrases), start=1):
            print(f"Phrase {i:2d}:")
            print(f"  [Original 1-line]: {u} ({len(u)} chars)")
            w_disp = w.replace("\\n", "\n                     ")
            print(f"  [Formatted \\n]:   {w_disp}")
            print("-" * 80)

    # --------------------------------------------------------------------------
    # Step 3: Strict Pre-Pack Automated Linter (Quality Gate)
    # --------------------------------------------------------------------------
    def step3_prepack_automated_linter(self):
        print("\n" + "=" * 80)
        print(" [*] [3/5] STRICT PRE-PACK AUTOMATED LINTER")
        print("=" * 80)

        total_gd_checked = 0
        total_tscn_checked = 0
        total_json_checked = 0
        violations: List[str] = []

        # 1. GDScript Linter
        for gd_path in self.patched_dir.rglob("*.gd"):
            total_gd_checked += 1
            rel_path = gd_path.relative_to(self.patched_dir).as_posix()
            vanilla_path = self.vanilla_dir / rel_path

            if not vanilla_path.exists():
                violations.append(f"GDScript {rel_path}: No corresponding vanilla file found.")
                continue

            v_lines = vanilla_path.read_text(encoding="utf-8", errors="ignore").splitlines()
            p_lines = gd_path.read_text(encoding="utf-8", errors="ignore").splitlines()

            # Rule A: Line count must match vanilla exactly
            if len(p_lines) != len(v_lines):
                violations.append(
                    f"GDScript {rel_path}: Line count mismatch! Vanilla={len(v_lines)}, Patched={len(p_lines)}"
                )

            # Rule B: Pure tab indentation only - NO lines starting with space
            for lno, line in enumerate(p_lines, start=1):
                if line.startswith(" "):
                    violations.append(f"GDScript {rel_path}:{lno}: Line starts with space instead of tab!")

            # Rule C: Function definitions must match vanilla lines
            for lno, (v_l, p_l) in enumerate(zip(v_lines, p_lines), start=1):
                if v_l.strip().startswith("func ") and not p_l.strip().startswith("func "):
                    violations.append(
                        f"GDScript {rel_path}:{lno}: Function definition missing or moved! Expected '{v_l.strip()}', got '{p_l.strip()}'"
                    )

            # Rule D: Balanced quotes check
            for lno, line in enumerate(p_lines, start=1):
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                test_line = stripped.replace(r'\"', '').replace(r"\'", '')
                dquotes = test_line.count('"')
                if dquotes % 2 != 0:
                    violations.append(f"GDScript {rel_path}:{lno}: Odd number of double-quotes ({dquotes})!")

        # 2. TSCN Linter
        for tscn_path in self.patched_dir.rglob("*.tscn"):
            total_tscn_checked += 1
            rel_path = tscn_path.relative_to(self.patched_dir).as_posix()
            vanilla_path = self.vanilla_dir / rel_path

            if vanilla_path.exists():
                v_lines = vanilla_path.read_text(encoding="utf-8", errors="ignore").splitlines()
                p_lines = tscn_path.read_text(encoding="utf-8", errors="ignore").splitlines()
                if len(p_lines) != len(v_lines):
                    violations.append(
                        f"TSCN {rel_path}: Line count mismatch! Vanilla={len(v_lines)}, Patched={len(p_lines)}"
                    )

            content = tscn_path.read_text(encoding="utf-8", errors="ignore")
            ext_ids: Set[str] = set(re.findall(r'\[ext_resource[^\]]+id=(\d+)', content))
            sub_ids: Set[str] = set(re.findall(r'\[sub_resource[^\]]+id=(\d+)', content))

            ext_usages = set(re.findall(r'ExtResource\(\s*(\d+)\s*\)', content))
            sub_usages = set(re.findall(r'SubResource\(\s*(\d+)\s*\)', content))

            missing_ext = ext_usages - ext_ids
            missing_sub = sub_usages - sub_ids

            if missing_ext:
                violations.append(f"TSCN {rel_path}: Undefined ExtResource IDs referenced: {missing_ext}")
            if missing_sub:
                violations.append(f"TSCN {rel_path}: Undefined SubResource IDs referenced: {missing_sub}")

        # 3. JSON Linter
        for json_path in self.patched_dir.rglob("*.json"):
            total_json_checked += 1
            rel_path = json_path.relative_to(self.patched_dir).as_posix()
            try:
                json.loads(json_path.read_text(encoding="utf-8"))
            except Exception as e:
                violations.append(f"JSON {rel_path}: Parse error: {e}")

        print(f"[*] Linter verified:")
        print(f"    - {total_gd_checked} GDScript files")
        print(f"    - {total_tscn_checked} TSCN scene files")
        print(f"    - {total_json_checked} JSON metadata files")

        if violations:
            print("\n[!] FATAL: LINTER VIOLATIONS FOUND:")
            for v in violations:
                print(f"    - {v}")
            raise RuntimeError(f"Pre-pack linter failed with {len(violations)} violations! Packaging aborted.")

        print("\n[+] PRE-PACK LINTER PASSED: 0 violations! 100% structural and syntax compliance.")

    # --------------------------------------------------------------------------
    # Step 4: Binary Repack of crueltysquad_ru_v2.pck
    # --------------------------------------------------------------------------
    def step4_binary_pck_rebuild(self):
        print("\n" + "=" * 80)
        print(" [*] [4/5] REBUILDING crueltysquad_ru_v2.pck (PURE PYTHON)")
        print("=" * 80)

        t0 = time.time()

        # Read TOCs from source archives
        with open(self.vanilla_pck_path, "rb") as f:
            v_hdr = struct.unpack("<4sIIII64xI", f.read(88))
            vanilla_files = {}
            for _ in range(v_hdr[5]):
                plen = struct.unpack("<I", f.read(4))[0]
                p = f.read(plen).rstrip(b"\x00").decode("utf-8", errors="replace")
                offset, size, md5 = struct.unpack("<QQ16s", f.read(32))
                vanilla_files[p] = {"offset": offset, "size": size, "md5": md5}

        with open(self.ru_pck_path, "rb") as f:
            ru_hdr = struct.unpack("<4sIIII64xI", f.read(88))
            ru_files = {}
            for _ in range(ru_hdr[5]):
                plen = struct.unpack("<I", f.read(4))[0]
                p = f.read(plen).rstrip(b"\x00").decode("utf-8", errors="replace")
                offset, size, md5 = struct.unpack("<QQ16s", f.read(32))
                ru_files[p] = {"offset": offset, "size": size, "md5": md5}

        # Build virtual table
        virtual_table: Dict[str, Dict[str, Any]] = {}

        # 1. Base vanilla
        for p, meta in vanilla_files.items():
            virtual_table[p] = {
                "type": "vanilla",
                "offset": meta["offset"],
                "size": meta["size"],
                "md5": meta["md5"],
            }

        # 2. Cyrillic Fonts from ru_2021.pck
        for font in FONTS_TO_IMPORT:
            if font in ru_files:
                virtual_table[font] = {
                    "type": "ru_pck",
                    "offset": ru_files[font]["offset"],
                    "size": ru_files[font]["size"],
                    "md5": ru_files[font]["md5"],
                }

        # 3. Cyrillic UI STEX from ru_2021.pck
        for stex in STEX_TO_IMPORT:
            if stex in ru_files:
                virtual_table[stex] = {
                    "type": "ru_pck",
                    "offset": ru_files[stex]["offset"],
                    "size": ru_files[stex]["size"],
                    "md5": ru_files[stex]["md5"],
                }

        # 4. All patched disk files (.tscn, .json, .gd)
        patched_disk_files = [p for p in self.patched_dir.rglob("*.*") if p.is_file()]
        gdc_removed = 0
        remap_removed = 0
        scn_removed = 0

        for disk_p in patched_disk_files:
            rel = disk_p.relative_to(self.patched_dir).as_posix()
            res_p = f"res://{rel}"
            data = disk_p.read_bytes()

            # If GDScript, strip .gdc and .remap so Godot compiles .gd directly
            if disk_p.suffix == ".gd":
                gdc_p = f"res://{rel[:-3]}.gdc"
                remap_p = f"res://{rel}.remap"
                if gdc_p in virtual_table:
                    del virtual_table[gdc_p]
                    gdc_removed += 1
                if remap_p in virtual_table:
                    del virtual_table[remap_p]
                    remap_removed += 1

            # If TSCN, strip .remap and .scn if present
            if disk_p.suffix == ".tscn":
                remap_p = f"res://{rel}.remap"
                scn_p = f"res://{rel[:-5]}.scn"
                if remap_p in virtual_table:
                    del virtual_table[remap_p]
                    remap_removed += 1
                if scn_p in virtual_table:
                    del virtual_table[scn_p]
                    scn_removed += 1

            virtual_table[res_p] = {
                "type": "disk",
                "disk_path": disk_p,
                "size": len(data),
                "md5": hashlib.md5(data).digest(),
            }

        print(f"[*] Virtual table files: {len(virtual_table):,}")
        print(f"    - Patched disk files integrated: {len(patched_disk_files)}")
        print(f"    - Stripped old bytecode (.gdc):   {gdc_removed}")
        print(f"    - Stripped old remaps (.remap):   {remap_removed}")
        print(f"    - Stripped compiled scenes (.scn): {scn_removed}")

        # Calculate TOC size and assign file offsets with 16-byte alignment
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

        data_start_offset = (toc_bytes_len + (FILE_ALIGNMENT - 1)) & ~(FILE_ALIGNMENT - 1)
        toc_padding = data_start_offset - toc_bytes_len

        current_offset = data_start_offset
        file_offsets: Dict[str, int] = {}
        for p in sorted_paths:
            entry = virtual_table[p]
            file_offsets[p] = current_offset
            size = entry["size"]
            aligned_size = (size + (FILE_ALIGNMENT - 1)) & ~(FILE_ALIGNMENT - 1)
            current_offset += aligned_size

        total_expected_size = current_offset
        print(f"[*] Writing binary PCK ({total_expected_size:,} bytes)...")

        with open(self.vanilla_pck_path, "rb") as f_vanilla, \
             open(self.ru_pck_path, "rb") as f_ru, \
             open(self.output_pck_path, "wb") as f_out:

            # 1. Header (88 bytes)
            f_out.write(
                struct.pack(
                    "<4sIIII64xI",
                    PCK_MAGIC,
                    PCK_FORMAT_VERSION,
                    3,
                    5,
                    2,
                    len(sorted_paths),
                )
            )

            # 2. File Index (TOC)
            for p in sorted_paths:
                entry = virtual_table[p]
                plen, pbytes = path_info[p]
                f_out.write(struct.pack("<I", plen))
                f_out.write(pbytes)
                f_out.write(
                    struct.pack(
                        "<QQ16s",
                        file_offsets[p],
                        entry["size"],
                        entry["md5"],
                    )
                )

            # Pad TOC to 16-byte alignment
            if toc_padding > 0:
                f_out.write(b"\x00" * toc_padding)

            # 3. Stream File Data
            for p in sorted_paths:
                entry = virtual_table[p]
                etype = entry["type"]

                if etype == "vanilla":
                    f_vanilla.seek(entry["offset"])
                    raw_data = f_vanilla.read(entry["size"])
                elif etype == "ru_pck":
                    f_ru.seek(entry["offset"])
                    raw_data = f_ru.read(entry["size"])
                elif etype == "disk":
                    raw_data = entry["disk_path"].read_bytes()
                else:
                    raise ValueError(f"Unknown entry type: {etype}")

                f_out.write(raw_data)
                padding = ((len(raw_data) + (FILE_ALIGNMENT - 1)) & ~(FILE_ALIGNMENT - 1)) - len(raw_data)
                if padding > 0:
                    f_out.write(b"\x00" * padding)

        elapsed = time.time() - t0
        final_size = self.output_pck_path.stat().st_size
        print(f"[+] Output PCK written in {elapsed:.2f}s: {final_size:,} bytes ({final_size / (1024*1024):.2f} MB)")

        # Sync to root dev directory
        shutil.copy2(self.output_pck_path, self.root_pck_path)
        print(f"[+] Copied to root workspace: {self.root_pck_path}")

    # --------------------------------------------------------------------------
    # Step 5: Verification & Integrity Report
    # --------------------------------------------------------------------------
    def step5_verify_and_report(self):
        print("\n" + "=" * 80)
        print(" [*] [5/5] VERIFYING OUTPUT ARCHIVE & SUBTITLES INTEGRITY")
        print("=" * 80)

        with open(self.output_pck_path, "rb") as f:
            hdr = struct.unpack("<4sIIII64xI", f.read(88))
            magic, version, major, minor, patch, file_count = hdr

            assert magic == PCK_MAGIC, f"Invalid magic: {magic}"
            assert version == PCK_FORMAT_VERSION, f"Invalid version: {version}"

            # Scan TOC for critical files
            toc = {}
            for _ in range(file_count):
                plen = struct.unpack("<I", f.read(4))[0]
                p = f.read(plen).rstrip(b"\x00").decode("utf-8", errors="replace")
                offset, size, md5 = struct.unpack("<QQ16s", f.read(32))
                toc[p] = (offset, size, md5)

        # 1. Verify Intro Cutscene subtitles in PCK
        c1_off, c1_sz, _ = toc["res://Cutscenes/Cutscene1.tscn"]
        with open(self.output_pck_path, "rb") as f:
            f.seek(c1_off)
            c1_text = f.read(c1_sz).decode("utf-8", errors="replace")

        assert "депрессивной спячки" in c1_text, "Verification failed: Intro Russian text missing in PCK!"
        assert "\\nЯ разбудил тебя" in c1_text, "Verification failed: Line wrapping \\n missing in Intro subtitles!"
        assert "\\nпосле увольнения" in c1_text, "Verification failed: Line wrapping \\n missing in Intro phrase 2!"
        print("[+] VERIFIED: Intro Cutscene subtitles contain correct natural \\n wrapping in binary PCK.")

        # 2. Verify Ending 2 subtitles in PCK
        c2_off, c2_sz, _ = toc["res://Cutscenes/CutsceneEnd2.tscn"]
        with open(self.output_pck_path, "rb") as f:
            f.seek(c2_off)
            c2_text = f.read(c2_sz).decode("utf-8", errors="replace")
        assert "\\nВставай рано" in c2_text, "Verification failed: Ending 2 \\n wrapping missing in binary PCK!"
        print("[+] VERIFIED: Ending 2 CEO mindset subtitles contain correct \\n wrapping in binary PCK.")

        print("\n" + "=" * 80)
        print(" TASK 10 COMPLETE: SAFE LINE WRAPPING APPLIED, ZERO RISK, PCK READY!")
        print("=" * 80)


def main():
    base_dir = Path("c:/dev/cs_loc")
    tool = IntroSubtitlesWrapTool(base_dir)
    tool.run_all()


if __name__ == "__main__":
    main()
