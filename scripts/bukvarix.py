#!/usr/bin/env python3
"""
bukvarix — запасной источник фраз, когда Мутаген не отвечает.

ВАЖНОЕ ОГРАНИЧЕНИЕ: Букварикс даёт список фраз и частотность, но НЕ даёт
конкуренцию. Это метрика Мутагена, аналога нет. Значит порог --max-strong
здесь не работает, и решение «пробьёмся ли в топ» принять не на чем.

Используй как разведку: собрать поле кандидатов, отсеять мусор, дождаться
Мутагена и проверить конкуренцию у выживших. Публиковать статью по теме,
отобранной только Буквариксом, — ставка вслепую.

Частотности Букварикса обновляются реже вордстатовских, цифры считать
ориентиром, а не точным значением.

Ключ: BUKVARIX_API_KEY или .bukvarix.token в корне. По умолчанию `free`
(бесплатный, с ограничением строк в ответе).

  python3 scripts/bukvarix.py tails "утепление веранды" [--min=10] [--num=300]
  python3 scripts/bukvarix.py check                 доступен ли API
"""
import csv, io, json, os, re, signal, subprocess, sys, urllib.parse, urllib.request
from pathlib import Path

try:
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
except (AttributeError, ValueError):
    pass

API = "http://api.bukvarix.com/v1/keywords/"


def root() -> Path:
    try:
        return Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"],
                                            stderr=subprocess.DEVNULL, text=True).strip())
    except Exception:
        return Path.cwd()


ROOT = root()
CACHE = ROOT / ".cache" / "bukvarix"

# Интент-фильтр общий с Мутагеном — берём оттуда, чтобы правила не разъезжались.
def _mutagen():
    import importlib.util
    p = ROOT / "scripts" / "mutagen.py"
    if not p.exists():
        sys.exit("нет scripts/mutagen.py — интент-фильтр берётся оттуда")
    spec = importlib.util.spec_from_file_location("mtg", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def key() -> str:
    k = os.environ.get("BUKVARIX_API_KEY")
    if k:
        return k.strip()
    p = ROOT / ".bukvarix.token"
    if p.exists():
        return p.read_text().strip()
    return "free"


def call(phrase: str, num: int = 300, region: str = "rus"):
    params = {"q": phrase, "api_key": key(), "format": "csv",
              "num": str(num), "region": region}
    url = API + "?" + urllib.parse.urlencode(params, encoding="utf-8")
    req = urllib.request.Request(url, headers={"User-Agent": "mir-doma/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.read().decode("utf-8-sig", "replace")
    except Exception as e:
        sys.exit(f"Букварикс недоступен: {e}")


def parse(raw: str):
    """Колонки ищем по названиям — формат ответа может меняться."""
    if not raw.strip():
        return []
    delim = max([";", ",", "\t"], key=lambda d: raw[:2000].count(d))
    rows = list(csv.reader(io.StringIO(raw), delimiter=delim))
    if not rows:
        return []
    header = [h.strip().lower() for h in rows[0]]
    ki = fi = None
    for i, h in enumerate(header):
        if ki is None and any(w in h for w in ("keyword", "запрос", "фраза", "ключ")):
            ki = i
        if fi is None and any(w in h for w in ("freq", "частот", "wordstat", "ws")):
            fi = i
    if ki is None:
        # шапки нет — считаем первый столбец фразой, второй числом
        ki, fi, rows = 0, (1 if len(rows[0]) > 1 else None), [[]] + rows
    out = []
    for r in rows[1:]:
        if not r or ki >= len(r):
            continue
        kw = r[ki].strip()
        if not kw:
            continue
        f = 0
        if fi is not None and fi < len(r):
            m = re.search(r"\d+", r[fi].replace(" ", "").replace("\xa0", ""))
            f = int(m.group()) if m else 0
        out.append((kw, f))
    return out


def cmd_check(_):
    raw = call("дача", num=5)
    rows = parse(raw)
    if rows:
        print(f"Букварикс отвечает, ключ {'free' if key()=='free' else 'платный'}. "
              f"Пробный запрос вернул {len(rows)} строк.")
        print("Первые строки:", ", ".join(f"{k} ({f})" for k, f in rows[:3]))
    else:
        print("Ответ пустой или формат не распознан. Сырой ответ, первые 300 символов:")
        print(raw[:300])


def cmd_tails(args):
    minf, num, kws = 10, 300, []
    for a in args:
        if a.startswith("--min="):
            minf = int(a.split("=")[1])
        elif a.startswith("--num="):
            num = int(a.split("=")[1])
        else:
            kws.append(a)
    phrase = " ".join(kws)
    if not phrase:
        sys.exit('укажи фразу: bukvarix.py tails "утепление веранды"')

    CACHE.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^a-zа-яё0-9_-]+", "_", phrase.lower())[:110]
    f = CACHE / f"{safe}_{minf}_{num}.json"
    if f.exists():
        rows = json.loads(f.read_text(encoding="utf-8"))
    else:
        rows = parse(call(phrase, num=num))
        if rows:
            f.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")

    m = _mutagen()
    arts = m.known_slugs()
    # Региональные запросы: локальную выдачу мы не выигрываем, а читатель
    # из другого города на такой странице бесполезен.
    REG = ["минск", "москв", "спб", "петербург", "новгород", "екатеринбург",
           "казан", "новосибирск", "самар", "ростов", "краснодар", "воронеж",
           "челябинск", "омск", "уф", "пермь", "волгоград", "красноярск",
           "саратов", "тюмен", "тольятт", "ижевск", "барнаул", "ульяновск",
           "иркутск", "хабаровск", "ярославл", "владивосток", "томск", "кемеров",
           "рязан", "астрахан", "пенз", "липецк", "тул", "киров", "чебоксар",
           "калининград", "брянск", "курск", "иванов", "тверь", "белгород",
           "сочи", "владимир", "калуг", "смоленск", "курган", "орёл", "орел",
           "могилев", "гомел", "витебск", "брест", "алмат", "астан", "киев",
           "харьков", "одесс", "область", "районе", " рядом", "недорого рядом"]
    stat = {"всего": len(rows), "мало частотности": 0, "диагностика": 0,
            "нейтр": 0, "регион": 0, "дубль": 0}
    good = []
    for kw, fr in rows:
        if fr < minf:
            stat["мало частотности"] += 1
            continue
        low = kw.lower()
        if any(r in low for r in REG):
            stat["регион"] += 1
            continue
        it = m.intent(kw)
        if it != "действие":
            stat[it if it in stat else "нейтр"] += 1
            continue
        ov = m.overlaps(kw, arts)
        if ov.startswith("дубль"):
            stat["дубль"] += 1
            continue
        good.append((fr, kw, ov))
    good.sort(key=lambda x: -x[0])
    print(f"# «{phrase}»: фраз {stat['всего']} → кандидатов {len(good)}")
    print("# отсеяно: " + ", ".join(f"{k} {v}" for k, v in stat.items()
                                    if k != "всего" and v))
    for fr, kw, ov in good[:30]:
        print(f"{fr}\t{kw}\t{ov}")
    print("\n# Данные: Букварикс. КОНКУРЕНЦИЯ НЕ ПРОВЕРЕНА — Букварикс её не даёт.")
    print("# Прежде чем писать, прогони выживших через Мутаген:")
    print('#   python3 scripts/mutagen.py strong "<фраза>"')
    print("# Частотности Букварикса обновляются реже вордстатовских — это ориентир.")


CMDS = {"tails": cmd_tails, "check": cmd_check}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in CMDS:
        print(__doc__)
        sys.exit(2)
    CMDS[sys.argv[1]](sys.argv[2:])
