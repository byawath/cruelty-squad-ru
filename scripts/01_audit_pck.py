#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
01_audit_pck.py
--------------------------------------------------------------------------------
Lead Localization Engineering & Reverse-Engineering Tool for Cruelty Squad (Godot 3.x)
Task 1: .pck index parser, binary audit, and decompiled tree inspection.
--------------------------------------------------------------------------------
"""

import os
import sys
import struct
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

# Constants for Godot 3.x PCK Format v1
PCK_MAGIC = b"GDPC"
PCK_HEADER_FMT = "<4sIIII64xI"
PCK_HEADER_SIZE = 88  # 4 (magic) + 4 (pack_ver) + 12 (ver_major, minor, rev) + 64 (reserved) + 4 (file_count)
STEX_MAGIC = b"GDST"


class PckAudit:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.pck_dir = base_dir / "_source_pcks"
        self.vanilla_pck_path = self.pck_dir / "vanilla_steam.pck"
        self.ru_pck_path = self.pck_dir / "ru_2021.pck"
        self.vanilla_new_dir = base_dir / "vanilla_new"
        self.ru_old_dir = base_dir / "ru_old"
        self.report_path = base_dir / "audit_report.json"

    def read_pck_toc(self, pck_path: Path) -> Dict[str, Any]:
        """
        Parses Godot 3.x .pck header and Table of Contents (TOC).
        """
        if not pck_path.exists():
            raise FileNotFoundError(f"PCK file not found: {pck_path}")

        files: Dict[str, Dict[str, Any]] = {}
        alignment_issues = []
        non_res_paths = []

        with open(pck_path, "rb") as f:
            header_bytes = f.read(PCK_HEADER_SIZE)
            if len(header_bytes) < PCK_HEADER_SIZE:
                raise ValueError(f"File {pck_path} is too small to contain a valid PCK header.")

            magic, pack_ver, ver_major, ver_minor, ver_rev, file_count = struct.unpack(
                PCK_HEADER_FMT, header_bytes
            )

            if magic != PCK_MAGIC:
                raise ValueError(f"Invalid magic: expected {PCK_MAGIC}, got {magic}")

            header_info = {
                "magic": magic.decode("ascii", errors="replace"),
                "pack_version": pack_ver,
                "engine_version": f"{ver_major}.{ver_minor}.{ver_rev}",
                "ver_major": ver_major,
                "ver_minor": ver_minor,
                "ver_rev": ver_rev,
                "file_count": file_count,
            }

            for idx in range(file_count):
                len_bytes = f.read(4)
                if len(len_bytes) < 4:
                    raise EOFError(f"Unexpected EOF reading path_len for file entry #{idx}")
                (path_len,) = struct.unpack("<I", len_bytes)

                raw_path_bytes = f.read(path_len)
                if len(raw_path_bytes) < path_len:
                    raise EOFError(f"Unexpected EOF reading path string for file entry #{idx}")

                meta_bytes = f.read(32)  # 8 (offset) + 8 (size) + 16 (md5)
                if len(meta_bytes) < 32:
                    raise EOFError(f"Unexpected EOF reading metadata for file entry #{idx}")

                offset, size, md5_raw = struct.unpack("<QQ16s", meta_bytes)
                md5_hex = md5_raw.hex()

                # Alignment validation (Godot 3.x aligns path length to 4-byte boundary)
                if path_len % 4 != 0:
                    alignment_issues.append((idx, path_len))

                # Clean null-padded string
                clean_path = raw_path_bytes.rstrip(b"\x00").decode("utf-8", errors="replace")
                raw_len = len(clean_path.encode("utf-8"))
                expected_padded_len = (raw_len + 3) & ~3 if (raw_len % 4 != 0) else raw_len

                if not clean_path.startswith("res://"):
                    non_res_paths.append((idx, clean_path))

                files[clean_path] = {
                    "path_len": path_len,
                    "raw_len": raw_len,
                    "expected_padded_len": expected_padded_len,
                    "offset": offset,
                    "size": size,
                    "md5": md5_hex,
                }

        return {
            "pck_path": str(pck_path),
            "header": header_info,
            "alignment_valid": len(alignment_issues) == 0,
            "alignment_issues_count": len(alignment_issues),
            "all_paths_res": len(non_res_paths) == 0,
            "non_res_paths": non_res_paths,
            "files": files,
        }

    def parse_stex_header(self, pck_path: Path, offset: int) -> Optional[Dict[str, Any]]:
        """
        Reads and parses the first 16 bytes of a StreamTexture (.stex) file.
        Header layout (Little-Endian):
        - 0..4: magic b'GDST'
        - 4..8: width (uint32)
        - 8..12: height (uint32)
        - 12..16: flags (uint32)
        """
        with open(pck_path, "rb") as f:
            f.seek(offset)
            hdr = f.read(16)
            if len(hdr) < 16:
                return None
            magic, width, height, flags = struct.unpack("<4sIII", hdr)
            return {
                "magic": magic.decode("ascii", errors="replace"),
                "is_gdst": magic == STEX_MAGIC,
                "width": width,
                "height": height,
                "flags": flags,
                "raw_header_hex": hdr.hex(),
            }

    def compare_pcks(
        self, vanilla_toc: Dict[str, Any], ru_toc: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compares TOCs of vanilla and ru_2021 PCK archives.
        """
        v_files = vanilla_toc["files"]
        r_files = ru_toc["files"]

        common_paths = sorted(set(v_files.keys()) & set(r_files.keys()))
        only_in_vanilla = sorted(set(v_files.keys()) - set(r_files.keys()))
        only_in_ru = sorted(set(r_files.keys()) - set(v_files.keys()))

        identical_files = []
        modified_files = []

        diff_fonts = []
        diff_stex = []
        diff_other = []

        stex_audits = []

        for path in common_paths:
            v_meta = v_files[path]
            r_meta = r_files[path]

            if v_meta["md5"] == r_meta["md5"]:
                identical_files.append(path)
            else:
                modified_files.append(path)
                lower_p = path.lower()

                if lower_p.endswith((".ttf", ".font", ".otf", ".fnt")):
                    diff_fonts.append(
                        {
                            "path": path,
                            "vanilla_size": v_meta["size"],
                            "ru_size": r_meta["size"],
                            "vanilla_md5": v_meta["md5"],
                            "ru_md5": r_meta["md5"],
                        }
                    )
                elif lower_p.endswith(".stex"):
                    v_stex = self.parse_stex_header(
                        Path(vanilla_toc["pck_path"]), v_meta["offset"]
                    )
                    r_stex = self.parse_stex_header(
                        Path(ru_toc["pck_path"]), r_meta["offset"]
                    )

                    dim_match = False
                    if v_stex and r_stex:
                        dim_match = (
                            v_stex["width"] == r_stex["width"]
                            and v_stex["height"] == r_stex["height"]
                        )

                    stex_info = {
                        "path": path,
                        "vanilla_size": v_meta["size"],
                        "ru_size": r_meta["size"],
                        "vanilla_md5": v_meta["md5"],
                        "ru_md5": r_meta["md5"],
                        "vanilla_header": v_stex,
                        "ru_header": r_stex,
                        "dimensions_match": dim_match,
                    }
                    diff_stex.append(path)
                    stex_audits.append(stex_info)
                else:
                    diff_other.append(path)

        return {
            "total_vanilla": len(v_files),
            "total_ru": len(r_files),
            "common_count": len(common_paths),
            "identical_count": len(identical_files),
            "modified_count": len(modified_files),
            "only_in_vanilla_count": len(only_in_vanilla),
            "only_in_vanilla": only_in_vanilla,
            "only_in_ru_count": len(only_in_ru),
            "only_in_ru": only_in_ru,
            "diff_fonts": diff_fonts,
            "diff_stex_count": len(diff_stex),
            "diff_stex_audits": stex_audits,
            "diff_other_sample": diff_other[:25],
            "diff_other_total": len(diff_other),
        }

    def scan_decompiled_dir(self, target_dir: Path) -> Dict[str, Any]:
        """
        Scans decompiled directory for .gd and .tscn files.
        """
        gd_files = {}
        tscn_files = {}

        if not target_dir.exists():
            return {"error": f"Directory not found: {target_dir}", "gd": {}, "tscn": {}}

        for root, _, filenames in os.walk(target_dir):
            for fname in filenames:
                ext = os.path.splitext(fname)[1].lower()
                if ext in (".gd", ".tscn"):
                    full_p = Path(root) / fname
                    rel_p = full_p.relative_to(target_dir).as_posix()
                    with open(full_p, "rb") as fp:
                        content = fp.read()
                        info = {
                            "size": len(content),
                            "md5": hashlib.md5(content).hexdigest(),
                        }
                    if ext == ".gd":
                        gd_files[rel_p] = info
                    else:
                        tscn_files[rel_p] = info

        return {
            "dir_path": str(target_dir),
            "gd_count": len(gd_files),
            "tscn_count": len(tscn_files),
            "total_count": len(gd_files) + len(tscn_files),
            "gd": gd_files,
            "tscn": tscn_files,
        }

    def compare_decompiled_trees(
        self, v_tree: Dict[str, Any], r_tree: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compares decompiled .gd and .tscn trees.
        """
        result = {}
        for kind in ("gd", "tscn"):
            v_dict = v_tree.get(kind, {})
            r_dict = r_tree.get(kind, {})

            all_keys = set(v_dict.keys()) | set(r_dict.keys())
            common_keys = sorted(set(v_dict.keys()) & set(r_dict.keys()))
            only_vanilla = sorted(set(v_dict.keys()) - set(r_dict.keys()))
            only_ru = sorted(set(r_dict.keys()) - set(v_dict.keys()))

            identical = []
            modified = []

            for k in common_keys:
                if v_dict[k]["md5"] == r_dict[k]["md5"]:
                    identical.append(k)
                else:
                    modified.append(
                        {
                            "file": k,
                            "vanilla_size": v_dict[k]["size"],
                            "ru_size": r_dict[k]["size"],
                            "vanilla_md5": v_dict[k]["md5"],
                            "ru_md5": r_dict[k]["md5"],
                        }
                    )

            result[kind] = {
                "vanilla_total": len(v_dict),
                "ru_total": len(r_dict),
                "identical_count": len(identical),
                "modified_count": len(modified),
                "modified": modified,
                "only_vanilla": only_vanilla,
                "only_ru": only_ru,
            }

        return result

    def run_full_audit(self) -> Dict[str, Any]:
        """
        Executes full audit pipeline and outputs report.
        """
        print("=" * 80)
        print(" CRUELTY SQUAD - GODOT 3.x PCK & DECOMPILED SOURCE AUDIT (TASK 1)")
        print("=" * 80)

        # 1. Parse PCK Headers and TOCs
        print(f"\n[*] Parsing Vanilla PCK: {self.vanilla_pck_path.name}...")
        v_toc = self.read_pck_toc(self.vanilla_pck_path)
        print(
            f"    -> Magic: {v_toc['header']['magic']} | Format: v{v_toc['header']['pack_version']} | "
            f"Engine: Godot {v_toc['header']['engine_version']} | Files: {v_toc['header']['file_count']:,}"
        )

        print(f"\n[*] Parsing RU 2021 PCK: {self.ru_pck_path.name}...")
        r_toc = self.read_pck_toc(self.ru_pck_path)
        print(
            f"    -> Magic: {r_toc['header']['magic']} | Format: v{r_toc['header']['pack_version']} | "
            f"Engine: Godot {r_toc['header']['engine_version']} | Files: {r_toc['header']['file_count']:,}"
        )

        # 2. Check path format & alignment
        v_align_ok = v_toc["alignment_valid"] and v_toc["all_paths_res"]
        r_align_ok = r_toc["alignment_valid"] and r_toc["all_paths_res"]
        print(f"\n[*] Validating TOC structure and alignment:")
        print(
            f"    [Vanilla] All paths start with 'res://': {v_toc['all_paths_res']} | "
            f"4-byte alignment valid: {v_toc['alignment_valid']}"
        )
        print(
            f"    [RU 2021] All paths start with 'res://': {r_toc['all_paths_res']} | "
            f"4-byte alignment valid: {r_toc['alignment_valid']}"
        )

        # 3. Compare PCKs
        print("\n[*] Comparing binary entries between archives...")
        pck_cmp = self.compare_pcks(v_toc, r_toc)
        print(f"    - Identical binary files: {pck_cmp['identical_count']:,}")
        print(f"    - Modified binary files:  {pck_cmp['modified_count']:,}")
        print(f"    - Unique to Vanilla:      {pck_cmp['only_in_vanilla_count']:,}")
        print(f"    - Unique to RU 2021:      {pck_cmp['only_in_ru_count']:,}")

        # Font audit
        print(f"\n[*] Modified Fonts ({len(pck_cmp['diff_fonts'])} found):")
        for f_info in pck_cmp["diff_fonts"]:
            print(
                f"    - {f_info['path']} (vanilla: {f_info['vanilla_size']} bytes -> ru: {f_info['ru_size']} bytes)"
            )

        # Stex audit
        print(
            f"\n[*] Modified Compiled Textures (.stex) ({pck_cmp['diff_stex_count']} found):"
        )
        all_stex_dims_match = True
        for st in pck_cmp["diff_stex_audits"]:
            vh = st["vanilla_header"]
            rh = st["ru_header"]
            dim_status = "[OK] MATCH" if st["dimensions_match"] else "[MISMATCH]"
            if not st["dimensions_match"]:
                all_stex_dims_match = False
            v_res = f"{vh['width']}x{vh['height']}" if vh else "N/A"
            r_res = f"{rh['width']}x{rh['height']}" if rh else "N/A"
            print(
                f"    - {st['path']}\n"
                f"        Vanilla: {v_res} (flags={vh['flags']}, {st['vanilla_size']:,} bytes)\n"
                f"        RU 2021: {r_res} (flags={rh['flags']}, {st['ru_size']:,} bytes) => {dim_status}"
            )
        print(f"    -> All modified .stex textures preserve resolution: {all_stex_dims_match}")

        # 4. Scan decompiled directories
        print(f"\n[*] Scanning decompiled source trees:")
        v_decomp = self.scan_decompiled_dir(self.vanilla_new_dir)
        r_decomp = self.scan_decompiled_dir(self.ru_old_dir)
        print(
            f"    [vanilla_new] .gd: {v_decomp['gd_count']} | .tscn: {v_decomp['tscn_count']} (total: {v_decomp['total_count']})"
        )
        print(
            f"    [ru_old]      .gd: {r_decomp['gd_count']} | .tscn: {r_decomp['tscn_count']} (total: {r_decomp['total_count']})"
        )

        decomp_cmp = self.compare_decompiled_trees(v_decomp, r_decomp)
        print(f"\n[*] Decompiled Scripts (.gd) Diff:")
        print(f"    - Identical: {decomp_cmp['gd']['identical_count']}")
        print(f"    - Modified:  {decomp_cmp['gd']['modified_count']}")
        print(f"    - Only in vanilla: {decomp_cmp['gd']['only_vanilla']}")
        print(f"    - Only in ru_old:  {decomp_cmp['gd']['only_ru']}")

        print(f"\n[*] Decompiled Scenes (.tscn) Diff:")
        print(f"    - Identical: {decomp_cmp['tscn']['identical_count']}")
        print(f"    - Modified:  {decomp_cmp['tscn']['modified_count']}")
        print(f"    - Only in vanilla: {decomp_cmp['tscn']['only_vanilla']}")
        print(f"    - Only in ru_old:  {decomp_cmp['tscn']['only_ru']}")

        # 5. Build and save full report
        full_report = {
            "meta": {
                "task": "TASK 1: PCK index parser and localization audit",
                "engine": "Godot 3.x",
                "pck_format_version": 1,
            },
            "pck_vanilla": {
                "header": v_toc["header"],
                "alignment_valid": v_toc["alignment_valid"],
                "all_paths_res": v_toc["all_paths_res"],
                "file_count": len(v_toc["files"]),
            },
            "pck_ru_2021": {
                "header": r_toc["header"],
                "alignment_valid": r_toc["alignment_valid"],
                "all_paths_res": r_toc["all_paths_res"],
                "file_count": len(r_toc["files"]),
            },
            "pck_diff": pck_cmp,
            "decompiled_trees": {
                "vanilla_new_counts": {
                    "gd": v_decomp["gd_count"],
                    "tscn": v_decomp["tscn_count"],
                },
                "ru_old_counts": {
                    "gd": r_decomp["gd_count"],
                    "tscn": r_decomp["tscn_count"],
                },
                "diff": decomp_cmp,
            },
        }

        with open(self.report_path, "w", encoding="utf-8") as f:
            json.dump(full_report, f, indent=2, ensure_ascii=False)

        print(f"\n[+] Full audit report saved to: {self.report_path.resolve()}")
        print("=" * 80)
        return full_report


def main():
    # Detect workspace root
    script_dir = Path(__file__).resolve().parent
    if (script_dir / "_source_pcks").exists():
        base_dir = script_dir
    elif (script_dir / "cs_loc" / "_source_pcks").exists():
        base_dir = script_dir / "cs_loc"
    elif (Path.cwd() / "_source_pcks").exists():
        base_dir = Path.cwd()
    elif (Path.cwd() / "cs_loc" / "_source_pcks").exists():
        base_dir = Path.cwd() / "cs_loc"
    else:
        base_dir = script_dir

    auditor = PckAudit(base_dir)
    auditor.run_full_audit()


if __name__ == "__main__":
    main()
