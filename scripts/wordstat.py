#!/usr/bin/env python3
"""
wordstat — частотность и похожие фразы из официального Wordstat API Яндекса
(в составе Yandex Cloud Search API).

Даёт спрос, но НЕ конкуренцию — шкала 1-25 есть только у Мутагена.
Порядок источников в проекте:
    спрос      → Wordstat (свежий первоисточник), запасной — Букварикс
    проходимость → только Мутаген, замены нет

Настройка (один раз):
  1. Yandex Cloud → каталог → сервисный аккаунт
  2. Роль сервисному аккаунту: search-api.webSearch.user
  3. API-ключ для него с областью действия yc.search-api.execute
  4. Положить в корень репозитория:
       .yandex.token   — API-ключ
       .yandex.folder  — идентификатор каталога
     Оба обязательно в .gitignore.

  python3 scripts/wordstat.py check                     проверить доступ
  python3 scripts/wordstat.py top "утепление веранды"   похожие фразы + частотность
  python3 scripts/wordstat.py freq "фраза1" "фраза2"    частотность списка
  python3 scripts/wordstat.py tails "фраза" [--min=10]  как у mutagen/bukvarix
"""
import json, os, re, signal, subprocess, sys, time, urllib.error, urllib.request
from pathlib import Path

try:
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
except (AttributeError, ValueError):
    pass

BASE = "https://searchapi.api.cloud.yandex.net/v2/wordstat"
REGION_RU = "225"          # вся Россия; Москва — 213, справочник: getRegionsTree


def root() -> Path:
    try:
        return Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"],
                                            stderr=subprocess.DEVNULL, text=True).strip())
    except Exception:
        return Path.cwd()


ROOT = root()
CACHE = ROOT / ".cache" / "wordstat"


def _read(env: str, fname: str, what: str) -> str:
    v = os.environ.get(env)
    if v:
        return v.strip()
    p = ROOT / fname
    if p.exists():
        return p.read_text().strip()
    sys.exit(f"нет {what}: положи в {fname} или переменную {env} "
             f"(файл обязательно в .gitignore)")


def api_key():
    return _read("YANDEX_API_KEY", ".yandex.token", "API-ключа")


def folder():
    return _read("YANDEX_FOLDER_ID", ".yandex.folder", "идентификатора каталога")


def call(method: str, body: dict, retries: int = 3):
    body = dict(body)
    body["folderId"] = folder()
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    last = None
    # Регистр метода в REST-путях у Яндекса неоднороден — пробуем оба варианта.
    for name in (method, method[0].lower() + method[1:], method.lower()):
        url = f"{BASE}/{name}"
        req = urllib.request.Request(url, data=data, headers={
            "Authorization": f"Api-key {api_key()}",
            "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:300]
            if e.code == 404:
                last = RuntimeError(f"404 на {url}")
                continue
            if e.code in (401, 403):
                sys.exit(f"доступ отклонён ({e.code}). Проверь: у сервисного аккаунта "
                         f"роль search-api.webSearch.user, у ключа область действия "
                         f"yc.search-api.execute.\n{detail}")
            sys.exit(f"HTTP {e.code}: {detail}")
        except Exception as e:
            # Канал до Яндекса прогревается: первое соединение после паузы
            # часто рвётся на TLS. Повторяем, прежде чем сдаваться.
            last = e
            for attempt in range(retries - 1):
                time.sleep(3 * (attempt + 1))
                try:
                    with urllib.request.urlopen(req, timeout=90) as r:
                        return json.loads(r.read().decode("utf-8"))
                except Exception as e2:
                    last = e2
    sys.exit(f"метод {method} не отвечает: {last}")


def num(v):
    try:
        return int(str(v).strip())
    except Exception:
        return 0


def get_top(phrase: str, n: int = 100, region: str = REGION_RU):
    CACHE.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^a-zа-яё0-9_-]+", "_", phrase.lower())[:110]
    f = CACHE / f"top_{safe}_{n}_{region}.json"
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8"))
    res = call("getTop", {"phrase": phrase, "numPhrases": n,
                          "regions": [region], "devices": ["DEVICE_ALL"]})
    if "results" in res or "associations" in res:
        f.write_text(json.dumps(res, ensure_ascii=False), encoding="utf-8")
    return res


def rows_of(res):
    """results — фразы с этим ключом, associations — что ещё искали по теме."""
    out = []
    for key in ("results", "associations"):
        for it in res.get(key) or []:
            p = (it.get("phrase") or "").strip()
            if p:
                out.append((p, num(it.get("count")), key))
    return out



def monday_range(weeks: int = 4):
    """dynamics требует: начало — понедельник, конец — воскресенье."""
    from datetime import date, timedelta
    today = date.today()
    last_sunday = today - timedelta(days=today.weekday() + 1)
    first_monday = last_sunday - timedelta(days=7 * weeks - 1)
    return (first_monday.isoformat() + "T00:00:00Z",
            last_sunday.isoformat() + "T00:00:00Z")


def freq_of(phrase: str, weeks: int = 4, region: str = REGION_RU):
    """Средняя недельная частотность фразы. Метод dynamics — рабочий,
    в отличие от getTop, который у Яндекса пока отдаёт 404."""
    CACHE.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^a-zа-яё0-9_-]+", "_", phrase.lower())[:110]
    f = CACHE / f"dyn_{safe}_{weeks}_{region}.json"
    if f.exists():
        res = json.loads(f.read_text(encoding="utf-8"))
    else:
        fr, to = monday_range(weeks)
        res = call("dynamics", {"phrase": phrase, "period": "PERIOD_WEEKLY",
                                "fromDate": fr, "toDate": to,
                                "regions": [region], "devices": ["DEVICE_ALL"]})
        if "results" in res:
            f.write_text(json.dumps(res, ensure_ascii=False), encoding="utf-8")
    rows = res.get("results") or []
    if not rows:
        return 0, []
    counts = [num(r.get("count")) for r in rows]
    return sum(counts) // len(counts), [(r.get("date", "")[:10], num(r.get("count")))
                                        for r in rows]

def cmd_check(_):
    avg, rows = freq_of("дача", weeks=3)
    if not rows:
        sys.exit("Wordstat ответил, но данных нет — проверь права и биллинг.")
    print(f"Wordstat отвечает. «дача»: в среднем {avg} показов в неделю.")
    for d, c in rows:
        print(f"  {d}  {c}")
    print("# Метод dynamics. getTop у Яндекса пока отдаёт 404 — расширение фраз "
          "берём у Мутагена или Букварикса.")


def cmd_top(args):
    sys.exit("Метод getTop у Яндекса сейчас отдаёт 404 — расширение списка фраз\n"
             "через Wordstat недоступно. Работает только частотность:\n"
             '  python3 scripts/wordstat.py freq "фраза1" "фраза2"\n'
             "Список фраз собирай Мутагеном или Буквариксом:\n"
             '  python3 scripts/mutagen.py tails "<фраза>"\n'
             '  python3 scripts/bukvarix.py tails "<фраза>"')


def cmd_freq(args):
    weeks, phrases = 4, []
    for a in args:
        if a.startswith("--weeks="):
            weeks = int(a.split("=")[1])
        else:
            phrases.append(a)
    if not phrases:
        sys.exit('укажи фразы: wordstat.py freq "фраза1" "фраза2"')
    for phrase in phrases:
        avg, _ = freq_of(phrase, weeks=weeks)
        print(f"{avg:>9}\t{phrase}")
    print(f"# Средняя частотность за {weeks} нед. Данные: Яндекс Вордстат.")
    print("# Конкуренция не проверена — это делает только Мутаген.")


def cmd_tails(args):
    cmd_top(args)


CMDS = {"check": cmd_check, "top": cmd_top, "freq": cmd_freq, "tails": cmd_tails}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in CMDS:
        print(__doc__)
        sys.exit(2)
    CMDS[sys.argv[1]](sys.argv[2:])
