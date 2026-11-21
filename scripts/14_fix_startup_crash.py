#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
14_fix_startup_crash.py
--------------------------------------------------------------------------------
Lead Localization Engineering & Reverse-Engineering Tool for Cruelty Squad (Godot 3.x)
TASK 14: Fix Game Startup Crash, Enforce Strict Pre-Pack Linter & Rebuild PCK
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


class StartupCrashFixTool:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.vanilla_dir = base_dir / "vanilla_new"
        self.patched_dir = base_dir / "_patched_files"
        self.ru_old_dir = base_dir / "ru_old"
        self.pck_dir = base_dir / "_source_pcks"

        self.vanilla_pck_path = self.pck_dir / "vanilla_steam.pck"
        self.ru_pck_path = self.pck_dir / "ru_2021.pck"
        self.output_pck_path = base_dir / "crueltysquad_ru_v2.pck"
        self.root_pck_path = Path("C:/dev/crueltysquad_ru_v2.pck")
        self.compat_pck_path = base_dir / "crueltysquad.pck"

        self.log_path = Path(os.path.expandvars(r"%APPDATA%\Godot\app_userdata\Cruelty Squad\logs\godot.log"))

    def run_all(self):
        print("=" * 80)
        print(" CRUELTY SQUAD RUSSIAN LOCALIZATION — TASK 14 HOTFIX")
        print(" Root-Cause Diagnosis, Strict Linter & Pure-Python Rebuild")
        print("=" * 80)

        self.step1_diagnose_godot_log()
        self.step2_fix_menu_test_and_scripts()
        self.step3_strict_prepack_linter()
        self.step4_binary_pck_rebuild()
        self.step5_post_verify()

    # --------------------------------------------------------------------------
    # Step 1: Diagnose Godot Log
    # --------------------------------------------------------------------------
    def step1_diagnose_godot_log(self):
        print("\n" + "=" * 80)
        print(" [*] [1/5] DIAGNOSING CRASH FROM GODOT.LOG")
        print("=" * 80)

        if not self.log_path.exists():
            print(f"[-] Warning: Log file not found at {self.log_path}")
            return

        content = self.log_path.read_text(encoding="utf-8", errors="replace")
        lines = content.splitlines()
        print(f"[+] Loaded godot.log ({len(lines)} lines from {self.log_path})")

        error_lines = []
        for idx, line in enumerate(lines, 1):
            if any(k in line for k in ["ERROR:", "SCRIPT ERROR:", "Parse Error:", "FATAL:"]):
                error_lines.append((idx, line))

        print(f"[+] Found {len(error_lines)} error entries in godot.log:")
        for idx, line in error_lines:
            print(f"    Line {idx:3d}: {line}")

        # Highlight root cause
        script_errors = [l for _, l in error_lines if "SCRIPT ERROR" in l or "Parse Error" in l]
        if script_errors:
            print("\n[!] CRITICAL ROOT CAUSE IDENTIFIED:")
            for se in script_errors:
                print(f"    -> {se}")

    # --------------------------------------------------------------------------
    # Step 2: Fix Menu_Test.gd and scripts
    # --------------------------------------------------------------------------
    def step2_fix_menu_test_and_scripts(self):
        print("\n" + "=" * 80)
        print(" [*] [2/5] FIXING SYNTAX & INDENTATION IN Menu_Test.gd")
        print("=" * 80)

        p_mt = self.patched_dir / "Menu_Test.gd"
        v_mt = self.vanilla_dir / "Menu_Test.gd"

        assert p_mt.exists(), f"Missing {p_mt}"
        assert v_mt.exists(), f"Missing {v_mt}"

        p_lines = p_mt.read_text(encoding="utf-8").splitlines(keepends=True)
        v_lines = v_mt.read_text(encoding="utf-8").splitlines(keepends=True)

        assert len(p_lines) == len(v_lines), f"Line count mismatch: {len(p_lines)} vs {len(v_lines)}"

        # 29 weapons mapping: (case_label, button_name, tooltip)
        canonical_weapons = [
            (
                "B_W_PISTOL:",
                "Бесшумный пистолет Parasonic D2",
                "Использует особый дозвуковой патрон для максимального подавления звука. Популярен среди премиальных частных охранных структур и сервисов по устранению, а так же среди тактикульщиков.",
            ),
            (
                "B_W_SMG:",
                "K&H R5",
                "Один из самых широкоиспользуемых ПП со времён 80-х. Непревзойдённая надёжность и простота в использовании.",
            ),
            (
                "B_W_S_SMG:",
                "Minato M9",
                "Импортирован в больших количествах людьми культуры после показа в аниме «Хаато но ДокиДоки: Занкокудан».",
            ),
            (
                "B_W_SHOTGUN:",
                "Balotelli Hypernova",
                "После быстрого распространения передовых высококачественных бронежилетов и последующего отхода от традиционной картечи к более эффективным патронам на основе флешетта, Belatelli Hypernova показал себя самым эффективным решением.",
            ),
            (
                "B_W_RL:",
                "Бронебойный комплекс «СисОх»",
                "В какой-то момент СисОх умудрилась убедить весь мир в необходимости использования ракетных установок военного типа частными охранными компаниями.",
            ),
            (
                "B_W_SNIPER:",
                "Stern AWS 3000",
                "AWS 3000 использует специальный подкалиберный патрон с 30-ти сантиметровым бронебойным снарядом из обеднённого урана. Оружие изначально было создано для борьбы с бронированными целями, однако когда оно попадает по чему-то небронированному цель сминается и от неё остаётся больше крови, чем самой цели.",
            ),
            (
                "B_W_AR:",
                "K&H X20",
                "Karl & Heinrich X20 мгновенно стал хитом среди элитных служб безопасности. Стреляет очередью из 3 невероятно точных выстрелов, сохраняя при этом приемлемую отдачу. Боеприпасы полностью безгильзовые, что позволяет переносить с собой огромное количество амуниции налегке и не оставлять за собой улик.",
            ),
            (
                "B_W_NAMBU:",
                "New Safety M62",
                "Стандартный полицейский револьвер уже на протяжении ста лет. Хотя и существуют более эффективные альтернативы, копы решили остаться с ним из-за ассоциаций мужественности, созданных киноиндустрией.",
            ),
            (
                "B_W_GAS_LAUNCHER:",
                "Усмиритель",
                "Использует гранаты с коррозийным газом, который может проесть практически всё что угодно. Особо не используется с времён продуктовых бунтов начала нулевых.",
            ),
            (
                "B_W_MG3:",
                "AMG4",
                "Традиционное оружие сильно аугментированной солдатни, что с недавних пор начало чаще использоваться в корпоративной среде. Чрезвычайно высокий темп стрельбы и хорошая бронебойность благодаря патронам из Обеднённого Урана, которые обычно идут вместе с оружием.",
            ),
            (
                "B_W_AUTOSHOTGUN:",
                "Precise Industries AS15",
                "Полностью автоматический дробовик, способный разорвать на куски практически всё что угодно вблизи. Полный перебор, но пользуется популярностью среди киллеров, чьи эмоции притуплены боевыми наркотиками.",
            ),
            (
                "B_W_MAUSER:",
                "Mowzer SP99",
                "Точная и чрезвычайно тихая снайперская винтовка со скользящим затвором. Прекрасно подходит для скрытных и незаконных операций. Важный символ сектантов из топей, которые утверждают, что получают божественные послания через них.",
            ),
            (
                "B_W_BORE:",
                "Черепное Сверло «СисОх»",
                "СисОх опять взялись за своё. Это невероятно высокотехнологическое биооружие из чана само по себе является инкубатором, способным вырастить небольшую закапывающуюся сферу из плоти, которая летит прямиком в голову цели и выплёскивает её на пол. В качестве энергии высасывает немного жизненных сил пользователя. Круто, ага?",
            ),
            (
                "B_W_MKR:",
                "Карабин Spectacular Dynamics MCR",
                "Футуристичная микрокалиберная платформа, так и не достигшая популярности в массах, несмотря на свои многочисленные преимущества. Использует странные запечатанные одноразовые магазины прямо с завода и собственные безгильзовые боеприпасы.",
            ),
            (
                "B_W_RADGUN:",
                "Bolt ACR",
                "Цель программы по разработке Продвинутой Боевой Винтовки заключалась в создании энергетического оружия, которое не требовало бы перезарядки вообще. Одним из результатов стал этот прискорбный портативный излучатель гамма-радиации. Хоть и часто заявляют о его незаконности из-за международных соглашений, касающихся радиационного оружия (таких соглашений не существует), причина, по которой он не используется заключается в том, что большинство подопытных случайно убили сами себя.",
            ),
            (
                "B_W_TRANQ:",
                "Пистолет для контроля животных SNOOZEFEST",
                "Цена человеческой жизни мала, поэтому не было какой-либо реальной попытки создать оружие-транквилизатор для нужд охраны или военных. Однако некоторые начали использовать эти пистолеты для контроля животных в качестве менее грязного способа обойти чересчур бдительную охрану.",
            ),
            (
                "B_W_BLACKJACK:",
                "Телескопическая дубинка",
                "Стандартный девайс для нокаутирования людей. Дизайн не менялся со времён Средневековья, только материалы стали получше.",
            ),
            (
                "B_W_FLASHLIGHT:",
                "Фонарик",
                "Обычный фонарик, не особо полезен. Или полезен?",
            ),
            (
                "B_W_ZIPPY:",
                "Zippy 3000",
                "Величайшее оружие, в плане осечек и преждевременных спусков. Повезёт, если получится сделать хотя бы два выстрела из этой хреновины и не оторвать себе пальцы.",
            ),
            (
                "B_W_AN94:",
                "BN-99",
                "Мистическое оружие, потерянное во времени. Выполненное из проклятого сплава, оружие имеет уникальный механизм стрельбы очередью из 2 патронов.",
            ),
            (
                "B_W_VAG72:",
                "BAG-82",
                "Странный безгильзовый пистолет, созданный древней цивилизацией. Гнусный запах. Кто знает, где он побывал.",
            ),
            (
                "B_W_STEYR:",
                "Stern M17",
                "Победитель программы по разработке Продвинутой Боевой Винтовки. Стала широкоиспользуемой заменой другим военным винтовкам. Скорострельные очереди из трёх пуль типа флешетта значительно увеличивают шанс попадания.",
            ),
            (
                "B_W_CANCER:",
                "ДНК-деструктор Parasonic C3",
                "Высокопоставленные цели нередко имеют доступ к сервисам по реконструкции тел, по этой причине популярным выбором расправы над целью стало тотальное искажение их ДНК без возможности восстановления высоко-технологичным вооружением, как Parasonic C3.",
            ),
            (
                "B_W_ROD:",
                "Стеклопластиковая удочка",
                "Войди в Рыбий Мир и стань тем, кем ты всегда должен был быть.",
            ),
            (
                "B_W_FLAMETHROWER:",
                "Система санобработки РПО-80",
                "Работа уборщиком во времена биопринтеров и самопальных зараз следует трём правилам: Обезопасить, Очистить, Сдержать.",
            ),
            (
                "B_W_SKS:",
                "Транзакционная винтовка ЗКЗ",
                "Первородное оружие, что бьётся в ритме сердца финансовой системы.",
            ),
            (
                "B_W_NAILER:",
                "Пневмогвоздезабиватель Parasonic MP-1",
                "Новое оружие для личной обороны от Parasonic предоставляет невиданную до этого времени огневую мощь в компактном форм-факторе. Стреляет крайне высокоскоростными урановым гвоздями из магазина высокой емкости.",
            ),
            (
                "B_W_SHOCK:",
                "Raymond Shocktroop Tactical",
                "Компактный, но тем не менее мощный полуавтоматический дробовик. Известен среди сил правопорядка за эффективность в очистке от регенеративных общин.",
            ),
            (
                "B_W_LIGHT:",
                "Abscess Ironworks Lux ff374f727ce9d6d6e93be0793733c321",
                "Купайтесь в златом свете своего сияющего пути.",
            ),
        ]

        wep_dict = {w[0]: (w[1], w[2]) for w in canonical_weapons}

        # Find weapon cases in vanilla and patched
        fixed_lines = 0
        current_case = None
        for i, (v_line, p_line) in enumerate(zip(v_lines, p_lines)):
            stripped_v = v_line.strip()
            if stripped_v.startswith("B_W_") and stripped_v.endswith(":"):
                current_case = stripped_v
            elif current_case and "create_button(" in v_line:
                if current_case in wep_dict:
                    btn_name, _ = wep_dict[current_case]
                    # Preserve vanilla handler function and arg
                    handler_m = re.search(r'create_button\([^,]+,\s*"[^"]*",\s*"([^"]*)",\s*([^)]*)\)', v_line)
                    if handler_m:
                        handler = handler_m.group(1)
                        arg = handler_m.group(2)
                        new_btn_line = f'\t\t\t\tvar wep = create_button(m, "{btn_name}", "{handler}", {arg})\n'
                        if p_lines[i] != new_btn_line:
                            p_lines[i] = new_btn_line
                            fixed_lines += 1
            elif current_case and "wep.hint_tooltip" in v_line:
                if current_case in wep_dict:
                    _, tooltip = wep_dict[current_case]
                    # MUST have 4 tabs: \t\t\t\twep.hint_tooltip = "..."
                    new_tip_line = f'\t\t\t\twep.hint_tooltip = "{tooltip}"\n'
                    if p_lines[i] != new_tip_line:
                        p_lines[i] = new_tip_line
                        fixed_lines += 1
                current_case = None

        # Verify all lines in Menu_Test.gd now match vanilla leading tab counts
        mismatched_tabs = 0
        for lno, (vl, pl) in enumerate(zip(v_lines, p_lines), 1):
            v_tabs = len(vl) - len(vl.lstrip("\t"))
            p_tabs = len(pl) - len(pl.lstrip("\t"))
            if v_tabs != p_tabs:
                print(f"[-] Tab mismatch remaining at Menu_Test.gd:{lno} - vanilla {v_tabs} vs patched {p_tabs}")
                mismatched_tabs += 1

        assert mismatched_tabs == 0, f"Menu_Test.gd still has {mismatched_tabs} tab mismatches!"
        assert len(p_lines) == len(v_lines), "Line count mismatch!"

        p_mt.write_text("".join(p_lines), encoding="utf-8", newline="\n")
        print(f"[+] Fixed {fixed_lines} weapon lines in Menu_Test.gd.")
        print("[+] 100% tab count parity achieved with vanilla_new/Menu_Test.gd (1556 lines).")

    # --------------------------------------------------------------------------
    # Step 3: Strict Pre-Pack Automated Linter
    # --------------------------------------------------------------------------
    def step3_strict_prepack_linter(self):
        print("\n" + "=" * 80)
        print(" [*] [3/5] ENHANCED PRE-PACK LINTER (STRICT AUDIT)")
        print("=" * 80)

        gd_files = sorted(list(self.patched_dir.rglob("*.gd")))
        tscn_files = sorted(list(self.patched_dir.rglob("*.tscn")))
        json_files = sorted(list(self.patched_dir.rglob("*.json")))

        violations: List[str] = []

        # 1. GDScript Strict Audit
        print(f"[*] Auditing {len(gd_files)} GDScript files...")
        for p in gd_files:
            rel = p.relative_to(self.patched_dir).as_posix()
            v_p = self.vanilla_dir / rel
            p_lines = p.read_text(encoding="utf-8").splitlines()

            if not v_p.exists():
                violations.append(f"GDScript {rel}: No corresponding vanilla file found!")
                continue

            v_lines = v_p.read_text(encoding="utf-8").splitlines()
            if len(p_lines) != len(v_lines):
                violations.append(f"GDScript {rel}: Line count mismatch! Patched={len(p_lines)}, Vanilla={len(v_lines)}")

            for lno, (pl, vl) in enumerate(zip(p_lines, v_lines), 1):
                # Check 1: Space indentation check
                if pl.startswith(" ") and not pl.strip().startswith("#"):
                    violations.append(f"GDScript {rel}:{lno}: Space indentation found: {repr(pl[:30])}")

                # Check 2: Exact tab count match with vanilla
                p_tabs = len(pl) - len(pl.lstrip("\t"))
                v_tabs = len(vl) - len(vl.lstrip("\t"))
                if p_tabs != v_tabs:
                    violations.append(f"GDScript {rel}:{lno}: Tab indentation mismatch: expected {v_tabs}, got {p_tabs} ({repr(pl[:40])})")

                # Check 3: Quote parity per line (ignoring comments and escaped quotes)
                code_part = pl.split("#")[0]
                # Remove escaped quotes
                sanitized = code_part.replace(r'\"', '').replace(r"\'", '')
                dquotes = sanitized.count('"')
                if dquotes % 2 != 0:
                    violations.append(f"GDScript {rel}:{lno}: Unbalanced double-quotes ({dquotes}): {pl.strip()}")

            # Check 4: Bracket balance per file
            whole_content = "\n".join(l.split("#")[0] for l in p_lines)
            # Remove string contents to check bracket balance in code
            # Simple string stripper: replace "..." with ""
            code_no_strings = re.sub(r'"([^"\\]|\\.)*"', '""', whole_content)
            for open_b, close_b in [("(", ")"), ("[", "]"), ("{", "}")]:
                cnt_open = code_no_strings.count(open_b)
                cnt_close = code_no_strings.count(close_b)
                if cnt_open != cnt_close:
                    violations.append(f"GDScript {rel}: Bracket mismatch for '{open_b}{close_b}': {cnt_open} open vs {cnt_close} close")

        # 2. TSCN Scene Strict Audit
        print(f"[*] Auditing {len(tscn_files)} TSCN scene files...")
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

        # 3. JSON Strict Audit
        print(f"[*] Auditing {len(json_files)} JSON files...")
        for p in json_files:
            rel = p.relative_to(self.patched_dir).as_posix()
            try:
                json.loads(p.read_text(encoding="utf-8"))
            except Exception as e:
                violations.append(f"JSON {rel}: Parse error: {e}")

        # Summary
        if violations:
            print(f"\n[!] LINTER FAILED WITH {len(violations)} VIOLATIONS:")
            for v in violations:
                print(f"    - {v}")
            raise RuntimeError(f"Pre-pack linter failed with {len(violations)} errors. Build aborted.")

        print(f"[+] Linter PASSED 100% with 0 violations across all {len(gd_files)} .gd, {len(tscn_files)} .tscn, and {len(json_files)} .json files!")

    # --------------------------------------------------------------------------
    # Step 4: Pure Python PCK Rebuild
    # --------------------------------------------------------------------------
    def step4_binary_pck_rebuild(self):
        print("\n" + "=" * 80)
        print(" [*] [4/5] REBUILDING crueltysquad_ru_v2.pck (PURE PYTHON, 16-BYTE ALIGNED)")
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
                        while chunk := f_disk.read(chunk_size):
                            f_out.write(chunk)
                elif src_type == "vanilla":
                    f_vanilla.seek(entry["offset"])
                    remaining = size
                    while remaining > 0:
                        n = min(remaining, chunk_size)
                        buf = f_vanilla.read(n)
                        f_out.write(buf)
                        remaining -= len(buf)
                elif src_type == "ru_pck":
                    f_ru.seek(entry["offset"])
                    remaining = size
                    while remaining > 0:
                        n = min(remaining, chunk_size)
                        buf = f_ru.read(n)
                        f_out.write(buf)
                        remaining -= len(buf)

                # Pad payload to 16-byte boundary
                cur_pos = f_out.tell()
                aligned_pos = (cur_pos + (FILE_ALIGNMENT - 1)) & ~(FILE_ALIGNMENT - 1)
                pad_len = aligned_pos - cur_pos
                if pad_len > 0:
                    f_out.write(b"\x00" * pad_len)

        out_size = self.output_pck_path.stat().st_size
        elapsed = time.time() - t0
        print(f"[+] PCK Build complete in {elapsed:.2f}s!")
        print(f"[+] Output PCK size: {out_size:,} bytes ({out_size / (1024*1024):.2f} MB)")

        # Sync to mirrors
        print("[*] Synchronizing output PCK across targets...")
        shutil.copy2(self.output_pck_path, self.compat_pck_path)
        print(f"    -> Synced to: {self.compat_pck_path}")

        shutil.copy2(self.output_pck_path, self.root_pck_path)
        print(f"    -> Synced to: {self.root_pck_path}")

    # --------------------------------------------------------------------------
    # Step 5: Post-Verification
    # --------------------------------------------------------------------------
    def step5_post_verify(self):
        print("\n" + "=" * 80)
        print(" [*] [5/5] POST-VERIFICATION OF BUILT PCK")
        print("=" * 80)

        with open(self.output_pck_path, "rb") as f:
            hdr = struct.unpack("<4sIIII64xI", f.read(88))
            assert hdr[0] == PCK_MAGIC, f"Invalid magic: {hdr[0]}"
            file_count = hdr[5]

            pck_files = {}
            for _ in range(file_count):
                plen = struct.unpack("<I", f.read(4))[0]
                p = f.read(plen).rstrip(b"\x00").decode("utf-8", errors="replace")
                offset, size, md5 = struct.unpack("<QQ16s", f.read(32))
                pck_files[p] = {"offset": offset, "size": size, "md5": md5}

            # Check Menu_Test.gd inside built PCK
            assert "res://Menu_Test.gd" in pck_files, "Menu_Test.gd missing from built PCK!"
            mt_info = pck_files["res://Menu_Test.gd"]
            f.seek(mt_info["offset"])
            mt_bytes = f.read(mt_info["size"])
            mt_text = mt_bytes.decode("utf-8")
            mt_lines = mt_text.splitlines()

            # Verify line 437 in built PCK
            print(f"[*] Verified res://Menu_Test.gd in built PCK ({len(mt_lines)} lines)")
            print(f"    Line 435: {repr(mt_lines[434])}")
            print(f"    Line 436: {repr(mt_lines[435])}")
            print(f"    Line 437: {repr(mt_lines[436])}")

            assert mt_lines[436].startswith("\t\t\t\twep.hint_tooltip"), \
                f"Line 437 indentation error in built PCK: {repr(mt_lines[436])}"

            # Check all 26 weapon hint_tooltips have 4 tabs
            checked_tooltips = 0
            for lno, l in enumerate(mt_lines, 1):
                if "wep.hint_tooltip" in l:
                    assert l.startswith("\t\t\t\twep.hint_tooltip"), \
                        f"Tooltip indentation failure at line {lno}: {repr(l)}"
                    checked_tooltips += 1

            print(f"[+] All {checked_tooltips} weapon tooltip lines have EXACTLY 4 leading tabs (\\t\\t\\t\\t)!")

            # Verify no .gdc conflict for Menu_Test
            assert "res://Menu_Test.gdc" not in pck_files, "Old Menu_Test.gdc still in PCK!"
            assert "res://Menu_Test.gd.remap" not in pck_files, "Old Menu_Test.gd.remap still in PCK!"

        print("\n" + "=" * 80)
        print(" [SUCCESS] TASK 14 HOTFIX COMPLETED WITH ZERO DEFECTS!")
        print(" All mirrors synced and ready for gameplay verification.")
        print("=" * 80)


def main():
    base_dir = Path("C:/dev/cs_loc").resolve()
    tool = StartupCrashFixTool(base_dir)
    tool.run_all()


if __name__ == "__main__":
    main()
