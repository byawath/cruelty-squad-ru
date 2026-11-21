#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_glossary.py
--------------------------------------------------------------------------------
Lead Localization Engineering & Reverse-Engineering Tool for Cruelty Squad (Godot 3.x)
Task 3: Canonical Lore & Terminology Glossary Builder.
--------------------------------------------------------------------------------
"""

import json
from pathlib import Path

GLOSSARY_DATA = {
    "meta": {
        "title": "Cruelty Squad Canonical Localization Glossary",
        "version": "1.0.0",
        "style_guide": (
            "Смесь стерильного корпоративного канцелярита, клинической биотехнологической "
            "терминологии, гностического фатализма и абсурдного ультракапиталистического цинизма. "
            "Эстетика: биопанк, боди-хоррор, экономический солипсизм."
        ),
        "code_safety_rules": [
            {
                "rule": "TICKER_PRESERVATION",
                "detail": (
                    "Биржевые тикеры (CRUS, GDHD, GTC, PIHO, AOI, GAGA, PWR, VEME, FBCA, SCRD, "
                    "а также тикеры рыб FLSH, CIV, POOL, DRMP, FISH и т.д.) используются "
                    "как ключи словарей в savegame.save и внутренних индексах. "
                    "Они ОБЯЗАНЫ оставаться строго в оригинальной латинице."
                )
            },
            {
                "rule": "LEVEL_NAME_KEYS_ISOLATION",
                "detail": (
                    "В Game_Manager.gd ключи рекордов и S-рангов формируются конкатенацией: "
                    "level_name + '_raw_time', level_name + '_string_time' и т.д., где level_name "
                    "берется из поля 'name' соответствующего LevelX.json. Изменение поля 'name' "
                    "в LevelX.json ломает чтение рекордов старых сохранений. "
                    "Решение: внутреннее имя 'name' в json оставлять на латинице, а для локализованного "
                    "отображения в UI добавить отдельное поле 'display_name' либо локализовать "
                    "через таблицу в Menu_Test.gd."
                )
            },
            {
                "rule": "WEAPON_AND_FISH_NAMES_SEPARATION",
                "detail": (
                    "В рыболовной системе массив FISH_FOUND хранит тикеры (current_fish.ticker). "
                    "Поле s_name является чисто визуальным и безопасно для перевода. "
                    "В оружейной системе массив WEAPONS_UNLOCKED индексируется целочисленными ID "
                    "(W_PISTOL, W_SMG и т.д.), поэтому названия в W_NAMES и кнопках меню "
                    "безопасны для полной локализации."
                )
            }
        ]
    },
    "glossary": [
        # ======================================================================
        # 1. CORE LORE & GNOSTIC CONCEPTS (Ключевые лор-концепты)
        # ======================================================================
        {
            "category": "lore",
            "id": "divine_light_severed",
            "en": "Divine Light Severed",
            "ru_legacy": "Божественный Свет Прерван",
            "ru_canonical": "БОЖЕСТВЕННЫЙ СВЕТ ОТСЕЧЕН",
            "notes": "Канонический статус смерти. В гностицизме свет именно отсекается демиургическим миром."
        },
        {
            "category": "lore",
            "id": "flesh_automaton",
            "en": "Flesh Automaton Animated by Neurotransmitters",
            "ru_legacy": "Плотский Автоматон Движимый Нейромедиаторами",
            "ru_canonical": "МЯСНОЙ АВТОМАТОН, ДВИЖИМЫЙ НЕЙРОМЕДИАТОРАМИ",
            "notes": "Определение протагониста в депрессивном состоянии. 'Мясной' точнее передает биопанк игры, чем 'плотский'."
        },
        {
            "category": "lore",
            "id": "hope_eradicated",
            "en": "Hope Eradicated",
            "ru_legacy": "Надежда Уничтожена",
            "ru_canonical": "НАДЕЖДА ИСКОРЕНЕНА",
            "notes": "Статус провала / упадка. 'Искоренена' подчеркивает клиническую необратимость."
        },
        {
            "category": "lore",
            "id": "power_in_misery",
            "en": "Power in Misery",
            "ru_legacy": "Сила в Страданиях",
            "ru_canonical": "СИЛА В СТРАДАНИИ",
            "notes": "Высшее трансцендентное состояние персонажа при нулевом коэффициенте человечности."
        },
        {
            "category": "lore",
            "id": "ceo_mindset",
            "en": "CEO Mindset",
            "ru_legacy": "Мышление CEO",
            "ru_canonical": "МЫШЛЕНИЕ СЕО",
            "notes": "Ироничный мем ультракапитализма. Сохраняем 'СЕО' для передачи кричащего корпоративного цинизма."
        },
        {
            "category": "lore",
            "id": "gorbino_quest",
            "en": "Gorbino's Quest",
            "ru_legacy": "Gorbino's Quest",
            "ru_canonical": "Квест Горбино",
            "notes": "Легендарная игра вселенной CS, 500 часов геймплея майнд-брейка."
        },
        {
            "category": "lore",
            "id": "chunkopops",
            "en": "Chunkopops",
            "ru_legacy": "Чункопопы",
            "ru_canonical": "Чанкопопы",
            "notes": "Пародия на виниловые фигурки Funko Pop, объект бездумного спекулятивного коллекционирования."
        },
        {
            "category": "lore",
            "id": "cruelty_squad",
            "en": "Cruelty Squad",
            "ru_legacy": "Отряд Жестокости",
            "ru_canonical": "Отряд Жестокости",
            "notes": "Корпоративная ЧВК мокрой зачистки. Удачная устоявшаяся находка старого перевода."
        },
        {
            "category": "lore",
            "id": "punishment_mode",
            "en": "Punishment Mode",
            "ru_legacy": "Режим Кары",
            "ru_canonical": "Режим кары",
            "notes": "Базовое состояние наказания и страданий игрока."
        },
        {
            "category": "lore",
            "id": "chaos_mode",
            "en": "Chaos Mode",
            "ru_legacy": "Режим Хаоса",
            "ru_canonical": "Режим хаоса",
            "notes": "Высший режим безумия и энтропии."
        },
        {
            "category": "lore",
            "id": "trauma_loop",
            "en": "Trauma Loop",
            "ru_legacy": "Травматический Цикл",
            "ru_canonical": "Травматический цикл",
            "notes": "Финальная зона и циклическая природа бесконечного воскрешения."
        },
        {
            "category": "lore",
            "id": "biocurrency",
            "en": "Biocurrency",
            "ru_legacy": "Биовалюта",
            "ru_canonical": "Биовалюта",
            "notes": "Органы и ткани как универсальный платежный эквивалент."
        },
        {
            "category": "lore",
            "id": "handler",
            "en": "Handler",
            "ru_legacy": "Куратор",
            "ru_canonical": "Куратор",
            "notes": "Лицо с кожей-сеткой, раздающее брифинги и миссии."
        },
        {
            "category": "lore",
            "id": "target",
            "en": "Target",
            "ru_legacy": "Цель",
            "ru_canonical": "Цель",
            "notes": "Субъект корпоративной ликвидации."
        },

        # ======================================================================
        # 2. WEAPONS & AMMUNITION (Оружие и боеприпасы)
        # ======================================================================
        {
            "category": "weapons",
            "id": "w_pistol",
            "en": "Parasonic D2 Silenced Pistol",
            "ru_legacy": "Пистолет с глушителем Parasonic D2",
            "ru_canonical": "Бесшумный пистолет Parasonic D2",
            "notes": "Стартовое табельное оружие скрытного устранения."
        },
        {
            "category": "weapons",
            "id": "w_smg",
            "en": "K&H R5",
            "ru_legacy": "K&H R5",
            "ru_canonical": "K&H R5",
            "notes": "Оружейный бренд (пародия на H&K), оставляется в латинице."
        },
        {
            "category": "weapons",
            "id": "w_s_smg",
            "en": "Minato M9",
            "ru_legacy": "Минато M9",
            "ru_canonical": "Minato M9",
            "notes": "Компактный пистолет-пулемет, японский бренд."
        },
        {
            "category": "weapons",
            "id": "w_shotgun",
            "en": "Balotelli Hypernova",
            "ru_legacy": "Balotelli Hypernova",
            "ru_canonical": "Balotelli Hypernova",
            "notes": "Тяжелый полуавтоматический дробовик (пародия на Benelli Supernova)."
        },
        {
            "category": "weapons",
            "id": "w_rl",
            "en": "Security Systems Anti-Armor Device",
            "ru_legacy": "Бронебойный аппарат СисОх",
            "ru_canonical": "Бронебойный комплекс «СисОх»",
            "notes": "Тяжелый ракетный гранатомет корпорации СисОх (Security Systems)."
        },
        {
            "category": "weapons",
            "id": "w_sniper",
            "en": "Stern AWS 3000",
            "ru_legacy": "Stern AWS 3000",
            "ru_canonical": "Stern AWS 3000",
            "notes": "Снайперская винтовка высокой точности (пародия на AI AWM / Steyr)."
        },
        {
            "category": "weapons",
            "id": "w_ar",
            "en": "K&H X20",
            "ru_legacy": "K&H X20",
            "ru_canonical": "K&H X20",
            "notes": "Штурмовая винтовка корпоративного класса (пародия на HK G36/XM8)."
        },
        {
            "category": "weapons",
            "id": "w_nambu",
            "en": "New Safety M62",
            "ru_legacy": "New Safety M62",
            "ru_canonical": "New Safety M62",
            "notes": "Дешевый служебный пистолет."
        },
        {
            "category": "weapons",
            "id": "w_gas",
            "en": "Riot Pacifier",
            "ru_legacy": "Демократизатор",
            "ru_canonical": "Усмиритель бунтов",
            "notes": "В старом переводе 'Демократизатор' (сленг для дубинки), но в игре это слезоточивый гранатомет."
        },
        {
            "category": "weapons",
            "id": "w_mg3",
            "en": "AMG4",
            "ru_legacy": "AMG4",
            "ru_canonical": "AMG4",
            "notes": "Единый пулемет."
        },
        {
            "category": "weapons",
            "id": "w_autoshotgun",
            "en": "Precise Industries AS15",
            "ru_legacy": "Precise Industries AS15",
            "ru_canonical": "Precise Industries AS15",
            "notes": "Автоматический дробовик барабанного типа."
        },
        {
            "category": "weapons",
            "id": "w_mauser",
            "en": "Mowzer SP99",
            "ru_legacy": "Mowzer SP99",
            "ru_canonical": "Mowzer SP99",
            "notes": "Пистолет со шнековым магазином (пародия на Mauser / Calico)."
        },
        {
            "category": "weapons",
            "id": "w_bore",
            "en": "Security Systems Cerebral Bore",
            "ru_legacy": "Черепное Сверло СисОх",
            "ru_canonical": "Черепной бур «СисОх»",
            "notes": "Оружие самонаведения в черепную коробку жертвы."
        },
        {
            "category": "weapons",
            "id": "w_mkr",
            "en": "Spectacular Dynamics MCR Carbine",
            "ru_legacy": "Карабин Spectacular Dynamics MCR",
            "ru_canonical": "Карабин Spectacular Dynamics MCR",
            "notes": "Высокотехнологичный карабин корпорации Spectacular Dynamics."
        },
        {
            "category": "weapons",
            "id": "w_radgun",
            "en": "Bolt ACR",
            "ru_legacy": "ПБВ 'Болт'",
            "ru_canonical": "Bolt ACR",
            "notes": "Радиационное оружие."
        },
        {
            "category": "weapons",
            "id": "w_tranq",
            "en": "SNOOZEFEST Animal Control Pistol",
            "ru_legacy": "Пистолет Для Контроля Животных SNOOZEFEST",
            "ru_canonical": "Пистолет службы отлова животных SNOOZEFEST",
            "notes": "Транквилизаторный пистолет."
        },
        {
            "category": "weapons",
            "id": "w_blackjack",
            "en": "Expandable Baton",
            "ru_legacy": "Телескопическая Дубинка",
            "ru_canonical": "Телескопическая дубинка",
            "notes": "Оружие ближнего боя."
        },
        {
            "category": "weapons",
            "id": "w_flashlight",
            "en": "Flashlight",
            "ru_legacy": "Фонарик",
            "ru_canonical": "Фонарик",
            "notes": "Навесной световой прибор."
        },
        {
            "category": "weapons",
            "id": "w_zippy",
            "en": "Zippy 3000",
            "ru_legacy": "Зиппи 3000",
            "ru_canonical": "Zippy 3000",
            "notes": "Смехотворное скорострельное оружие кустарного производства."
        },
        {
            "category": "weapons",
            "id": "w_dna",
            "en": "Parasonic C3 DNA Scrambler",
            "ru_legacy": "Меситель ДНК Parasonic C3",
            "ru_canonical": "ДНК-деструктор Parasonic C3",
            "notes": "Генетическое биооружие, разжижающее клеточную структуру."
        },
        {
            "category": "weapons",
            "id": "w_rod",
            "en": "Fiberglass Fishing Rod",
            "ru_legacy": "Удочка из Стекловолокна",
            "ru_canonical": "Стеклопластиковая удочка",
            "notes": "Инструмент ловли биоресурсов."
        },
        {
            "category": "weapons",
            "id": "w_ft",
            "en": "RPO-80 Sanitization System",
            "ru_legacy": "Система Обеззараживания РПО-80",
            "ru_canonical": "Система санобработки РПО-80",
            "notes": "Огнемет санитарного назначения."
        },
        {
            "category": "weapons",
            "id": "w_sks",
            "en": "ZKZ Transactional Rifle",
            "ru_legacy": "Торгово-обменная винтовка ЗКЗ",
            "ru_canonical": "Транзакционная винтовка ЗКЗ",
            "notes": "Винтовка, выстрелы которой списывают деньги со счета."
        },
        {
            "category": "weapons",
            "id": "w_nailer",
            "en": "Parasonic MP-1 Nailer",
            "ru_legacy": "Гвоздомет Parasonic MP-1",
            "ru_canonical": "Пневмогвоздезабиватель Parasonic MP-1",
            "notes": "Строительный инструмент в качестве летального оружия."
        },

        # ======================================================================
        # 3. IMPLANTS & CYBERNETICS (Импланты и биомодификации)
        # ======================================================================
        {
            "category": "implants",
            "id": "imp_speed_gland",
            "en": "Speed Enhancer Gland",
            "ru_legacy": "Гланды Улучшения Скорости",
            "ru_canonical": "Железа стимуляции скорости",
            "notes": "Биоорган секреции синтетических гормонов ускорения."
        },
        {
            "category": "implants",
            "id": "imp_speed_cluster",
            "en": "Speed Enhancer Node Cluster",
            "ru_legacy": "Скопление Лимфоузлов Улучшения Скорости",
            "ru_canonical": "Узловой кластер стимуляции скорости",
            "notes": "Эндокринный заменитель для разгона метаболизма."
        },
        {
            "category": "implants",
            "id": "imp_speed_total",
            "en": "Speed Enhancer Total Organ Package",
            "ru_legacy": "Полный Набор Органов Улучшения Скорости",
            "ru_canonical": "Органокомплекс тотальной стимуляции скорости",
            "notes": "Полная замена внутренних органов на сверхбыстрые хрупкие биореплики."
        },
        {
            "category": "implants",
            "id": "imp_armor_2",
            "en": "CSIJ Level II Body Armor",
            "ru_legacy": "Броня II класса CSIJ",
            "ru_canonical": "Бронежилет CSIJ Класс II",
            "notes": "Бюджетный защитный комплект."
        },
        {
            "category": "implants",
            "id": "imp_armor_2b",
            "en": "CSIJ Level IIB Body Armor",
            "ru_legacy": "Броня IIВ класса CSIJ",
            "ru_canonical": "Бронежилет CSIJ Класс II-B",
            "notes": "Легкий кевларовый комплект повышенной прочности."
        },
        {
            "category": "implants",
            "id": "imp_armor_3",
            "en": "CSIJ Level III Body Armor",
            "ru_legacy": "Броня III класса CSIJ",
            "ru_canonical": "Бронежилет CSIJ Класс III",
            "notes": "Композитный бронежилет со сверхвысокомолекулярными пластинами."
        },
        {
            "category": "implants",
            "id": "imp_armor_4",
            "en": "CSIJ Level IV Body Armor",
            "ru_legacy": "Броня IV класса CSIJ",
            "ru_canonical": "Бронежилет CSIJ Класс IV",
            "notes": "Биопаутинный армированный бронежилет."
        },
        {
            "category": "implants",
            "id": "imp_armor_5",
            "en": "CSIJ Level V Biosuit",
            "ru_legacy": "Биокостюм V класса CSIJ",
            "ru_canonical": "Биокостюм CSIJ Класс V",
            "notes": "Тяжелая биосинтетическая броня высшего класса."
        },
        {
            "category": "implants",
            "id": "imp_hazmat",
            "en": "Hazmat Suit",
            "ru_legacy": "Костюм Химзащиты",
            "ru_canonical": "Костюм биохимзащиты",
            "notes": "Изолирующий защитный комплект."
        },
        {
            "category": "implants",
            "id": "imp_nvg",
            "en": "Night Vision Goggles",
            "ru_legacy": "Очки Ночного Видения",
            "ru_canonical": "Прибор ночного видения",
            "notes": "Тактический оптический ПНВ."
        },
        {
            "category": "implants",
            "id": "imp_nightmare_vg",
            "en": "Nightmare Vision Goggles",
            "ru_legacy": "Очки Кошмарного Видения",
            "ru_canonical": "Прибор кошмарного видения",
            "notes": "Спектральный прибор восприятия потусторонних частот."
        },
        {
            "category": "implants",
            "id": "imp_corp_eyes",
            "en": "Eyes of Corporate Insight",
            "ru_legacy": "Глаз Корповидения",
            "ru_canonical": "Очи корпоративного прозрения",
            "notes": "Имплант, открывающий скрытые финансовые и рыночные потоки."
        },
        {
            "category": "implants",
            "id": "imp_holy_scope",
            "en": "Holy Scope",
            "ru_legacy": "Священный Прицел",
            "ru_canonical": "Сакральный оптический прицел",
            "notes": "Гностический прицел, поражающий трансцендентные сущности."
        },
        {
            "category": "implants",
            "id": "imp_skullgun",
            "en": "Skullgun",
            "ru_legacy": "Черепопушка",
            "ru_canonical": "Черепное орудие (Черепопушка)",
            "notes": "Культовая отсылка к Deus Ex. В интерфейсе можно сохранить ироничное 'Черепопушка'."
        },
        {
            "category": "implants",
            "id": "imp_cortical",
            "en": "Cortical Scaledown+",
            "ru_legacy": "Кортикальный Уменьшатель+",
            "ru_canonical": "Кортикальный редуктор+",
            "notes": "Сжатие коры мозга для снижения получаемого урона."
        },
        {
            "category": "implants",
            "id": "imp_rain_hat",
            "en": "Tattered Rain Hat",
            "ru_legacy": "Бывалая Дождевая Шляпа",
            "ru_canonical": "Потрёпанная дождевая шляпа",
            "notes": "Защита от кислотных осадков."
        },
        {
            "category": "implants",
            "id": "imp_flowerchute",
            "en": "Flowerchute",
            "ru_legacy": "Парашют-Цветок",
            "ru_canonical": "Цветочный парашют",
            "notes": "Органический замедлитель падения."
        },
        {
            "category": "implants",
            "id": "imp_goo_overdrive",
            "en": "Goo Overdrive",
            "ru_legacy": "Слизь-Перегруз",
            "ru_canonical": "Слизевой форсаж",
            "notes": "Впрыск мутагенной биомассы для ускорения."
        },
        {
            "category": "implants",
            "id": "imp_grappendix",
            "en": "Grappendix",
            "ru_legacy": "Грапендикс",
            "ru_canonical": "Грапендикс",
            "notes": "Орган-крюк (аппендикс-кошка). Шедевр абсурдного словообразования, сохраняем 1:1."
        },
        {
            "category": "implants",
            "id": "imp_abominator",
            "en": "Abominator",
            "ru_legacy": "Богомерз",
            "ru_canonical": "Богомерз (Мерзость)",
            "notes": "Гротескное оружие судного дня."
        },
        {
            "category": "implants",
            "id": "imp_gunkboosters",
            "en": "Gunkboosters",
            "ru_legacy": "Гноеплюй",
            "ru_canonical": "Гноевые ускорители",
            "notes": "Прыжковые сопла на токсичных выделениях."
        },
        {
            "category": "implants",
            "id": "imp_funkgrunters",
            "en": "Funkgrunters",
            "ru_legacy": "Фанковорчалки",
            "ru_canonical": "Фанк-хрюкатели",
            "notes": "Органические вокализаторы шума."
        },
        {
            "category": "implants",
            "id": "imp_pneumatic_legs",
            "en": "Pneumatic Legs",
            "ru_legacy": "Пневматические Ноги",
            "ru_canonical": "Пневматические ноги",
            "notes": "Кибернетические протезы прыжка."
        },
        {
            "category": "implants",
            "id": "imp_alien_wetware",
            "en": "Alien Leg Wetware",
            "ru_legacy": "Инопланетное Биологическое Обеспечение Для Ног",
            "ru_canonical": "Инопланетный нейроинтерфейс ног",
            "notes": "Wetware переводится как 'нейроинтерфейс' или 'биологическое обеспечение'."
        },
        {
            "category": "implants",
            "id": "imp_vertical_entry",
            "en": "Vertical Entry Device",
            "ru_legacy": "Девайс Вертикального Проникновения",
            "ru_canonical": "Устройство вертикального проникновения",
            "notes": "Устройство пробития потолков и перекрытий."
        },
        {
            "category": "implants",
            "id": "imp_icaros",
            "en": "Icaros Machine",
            "ru_legacy": "Машина Икароса",
            "ru_canonical": "Аппарат «Икарос»",
            "notes": "Механизм сверхвысоких прыжков."
        },

        # ======================================================================
        # 4. LOCATIONS & LEVELS (Локации и уровни)
        # ======================================================================
        {
            "category": "levels",
            "id": "level_hq",
            "en": "Cruelty Squad Headquarters",
            "ru_legacy": "Штаб Отряда Жестокости",
            "ru_canonical": "Штаб-квартира Отряда Жестокости",
            "notes": "Учебная база и квартира протагониста."
        },
        {
            "category": "levels",
            "id": "level_1",
            "en": "Pharmakokinetiks",
            "ru_legacy": "Фармакокинетикс",
            "ru_canonical": "Фармакокинетика (Pharmakokinetiks)",
            "notes": "Штаб-квартира фармацевтического гиганта. Ключ сохранения в JSON сохранять как латиницу!"
        },
        {
            "category": "levels",
            "id": "level_2",
            "en": "Paradise",
            "ru_legacy": "Парадайз",
            "ru_canonical": "Парадайз (Райские кущи)",
            "notes": "Элитный закрытый пригород миллионеров."
        },
        {
            "category": "levels",
            "id": "level_3",
            "en": "Sin Space Engineering",
            "ru_legacy": "Космическая Инженерия 'ГРЕХ'",
            "ru_canonical": "Аэрокосмическая инженерия «Грех»",
            "notes": "Корпорация орбитального ракетостроения."
        },
        {
            "category": "levels",
            "id": "level_4",
            "en": "Androgen Assault",
            "ru_legacy": "Андрогенный Штурм",
            "ru_canonical": "Андрогенный штурм",
            "notes": "Лаборатория стероидов и гормональных стимуляторов."
        },
        {
            "category": "levels",
            "id": "level_5",
            "en": "Mall Madness",
            "ru_legacy": "Торговое Безумие",
            "ru_canonical": "Безумие в мегамолле",
            "notes": "Торгово-развлекательный молл гиперпотребления."
        },
        {
            "category": "levels",
            "id": "level_6",
            "en": "Apartment Atrocity",
            "ru_legacy": "Резня в Апартаментах",
            "ru_canonical": "Зверство в жилом комплексе",
            "notes": "Многоквартирный сектор низшего класса."
        },
        {
            "category": "levels",
            "id": "level_7",
            "en": "Seaside Shock",
            "ru_legacy": "Прибрежный Шок",
            "ru_canonical": "Прибрежный шок",
            "notes": "Портовая промзона."
        },
        {
            "category": "levels",
            "id": "level_8",
            "en": "Bog Business",
            "ru_legacy": "Болотный бизнесс",
            "ru_canonical": "Болотный бизнес",
            "notes": "Грязные болота и нелегальный промысел биомассы."
        },
        {
            "category": "levels",
            "id": "level_9",
            "en": "Casino Catastrophe",
            "ru_legacy": "Катастрофа в Казино",
            "ru_canonical": "Катастрофа в казино",
            "notes": "Игорный комплекс Фатберга."
        },
        {
            "category": "levels",
            "id": "level_10",
            "en": "Idiot Party",
            "ru_legacy": "Вечеринка Идиотов",
            "ru_canonical": "Вечеринка идиотов",
            "notes": "Политический раут олигархов."
        },
        {
            "category": "levels",
            "id": "level_11",
            "en": "Office",
            "ru_legacy": "Офис",
            "ru_canonical": "Офис",
            "notes": "Безликий опенспейс офисного планктона."
        },
        {
            "category": "levels",
            "id": "level_12",
            "en": "Archon Grid",
            "ru_legacy": "Архонт Сеть",
            "ru_canonical": "Сетка Архонтов",
            "notes": "Гностическая энергосеть владык материального мира."
        },
        {
            "category": "levels",
            "id": "level_bonus1",
            "en": "Darkworld",
            "ru_legacy": "Тёмномирье",
            "ru_canonical": "Тёмный мир",
            "notes": "Секретный потусторонний уровень."
        },
        {
            "category": "levels",
            "id": "level_bonus2",
            "en": "Alpine Hospitality",
            "ru_legacy": "Альпийское Гостеприимство",
            "ru_canonical": "Альпийское гостеприимство",
            "notes": "Горный курорт элиты."
        },
        {
            "category": "levels",
            "id": "level_bonus3",
            "en": "Miner's Miracle",
            "ru_legacy": "Шахтёрское Чудо",
            "ru_canonical": "Чудо шахтёра",
            "notes": "Глубоководные буровые шахты."
        },
        {
            "category": "levels",
            "id": "level_bonus4",
            "en": "Neuron Activator",
            "ru_legacy": "Нейронный Активатор",
            "ru_canonical": "Активатор нейронов",
            "notes": "Бионейросетевой испытательный комплекс."
        },
        {
            "category": "levels",
            "id": "level_bonus5",
            "en": "House",
            "ru_legacy": "Дом",
            "ru_canonical": "Дом",
            "notes": "Загородный особняк топ-менеджера."
        },

        # ======================================================================
        # 5. CORPORATIONS & STOCKS (Компании и биржевые активы)
        # ======================================================================
        {
            "category": "stocks",
            "id": "stock_crus",
            "ticker": "CRUS",
            "en": "Cruelty Squad",
            "ru_legacy": "Отряд Жестокости",
            "ru_canonical": "ЧВК «Отряд Жестокости»",
            "notes": "Голубая фишка на рынке охранных и ликвидационных услуг."
        },
        {
            "category": "stocks",
            "id": "stock_gdhd",
            "ticker": "GDHD",
            "en": "Godhead Heavy Industries",
            "ru_legacy": "Godhead Heavy Industries",
            "ru_canonical": "Тяжпром «Годхэд»",
            "notes": "Оборонный индустриальный гигант."
        },
        {
            "category": "stocks",
            "id": "stock_gtc",
            "ticker": "GTC",
            "en": "G-Tech",
            "ru_legacy": "G-Тек",
            "ru_canonical": "Джи-Тек",
            "notes": "Стартап в сфере биотеха и нейровычислений."
        },
        {
            "category": "stocks",
            "id": "stock_piho",
            "ticker": "PIHO",
            "en": "Pizza House",
            "ru_legacy": "Пицца Хаус",
            "ru_canonical": "«Пицца Хаус»",
            "notes": "Глобальная монополия фастфуда."
        },
        {
            "category": "stocks",
            "id": "stock_aoi",
            "ticker": "AOI",
            "en": "Advanced Orbital Instruments",
            "ru_legacy": "Advanced Orbital Instruments",
            "ru_canonical": "Передовые орбитальные приборы",
            "notes": "Агрокосмические решения для фермеров 22-го века."
        },
        {
            "category": "stocks",
            "id": "stock_gaga",
            "ticker": "GAGA",
            "en": "GamesGames",
            "ru_legacy": "GamesGames",
            "ru_canonical": "«ГеймсГеймс»",
            "notes": "Убыточная сеть магазинов видеоигр (пародия на GameStop)."
        },
        {
            "category": "stocks",
            "id": "stock_pwr",
            "ticker": "PWR",
            "en": "Power Monger Shipping Company",
            "ru_legacy": "Логистическая Служба Power Monger",
            "ru_canonical": "Судоходная компания «Пауэр Монгер»",
            "notes": "Логистический конгломерат с рабским трудом курьеров."
        },
        {
            "category": "stocks",
            "id": "stock_veme",
            "ticker": "VEME",
            "en": "Veggo's Meatoids",
            "ru_legacy": "Мясоиды Веггос",
            "ru_canonical": "«Мясоиды Вегго»",
            "notes": "Стартап синтетического вегетарианского суррогата мяса."
        },
        {
            "category": "stocks",
            "id": "stock_fbca",
            "ticker": "FBCA",
            "en": "Fatberg Casino",
            "ru_legacy": "Казино Фатберг",
            "ru_canonical": "Казино «Фатберг»",
            "notes": "Игорный бизнес сэра Фатберга в западных топях."
        },
        {
            "category": "stocks",
            "id": "stock_scrd",
            "ticker": "SCRD",
            "en": "Security Redefined",
            "ru_legacy": "СисОх",
            "ru_canonical": "СБ «Новый рубеж» (СисОх)",
            "notes": "Частная охранная служба (Security Systems)."
        },

        # ======================================================================
        # 6. ORGANS & BIOLOGICAL ASSETS (Органы и трофеи)
        # ======================================================================
        {
            "category": "organs",
            "id": "organ_brain",
            "en": "Brain",
            "ru_legacy": "Мозг",
            "ru_canonical": "Мозг",
            "notes": "Базовый биоактив."
        },
        {
            "category": "organs",
            "id": "organ_heart",
            "en": "Heart",
            "ru_legacy": "Сердце",
            "ru_canonical": "Сердце",
            "notes": "Высоколиквидный орган."
        },
        {
            "category": "organs",
            "id": "organ_liver",
            "en": "Liver",
            "ru_legacy": "Печень",
            "ru_canonical": "Печень",
            "notes": "Стандартная печень."
        },
        {
            "category": "organs",
            "id": "organ_kidney",
            "en": "Kidney",
            "ru_legacy": "Почка",
            "ru_canonical": "Почка",
            "notes": "Почка коммерческого качества."
        },
        {
            "category": "organs",
            "id": "organ_pancreas",
            "en": "Pancreas",
            "ru_legacy": "Поджелудочная",
            "ru_canonical": "Поджелудочная железа",
            "notes": "Ферментный орган."
        },
        {
            "category": "organs",
            "id": "organ_adv_pancreas",
            "en": "Advanced Pancreas",
            "ru_legacy": "Продвинутая Поджелудочная",
            "ru_canonical": "Модифицированная поджелудочная",
            "notes": "Генетически аугментированный орган."
        },
        {
            "category": "organs",
            "id": "organ_black_heart",
            "en": "Black Heart",
            "ru_legacy": "Чёрное Сердце",
            "ru_canonical": "Чёрное сердце",
            "notes": "Сердце, пораженное некрозом и жаждой наживы."
        },
        {
            "category": "organs",
            "id": "organ_dog_intestine",
            "en": "Dog Intestine",
            "ru_legacy": "Собачий Кишечник",
            "ru_canonical": "Собачий кишечник",
            "notes": "Низкосортный субпродукт."
        },
        {
            "category": "organs",
            "id": "organ_nuclear_stomach",
            "en": "Nuclear Stomach",
            "ru_legacy": "Ядерный Желудок",
            "ru_canonical": "Ядерный желудок",
            "notes": "Радиоактивный пищеварительный тракт."
        },
        {
            "category": "organs",
            "id": "organ_psycho_brain",
            "en": "Psycho Brain",
            "ru_legacy": "Психомозг",
            "ru_canonical": "Психомозг",
            "notes": "Мозг, насыщенный боевыми психоделиками."
        },
        {
            "category": "organs",
            "id": "organ_tactical_liver",
            "en": "Tactical Liver",
            "ru_legacy": "Тактическая Печень",
            "ru_canonical": "Тактическая печень",
            "notes": "Печень военного стандарта с фильтрацией боевых отравляющих веществ."
        },

        # ======================================================================
        # 7. FISH & FAUNA (Рыбы и биоресурсы)
        # ======================================================================
        {
            "category": "fish",
            "id": "fish_flsh",
            "ticker": "FLSH",
            "en": "Fleshrat",
            "ru_legacy": "Плотекрыса",
            "ru_canonical": "Плотекрыса",
            "notes": "Сгусток живой мышечной ткани в форме грызуна."
        },
        {
            "category": "fish",
            "id": "fish_civ",
            "ticker": "CIV",
            "en": "Civilian",
            "ru_legacy": "Гражданский",
            "ru_canonical": "Гражданский (рыба)",
            "notes": "Водный биоактив с человеческим лицом."
        },
        {
            "category": "fish",
            "id": "fish_brny",
            "ticker": "BRNY",
            "en": "Brainy",
            "ru_legacy": "Брэйни",
            "ru_canonical": "Мозговик",
            "notes": "Рыба со сверхрасширенными полушариями мозга."
        },
        {
            "category": "fish",
            "id": "fish_pool",
            "ticker": "POOL",
            "en": "Poolsucker",
            "ru_legacy": "Бассейносос",
            "ru_canonical": "Бассейносос",
            "notes": "Придонный паразит хлорированных водоемов."
        },
        {
            "category": "fish",
            "id": "fish_brst",
            "ticker": "BRST",
            "en": "Brimstone",
            "ru_legacy": "Бримстоун",
            "ru_canonical": "Серный сом",
            "notes": "Рыба из адских токсичных серных источников."
        },
        {
            "category": "fish",
            "id": "fish_drmp",
            "ticker": "DRMP",
            "en": "Drimp",
            "ru_legacy": "Дримп",
            "ru_canonical": "Дримп",
            "notes": "Маленький токсичный рачок-мутант."
        },
        {
            "category": "fish",
            "id": "fish_glom",
            "ticker": "GLOM",
            "en": "Gloomoid",
            "ru_legacy": "Глумоид",
            "ru_canonical": "Глумоид",
            "notes": "Мрачная глубоководная биомасса."
        },
        {
            "category": "fish",
            "id": "fish_fish",
            "ticker": "FISH",
            "en": "Fish",
            "ru_legacy": "Рыба",
            "ru_canonical": "Рыба обыкновенная",
            "notes": "Платонический идеал рыбы."
        },
        {
            "category": "fish",
            "id": "fish_moon",
            "ticker": "MOON",
            "en": "Moonfish",
            "ru_legacy": "Лунная рыба",
            "ru_canonical": "Лунная рыба",
            "notes": "Сырье для производства химического оружия."
        },
        {
            "category": "fish",
            "id": "fish_psyk",
            "ticker": "PSYK",
            "en": "Psychofish",
            "ru_legacy": "Психорыба",
            "ru_canonical": "Психорыба",
            "notes": "Психоактивный биообразец."
        },
        {
            "category": "fish",
            "id": "fish_dos",
            "ticker": "DOS",
            "en": "DOSfish",
            "ru_legacy": "DOS-рыба",
            "ru_canonical": "DOS-рыба",
            "notes": "Древняя кибернетическая рыба с DOS-терминалом."
        },
        {
            "category": "fish",
            "id": "fish_sun",
            "ticker": "SUN",
            "en": "Sunfish",
            "ru_legacy": "Солнечная рыба",
            "ru_canonical": "Солнечная рыба",
            "notes": "Сверхбыстрая ослепляющая рыба."
        },
        {
            "category": "fish",
            "id": "fish_dark",
            "ticker": "DFSH",
            "en": "Darkfish",
            "ru_legacy": "Тёмная рыба",
            "ru_canonical": "Тёмная рыба",
            "notes": "Злокачественный нарциссический хищник."
        },
        {
            "category": "fish",
            "id": "fish_ice",
            "ticker": "ICE",
            "en": "Icefish",
            "ru_legacy": "Ледяная рыба",
            "ru_canonical": "Ледяная рыба",
            "notes": "Рыба экстремально низких температур."
        },
        {
            "category": "fish",
            "id": "fish_balls",
            "ticker": "BLLS",
            "en": "Ballsfish",
            "ru_legacy": "Шарорыба",
            "ru_canonical": "Шарорыба",
            "notes": "Гротескная сферическая рыба."
        }
    ]
}

def main():
    out_path = Path(__file__).resolve().parent / "glossary.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(GLOSSARY_DATA, f, indent=2, ensure_ascii=False)
    print(f"[+] Saved canonical glossary to {out_path} ({len(GLOSSARY_DATA['glossary'])} terms)")

if __name__ == "__main__":
    main()
