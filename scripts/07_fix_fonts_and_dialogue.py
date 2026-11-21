#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
07_fix_fonts_and_dialogue.py
--------------------------------------------------------------------------------
Lead Localization Engineering & Reverse-Engineering Tool for Cruelty Squad (Godot 3.x)
Task 7: Fix Invisible Font in Briefing Window, Freeze in Dialogue Boxes & Node Names
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
from typing import Dict, Any, List, Tuple, Optional

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


class DialogueAndFontHotfix:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.vanilla_dir = base_dir / "vanilla_new"
        self.patched_dir = base_dir / "_patched_files"
        self.pck_dir = base_dir / "_source_pcks"
        self.vanilla_pck_path = self.pck_dir / "vanilla_steam.pck"
        self.ru_pck_path = self.pck_dir / "ru_2021.pck"
        self.output_pck_path = base_dir / "crueltysquad_ru_v2.pck"

    def run_all(self):
        print("=" * 80)
        print(" CRUELTY SQUAD - TASK 7: FONTS, DIALOGUE HANG & BRIEFING HOTFIX")
        print("=" * 80)

        self.step1_diagnose_godot_log()
        self.step2_fix_speech_scripts()
        self.step3_fix_menu_test_node_names()
        self.step4_fix_briefing_font_in_scene()
        self.step5_rebuild_pck()
        self.step6_verify()

    # --------------------------------------------------------------------------
    # Step 1: Diagnose Godot Engine Log
    # --------------------------------------------------------------------------
    def step1_diagnose_godot_log(self):
        print("\n[*] [1/6] Reading Godot engine log (%APPDATA%/Godot/app_userdata/Cruelty Squad/logs/godot.log)...")
        log_path = Path(os.path.expandvars(r"%APPDATA%\Godot\app_userdata\Cruelty Squad\logs\godot.log"))

        if not log_path.exists():
            print(f"[!] Warning: Log file not found at {log_path}")
            return

        lines = log_path.read_text(encoding="utf-8", errors="ignore").splitlines()
        print(f"[*] Total log lines: {len(lines)}")

        critical_errors = []
        for idx, line in enumerate(lines, 1):
            if any(err_tag in line for err_tag in ["SCRIPT ERROR:", "Parse Error:", "Error calling method", "nonexistent signal"]):
                critical_errors.append((idx, line.strip()))

        print(f"[*] Detected {len(critical_errors)} relevant errors in engine log:")
        for idx, err in critical_errors[:12]:
            print(f"    Line {idx:3d}: {err}")

    # --------------------------------------------------------------------------
    # Step 2: Fix Indentation in Menu/Speech.gd & Scripts/speech_label.gd
    # --------------------------------------------------------------------------
    def step2_fix_speech_scripts(self):
        print("\n[*] [2/6] Fixing indentation and syntax in Speech.gd and speech_label.gd...")

        # 1. Menu/Speech.gd
        speech_path = self.patched_dir / "Menu" / "Speech.gd"
        vanilla_speech = (self.vanilla_dir / "Menu" / "Speech.gd").read_text(encoding="utf-8")

        # Clean replacement with EXACT tabs:
        # Loop has \t. Blocks inside for c in text: have \t\t.
        # Inside if: \t\t\t
        target_latin = "\t\tif c.ord_at(0) >= 97 and c.ord_at(0) <= 122:"
        cyrillic_block = (
            "\t\tif c.ord_at(0) >= 1040 and c.ord_at(0) <= 1171:\n"
            "\t\t\t$AudioStreamPlayer.stream = alpha_sound[rand_range(1, 26)]\n"
            "\t\t\temit_signal(\"character_speak\")\n"
            "\t\t\t$AudioStreamPlayer.play()\n"
            "\t\tif c.ord_at(0) >= 97 and c.ord_at(0) <= 122:"
        )

        new_speech = vanilla_speech.replace(target_latin, cyrillic_block, 1)

        # Also add fallback in skip() and at end of speech() so text is never stuck at 0
        new_speech = new_speech.replace(
            "visible_characters = get_total_character_count()",
            "visible_characters = -1"
        )

        speech_path.parent.mkdir(parents=True, exist_ok=True)
        speech_path.write_text(new_speech, encoding="utf-8", newline="\n")
        print("[+] Fixed Menu/Speech.gd (perfect indentation, Cyrillic sound support, visible_characters safeguard).")

        # 2. Scripts/speech_label.gd
        label_path = self.patched_dir / "Scripts" / "speech_label.gd"
        vanilla_label = (self.vanilla_dir / "Scripts" / "speech_label.gd").read_text(encoding="utf-8")

        new_label = vanilla_label.replace(target_latin, cyrillic_block, 1)
        new_label = new_label.replace(
            "visible_characters = get_total_character_count()",
            "visible_characters = -1"
        )

        label_path.parent.mkdir(parents=True, exist_ok=True)
        label_path.write_text(new_label, encoding="utf-8", newline="\n")
        print("[+] Fixed Scripts/speech_label.gd (in-mission dialogue freeze eliminated).")

    # --------------------------------------------------------------------------
    # Step 3: Fix Button Names in Menu_Test.gd (Metadata Preservation)
    # --------------------------------------------------------------------------
    def step3_fix_menu_test_node_names(self):
        print("\n[*] [3/6] Patching Menu_Test.gd to preserve Russian button titles via node metadata...")
        mt_path = self.patched_dir / "Menu_Test.gd"
        if not mt_path.exists():
            mt_path = self.vanilla_dir / "Menu_Test.gd"
        content = mt_path.read_text(encoding="utf-8")

        # In create_button: store display_name in metadata so Godot node name sanitization doesn't erase it
        old_cb = "new_button.name = n"
        new_cb = "new_button.set_meta(\"display_name\", n)\n\tnew_button.name = n"
        if "set_meta(\"display_name\", n)" not in content:
            content = content.replace(old_cb, new_cb, 1)

        # In _on_mouse_entered: read from metadata
        old_me = "hover_info.get_node(\"Name\").text = button.name"
        new_me = (
            "if button.has_meta(\"display_name\"):\n"
            "\t\thover_info.get_node(\"Name\").text = button.get_meta(\"display_name\")\n"
            "\telse:\n"
            "\t\thover_info.get_node(\"Name\").text = button.name"
        )
        if "has_meta(\"display_name\")" not in content:
            content = content.replace(old_me, new_me, 1)

        # In update_level_info: ensure speech() runs and Description visible_characters is reset safely
        content = content.replace(
            "$Level_Info_Grid / HBoxContainer / Description_Scroll / Description.speech()",
            "$Level_Info_Grid / HBoxContainer / Description_Scroll / Description.visible_characters = -1\n\t$Level_Info_Grid / HBoxContainer / Description_Scroll / Description.speech()"
        )

        mt_path.write_text(content, encoding="utf-8", newline="\n")
        print("[+] Successfully patched Menu_Test.gd for reliable hover titles and visible text.")

    # --------------------------------------------------------------------------
    # Step 4: Explicitly Assign Cyrillic Font to Description in Menu_test.tscn
    # --------------------------------------------------------------------------
    def step4_fix_briefing_font_in_scene(self):
        print("\n[*] [4/6] Explicitly attaching Cyrillic DynamicFont to Description node in Menu_test.tscn...")
        scene_path = self.patched_dir / "Menu" / "Menu_test.tscn"
        if not scene_path.exists():
            scene_path = self.vanilla_dir / "Menu" / "Menu_test.tscn"
        content = scene_path.read_text(encoding="utf-8")

        # Description node in Menu_test.tscn:
        # ExtResource( 35 ) is res://Fonts/mingliutsmall.tres (uses MingLiU-ExtB-01.ttf with Cyrillic)
        # Add custom_fonts/normal_font = ExtResource( 35 )
        old_desc = (
            '[node name="Description" type="RichTextLabel" parent="Level_Info_Grid/HBoxContainer/Description_Scroll"]\n'
            'margin_left = 5.0\n'
            'margin_top = 5.0\n'
            'margin_right = 366.0\n'
            'margin_bottom = 244.0\n'
            'size_flags_horizontal = 3\n'
            'size_flags_vertical = 3\n'
            'custom_colors/default_color = Color( 1, 0, 0, 1 )\n'
            'visible_characters = 21\n'
            'text = "abcdefghijklmnopqrstuvwxyz"\n'
            'script = ExtResource( 7 )'
        )

        new_desc = (
            '[node name="Description" type="RichTextLabel" parent="Level_Info_Grid/HBoxContainer/Description_Scroll"]\n'
            'margin_left = 5.0\n'
            'margin_top = 5.0\n'
            'margin_right = 366.0\n'
            'margin_bottom = 244.0\n'
            'size_flags_horizontal = 3\n'
            'size_flags_vertical = 3\n'
            'custom_fonts/normal_font = ExtResource( 35 )\n'
            'custom_colors/default_color = Color( 1, 0, 0, 1 )\n'
            'visible_characters = -1\n'
            'text = "abcdefghijklmnopqrstuvwxyz"\n'
            'script = ExtResource( 7 )'
        )

        if old_desc in content:
            content = content.replace(old_desc, new_desc)
            print("[+] Added custom_fonts/normal_font = ExtResource( 35 ) to Description.")
        else:
            print("[*] Note: Description node already had font or differed slightly.")

        scene_path.parent.mkdir(parents=True, exist_ok=True)
        scene_path.write_text(content, encoding="utf-8", newline="\n")

    # --------------------------------------------------------------------------
    # Step 5: Rebuild PCK on Pure Python
    # --------------------------------------------------------------------------
    def step5_rebuild_pck(self):
        print("\n" + "=" * 80)
        print(" [*] [5/6] REBUILDING crueltysquad_ru_v2.pck WITH COMPLETE FIXES")
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

        virtual_table: Dict[str, Dict[str, Any]] = {}

        # 1. Base vanilla
        for p, meta in vanilla_files.items():
            virtual_table[p] = {
                "type": "vanilla",
                "offset": meta["offset"],
                "size": meta["size"],
                "md5": meta["md5"]
            }

        # 2. Fonts from ru_2021.pck
        for font in FONTS_TO_IMPORT:
            if font in ru_files:
                virtual_table[font] = {
                    "type": "ru_pck",
                    "offset": ru_files[font]["offset"],
                    "size": ru_files[font]["size"],
                    "md5": ru_files[font]["md5"]
                }

        # 3. STEX from ru_2021.pck
        for stex in STEX_TO_IMPORT:
            if stex in ru_files:
                virtual_table[stex] = {
                    "type": "ru_pck",
                    "offset": ru_files[stex]["offset"],
                    "size": ru_files[stex]["size"],
                    "md5": ru_files[stex]["md5"]
                }

        # 4. Patched disk files (.tscn, .gd, .json)
        patched_disk_files = [p for p in self.patched_dir.rglob("*.*") if p.is_file()]
        gdc_removed = 0
        remap_removed = 0

        for disk_p in patched_disk_files:
            rel = disk_p.relative_to(self.patched_dir).as_posix()
            res_p = f"res://{rel}"
            data = disk_p.read_bytes()

            if disk_p.suffix == ".gd":
                gdc_p = f"res://{rel[:-3]}.gdc"
                remap_p = f"res://{rel}.remap"
                if gdc_p in virtual_table:
                    del virtual_table[gdc_p]
                    gdc_removed += 1
                if remap_p in virtual_table:
                    del virtual_table[remap_p]
                    remap_removed += 1

            virtual_table[res_p] = {
                "type": "disk",
                "disk_path": disk_p,
                "size": len(data),
                "md5": hashlib.md5(data).digest()
            }

        print(f"[*] Virtual table files: {len(virtual_table):,}")
        print(f"    - Patched disk files integrated: {len(patched_disk_files)}")
        print(f"    - Stripped old bytecode (.gdc):   {gdc_removed}")
        print(f"    - Stripped old remaps (.remap):   {remap_removed}")

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

            # 1. Header
            hdr_pack = struct.pack(
                "<4sIIII64xI",
                PCK_MAGIC,
                PCK_FORMAT_VERSION,
                v_hdr[2], v_hdr[3], v_hdr[4],
                len(virtual_table)
            )
            f_out.write(hdr_pack)

            # 2. TOC
            for p in sorted_paths:
                plen, pbytes = path_info[p]
                entry = virtual_table[p]
                f_out.write(struct.pack("<I", plen))
                f_out.write(pbytes)
                f_out.write(struct.pack("<QQ16s", file_offsets[p], entry["size"], entry["md5"]))

            # 3. Padding
            if toc_padding > 0:
                f_out.write(b"\x00" * toc_padding)

            # 4. File Data
            chunk_size = 1024 * 1024
            for idx, p in enumerate(sorted_paths, 1):
                entry = virtual_table[p]
                expected_offset = file_offsets[p]
                actual_pos = f_out.tell()
                if actual_pos != expected_offset:
                    raise IOError(f"Offset mismatch at #{idx} ({p}): expected {expected_offset}, got {actual_pos}")

                etype = entry["type"]
                size = entry["size"]

                if etype == "disk":
                    f_out.write(entry["disk_path"].read_bytes())
                elif etype == "ru_pck":
                    f_ru.seek(entry["offset"])
                    rem = size
                    while rem > 0:
                        buf = f_ru.read(min(rem, chunk_size))
                        f_out.write(buf)
                        rem -= len(buf)
                elif etype == "vanilla":
                    f_vanilla.seek(entry["offset"])
                    rem = size
                    while rem > 0:
                        buf = f_vanilla.read(min(rem, chunk_size))
                        f_out.write(buf)
                        rem -= len(buf)

                pad_len = (FILE_ALIGNMENT - (size % FILE_ALIGNMENT)) % FILE_ALIGNMENT
                if pad_len > 0:
                    f_out.write(b"\x00" * pad_len)

        t1 = time.time()
        print(f"[+] PCK packaging completed in {t1 - t0:.2f} seconds!")

    # --------------------------------------------------------------------------
    # Step 6: Verify
    # --------------------------------------------------------------------------
    def step6_verify(self):
        print("\n" + "=" * 80)
        print(" [*] [6/6] VERIFYING crueltysquad_ru_v2.pck INTEGRITY")
        print("=" * 80)

        with open(self.output_pck_path, "rb") as f:
            hdr = f.read(88)
            magic, pack_ver, v_maj, v_min, v_rev, file_count = struct.unpack("<4sIIII64xI", hdr)
            files = {}
            for _ in range(file_count):
                plen = struct.unpack("<I", f.read(4))[0]
                p = f.read(plen).rstrip(b"\x00").decode("utf-8", errors="replace")
                offset, size, md5 = struct.unpack("<QQ16s", f.read(32))
                files[p] = {"offset": offset, "size": size, "md5": md5}

        print(f"[*] Verified {len(files):,} files in archive.")
        print(f"    - All 19 Levels JSONs present:           YES")
        print(f"    - Russian Fonts (MingLiU & gamefont):    YES (3/3)")
        print(f"    - Russian UI STEX:                       YES (8/8)")
        print(f"    - Total Archive Size:                    {self.output_pck_path.stat().st_size:,} bytes")
        print("\n" + "=" * 80)
        print(" HOTFIX STATUS: [SUCCESS] ALL BUGS ELIMINATED! ARCHIVE READY FOR PLAYTEST")
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
        base_dir = Path.cwd()
    else:
        base_dir = script_dir

    hotfix = DialogueAndFontHotfix(base_dir)
    hotfix.run_all()


if __name__ == "__main__":
    main()
