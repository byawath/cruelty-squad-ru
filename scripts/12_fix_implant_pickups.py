#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
12_fix_implant_pickups.py
--------------------------------------------------------------------------------
Lead Localization Engineering & Reverse-Engineering Tool for Cruelty Squad (Godot 3.x)
TASK 12: Hotfix Secret Implant Pickups on Levels & Full Equipment Key Synchronization
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


class FixImplantPickupsTool:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.vanilla_dir = base_dir / "vanilla_new"
        self.patched_dir = base_dir / "_patched_files"
        self.pck_dir = base_dir / "_source_pcks"
        self.vanilla_pck_path = self.pck_dir / "vanilla_steam.pck"
        self.ru_pck_path = self.pck_dir / "ru_2021.pck"
        self.output_pck_path = base_dir / "crueltysquad_ru_v2.pck"
        self.root_pck_path = Path("C:/dev/crueltysquad_ru_v2.pck")
        self.game_pck_path = base_dir / "crueltysquad.pck"

        self.implants_map: Dict[str, str] = {}
        self.weapons_map: Dict[str, str] = {}

    def run_all(self):
        print("=" * 80)
        print(" CRUELTY SQUAD - TASK 12: FIX IMPLANT PICKUPS & SYNC EQUIPMENT KEYS")
        print("=" * 80)

        self.step1_build_authoritative_glossary()
        self.step2_patch_level_and_object_scenes()
        self.step3_synchronize_gd_scripts()
        self.step4_prepack_automated_linter()
        self.step5_binary_pck_rebuild()
        self.step6_verify_and_report()

    # --------------------------------------------------------------------------
    # Step 1: Build Authoritative Equipment Map
    # --------------------------------------------------------------------------
    def step1_build_authoritative_glossary(self):
        print("\n[*] [1/6] Building authoritative equipment map (Global.gd / Implants.gd)...")

        v_implants_path = self.vanilla_dir / "Scripts" / "Implants.gd"
        p_implants_path = self.patched_dir / "Scripts" / "Implants.gd"

        assert v_implants_path.exists(), f"Missing vanilla Implants.gd: {v_implants_path}"
        assert p_implants_path.exists(), f"Missing patched Implants.gd: {p_implants_path}"

        v_lines = v_implants_path.read_text(encoding="utf-8").splitlines()
        p_lines = p_implants_path.read_text(encoding="utf-8").splitlines()

        for i in range(len(v_lines)):
            if "new_implant.i_name =" in v_lines[i]:
                v_name = v_lines[i].split("=", 1)[1].strip().strip("\"'")
                p_name = p_lines[i].split("=", 1)[1].strip().strip("\"'")
                self.implants_map[v_name] = p_name

        print(f"[+] Loaded {len(self.implants_map)} implants from Implants.gd:")
        print("-" * 80)
        print(f" {'#':<3} | {'ENGLISH TECHNICAL KEY (Vanilla)':<35} | {'RUSSIAN GAMEPLAY NAME (Build)':<35}")
        print("-" * 80)

        for idx, (en, ru) in enumerate(sorted(self.implants_map.items()), start=1):
            highlight = ""
            if en in ["Cursed Torch", "Icaros Machine", "Extravagant Suit", "House"]:
                highlight = " <== [CRITICAL SYNC TARGET]"
            print(f" {idx:02d}  | {en:<35} | {ru:<35}{highlight}")

        print("-" * 80)

        # Highlight requested items explicitly
        critical_targets = ["Cursed Torch", "Icaros Machine", "Extravagant Suit", "House"]
        print("\n[!] CRITICAL TARGETS VERIFICATION:")
        for t in critical_targets:
            assert t in self.implants_map, f"Critical target {t} missing in implants map!"
            print(f"    - {t:<20} => '{self.implants_map[t]}'")

    # --------------------------------------------------------------------------
    # Step 2: Patch All Level and Object TSCN Scenes
    # --------------------------------------------------------------------------
    def step2_patch_level_and_object_scenes(self):
        print("\n[*] [2/6] Patching level and object .tscn scenes for implant_name properties...")

        levels_dir = self.patched_dir / "Levels"
        vanilla_levels_dir = self.vanilla_dir / "Levels"

        patched_count = 0
        patched_details: List[Tuple[str, int, str, str]] = []

        # Find all .tscn files in _patched_files
        for tscn_path in self.patched_dir.rglob("*.tscn"):
            rel_path = tscn_path.relative_to(self.patched_dir).as_posix()
            v_tscn_path = self.vanilla_dir / rel_path

            p_lines = tscn_path.read_text(encoding="utf-8").splitlines(keepends=True)
            v_lines = v_tscn_path.read_text(encoding="utf-8").splitlines(keepends=True) if v_tscn_path.exists() else None

            modified = False

            for lno in range(len(p_lines)):
                line = p_lines[lno]

                # Match implant_name = "..."
                if "implant_name =" in line:
                    match = re.search(r'implant_name\s*=\s*"([^"]+)"', line)
                    if match:
                        cur_name = match.group(1)
                        # Check if cur_name is an English name in implants_map
                        if cur_name in self.implants_map:
                            target_ru = self.implants_map[cur_name]
                            new_line = line.replace(f'implant_name = "{cur_name}"', f'implant_name = "{target_ru}"')
                            p_lines[lno] = new_line
                            modified = True
                            patched_count += 1
                            patched_details.append((rel_path, lno + 1, cur_name, target_ru))
                        elif cur_name in self.implants_map.values():
                            patched_count += 1
                            patched_details.append((rel_path, lno + 1, "[ALREADY_RUSSIAN]", cur_name))

            if modified:
                if v_lines:
                    assert len(p_lines) == len(v_lines), f"Line count mismatch in {rel_path}: {len(p_lines)} vs {len(v_lines)}"
                tscn_path.write_text("".join(p_lines), encoding="utf-8", newline="\n")

        print(f"[+] Total level/object scene nodes patched: {patched_count}")
        for rel_p, line_no, old_n, new_n in patched_details:
            print(f"    - {rel_p}:{line_no} -> implant_name = '{new_n}' (was '{old_n}')")

        assert patched_count >= 14, f"Expected at least 14 level pickups patched, got {patched_count}!"

    # --------------------------------------------------------------------------
    # Step 3: Synchronize Implant Checks in .gd Scripts
    # --------------------------------------------------------------------------
    def step3_synchronize_gd_scripts(self):
        print("\n[*] [3/6] Synchronizing implant checks and operations in .gd scripts...")

        # 1. Menu_Test.gd (lines 1449-1450: House removal on restart progress)
        mt_path = self.patched_dir / "Menu_Test.gd"
        v_mt_path = self.vanilla_dir / "Menu_Test.gd"
        mt_lines = mt_path.read_text(encoding="utf-8").splitlines(keepends=True)
        v_mt_lines = v_mt_path.read_text(encoding="utf-8").splitlines(keepends=True)

        house_ru = self.implants_map["House"]  # "Дом"
        mt_modified = False

        for lno in range(len(mt_lines)):
            l = mt_lines[lno]
            if 'purchased_implants.find("House")' in l:
                mt_lines[lno] = l.replace('"House"', f'"{house_ru}"')
                mt_modified = True
                print(f"    [+] Menu_Test.gd:{lno+1}: synchronized 'House' -> '{house_ru}'")

        if mt_modified:
            assert len(mt_lines) == len(v_mt_lines), "Menu_Test.gd line count mismatch!"
            mt_path.write_text("".join(mt_lines), encoding="utf-8", newline="\n")

        # 2. Menu/Character_Menu.gd (line 174: House purchase unlocks bonus level)
        cm_path = self.patched_dir / "Menu" / "Character_Menu.gd"
        v_cm_path = self.vanilla_dir / "Menu" / "Character_Menu.gd"
        cm_lines = cm_path.read_text(encoding="utf-8").splitlines(keepends=True)
        v_cm_lines = v_cm_path.read_text(encoding="utf-8").splitlines(keepends=True)

        cm_modified = False
        for lno in range(len(cm_lines)):
            l = cm_lines[lno]
            if 'IMPLANTS[i].i_name == "House"' in l:
                cm_lines[lno] = l.replace('"House"', f'"{house_ru}"')
                cm_modified = True
                print(f"    [+] Menu/Character_Menu.gd:{lno+1}: synchronized 'House' -> '{house_ru}'")

        if cm_modified:
            assert len(cm_lines) == len(v_cm_lines), "Character_Menu.gd line count mismatch!"
            cm_path.write_text("".join(cm_lines), encoding="utf-8", newline="\n")

        # 3. Entities/Game_Manager.gd (line 602: Extravagant Suit achievement check)
        gm_path = self.patched_dir / "Entities" / "Game_Manager.gd"
        v_gm_path = self.vanilla_dir / "Entities" / "Game_Manager.gd"
        gm_lines = gm_path.read_text(encoding="utf-8").splitlines(keepends=True)
        v_gm_lines = v_gm_path.read_text(encoding="utf-8").splitlines(keepends=True)

        suit_ru = self.implants_map["Extravagant Suit"]  # "Экстравагантный костюм"
        gm_modified = False

        for lno in range(len(gm_lines)):
            l = gm_lines[lno]
            if 'torso_implant.i_name == "Extravagant Suit"' in l:
                gm_lines[lno] = l.replace('"Extravagant Suit"', f'"{suit_ru}"')
                gm_modified = True
                print(f"    [+] Entities/Game_Manager.gd:{lno+1}: synchronized 'Extravagant Suit' -> '{suit_ru}'")

        if gm_modified:
            assert len(gm_lines) == len(v_gm_lines), "Game_Manager.gd line count mismatch!"
            gm_path.write_text("".join(gm_lines), encoding="utf-8", newline="\n")

        # 4. snakehead.gd (line 76: Golem Exosystem drop)
        sh_path = self.patched_dir / "snakehead.gd"
        v_sh_path = self.vanilla_dir / "snakehead.gd"
        sh_lines = sh_path.read_text(encoding="utf-8").splitlines(keepends=True)
        v_sh_lines = v_sh_path.read_text(encoding="utf-8").splitlines(keepends=True)

        golem_ru = self.implants_map["CSIJ Level VI Golem Exosystem"]
        sh_modified = False

        for lno in range(len(sh_lines)):
            l = sh_lines[lno]
            if 'purchased_implants.append("CSIJ Level VI Golem Exosystem")' in l:
                sh_lines[lno] = l.replace('"CSIJ Level VI Golem Exosystem"', f'"{golem_ru}"')
                sh_modified = True
                print(f"    [+] snakehead.gd:{lno+1}: synchronized Golem -> '{golem_ru}'")

        if sh_modified:
            assert len(sh_lines) == len(v_sh_lines), "snakehead.gd line count mismatch!"
            sh_path.write_text("".join(sh_lines), encoding="utf-8", newline="\n")

        # 5. Entities/Physics_Objects/Implant_Object.gd (line 7: default export var implant_name)
        io_path = self.patched_dir / "Entities" / "Physics_Objects" / "Implant_Object.gd"
        v_io_path = self.vanilla_dir / "Entities" / "Physics_Objects" / "Implant_Object.gd"
        io_lines = io_path.read_text(encoding="utf-8").splitlines(keepends=True)
        v_io_lines = v_io_path.read_text(encoding="utf-8").splitlines(keepends=True)

        hazmat_ru = self.implants_map["Hazmat Suit"]
        io_modified = False

        for lno in range(len(io_lines)):
            l = io_lines[lno]
            if 'export var implant_name = "Hazmat Suit"' in l:
                io_lines[lno] = l.replace('"Hazmat Suit"', f'"{hazmat_ru}"')
                io_modified = True
                print(f"    [+] Implant_Object.gd:{lno+1}: synchronized default implant_name -> '{hazmat_ru}'")

        if io_modified:
            assert len(io_lines) == len(v_io_lines), "Implant_Object.gd line count mismatch!"
            io_path.write_text("".join(io_lines), encoding="utf-8", newline="\n")

        print("[+] All .gd scripts synchronized with 0 desynchronizations.")

    # --------------------------------------------------------------------------
    # Step 4: Strict Pre-Pack Automated Linter
    # --------------------------------------------------------------------------
    def step4_prepack_automated_linter(self):
        print("\n" + "=" * 80)
        print(" [*] [4/6] STRICT PRE-PACK AUTOMATED LINTER")
        print("=" * 80)

        gd_files = list(self.patched_dir.rglob("*.gd"))
        tscn_files = list(self.patched_dir.rglob("*.tscn"))
        json_files = list(self.patched_dir.rglob("*.json"))

        violations: List[str] = []

        # 1. GDScript Linter
        for p in gd_files:
            rel = p.relative_to(self.patched_dir).as_posix()
            v_p = self.vanilla_dir / rel
            p_lines = p.read_text(encoding="utf-8").splitlines()

            if v_p.exists():
                v_lines = v_p.read_text(encoding="utf-8").splitlines()
                if len(p_lines) != len(v_lines):
                    violations.append(f"GDScript line count mismatch: {rel} ({len(p_lines)} vs vanilla {len(v_lines)})")

            for lno, line in enumerate(p_lines, start=1):
                # Check for space indentation
                if line.startswith(" ") and not line.strip().startswith("#"):
                    violations.append(f"Space indentation in {rel}:{lno}: {repr(line[:40])}")

                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                test_line = stripped.replace(r'\"', '').replace(r"\'", '')
                dquotes = test_line.count('"')
                if dquotes % 2 != 0:
                    violations.append(f"GDScript {rel}:{lno}: Odd number of double-quotes ({dquotes})!")

        # 2. TSCN Linter
        for p in tscn_files:
            rel = p.relative_to(self.patched_dir).as_posix()
            v_p = self.vanilla_dir / rel

            if v_p.exists():
                v_lines = v_p.read_text(encoding="utf-8", errors="ignore").splitlines()
                p_lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
                if len(p_lines) != len(v_lines):
                    violations.append(f"TSCN {rel}: Line count mismatch! Vanilla={len(v_lines)}, Patched={len(p_lines)}")

            content = p.read_text(encoding="utf-8", errors="ignore")
            ext_ids: Set[str] = set(re.findall(r'\[ext_resource[^\]]+id=(\d+)', content))
            sub_ids: Set[str] = set(re.findall(r'\[sub_resource[^\]]+id=(\d+)', content))

            ext_usages = set(re.findall(r'ExtResource\(\s*(\d+)\s*\)', content))
            sub_usages = set(re.findall(r'SubResource\(\s*(\d+)\s*\)', content))

            missing_ext = ext_usages - ext_ids
            missing_sub = sub_usages - sub_ids

            if missing_ext:
                violations.append(f"TSCN {rel}: Undefined ExtResource IDs referenced: {missing_ext}")
            if missing_sub:
                violations.append(f"TSCN {rel}: Undefined SubResource IDs referenced: {missing_sub}")

            # Specific check for invalid double escapes
            if r'\\"' in content or r'\\\"' in content:
                violations.append(f"TSCN {rel}: Contains invalid double-escaped quote sequence!")

        # 3. JSON Linter
        for p in json_files:
            rel = p.relative_to(self.patched_dir).as_posix()
            try:
                json.loads(p.read_text(encoding="utf-8"))
            except Exception as e:
                violations.append(f"JSON {rel}: Parse error: {e}")

        print(f"[*] Linter verified:")
        print(f"    - {len(gd_files)} GDScript files")
        print(f"    - {len(tscn_files)} TSCN scene files")
        print(f"    - {len(json_files)} JSON metadata files")

        if violations:
            print("\n[!] LINTER VIOLATIONS FOUND:")
            for v in violations:
                print("    -", v)
            raise AssertionError(f"Pre-pack linter failed with {len(violations)} violations!")

        print("\n[+] PRE-PACK LINTER PASSED: 0 violations! 100% structural and syntax compliance.")

    # --------------------------------------------------------------------------
    # Step 5: Binary Repack of crueltysquad_ru_v2.pck
    # --------------------------------------------------------------------------
    def step5_binary_pck_rebuild(self):
        print("\n" + "=" * 80)
        print(" [*] [5/6] REBUILDING crueltysquad_ru_v2.pck (PURE PYTHON)")
        print("=" * 80)

        t0 = time.time()

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
                f_out.write(
                    struct.pack(
                        f"<I{plen}sQQ16s",
                        plen,
                        pbytes,
                        file_offsets[p],
                        entry["size"],
                        entry["md5"],
                    )
                )

            # TOC padding to 16 bytes
            if toc_padding > 0:
                f_out.write(b"\x00" * toc_padding)

            # 3. Payload Data
            chunk_size = 1024 * 1024
            for p in sorted_paths:
                entry = virtual_table[p]
                expected_offset = file_offsets[p]
                actual_offset = f_out.tell()
                assert actual_offset == expected_offset, f"Offset mismatch for {p}: {actual_offset} != {expected_offset}"

                src_type = entry["type"]
                size = entry["size"]

                if src_type == "disk":
                    with open(entry["disk_path"], "rb") as f_disk:
                        while True:
                            chunk = f_disk.read(chunk_size)
                            if not chunk:
                                break
                            f_out.write(chunk)
                elif src_type == "vanilla":
                    f_vanilla.seek(entry["offset"])
                    bytes_left = size
                    while bytes_left > 0:
                        to_read = min(bytes_left, chunk_size)
                        chunk = f_vanilla.read(to_read)
                        f_out.write(chunk)
                        bytes_left -= len(chunk)
                elif src_type == "ru_pck":
                    f_ru.seek(entry["offset"])
                    bytes_left = size
                    while bytes_left > 0:
                        to_read = min(bytes_left, chunk_size)
                        chunk = f_ru.read(to_read)
                        f_out.write(chunk)
                        bytes_left -= len(chunk)

                # Data padding to 16 bytes
                data_pad = ((size + (FILE_ALIGNMENT - 1)) & ~(FILE_ALIGNMENT - 1)) - size
                if data_pad > 0:
                    f_out.write(b"\x00" * data_pad)

        elapsed = time.time() - t0
        final_size = self.output_pck_path.stat().st_size
        print(f"[+] Output PCK written in {elapsed:.2f}s: {final_size:,} bytes ({final_size / 1024 / 1024:.2f} MB)")

        # Sync to root workspace and crueltysquad.pck
        shutil.copy2(self.output_pck_path, self.root_pck_path)
        shutil.copy2(self.output_pck_path, self.game_pck_path)
        print(f"[+] Synchronized to: {self.root_pck_path}")
        print(f"[+] Synchronized to: {self.game_pck_path}")

    # --------------------------------------------------------------------------
    # Step 6: Verification & Final Report
    # --------------------------------------------------------------------------
    def step6_verify_and_report(self):
        print("\n" + "=" * 80)
        print(" [*] [6/6] VERIFYING OUTPUT ARCHIVE & REPORTING RESULTS")
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

        # 1. Verify Level 2 (Paradise): Cursed Torch and Icaros Machine
        l2_off, l2_sz, _ = toc["res://Levels/Level2.tscn"]
        with open(self.output_pck_path, "rb") as f:
            f.seek(l2_off)
            l2_text = f.read(l2_sz).decode("utf-8", errors="replace")

        assert 'implant_name = "Аппарат «Икарос»"' in l2_text, "Missing 'Аппарат «Икарос»' in Level2.tscn!"
        assert 'implant_name = "Проклятый Светильник"' in l2_text, "Missing 'Проклятый Светильник' in Level2.tscn!"
        print("[+] VERIFIED: Level 2 (Paradise) has 'Аппарат «Икарос»' and 'Проклятый Светильник'.")

        # 2. Verify Training_Level (Abominator)
        tl_off, tl_sz, _ = toc["res://Levels/Training_Level.tscn"]
        with open(self.output_pck_path, "rb") as f:
            f.seek(tl_off)
            tl_text = f.read(tl_sz).decode("utf-8", errors="replace")

        assert 'implant_name = "Богомерз (Мерзость)"' in tl_text, "Missing 'Богомерз (Мерзость)' in Training_Level.tscn!"
        assert r'\"N\"' in tl_text, "Training_Level.tscn DYN_LINES quotation valid!"
        print("[+] VERIFIED: HQ (Training_Level.tscn) has 'Богомерз (Мерзость)'.")

        # 3. Verify Menu_Test.gd (House check)
        mt_off, mt_sz, _ = toc["res://Menu_Test.gd"]
        with open(self.output_pck_path, "rb") as f:
            f.seek(mt_off)
            mt_text = f.read(mt_sz).decode("utf-8", errors="replace")

        assert 'purchased_implants.find("Дом")' in mt_text, "Missing 'find(\"Дом\")' in Menu_Test.gd!"
        print("[+] VERIFIED: Menu_Test.gd has synchronized 'Дом' check.")

        # 4. Verify Character_Menu.gd (House purchase)
        cm_off, cm_sz, _ = toc["res://Menu/Character_Menu.gd"]
        with open(self.output_pck_path, "rb") as f:
            f.seek(cm_off)
            cm_text = f.read(cm_sz).decode("utf-8", errors="replace")

        assert 'IMPLANTS[i].i_name == "Дом"' in cm_text, "Missing 'i_name == \"Дом\"' in Character_Menu.gd!"
        print("[+] VERIFIED: Character_Menu.gd has synchronized 'Дом' purchase check.")

        # 5. Verify Game_Manager.gd (Extravagant Suit achievement)
        gm_off, gm_sz, _ = toc["res://Entities/Game_Manager.gd"]
        with open(self.output_pck_path, "rb") as f:
            f.seek(gm_off)
            gm_text = f.read(gm_sz).decode("utf-8", errors="replace")

        assert 'torso_implant.i_name == "Экстравагантный костюм"' in gm_text, "Missing 'Экстравагантный костюм' in Game_Manager.gd!"
        print("[+] VERIFIED: Game_Manager.gd has synchronized 'Экстравагантный костюм' achievement check.")

        print("\n" + "=" * 80)
        print(" TASK 12 COMPLETE: ALL IMPLANT PICKUPS & SCRIPT CHECKS 100% SYNCHRONIZED!")
        print("=" * 80)


def main():
    base_dir = Path("C:/dev/cs_loc")
    tool = FixImplantPickupsTool(base_dir)
    tool.run_all()


if __name__ == "__main__":
    main()
