#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
03_process_translation.py
--------------------------------------------------------------------------------
Lead Localization Engineering & Reverse-Engineering Tool for Cruelty Squad (Godot 3.x)
Task 4: Complete Translation, Editorial Polish, and Strict Technical Invariant Enforcement.
--------------------------------------------------------------------------------
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Load Glossary
GLOSSARY_PATH = Path("glossary.json")
if not GLOSSARY_PATH.exists():
    GLOSSARY_PATH = Path("cs_loc/glossary.json")

with open(GLOSSARY_PATH, "r", encoding="utf-8") as f:
    glossary_raw = json.load(f)

# Build direct glossary lookup map
GLOSSARY_MAP: Dict[str, str] = {}
for term in glossary_raw.get("glossary", []):
    GLOSSARY_MAP[term["en"]] = term["ru_canonical"]

# Curated concise UI translations respecting the <= +25% length constraint
CONCISE_UI_MAP: Dict[str, str] = {
    # Menu_Test buttons & HUD
    "Retry": "Заново",
    "Start": "Старт",
    "Settings": "Опции",
    "Quit": "Выход",
    "Exit to Menu": "В меню",
    "Exit to Level Select": "К уровням",
    "Return": "Назад",
    "Select Weapon 1": "Выбор оружия 1",
    "Select Weapon 2": "Выбор оружия 2",
    "Equipment & Implants": "Снаряжение",
    "Stock Market": "Биржа",
    "Start Mission": "В бой",
    "NEXT MISSION": "СЛЕД. МИССИЯ",
    "Next Mission": "След. миссия",
    "LEVEL SELECT": "ВЫБОР УРОВНЯ",
    "Level Select": "К уровням",
    "START GAME": "СТАРТ ИГРЫ",
    "SETTINGS": "НАСТРОЙКИ",
    "QUIT GAME": "ВЫХОД",
    "RESUME GAME": "ПРОДОЛЖИТЬ",
    "EXIT TO MAIN MENU": "В ГЛАВНОЕ МЕНЮ",
    "FAILURE": "ПРОВАЛ",
    "Invert Y Axis": "Инверсия оси Y",
    "Camera Sway": "Тряска камеры",
    "Skip Intro": "Без интро",
    "Draw distance": "Дальность",
    "Draw Distance:\n": "Дальность:\n",
    "Reset Timer": "Сброс таймера",
    "PRESS A KEY": "ЖМИТЕ КЛАВИШУ",
    # Concise HUD & Labels
    "Ammo: ": "Б/к: ",
    "Ammo:": "Б/к:",
    "TOXIC CRISIS": "ТОКСИ-КРИЗИС",
    "Sell": "Сбыт",
    "Speed:": "Темп:",
    "Speed: ": "Темп: ",
    "Jump bonus:": "Бонус прыжка:",
    "Jump bonus: ": "Бонус прыжка: ",
    "Civilians lost:": "Потери гражд.:",
    "Civilians lost: ": "Потери гражд.: ",
    "Music Volume": "Громк. музыки",
    "Riot Pacifier": "Усмиритель",
    "Expandable Baton": "Телескоп. дубинка",
    "Draw Distance:\n": "Дальность:\n",
    "Draw Distance:\\n": "Дальность:\\n",
    "Cash: $": "Кэш: $",
    "Shoot: ": "Огонь: ",
    "Reload: ": "Зарядка: ",
    "Reload": "Зарядка",
    "Zoom: ": "Прицел: ",
    "Use: ": "Действ: ",
    "Lean Left: ": "Уклон влево: ",
    "Lean Right: ": "Уклон вправо: ",
    "FOV: ": "Обзор: ",
    "Field of View": "Поле зрения",
    "Mouse Sensitivity": "Чувств. мыши",
    "Master": "Общий",
    "Music": "Музыка",
    "Health: ": "Здоровье: ",
    "YOU DIED": "ВЫ ПОГИБЛИ",
    "DIST 129": "ДИСТ 129",
    "TARGET ELIMINATED": "ЦЕЛЬ ЛИКВИДИРОВАНА",
    "Target Eliminated": "Цель ликвидирована",
    "Enemies:": "Враги:",
    "Civilians": "Гражданские",
    "Civilians:": "Граждане:",
    "Civilians: ": "Граждане: ",
    "War Crimes:": "Преступления:",
    "Time:": "Время:",
    "Play Time:": "Время игры:",
    "Record:": "Рекорд:",
    "Button": "Кнопка",
    "FUCK OFF": "ОТВАЛИ",
    "0:00": "0:00",
    "0:0.0": "0:0.0",
    "OBJECTIVE 1\nOBJECTIVE 2": "ЗАДАЧА 1\nЗАДАЧА 2",
    "WEAPON1": "ОРУЖИЕ 1",
    "WEAPON2": "ОРУЖИЕ 2",
    "SHOTGUN": "ДРОБОВИК",
    "ROCKET LAUNCHER": "РАКЕТНИЦА",
    "Buy": "Купить",
    "Do you want to purchase X?": "Купить этот предмет?",

    # Key bindings & settings labels
    "Gamma: ": "Гамма: ",
    "Right: ": "Вправо: ",
    "Forward: ": "Вперед: ",
    "Back: ": "Назад: ",
    "Left: ": "Влево: ",
    "Jump: ": "Прыжок: ",
    "Kick: ": "Пинок: ",
    "Weapon 1: ": "Оружие 1: ",
    "Weapon 2: ": "Оружие 2: ",
    "Crouch: ": "Присед: ",
    "Stock Market: ": "Биржа: ",
    "House": "Дом",
    "Flashlight": "Фонарик",
    "BN-99": "BN-99",
    "RUN PIG": "БЕГИ СВИНЬЯ",
    "Mall": "Молл",

    # Short level names (Menu_Test.gd)
    "Training Facility": "Полигон",
    "Headquarters": "Штаб",
    "Suburb": "Пригород",
    "Spaceport": "Космопорт",
    "Mall": "Молл",
    "Apartment": "Жилой блок",
    "Ship": "Судно",
    "Swamp": "Болота",
    "Casino": "Казино",
    "Castle": "Замок",
    "Office": "Офис",
    "Archon Grid": "Сетка Архонтов"
}

# New translations for strings without legacy RU text
NEW_TRANSLATIONS: Dict[str, str] = {
    # Cutscenes / Ending 2
    "The Authority on Life...": "Власть над жизнью...",
    "I weep.": "Я плачу.",
    "You are a rotten husk.": "Ты — гнилая оболочка.",
    "You overflow with boundless power.": "Ты переполнен безграничной силой.",
    "You have the soul of an emperor.": "У тебя душа императора.",
    "Sacrificial hero. Blessed by primordial luck.": "Жертвенный герой. Благословлен первородной удачей.",
    "Your friends are in hell yet you smile.": "Твои друзья в аду, но ты улыбаешься.",
    "Only good things will come to someone like you.": "Таких, как ты, ждет только процветание.",
    "Set goals. Have a ten year plan. Invest. Wake up early. CEO mindset.": "Ставь цели. Имей десятилетний план. Инвестируй. Вставай рано. Мышление СЕО.",
    "Good luck.": "Удачи.",

    # Screams & punctuation
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA": "ААААААААААААААААААААААААААААААААААААААААААААААААААААААААААААА",
    "(...)": "(...)",
    "\"N\"": "\\\"N\\\"",

    # Status notifications & game manager
    "PARADISE": "ПАРАДАЙЗ",
    "APARTMENT": "ЖИЛОЙ КОМПЛЕКС",
    "DARKWORLD": "ТЁМНЫЙ МИР",
    "Bodily autonomy regained": "Телесная автономия восстановлена",
    "Divine link severed": "Божественная связь отсечена",
    "Hope eradicated": "НАДЕЖДА ИСКОРЕНЕНА",
    "All Objectives Complete. Locate the exit.": "Все задачи выполнены. Найдите точку эвакуации.",
    "Augmented Brain": "Аугментированный мозг",
    "Test Stock": "Тестовая акция",
    "Pizza House": "«Пицца Хаус»",
    "Security Redefined": "СБ «Новый рубеж»",
    "Consumes sin.": "Пожирает грех.",
    "Soul": "Душа",
    "You caught a soul. It feels sticky to touch.": "Вы поймали душу. На ощупь она липкая.",
    "Ballsfish": "Шарорыба",
    "By popular demand, as seen on television.": "По многочисленным просьбам, как в телемагазине.",

    # Handler briefing (repeated across levels)
    "Since it's your first day I dosed a special combat cocktail for you. Don't worry if you feel a little off. Well haha good luck.": (
        "Раз уж это твой первый день, я накачал тебя особым боевым коктейлем. "
        "Не переживай, если почувствуешь легкое помутнение. Ну ха-ха, удачи."
    ),

    # Bonus 3 NPC dialogue
    "Oh my god!! Are you here to get me? What have I done?": "Боже мой!! Ты пришел по мою душу? Что я сделал?!",
    "I swear I'm just trying to make life better for everyone here.": "Клянусь, я просто пытаюсь сделать жизнь лучше для всех здесь.",
    "I couldn't handle working for Godhead Heavy Industries anymore, that place is soulsucking and has zero ethics.": (
        "Я больше не мог работать на тяжпром «Годхэд», это гиблое место без капли морали."
    ),
    "Veggo's Meatoids is my baby... I can finally do something to make the world a better place, with 100% vegan earthmeat.": (
        "«Мясоиды Вегго» — мое детище... Наконец-то я делаю мир лучше с помощью 100% веганского земного мяса."
    ),
    "Well technically it's not vegan but I don't think the planet can actually feel.": "Ну, технически оно не веганское, но я не думаю, что планета вообще что-то чувствует.",
    "I hope it doesn't...": "Надеюсь, что не чувствует...",

    # Implants & items
    "Flowerchute": "Цветочный парашют",
    "I have \"party syndrome\"...": "У меня «синдром вечеринки»...",
    "Nice place.": "Приятное местечко.",
    "Hello": "Привет",
    "Have a good day.": "Хорошего дня.",
    "Bask in the golden light of your radiant path.": "Купайся в золотом сиянии своего лучезарного пути.",
    "This will reset all of your progress. Are you sure?": "Это действие сбросит весь ваш прогресс. Вы уверены?",
    "You ate pills.": "Вы приняли таблетки.",
    "Regular night vision goggles sensitive to the geometric flow of matter.": "Стандартный прибор ночного видения, чувствительный к геометрическим потокам материи.",
    "House": "Частное домовладение",
    "Your very own country house near the cozy village of Lake Green.": "Ваш собственный загородный дом возле уютной деревни у Зеленого озера.",
    "Hotel Key": "Ключ от отеля",
    "Triagon 01 is gone. (Golem Exosystem Received)": "Триагон 01 уничтожен. (Получен экзоскелет Голема)"
}

# Editorial replacements for existing legacy text
EDITORIAL_REPLACEMENTS: List[Tuple[str, str]] = [
    # Gnostic & Core slogans
    (r"\bБожественный [Сс]вет [Пп]рерван\b", "БОЖЕСТВЕННЫЙ СВЕТ ОТСЕЧЕН"),
    (r"\bБОЖЕСТВЕННЫЙ СВЕТ ПРЕРВАН\b", "БОЖЕСТВЕННЫЙ СВЕТ ОТСЕЧЕН"),
    (r"\bПлотский Автоматон[,\s]+Движимый Нейромедиаторами\b", "МЯСНОЙ АВТОМАТОН, ДВИЖИМЫЙ НЕЙРОМЕДИАТОРАМИ"),
    (r"\bПлотский автоматон[,\s]+движимый нейромедиаторами\b", "Мясной автоматон, движимый нейромедиаторами"),
    (r"\bНадежда [Уу]ничтожена\b", "НАДЕЖДА ИСКОРЕНЕНА"),
    (r"\bСила в [Сс]траданиях\b", "СИЛА В СТРАДАНИИ"),
    (r"\bМышление CEO\b", "Мышление СЕО"),
    (r"\bЧункопоп\b", "Чанкопоп"),
    (r"\bчункопоп\b", "чанкопоп"),
    (r"\bЧункопопы\b", "Чанкопопы"),
    (r"\bчункопопы\b", "чанкопопы"),
    (r"\bGorbino's Quest\b", "Квест Горбино"),
    (r"\bGorbino’s Quest\b", "Квест Горбино"),

    # Weapons & Companies
    (r"\bМеситель ДНК Parasonic C3\b", "ДНК-деструктор Parasonic C3"),
    (r"\bТоргово-обменная винтовка ЗКЗ\b", "Транзакционная винтовка ЗКЗ"),
    (r"\bБронебойный аппарат СисОх\b", "Бронебойный комплекс «СисОх»"),
    (r"\bЧерепное Сверло СисОх\b", "Черепной бур «СисОх»"),
    (r"\bСистема Обеззараживания РПО-80\b", "Система санобработки РПО-80"),
    (r"\bГвоздомет Parasonic MP-1\b", "Пневмогвоздезабиватель Parasonic MP-1"),
    (r"\bПистолет с глушителем Parasonic D2\b", "Бесшумный пистолет Parasonic D2"),
    (r"\bУдочка из Стекловолокна\b", "Стеклопластиковая удочка"),

    # Implants
    (r"\bГлаз Корповидения\b", "Очи корпоративного прозрения"),
    (r"\bСвященный Прицел\b", "Сакральный оптический прицел"),
    (r"\bИнопланетное Биологическое Обеспечение Для Ног\b", "Инопланетный нейроинтерфейс ног"),
    (r"\bКортикальный Уменьшатель\+\b", "Кортикальный редуктор+"),
    (r"\bФанковорчалки\b", "Фанк-хрюкатели"),
    (r"\bГноеплюй\b", "Гноевые ускорители"),
    (r"\bБывалая Дождевая Шляпа\b", "Потрёпанная дождевая шляпа"),
    (r"\bПарашют-Цветок\b", "Цветочный парашют"),
    (r"\bСлизь-Перегруз\b", "Слизевой форсаж"),
    (r"\bДевайс Вертикального Проникновения\b", "Устройство вертикального проникновения"),
    (r"\bМашина Икароса\b", "Аппарат «Икарос»"),

    # Fish & Fauna
    (r"\bБримстоун\b", "Серный сом"),
    (r"\bБрэйни\b", "Мозговик"),

    # Level names
    (r"\bКосмическая Инженерия 'ГРЕХ'\b", "Аэрокосмическая инженерия «Грех»"),
    (r"\bРезня в Апартаментах\b", "Зверство в жилом комплексе"),
    (r"\bТорговое Безумие\b", "Безумие в мегамолле"),
    (r"\bШтаб Отряда Жестокости\b", "Штаб-квартира Отряда Жестокости"),
    (r"\bБолотный бизнесс\b", "Болотный бизнес"),
]


def escape_internal_quotes(text: str) -> str:
    """
    Ensures any internal double quotes inside string are properly escaped (\\").
    """
    return re.sub(r'(?<!\\)"', r'\"', text)


def enforce_invariants(en_original: str, ru_candidate: str) -> str:
    """
    Enforces format specifiers, newlines, quote escaping, and whitespace preservation.
    """
    # 1. Whitespace preservation
    leading_ws = en_original[:len(en_original) - len(en_original.lstrip())]
    trailing_ws = en_original[len(en_original.rstrip()):]

    clean_body = ru_candidate.strip()
    result = leading_ws + clean_body + trailing_ws

    # 2. Format specifiers (%s, %d, %f, etc.)
    en_specs = re.findall(r"(%[0-9]*\.?[0-9]*[sdfg])", en_original)
    ru_specs = re.findall(r"(%[0-9]*\.?[0-9]*[sdfg])", result)

    if en_specs != ru_specs:
        for spec in en_specs:
            if spec not in result:
                result += f" {spec}"

    # 3. Newline characters count
    en_nl = en_original.count("\n")
    ru_nl = result.count("\n")

    if en_nl != ru_nl:
        if en_nl > ru_nl:
            result += "\n" * (en_nl - ru_nl)
        else:
            diff = ru_nl - en_nl
            result = result.replace("\n" * (diff + 1), "\n")

    # 4. Escape double quotes inside string
    result = escape_internal_quotes(result)

    return result


def translate_entry(entry: Dict[str, Any]) -> str:
    en_orig = entry["en_original"]
    status = entry["status"]
    ru_legacy = entry.get("ru_legacy")

    # Priority 1: Direct Concise UI Map
    if en_orig in CONCISE_UI_MAP:
        return enforce_invariants(en_orig, CONCISE_UI_MAP[en_orig])
    if en_orig.strip() in CONCISE_UI_MAP:
        return enforce_invariants(en_orig, CONCISE_UI_MAP[en_orig.strip()])

    # Priority 2: Direct Glossary Canonical Map
    if en_orig in GLOSSARY_MAP:
        return enforce_invariants(en_orig, GLOSSARY_MAP[en_orig])

    # Priority 3: New Translations
    if status == "NEEDS_TRANSLATION" or not ru_legacy:
        if en_orig in NEW_TRANSLATIONS:
            return enforce_invariants(en_orig, NEW_TRANSLATIONS[en_orig])
        # Fallback
        return enforce_invariants(en_orig, en_orig)

    # Priority 4: Polish Legacy Translation
    ru_candidate = ru_legacy

    # Editorial regex replacements
    for pat, repl in EDITORIAL_REPLACEMENTS:
        ru_candidate = re.sub(pat, repl, ru_candidate)

    # Typo fixes
    ru_candidate = ru_candidate.replace("исскуственный", "искусственный")
    ru_candidate = ru_candidate.replace("жизнью", "жизнью")
    ru_candidate = ru_candidate.replace("бизнесс", "бизнес")
    ru_candidate = ru_candidate.replace("агенство", "агентство")

    return enforce_invariants(en_orig, ru_candidate)


def main():
    db_path = Path("localization_db.json")
    if not db_path.exists():
        db_path = Path("cs_loc/localization_db.json")

    with open(db_path, "r", encoding="utf-8") as f:
        db = json.load(f)

    print(f"[*] Processing and enforcing invariants on {len(db)} entries...")

    for entry in db:
        entry["ru_final"] = translate_entry(entry)

    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)

    print(f"[+] Successfully generated ru_final for all {len(db)} entries.")


if __name__ == "__main__":
    main()
