# Cruelty Squad — Russian Localization Toolkit 🇷🇺

**Pure-Python pipeline for building, patching, and validating `.pck` localization packs for Cruelty Squad (Godot 3.x)**

> [!IMPORTANT]
> This repository contains **only** the build tools and documentation.
> No game assets, textures, audio, scenes, or copyrighted content is included.
> You need a **legitimate Steam copy** of [Cruelty Squad](https://store.steampowered.com/app/1388770/Cruelty_Squad/) to use these tools.

---

## 📥 Скачать готовый русификатор / Download Ready-to-Play Localization

Если вы просто хотите поиграть в **Cruelty Squad** на русском языке (с рабочими достижениями Steam, исправленной озвучкой Хендлера и всеми фиксами) без самостоятельного запуска скриптов сборки — перейдите по ссылке ниже:

- **Руководство Steam (актуальные ссылки и инструкция по установке):** [Актуальный русификатор Cruelty Squad (2026) — Рабочие достижения](https://steamcommunity.com/sharedfiles/filedetails/?id=3835672933)
- **ModDB Mirror:** *(скоро / coming soon)*

*(If you just want to install the finished Russian localization without running the Python build pipeline, use the official [Steam Community Guide](https://steamcommunity.com/sharedfiles/filedetails/?id=3835672933) above.)*

---

## 🇷🇺 Описание (RU)

Набор Python-инструментов для создания полной русской локализации Cruelty Squad — от распаковки `.pck` до финальной сборки и валидации. Весь пайплайн работает без внешних утилит (чистый Python, парсинг бинарного формата Godot 3.x PCK v1).

### Что входит в набор:
- **Аудит `.pck`** — парсер индекса и бинарный аудит ресурсов Godot 3.x
- **Экстрактор строк** — безопасное извлечение переводимых строк из `.gd`/`.tscn`/`.tres` с фильтрацией кода и ресурсов
- **Глоссарий** — канонический словарь лора и терминологии (200+ терминов)
- **3-way мердж перевода** — наложение перевода с сохранением технических инвариантов (тикеры, ноды, сигналы)
- **Валидатор базы** — проверка синтаксиса, длины строк, сохранности ключей
- **Сборщик `.pck`** — чистый Python-пакер с 16-байтным выравниванием и MD5-верификацией
- **Шаги 06–17** — поэтапные исправления: брифинги, шрифты, диалоги, субтитры, HQ 99%, импланты, оружие, краш запуска, речь Хендлера, баг «Дом», мультилайн-фикс
- **Pre-Pack Линтер** — финальная проверка всех `.gd`/`.tscn` перед упаковкой (кириллица в именах нод, сломанные GDScript, сдвиг индексов массивов)

### Как использовать:
1. Купите и установите [Cruelty Squad](https://store.steampowered.com/app/1388770/Cruelty_Squad/) в Steam
2. Скопируйте оригинальный `crueltysquad.pck` в папку `_source_pcks/`
3. Запускайте скрипты по порядку: `01_audit_pck.py` → `17_clean_multiline_house_fix.py`
4. Финальный `.pck` появится в корневой папке — замените им оригинал в Steam

---

## 🇬🇧 Description (EN)

A set of Python tools for building a complete Russian localization of Cruelty Squad — from `.pck` unpacking to final assembly and validation. The entire pipeline runs without external utilities (pure Python, binary parsing of Godot 3.x PCK v1 format).

### What's included:
- **`.pck` Auditor** — Godot 3.x PCK index parser and binary resource audit
- **String Extractor** — safe extraction of translatable strings from `.gd`/`.tscn`/`.tres` with code/resource filtering
- **Glossary Builder** — canonical lore & terminology dictionary (200+ terms)
- **3-way Translation Merge** — translation overlay preserving technical invariants (tickers, nodes, signals)
- **Database Validator** — syntax, string length, and key integrity checks
- **`.pck` Builder** — pure Python packer with 16-byte alignment and MD5 verification
- **Steps 06–17** — incremental fixes: briefings, fonts, dialogues, subtitles, HQ 99% freeze, implants, weapons, startup crash, Handler speech, "House" bug, multiline fix
- **Pre-Pack Linter** — final validation of all `.gd`/`.tscn` before packing (Cyrillic in node names, broken GDScript, array index shifts)

### How to use:
1. Purchase and install [Cruelty Squad](https://store.steampowered.com/app/1388770/Cruelty_Squad/) on Steam
2. Copy the original `crueltysquad.pck` into the `_source_pcks/` folder
3. Run scripts in order: `01_audit_pck.py` → `17_clean_multiline_house_fix.py`
4. The final `.pck` will appear in the root folder — replace the original in your Steam directory

---

## 📁 Repository Structure

```text
.
├── scripts/
│   ├── 01_audit_pck.py                    # PCK index parser & binary audit
│   ├── 02_extract_strings.py              # Safe string extractor
│   ├── 03_process_translation.py          # 3-way translation merge
│   ├── 04_validate_db.py                  # Database validator
│   ├── 05_build_pck_pure_python.py        # Pure Python PCK builder
│   ├── 06_fix_briefings_and_menu.py       # Mission select & briefing hotfix
│   ├── 07_fix_fonts_and_dialogue.py       # Font & dialogue freeze fix
│   ├── 08_restore_and_fix_menu.py         # Menu rollback & GDScript linter
│   ├── 09_complete_coverage_and_pack.py   # 100% coverage: intro, NPC, settings
│   ├── 10_wrap_intro_subtitles.py         # Intro/ending subtitle line wrapping
│   ├── 11_fix_hq_and_intro_pos.py         # HQ 99% freeze fix & subtitle positioning
│   ├── 12_fix_implant_pickups.py          # Secret implant pickup sync
│   ├── 13_fix_weapons_and_audit_stocks.py # Weapon/stock index audit
│   ├── 14_fix_startup_crash.py            # Startup crash fix & pre-pack linter
│   ├── 15_fix_handler_speech.py           # Handler speech & mouth animation restore
│   ├── 16_fix_house_and_implant_checks.py # "House" purchase bug fix
│   ├── 16_5_autoheal_and_clean_diff.py    # Auto-heal broken saves from v2.0-v2.2
│   ├── 17_clean_multiline_house_fix.py    # Final semicolon elimination
│   └── build_glossary.py                  # Canonical lore glossary builder
├── .gitignore
├── README.md
└── CHANGELOG.md
```

---

## ⚖️ License & Legal

This toolkit is provided as-is for educational and fan-localization purposes.
**No copyrighted game assets are distributed.**
Cruelty Squad is © Consumer Softproducts. All rights reserved.

---

## 🙏 Credits

- **Localization & Tooling**: Built with [Antigravity](https://deepmind.google/) (Google DeepMind)
- **Game**: [Cruelty Squad](https://store.steampowered.com/app/1388770/Cruelty_Squad/) by Consumer Softproducts
- **Engine**: [Godot Engine](https://godotengine.org/) 3.x