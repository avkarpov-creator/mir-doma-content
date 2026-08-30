#!/usr/bin/env python3
"""
mutagen — сбор тем через API Мутагена (mutagen.ru) под mir-doma.pro.

Принцип: API возвращает сотни строк JSON, в контекст попадают 10-20 отобранных.
Всё кэшируется на диск — повторный запрос того же ключа не тратит ни деньги, ни токены.

Токен: переменная окружения MUTAGEN_TOKEN или файл .mutagen.token в корне репозитория
(обязательно в .gitignore — в репозиторий он попасть не должен).

Данные получены из Мутагена (mutagen.ru).
"""
import sys, os, re, json, time, signal, urllib.request, urllib.error
from pathlib import Path

try:
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
except (AttributeError, ValueError):
    pass

API = "http://api.mutagen.ru/json/{token}/{method}/"


def root() -> Path:
    import subprocess
    try:
        return Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"],
                                            stderr=subprocess.DEVNULL, text=True).strip())
    except Exception:
        return Path.cwd()


ROOT = root()
CACHE = ROOT / ".cache" / "mutagen"
DOMAIN = os.environ.get("MD_DOMAIN", "mir-doma.pro")
REGION = os.environ.get("MD_REGION", "yandex_msk")

# --- интент-фильтр (правила проекта) ---
ACTION = ["как ", "чем ", "сколько", "какой", "какие", "что лучше", "своими руками",
          "пошагов", "расчет", "расчёт", "когда ", "нужно ли", "можно ли", "чтобы ",
          "инструкц", "схема", "размер", "норма", "пропорц", "выбрать", "сделать"]
DIAG = ["фото", "как выглядит", "выглядят", "симптом", "признак", "почему появля",
        "что такое", "виды ", "описание", "картинк", "значение"]

# слова, которые есть почти в каждом заголовке и не различают темы
GENERIC = {"свои", "своим", "рукам", "даче", "дачны", "зиму", "зимой", "дома", "домаш",
           "лучше", "прави", "быстр", "прост", "нужно", "можно", "делат", "сдела"}


def token() -> str:
    t = os.environ.get("MUTAGEN_TOKEN")
    if t:
        return t.strip()
    for p in (ROOT / ".mutagen.token", Path.home() / ".mutagen_token"):
        if p.exists():
            return p.read_text().strip()
    sys.exit("нет токена: положи в MUTAGEN_TOKEN или в .mutagen.token (и в .gitignore)")


def call(method: str, param=None, retries: int = 3):
    url = API.format(token=token(), method=method)
    data = json.dumps(param or {}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data,
                                 headers={"Content-Type": "application/json"})
    last = None
    for i in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            last = e
            time.sleep(2 * (i + 1))
    sys.exit(f"API недоступен: {last}")


def cached(key: str, producer):
    CACHE.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^a-zа-яё0-9_-]+", "_", key.lower())[:120]
    f = CACHE / f"{safe}.json"
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8"))
    val = producer()
    f.write_text(json.dumps(val, ensure_ascii=False), encoding="utf-8")
    return val


def rows(res):
    """Отчёты Мега-инструмента приходят списком или словарём — приводим к списку."""
    if isinstance(res, dict):
        if "error" in res:
            sys.exit(f"Мутаген: {res['error']}")
        for k in ("data", "result", "rows"):
            if k in res and isinstance(res[k], list):
                return res[k]
        return list(res.values()) if all(isinstance(v, dict) for v in res.values()) else []
    return res if isinstance(res, list) else []


def intent(kw: str) -> str:
    k = kw.lower()
    if any(d in k for d in DIAG):
        return "диагностика"
    if any(a in k for a in ACTION):
        return "действие"
    return "нейтр"


def known_slugs():
    """Слаги и заголовки существующих статей из индекса mdi.py."""
    idx = ROOT / ".mdi-index.json"
    if not idx.exists():
        print("# нет .mdi-index.json — сначала: python3 scripts/mdi.py index",
              file=sys.stderr)
        return []
    try:
        docs = json.loads(idx.read_text(encoding="utf-8"))["docs"]
        return [(slug, d.get("title", "")) for slug, d in docs.items()]
    except Exception as e:
        print(f"# индекс не читается ({e}) — пересобери: mdi.py index", file=sys.stderr)
        return []


def overlaps(kw: str, arts) -> str:
    words = {w[:5] for w in re.findall(r"[a-zа-яё0-9]+", kw.lower()) if len(w) > 3} - GENERIC
    best, name = 0, ""
    for slug, title in arts:
        tw = {w[:5] for w in re.findall(r"[a-zа-яё0-9]+",
                                        (title + " " + slug.replace("-", " ")).lower())
              if len(w) > 3} - GENERIC
        ov = len(words & tw)
        if ov > best:
            best, name = ov, slug
    if best >= 3:
        return f"дубль? {name}"
    if best == 2:
        return f"смежно {name}"
    return ""


# ---------------- команды ----------------

def cmd_balance(a):
    print(call("mutagen.balance"))


def cmd_strong(a):
    """Конкуренция по фразам (шкала Мутагена 1-25). Платно, поэтому кэшируется."""
    arts = known_slugs()
    for kw in a:
        def fetch(kw=kw):
            r = call("mutagen.check_key.new", {"key": kw})
            if "task_id" not in r:
                r = call("mutagen.check_key.new", {"keys": kw})
            tid = r.get("task_id")
            if not tid:
                return {"error": r}
            for _ in range(30):
                g = call("mutagen.check_key.get", {"task_id": tid})
                if g.get("status") == "completed":
                    return g
                time.sleep(4)
            return {"error": "timeout"}
        d = cached("strong_" + kw, fetch)
        if "error" in d:
            print(f"{kw}\tОШИБКА {d['error']}")
            continue
        s, ws = d.get("strong"), d.get("wordstat")
        verdict = "БРАТЬ" if isinstance(s, int) and s <= 12 else "тяжело"
        print(f"{s}\t{ws}\t{verdict}\t{intent(kw)}\t{kw}\t{overlaps(kw, arts)}")
    print("# конкуренция | вордстат | вердикт | интент | фраза | пересечение. Данные: Мутаген")


def cmd_tails(a):
    """Хвосты по фразе — основной источник тем. Один вызов = десятки кандидатов."""
    if not a:
        sys.exit("укажи фразу")
    limit, minf, kws = 400, 30, []
    for x in a:
        if x.startswith("--min="):
            minf = int(x.split("=")[1])
        elif x.startswith("--limit="):
            limit = int(x.split("=")[1])
        else:
            kws.append(x)
    phrase = " ".join(kws)
    param = {
        "region": "yandex_ru",
        "keyword": phrase,
        "report": "report_keyword_tailings",
        "filter": [
            {"column": "world_wsqso", "filter_type": "gr_or_eq", "val": minf},
            {"column": "words", "filter_type": "less_or_eq", "val": 7},
        ],
        "sort": "-world_wsqso",
        "limit": limit,
    }
    res = cached(f"tails_{phrase}_{minf}_{limit}", lambda: call("mutagen.serp.report", param))
    out = rows(res)
    arts = known_slugs()
    good = []
    for r in out:
        kw = r.get("keyword", "")
        it = intent(kw)
        if it == "диагностика":
            continue
        good.append((int(r.get("world_wsqso") or 0), kw, it, overlaps(kw, arts)))
    good.sort(key=lambda x: -x[0])
    print(f"# «{phrase}»: {len(out)} хвостов, после отсева диагностики {len(good)}. Данные: Мутаген")
    for f, kw, it, ov in good[:25]:
        print(f"{f}\t{it}\t{kw}\t{ov}")
    print("# частотность | интент | фраза | пересечение с существующими")


def cmd_lsi(a):
    """Связанные фразы — для наполнения H2 внутри уже выбранной темы."""
    phrase = " ".join(a)
    param = {"region": "yandex_ru", "keyword": phrase,
             "report": "report_keyword_expansion", "sort": "-similarity", "limit": 60}
    res = cached(f"lsi_{phrase}", lambda: call("mutagen.serp.report", param))
    for r in rows(res)[:20]:
        print(f"{r.get('similarity','')}\t{r.get('world_wsqso','')}\t{r.get('keyword','')}")
    print("# похожесть | частотность | фраза. Данные: Мутаген")


def cmd_gaps(a):
    """Упущенные ключи страницы — что есть у конкурентов и нет у нас."""
    if not a:
        sys.exit("укажи URL страницы")
    page = a[0]
    param = {"region": REGION, "page": page,
             "report": "report_page_recommended_keywords",
             "sort": "-region_wsqso", "limit": 200}
    res = cached(f"gaps_{page}", lambda: call("mutagen.serp.report", param))
    arts = known_slugs()
    n = 0
    for r in rows(res):
        kw = r.get("keyword", "")
        if intent(kw) == "диагностика":
            continue
        print(f"{r.get('region_wsqso','')}\t{intent(kw)}\t{kw}\t{overlaps(kw, arts)}")
        n += 1
        if n >= 20:
            break
    print(f"# упущенные ключи для {page}. Данные: Мутаген")


def cmd_watch(a):
    """Регресс-детектор: какие ключи домена упали и потерялись."""
    for rep, label in (("report_keywords_organic_down", "УПАЛ"),
                       ("report_keywords_organic_lost", "ПОТЕРЯН")):
        param = {"region": REGION, "domain": DOMAIN, "report": rep,
                 "sort": "-region_wsqso", "limit": 30}
        res = call("mutagen.serp.report", param)   # без кэша: нужен свежий срез
        for r in rows(res)[:10]:
            print(f"{label}\t{r.get('position','')}\t{r.get('region_wsqso','')}\t"
                  f"{r.get('keyword','')}\t{r.get('page','')}")
    print("# сигнал каннибализации: две наши страницы по одному ключу чередуются. Данные: Мутаген")


def cmd_topics(a):
    """Конвейер: хвосты → отсев диагностики → проверка дублей → конкуренция топ-N."""
    if not a:
        sys.exit("укажи опорную фразу кластера")
    n, kws = 8, []
    for x in a:
        if x.startswith("--check="):
            n = int(x.split("=")[1])
        else:
            kws.append(x)
    phrase = " ".join(kws)
    param = {"region": "yandex_ru", "keyword": phrase,
             "report": "report_keyword_tailings",
             "filter": [{"column": "world_wsqso", "filter_type": "gr_or_eq", "val": 30},
                        {"column": "words", "filter_type": "less_or_eq", "val": 7}],
             "sort": "-world_wsqso", "limit": 400}
    res = cached(f"tails_{phrase}_30_400", lambda: call("mutagen.serp.report", param))
    arts = known_slugs()
    cand = []
    for r in rows(res):
        kw = r.get("keyword", "")
        if intent(kw) != "действие":
            continue
        ov = overlaps(kw, arts)
        if ov.startswith("дубль"):
            continue
        cand.append((int(r.get("world_wsqso") or 0), kw, ov))
    cand.sort(key=lambda x: -x[0])
    print(f"# «{phrase}»: {len(cand)} кандидатов с действенным интентом, "
          f"проверяю конкуренцию у топ-{n}")
    cmd_strong([kw for _, kw, _ in cand[:n]])
    if len(cand) > n:
        print(f"# ещё {len(cand)-n} кандидатов без проверки конкуренции:")
        for f, kw, ov in cand[n:n + 12]:
            print(f"{f}\t{kw}\t{ov}")


CMDS = {k[4:]: v for k, v in list(globals().items()) if k.startswith("cmd_")}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in CMDS:
        print("команды:", " ".join(sorted(CMDS)))
        sys.exit(2)
    CMDS[sys.argv[1]](sys.argv[2:])
