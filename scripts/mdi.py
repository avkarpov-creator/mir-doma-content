#!/usr/bin/env python3
"""mdi — Mir-Doma Index. Отвечает на вопросы о репозитории, не загружая статьи в контекст.

Статья проекта весит 15-50 КБ. Прочитать десяток ради проверки перелинковки —
100k+ токенов. Этот скрипт читает файлы на диске и печатает 5-20 строк.

Без внешних зависимостей. Python 3.8+.

  python3 scripts/mdi.py index                     пересобрать индекс
  python3 scripts/mdi.py state                     общая картина проекта
  python3 scripts/mdi.py find <запрос>             найти статьи по теме
  python3 scripts/mdi.py dupe <тема>               риск каннибализации
  python3 scripts/mdi.py in <слаг>                 кто ссылается на статью
  python3 scripts/mdi.py out <слаг>                куда ссылается статья
  python3 scripts/mdi.py orphans                   страницы без входящих ссылок
  python3 scripts/mdi.py linkplan <слаг> [Рубрика] кто должен сослаться
  python3 scripts/mdi.py toc <слаг>                оглавление статьи
  python3 scripts/mdi.py sec <слаг> <H2>           один раздел статьи
  python3 scripts/mdi.py check [слаг]              валидация + битые ссылки
  python3 scripts/mdi.py new <слаг> <Рубрика>      скелет frontmatter
"""
import json
import os
import pathlib
import re
import signal
import sys

# Чтобы `mdi.py ... | head` не сыпал трейсбеком.
try:
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
except (AttributeError, ValueError):
    pass

ROOT = pathlib.Path(__file__).resolve().parent.parent
ARTICLES = ROOT / "articles"
EXTERNAL_SLUGS_FILE = ROOT / "external-slugs.txt"


def load_external_slugs():
    if not EXTERNAL_SLUGS_FILE.exists():
        return set()
    slugs = set()
    for line in EXTERNAL_SLUGS_FILE.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            slugs.add(line)
    return slugs
INDEX_PATH = ROOT / ".mdi-index.json"
SITE = "mir-doma.pro"

SEO_TITLE_MAX = 60
SEO_DESC_MAX = 160
IMAGES_EXPECTED = 6

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

STOP = set("""и в во не что он на я с со как а то все она так его но да ты к у же вы за бы по
только ее мне было вот от меня еще нет о из ему теперь когда даже ну вдруг ли если уже или ни
быть был него до вас нибудь опять уж вам ведь там потом себя ничего ей может они тут где есть
надо ней для мы тебя их чем была сам чтоб без будто чего раз тоже себе под будет ж тогда кто
этот того потому этого какой совсем ним здесь этом один почти мой тем чтобы нее сейчас были
куда зачем всех никогда можно при наконец два об другой хоть после над больше тот через эти
нас про всего них какая много разве三 свою этой перед иногда лучше чуть том нельзя такой им
более всегда конечно всю между это своими руками дача даче даче дачи как сделать своей""".split())

# ---------------------------------------------------------------- парсинг


def parse_frontmatter(text):
    if not text.startswith("---"):
        return None, text
    end = text.find("\n---", 3)
    if end == -1:
        return None, text
    front, body = text[4:end], text[end + 4:]
    meta, current = {}, None
    for line in front.splitlines():
        if not line.strip():
            continue
        item = re.match(r"^\s*-\s+(.*)$", line)
        if item and current is not None:
            meta[current].append(item.group(1).strip().strip("\"'"))
            continue
        kv = re.match(r"^([A-Za-z0-9_\-]+)\s*:\s*(.*)$", line)
        if kv:
            key, val = kv.group(1), kv.group(2).strip()
            if val == "":
                meta[key] = []
                current = key
            else:
                meta[key] = val.strip("\"'")
                current = None
    return meta, body


def words(text):
    return re.findall(r"[А-Яа-яЁёA-Za-z0-9]+", text)


def tokens(text):
    return {w.lower() for w in words(text) if len(w) > 3 and w.lower() not in STOP}


def stems(text):
    """Грубый стемминг: обрезаем русские окончания, чтобы «веранда» = «веранде»."""
    out = set()
    for t in tokens(text):
        out.add(t[:-2] if len(t) > 6 else t[:-1] if len(t) > 4 else t)
    return out


def outlinks(body):
    found = re.findall(r"https?://(?:www\.)?" + re.escape(SITE) + r"/([a-z0-9\-]+)/?", body)
    return sorted(set(found))


def headings(body):
    out = []
    for i, line in enumerate(body.splitlines(), 1):
        m = re.match(r"^(#{2,3})\s+(.*)$", line)
        if m:
            title = re.sub(r"[^\wА-Яа-яЁё0-9 ,:%\-—«»()/]+", "", m.group(2)).strip()
            out.append({"level": len(m.group(1)), "text": title, "line": i})
    return out


# ---------------------------------------------------------------- индекс


def build_index():
    if not ARTICLES.exists():
        sys.exit("Нет папки articles/ — запусти из корня репозитория.")
    docs = {}
    for path in sorted(ARTICLES.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(text)
        meta = meta or {}
        slug = meta.get("slug") or path.stem
        tags = meta.get("tags") if isinstance(meta.get("tags"), list) else []
        docs[slug] = {
            "file": path.name,
            "title": meta.get("title", ""),
            "category": meta.get("category", ""),
            "tags": tags,
            "focus": meta.get("focus_keyword", ""),
            "seo_title": meta.get("seo_title", ""),
            "seo_desc": meta.get("seo_description", ""),
            "adopt": str(meta.get("adopt_existing", "")).lower() == "true",
            "status": meta.get("status", ""),
            "images_fm": len(meta.get("images", []) if isinstance(meta.get("images"), list) else []),
            "images_body": len(re.findall(r"!\[.*?\]\(.*?\)", body)),
            "words": len(words(body)),
            "kb": path.stat().st_size // 1024,
            "h": headings(body),
            "out": outlinks(body),
        }
    index = {"docs": docs}
    INDEX_PATH.write_text(json.dumps(index, ensure_ascii=False), encoding="utf-8")
    return index


def load():
    if not INDEX_PATH.exists():
        return build_index()
    try:
        return json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    except Exception:
        return build_index()


def incoming(docs):
    inc = {s: [] for s in docs}
    for slug, d in docs.items():
        for target in d["out"]:
            if target in inc and target != slug:
                inc[target].append(slug)
    return inc


def profile(d):
    return stems(" ".join([d["title"], d["focus"], " ".join(d["tags"]),
                           " ".join(h["text"] for h in d["h"])]))


# ---------------------------------------------------------------- команды


def cmd_index():
    idx = build_index()
    print(f"Индекс собран: {len(idx['docs'])} статей → {INDEX_PATH.name}")


def cmd_state():
    docs = load()["docs"]
    inc = incoming(docs)
    cats = {}
    for d in docs.values():
        cats[d["category"] or "?"] = cats.get(d["category"] or "?", 0) + 1
    orph = sorted(s for s in docs if not inc[s])
    print(f"Статей: {len(docs)} | рубрик: {len(cats)} | сирот: {len(orph)}")
    print("Рубрики (толстые → тонкие):")
    for cat, n in sorted(cats.items(), key=lambda x: (-x[1], x[0])):
        mark = "  ← тонкая" if n <= 3 else ""
        print(f"  {n:>3}  {cat}{mark}")
    if orph:
        print("Сироты (нет входящих ссылок, не индексируются):")
        print("  " + ", ".join(orph))


def cmd_find(query):
    docs = load()["docs"]
    q = stems(query)
    scored = []
    for slug, d in docs.items():
        score = len(q & profile(d))
        if score:
            scored.append((score, slug, d))
    scored.sort(key=lambda x: -x[0])
    if not scored:
        print("Ничего не найдено.")
        return
    for score, slug, d in scored[:10]:
        print(f"{score:>2}  {slug:<44} [{d['category']}]")


def cmd_dupe(topic):
    docs = load()["docs"]
    q = stems(topic)
    if not q:
        sys.exit("Слишком короткий запрос.")
    scored = []
    for slug, d in docs.items():
        p = profile(d)
        overlap = q & p
        if not overlap:
            continue
        ratio = len(overlap) / len(q)
        scored.append((ratio, len(overlap), slug, d, overlap))
    scored.sort(key=lambda x: -x[0])
    if not scored:
        print("OK — пересечений нет, тема свободна.")
        return
    top = scored[0]
    if top[0] >= 0.6:
        print("РИСК ДУБЛЯ — сформулируй, чем интенты различаются, или не бери тему.")
    elif top[0] >= 0.35:
        print("СМЕЖНАЯ ТЕМА — можно писать, но развести интенты и поставить перекрёстные ссылки.")
    else:
        print("OK — тема свободна, ближайшие соседи ниже.")
    for ratio, n, slug, d, overlap in scored[:5]:
        print(f"  {ratio:.0%}  {slug:<40} [{d['category']}]  общее: {', '.join(sorted(overlap)[:5])}")
    unique = q - set().union(*(profile(d) for _, _, _, d, _ in scored[:5]))
    if unique:
        print("Уникально в теме (это и есть дифференциатор интента): " +
              ", ".join(sorted(unique)))
    else:
        print("Уникальных слов в теме нет — почти наверняка дубль.")


def cmd_in(slug):
    docs = load()["docs"]
    if slug not in docs:
        sys.exit(f"Нет статьи {slug}")
    inc = incoming(docs)[slug]
    if not inc:
        print(f"{slug}: ВХОДЯЩИХ НЕТ — страница не будет проиндексирована. Ставь ссылки.")
        return
    print(f"{slug}: входящих {len(inc)}")
    for s in inc:
        print(f"  ← {s}")


def cmd_out(slug):
    docs = load()["docs"]
    if slug not in docs:
        sys.exit(f"Нет статьи {slug}")
    d = docs[slug]
    print(f"{slug}: исходящих {len(d['out'])}")
    for s in d["out"]:
        mark = "" if s in docs else "  ← БИТЫЙ СЛАГ"
        print(f"  → {s}{mark}")


def cmd_orphans():
    docs = load()["docs"]
    inc = incoming(docs)
    orph = sorted((s for s in docs if not inc[s]), key=lambda s: docs[s]["category"])
    if not orph:
        print("Сирот нет.")
        return
    print(f"Сирот: {len(orph)} (без входящих ссылок = мёртвые для индекса)")
    for s in orph:
        print(f"  {s:<44} [{docs[s]['category']}]")


def cmd_linkplan(slug, category=None, topic=None):
    docs = load()["docs"]
    if slug in docs:
        target, cat = profile(docs[slug]), docs[slug]["category"]
    else:
        cat = category or ""
        target = stems(topic or slug.replace("-", " "))
        print(f"(статьи {slug} ещё нет — считаю по " +
              ("теме" if topic else "слагу; для латинского слага передай тему "
                                   "третьим аргументом по-русски") + ")")
    already = {s for s, d in docs.items() if slug in d["out"]}
    cands = []
    for s, d in docs.items():
        if s == slug or s in already:
            continue
        score = len(target & profile(d))
        if d["category"] == cat and cat:
            score += 2
        if score >= 2:
            cands.append((score, s, d))
    cands.sort(key=lambda x: -x[0])
    if already:
        print(f"Уже ссылаются ({len(already)}): " + ", ".join(sorted(already)))
    if not cands:
        print("Кандидатов-доноров нет — тема стоит особняком, ищи ссылки вручную.")
        return
    print("Доноры (поставь контекстную ссылку по тексту, а не блоком в конце):")
    for score, s, d in cands[:8]:
        print(f"  {score:>2}  {s:<42} [{d['category']}]")


def cmd_toc(slug):
    docs = load()["docs"]
    if slug not in docs:
        sys.exit(f"Нет статьи {slug}")
    d = docs[slug]
    print(f"{d['title']}")
    print(f"[{d['category']}] {d['words']} слов, {d['kb']}k, "
          f"картинок {d['images_body']}/{d['images_fm']}, "
          f"исходящих {len(d['out'])}, adopt_existing={d['adopt']}")
    for h in d["h"]:
        print(f"  {'  ' * (h['level'] - 2)}{'##' if h['level'] == 2 else '###'} {h['text']}  :{h['line']}")


def cmd_sec(slug, needle):
    docs = load()["docs"]
    if slug not in docs:
        sys.exit(f"Нет статьи {slug}")
    path = ARTICLES / docs[slug]["file"]
    _, body = parse_frontmatter(path.read_text(encoding="utf-8"))
    lines = body.splitlines()
    start = None
    n = needle.lower()
    for i, line in enumerate(lines):
        if re.match(r"^#{2,3}\s", line) and n in line.lower():
            start = i
            level = len(line.split()[0])
            break
    if start is None:
        sys.exit(f"Раздел «{needle}» не найден. Смотри: mdi.py toc {slug}")
    end = len(lines)
    for j in range(start + 1, len(lines)):
        m = re.match(r"^(#{2,3})\s", lines[j])
        if m and len(m.group(1)) <= level:
            end = j
            break
    print("\n".join(lines[start:end]))


def cmd_check(slug=None):
    docs = load()["docs"]
    external = load_external_slugs()
    targets = [slug] if slug else list(docs)
    if slug and slug not in docs:
        sys.exit(f"Нет статьи {slug}")
    problems = []
    external_hits = 0
    for s in targets:
        d = docs[s]
        path = ARTICLES / d["file"]
        text = path.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(text)
        p = []
        if not d["title"]:
            p.append("нет title")
        if not d["category"]:
            p.append("нет category")
        elif d["category"] not in VALID_CATEGORIES:
            p.append(f"категория вне списка: {d['category']}")
        if len(d["seo_title"]) > SEO_TITLE_MAX:
            p.append(f"seo_title {len(d['seo_title'])} > {SEO_TITLE_MAX}")
        if len(d["seo_desc"]) > SEO_DESC_MAX:
            p.append(f"seo_description {len(d['seo_desc'])} > {SEO_DESC_MAX}")
        if not d["seo_title"]:
            p.append("нет seo_title")
        if not d["seo_desc"]:
            p.append("нет seo_description")
        if d["images_body"] < IMAGES_EXPECTED:
            p.append(f"картинок в теле {d['images_body']}, ожидается {IMAGES_EXPECTED}")
        if d["images_fm"] < IMAGES_EXPECTED:
            p.append(f"картинок в frontmatter {d['images_fm']}, ожидается {IMAGES_EXPECTED}")
        for m in re.finditer(r"!\[(.*?)\]\((.*?)\)", body):
            if not m.group(1).strip():
                p.append(f"картинка без alt: {m.group(2)}")
        for line in [d["title"], d["seo_title"], d["seo_desc"]]:
            for w in re.findall(r"[А-Яа-яЁё]+[A-Za-z]+|[A-Za-z]+[А-Яа-яЁё]+", line):
                p.append(f"смесь кириллицы и латиницы: {w}")
        broken = [t for t in d["out"] if t not in docs and t not in external]
        ext_used = [t for t in d["out"] if t not in docs and t in external]
        external_hits += len(ext_used)
        if broken:
            p.append("битые слаги: " + ", ".join(broken))
        if not d["out"]:
            p.append("нет исходящих ссылок")
        if p:
            problems.append((s, p))
    if not problems:
        print(f"OK — проверено {len(targets)}, замечаний нет.")
        if external_hits:
            print(f"внешних ссылок: {external_hits}")
        return
    for s, p in problems:
        print(f"{s}:")
        for x in p:
            print(f"  - {x}")
    print(f"\nС замечаниями: {len(problems)} из {len(targets)}")
    if external_hits:
        print(f"внешних ссылок: {external_hits}")
    sys.exit(1)


def cmd_new(slug, category):
    if category not in VALID_CATEGORIES:
        sys.exit(f"Рубрика «{category}» вне списка. Допустимые:\n  " +
                 "\n  ".join(sorted(VALID_CATEGORIES)))
    path = ARTICLES / f"{slug}.md"
    if path.exists():
        sys.exit(f"{path} уже существует — правь через Edit, не перезаписывай.")
    tmpl = f"""---
title: ""
slug: "{slug}"
seo_title: ""
seo_description: ""
focus_keyword: ""
category: "{category}"
tags:
  -
status: draft
images:
  - images/{slug}.jpg
  - images/{slug}-2.jpg
  - images/{slug}-3.jpg
  - images/{slug}-4.jpg
  - images/{slug}-5.jpg
  - images/{slug}-6.jpg
---
"""
    path.write_text(tmpl, encoding="utf-8")
    print(f"Создан {path} — заполняй поля. seo_title ≤{SEO_TITLE_MAX}, "
          f"seo_description ≤{SEO_DESC_MAX}.")
    print("Для правки уже опубликованной статьи добавь adopt_existing: true")


COMMANDS = {
    "index": (cmd_index, 0), "state": (cmd_state, 0), "find": (cmd_find, 1),
    "dupe": (cmd_dupe, 1), "in": (cmd_in, 1), "out": (cmd_out, 1),
    "orphans": (cmd_orphans, 0), "linkplan": (cmd_linkplan, 1),
    "toc": (cmd_toc, 1), "sec": (cmd_sec, 2), "check": (cmd_check, 0),
    "new": (cmd_new, 2),
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(__doc__)
        sys.exit(0 if len(sys.argv) < 2 else 1)
    fn, need = COMMANDS[sys.argv[1]]
    args = sys.argv[2:]
    if len(args) < need:
        sys.exit(f"Команде {sys.argv[1]} нужно аргументов: {need}")
    if sys.argv[1] in ("find", "dupe"):
        args = [" ".join(args)]
    fn(*args)


if __name__ == "__main__":
    main()
