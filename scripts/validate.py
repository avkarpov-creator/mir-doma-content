#!/usr/bin/env python3
"""Валидатор статей. Проверяет frontmatter перед мёржем в main.

Без внешних зависимостей — работает на голом Python 3.
Падает с кодом 1, если хоть одна статья нарушает правила.
"""
import sys
import re
import pathlib

ARTICLES_DIR = pathlib.Path("articles")
REQUIRED = ["title", "category"]
SEO_TITLE_MAX = 60
SEO_DESC_MAX = 160

# Категории сайта — поле category должно совпадать с одной из них.
VALID_CATEGORIES = {
    "Овощи и зелень", "Плодовые деревья и кустарники",
    "Борьба с вредителями и болезнями", "Удобрения и подкормки",
    "Цветы и декоративные растения", "Ландшафтный дизайн",
    "Водоемы и системы полива", "Газоны и дорожки",
    "Заборы и ограждения", "Хозяйственные постройки",
    "Интерьер дачи", "Системы отопления", "Утепление и энергосбережение",
    "Электрика и сантехника", "Мебель своими руками",
    "Строительство на участке", "Кровля и фасады", "Ремонт дачного дома",
    "Внутренняя отделка", "Инструменты и материалы",
    "Консервация", "Заморозка", "Хранение урожая",
    "Погреба и кладовые", "Рецепты из своего урожая",
}


def parse_frontmatter(text):
    """Очень простой разбор frontmatter: key: value и списки."""
    if not text.startswith("---"):
        return None, text
    end = text.find("\n---", 3)
    if end == -1:
        return None, text
    front = text[4:end]
    body = text[end + 4:]
    meta = {}
    current_list = None
    for line in front.splitlines():
        if not line.strip():
            continue
        m_item = re.match(r"^\s*-\s+(.*)$", line)
        if m_item and current_list is not None:
            meta[current_list].append(m_item.group(1).strip().strip('"\''))
            continue
        m_kv = re.match(r"^([A-Za-z0-9_\-]+)\s*:\s*(.*)$", line)
        if m_kv:
            key, val = m_kv.group(1), m_kv.group(2).strip()
            if val == "":
                meta[key] = []
                current_list = key
            else:
                meta[key] = val.strip('"\'')
                current_list = None
    return meta, body


def validate_file(path):
    errors = []
    text = path.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(text)

    if meta is None:
        return [f"{path}: нет frontmatter (файл должен начинаться с ---)"]

    for field in REQUIRED:
        if not meta.get(field):
            errors.append(f"{path}: нет обязательного поля '{field}'")

    if meta.get("seo_title") and len(meta["seo_title"]) > SEO_TITLE_MAX:
        errors.append(f"{path}: seo_title длиннее {SEO_TITLE_MAX} ({len(meta['seo_title'])})")

    if meta.get("seo_description") and len(meta["seo_description"]) > SEO_DESC_MAX:
        errors.append(f"{path}: seo_description длиннее {SEO_DESC_MAX} ({len(meta['seo_description'])})")

    cat = meta.get("category")
    if cat and cat not in VALID_CATEGORIES:
        errors.append(f"{path}: категория '{cat}' не из списка сайта")

    # Картинки без alt-текста.
    for m in re.finditer(r"!\[(.*?)\]\((.*?)\)", body):
        if not m.group(1).strip():
            errors.append(f"{path}: картинка без alt-текста ({m.group(2)})")

    return errors


def main():
    if not ARTICLES_DIR.exists():
        print("Папка articles/ не найдена.")
        return 0
    all_errors = []
    files = sorted(ARTICLES_DIR.glob("*.md"))
    for path in files:
        all_errors.extend(validate_file(path))

    if all_errors:
        print("Найдены проблемы:")
        for e in all_errors:
            print("  -", e)
        return 1

    print(f"Проверено файлов: {len(files)}. Всё в порядке.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
