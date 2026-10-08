#!/usr/bin/env python3
"""
live — прямые запросы к Метрике, Вебмастеру, Search Console и GA4.

Печатает короткие сводки (20–30 строк), а не сырые таблицы: в контекст
попадают выводы. Доступ только на чтение. Без внешних зависимостей:
стандартная библиотека Python + openssl для подписи запроса Google.

Секреты — в ~/.config/mir-doma/secrets.env (вне репозитория, chmod 600):

    YANDEX_OAUTH_TOKEN=...        # права metrika:read и webmaster (чтение)
    METRIKA_COUNTER=...           # номер счётчика Метрики
    WEBMASTER_HOST_ID=https:mir-doma.pro:443
    GOOGLE_SA_KEY=/путь/к/ключу-сервисного-аккаунта.json
    GSC_SITE=sc-domain:mir-doma.pro     # или https://mir-doma.pro/
    GA4_PROPERTY=...              # числовой ID ресурса GA4

Команды:
    python3 scripts/live.py check                 какие источники настроены
    python3 scripts/live.py traffic [дней]        Метрика: визиты по дням и источники
    python3 scripts/live.py landing [дней]        Метрика: страницы входа
    python3 scripts/live.py gsc [дней]            GSC: страницы, веб и картинки отдельно
    python3 scripts/live.py gsc-queries <слаг> [дней]   GSC: запросы одной страницы
    python3 scripts/live.py inspect <слаг> [...]   GSC URL Inspection: в индексе ли, канонический, последний обход
    python3 scripts/live.py gindex                все опубликованные через URL Inspection (20+ мин) → seo/live/google-index.json
    python3 scripts/live.py grow [дней]           GSC: позиции 5–20 с показами — что дописать
    python3 scripts/live.py ywm                   Вебмастер: индекс и популярные запросы
    python3 scripts/live.py ga4 [дней]            GA4: сеансы по страницам
    python3 scripts/live.py week                  неделя к неделе: рост, падение, индекс (для брифа)

Значения секретов скрипт никогда не печатает.
"""
import base64, json, os, subprocess, sys, tempfile, time, urllib.parse, urllib.request
from datetime import date, timedelta
from pathlib import Path

SECRETS = Path(os.environ.get("MD_SECRETS", Path.home() / ".config" / "mir-doma" / "secrets.env"))
SITE = "https://mir-doma.pro/"


def load_env():
    env = {}
    if SECRETS.exists():
        for line in SECRETS.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    for k in list(env):
        env[k] = os.environ.get(k, env[k])
    return env


ENV = load_env()


def need(*keys):
    miss = [k for k in keys if not ENV.get(k)]
    if miss:
        sys.exit(f"Не настроено: {', '.join(miss)}. Заполните {SECRETS} (см. справку: live.py -h).")


def http(url, data=None, headers=None, method=None):
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "ignore")[:300]
        sys.exit(f"HTTP {e.code} от {urllib.parse.urlparse(url).netloc}: {body}")


# ---------- Яндекс ----------

def metrika(params):
    need("YANDEX_OAUTH_TOKEN", "METRIKA_COUNTER")
    q = {"ids": ENV["METRIKA_COUNTER"], "accuracy": "full", "limit": 100000}
    q.update(params)
    url = "https://api-metrika.yandex.net/stat/v1/data?" + urllib.parse.urlencode(q, doseq=True)
    return http(url, headers={"Authorization": "OAuth " + ENV["YANDEX_OAUTH_TOKEN"]})


def cmd_traffic(days="7"):
    d = int(days)
    r = metrika({"metrics": "ym:s:visits,ym:s:users,ym:s:pageDepth,ym:s:bounceRate",
                 "dimensions": "ym:s:date", "date1": f"{d}daysAgo", "date2": "today", "sort": "ym:s:date"})
    print(f"Метрика, {d} дн.: дата | визиты | посетители | глубина | отказы %")
    for row in r["data"]:
        m = row["metrics"]
        print(f"  {row['dimensions'][0]['name']} | {int(m[0])} | {int(m[1])} | {m[2]:.2f} | {m[3]:.0f}")
    t = r["totals"]
    print(f"  ИТОГО | {int(t[0])} | {int(t[1])} | {t[2]:.2f} | {t[3]:.0f}")
    s = metrika({"metrics": "ym:s:visits", "dimensions": "ym:s:lastTrafficSource",
                 "date1": f"{d}daysAgo", "date2": "today", "sort": "-ym:s:visits"})
    print("Источники:", ", ".join(f"{x['dimensions'][0]['name']} {int(x['metrics'][0])}" for x in s["data"]))
    e = metrika({"metrics": "ym:s:visits", "dimensions": "ym:s:searchEngine",
                 "date1": f"{d}daysAgo", "date2": "today", "sort": "-ym:s:visits"})
    if e["data"]:
        print("Поисковики:", ", ".join(f"{x['dimensions'][0]['name']} {int(x['metrics'][0])}" for x in e["data"][:5]))


def cmd_landing(days="7"):
    d = int(days)
    r = metrika({"metrics": "ym:s:visits,ym:s:pageDepth,ym:s:avgVisitDurationSeconds",
                 "dimensions": "ym:s:startURLPath", "date1": f"{d}daysAgo", "date2": "today",
                 "sort": "-ym:s:visits", "limit": 25})
    print(f"Страницы входа, {d} дн.: визиты | глубина | сек | путь")
    for row in r["data"]:
        m = row["metrics"]
        print(f"  {int(m[0]):>4} | {m[1]:.2f} | {int(m[2]):>4} | {row['dimensions'][0]['name']}")


def ywm(path):
    need("YANDEX_OAUTH_TOKEN")
    h = {"Authorization": "OAuth " + ENV["YANDEX_OAUTH_TOKEN"]}
    uid = http("https://api.webmaster.yandex.net/v4/user", headers=h)["user_id"]
    host = urllib.parse.quote(ENV.get("WEBMASTER_HOST_ID", "https:mir-doma.pro:443"), safe="")
    return http(f"https://api.webmaster.yandex.net/v4/user/{uid}/hosts/{host}{path}", headers=h)


def cmd_ywm(_=None):
    s = ywm("/summary")
    print("Вебмастер: страниц в поиске", s.get("searchable_pages_count"), "| исключено", s.get("excluded_pages_count"),
          "| ИКС", s.get("sqi"), "| проблем", s.get("site_problems"))
    q = ywm("/search-queries/popular?order_by=TOTAL_SHOWS&query_indicator=TOTAL_SHOWS"
            "&query_indicator=TOTAL_CLICKS&query_indicator=AVG_SHOW_POSITION")
    print("Популярные запросы (показы | клики | позиция):")
    for x in q.get("queries", [])[:20]:
        i = x.get("indicators", {})
        print(f"  {int(i.get('TOTAL_SHOWS', 0)):>4} | {int(i.get('TOTAL_CLICKS', 0)):>3} | "
              f"{i.get('AVG_SHOW_POSITION', 0):.1f} | {x.get('query_text')}")


# ---------- Google ----------

def google_token(scope):
    need("GOOGLE_SA_KEY")
    key = json.loads(Path(ENV["GOOGLE_SA_KEY"]).read_text(encoding="utf-8"))
    b64 = lambda b: base64.urlsafe_b64encode(b).rstrip(b"=")
    now = int(time.time())
    head = b64(json.dumps({"alg": "RS256", "typ": "JWT"}).encode())
    claim = b64(json.dumps({"iss": key["client_email"], "scope": scope,
                            "aud": "https://oauth2.googleapis.com/token", "iat": now, "exp": now + 3600}).encode())
    msg = head + b"." + claim
    with tempfile.TemporaryDirectory() as td:
        pem = Path(td) / "k.pem"
        pem.write_text(key["private_key"], encoding="utf-8")
        os.chmod(pem, 0o600)
        sig = subprocess.run(["openssl", "dgst", "-sha256", "-sign", str(pem)],
                             input=msg, capture_output=True, check=True).stdout
    jwt = msg + b"." + b64(sig)
    body = urllib.parse.urlencode({"grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                                   "assertion": jwt.decode()}).encode()
    return http("https://oauth2.googleapis.com/token", data=body,
                headers={"Content-Type": "application/x-www-form-urlencoded"})["access_token"]


def gsc(body):
    need("GSC_SITE")
    tok = google_token("https://www.googleapis.com/auth/webmasters.readonly")
    site = urllib.parse.quote(ENV["GSC_SITE"], safe="")
    return http(f"https://www.googleapis.com/webmasters/v3/sites/{site}/searchAnalytics/query",
                data=json.dumps(body).encode(), headers={"Authorization": "Bearer " + tok,
                                                         "Content-Type": "application/json"}).get("rows", [])


def period(days):
    end = date.today() - timedelta(days=2)  # данные GSC отстают на 2 дня
    return str(end - timedelta(days=int(days) - 1)), str(end)


def slug_of(url):
    p = urllib.parse.urlparse(url).path.strip("/")
    return p or "/"


def cmd_gsc(days="28"):
    a, b = period(days)
    for typ in ("web", "image"):
        raw = gsc({"startDate": a, "endDate": b, "dimensions": ["page"], "type": typ, "rowLimit": 25000})
        agg = {}
        for r in raw:
            u = r["keys"][0].split("#")[0]
            g = agg.setdefault(u, {"keys": [u], "impressions": 0, "clicks": 0, "_p": 0.0})
            g["impressions"] += r["impressions"]; g["clicks"] += r["clicks"]; g["_p"] += r["position"] * r["impressions"]
        rows = []
        for g in agg.values():
            g["position"] = g["_p"] / g["impressions"] if g["impressions"] else 0
            g["ctr"] = g["clicks"] / g["impressions"] if g["impressions"] else 0
            rows.append(g)
        rows.sort(key=lambda r: -r["impressions"])
        imp = sum(r["impressions"] for r in rows); clk = sum(r["clicks"] for r in rows)
        print(f"GSC {typ} {a}…{b}: страниц {len(rows)}, показов {int(imp)}, кликов {int(clk)}")
        for r in rows[:15]:
            print(f"  {int(r['impressions']):>5} | {int(r['clicks']):>3} | CTR {r['ctr']*100:4.1f} | поз {r['position']:5.1f} | {slug_of(r['keys'][0])}")


def cmd_gsc_queries(slug=None, days="28"):
    if not slug:
        sys.exit("Укажите слаг: live.py gsc-queries <слаг> [дней]")
    a, b = period(days)
    rows = gsc({"startDate": a, "endDate": b, "dimensions": ["query"], "type": "web", "rowLimit": 200,
                "dimensionFilterGroups": [{"filters": [{"dimension": "page", "operator": "contains",
                                                        "expression": f"/{slug}/"}]}]})
    rows.sort(key=lambda r: -r["impressions"])
    print(f"Запросы страницы {slug}, {a}…{b} (показы | клики | позиция):")
    for r in rows[:30]:
        print(f"  {int(r['impressions']):>4} | {int(r['clicks']):>3} | {r['position']:5.1f} | {r['keys'][0]}")


def inspect_url(tok, slug):
    url = f"https://mir-doma.pro/{slug}/"
    r = http("https://searchconsole.googleapis.com/v1/urlInspection/index:inspect",
             data=json.dumps({"inspectionUrl": url, "siteUrl": ENV["GSC_SITE"]}).encode(),
             headers={"Authorization": "Bearer " + tok, "Content-Type": "application/json"})
    return r.get("inspectionResult", {}).get("indexStatusResult", {})


def cmd_inspect(*slugs):
    """Состояние страницы в индексе Google — когда страница пропала из выдачи."""
    if not slugs:
        sys.exit("Укажите слаг: live.py inspect <слаг> [...]")
    need("GSC_SITE")
    tok = google_token("https://www.googleapis.com/auth/webmasters.readonly")
    for slug in slugs:
        x = inspect_url(tok, slug)
        print(f"{slug}: {x.get('verdict')} | {x.get('coverageState')}")
        print(f"  обход {x.get('lastCrawlTime', '—')} | робот {x.get('crawledAs', '—')} | "
              f"fetch {x.get('pageFetchState', '—')} | robots {x.get('robotsTxtState', '—')}")
        gc, uc = x.get("googleCanonical"), x.get("userCanonical")
        if gc and gc != uc:
            print(f"  ВНИМАНИЕ: Google выбрал канонический {gc} (наш {uc})")
        refs = x.get("referringUrls") or []
        print(f"  ссылаются (известные Google): {len(refs)}" + (f" — {', '.join(slug_of(u) for u in refs[:5])}" if refs else ""))


GINDEX = Path(__file__).resolve().parent.parent / "seo" / "live" / "google-index.json"


def cmd_gindex(_=None):
    """Все опубликованные записи через URL Inspection: что в индексе Google. ~5 с на URL, 200+ URL — 20+ минут.
    Снимок по слагам — seo/live/google-index.json, итог дописывается в snapshots.jsonl."""
    need("GSC_SITE")
    slugs, page = [], 1
    while True:
        try:
            d = http(f"https://mir-doma.pro/wp-json/wp/v2/posts?per_page=100&page={page}&_fields=slug,date")
        except SystemExit:
            break
        if not d:
            break
        slugs += [(x["slug"], x["date"][:10]) for x in d]
        page += 1
    tok, t0 = google_token("https://www.googleapis.com/auth/webmasters.readonly"), time.time()
    out = {}
    for i, (s, dt) in enumerate(slugs, 1):
        if time.time() - t0 > 3000:  # токен живёт час
            tok, t0 = google_token("https://www.googleapis.com/auth/webmasters.readonly"), time.time()
        for attempt in range(3):
            try:
                x = inspect_url(tok, s)
                out[s] = {"date": dt, "cov": x.get("coverageState"), "crawl": x.get("lastCrawlTime", "")[:10],
                          "gcanon": x.get("googleCanonical")}
                break
            except (SystemExit, Exception) as e:  # сеть на WSL иногда отваливается — повторяем
                out[s] = {"date": dt, "cov": "ERR " + str(e)[:60]}
                time.sleep(5)
        if i % 25 == 0:
            print(f"  …{i}/{len(slugs)}", file=sys.stderr)
    GINDEX.parent.mkdir(parents=True, exist_ok=True)
    GINDEX.write_text(json.dumps(out, ensure_ascii=False, indent=0), encoding="utf-8")
    grp = lambda c: ("indexed" if c.startswith("Submitted") or c == "Indexed, not submitted in sitemap"
                     else "unknown" if "unknown" in c else "crawled_not_indexed" if "not indexed" in c else "other")
    cnt = {}
    for v in out.values():
        k = grp(v["cov"] or "")
        cnt[k] = cnt.get(k, 0) + 1
    print(f"Google, {len(out)} опубликованных: " + " | ".join(f"{k} {v}" for k, v in sorted(cnt.items())))
    with SNAP.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"date": str(date.today()), **{"g_" + k: v for k, v in cnt.items()}}) + "\n")


def cmd_grow(days="28"):
    a, b = period(days)
    rows = gsc({"startDate": a, "endDate": b, "dimensions": ["page", "query"], "type": "web", "rowLimit": 25000})
    # якорные URL (#раздел) Google считает отдельными страницами — складываем по статье
    agg = {}
    for r in rows:
        k = (slug_of(r["keys"][0].split("#")[0]), r["keys"][1])
        g = agg.setdefault(k, [0, 0.0, 0])
        g[0] += r["impressions"]; g[1] += r["position"] * r["impressions"]; g[2] += r["clicks"]
    pick = [(k, v[0], v[1] / v[0], v[2]) for k, v in agg.items() if v[0] >= 5 and 5 <= v[1] / v[0] <= 20]
    pick.sort(key=lambda x: -x[1])
    print(f"Позиции 5–20 с показами ≥5, {a}…{b} — кандидаты на доработку (показы | клики | позиция):")
    for (slug, q), imp, pos, clk in pick[:25]:
        print(f"  {int(imp):>4} | {int(clk):>2} | поз {pos:5.1f} | {slug} | {q}")


def cmd_ga4(days="7"):
    need("GA4_PROPERTY")
    tok = google_token("https://www.googleapis.com/auth/analytics.readonly")
    body = {"dateRanges": [{"startDate": f"{int(days)}daysAgo", "endDate": "today"}],
            "dimensions": [{"name": "pagePath"}],
            "metrics": [{"name": "sessions"}, {"name": "engagementRate"}, {"name": "averageSessionDuration"}],
            "orderBys": [{"metric": {"metricName": "sessions"}, "desc": True}], "limit": 25}
    r = http(f"https://analyticsdata.googleapis.com/v1beta/properties/{ENV['GA4_PROPERTY']}:runReport",
             data=json.dumps(body).encode(), headers={"Authorization": "Bearer " + tok,
                                                      "Content-Type": "application/json"})
    print(f"GA4, {days} дн.: сеансы | вовлечённость % | сек | путь")
    for row in r.get("rows", []):
        m = [x["value"] for x in row["metricValues"]]
        print(f"  {int(m[0]):>4} | {float(m[1])*100:4.0f} | {float(m[2]):5.0f} | {row['dimensionValues'][0]['value']}")


def cmd_check(_=None):
    print("Файл секретов:", SECRETS, "— есть" if SECRETS.exists() else "— НЕТ")
    for k in ["YANDEX_OAUTH_TOKEN", "METRIKA_COUNTER", "WEBMASTER_HOST_ID", "GOOGLE_SA_KEY", "GSC_SITE", "GA4_PROPERTY"]:
        v = ENV.get(k)
        ok = bool(v) and (k != "GOOGLE_SA_KEY" or Path(v).exists())
        print(f"  {k:<20} {'задано' if ok else 'нет'}")


# ---------- Неделя к неделе ----------

SNAP = Path(__file__).resolve().parent.parent / "seo" / "live" / "snapshots.jsonl"


def metrika_period(a, b, dims):
    return metrika({"metrics": "ym:s:visits,ym:s:pageDepth,ym:s:bounceRate", "dimensions": dims,
                    "date1": a, "date2": b, "sort": "-ym:s:visits", "limit": 50})


def gsc_pages(a, b, typ):
    agg = {}
    for r in gsc({"startDate": a, "endDate": b, "dimensions": ["page"], "type": typ, "rowLimit": 25000}):
        k = slug_of(r["keys"][0].split("#")[0])
        g = agg.setdefault(k, [0, 0, 0.0])
        g[0] += r["impressions"]; g[1] += r["clicks"]; g[2] += r["position"] * r["impressions"]
    return {k: (v[0], v[1], v[2] / v[0] if v[0] else 0) for k, v in agg.items()}


def gsc_queries(a, b):
    out = {}
    for r in gsc({"startDate": a, "endDate": b, "dimensions": ["query"], "type": "web", "rowLimit": 25000}):
        out[r["keys"][0]] = (r["impressions"], r["clicks"], r["position"])
    return out


def cmd_week(_=None):
    """Последние 7 дней против предыдущих 7 — окна не пересекаются."""
    t = date.today()
    y1, y0 = str(t - timedelta(days=7)), str(t - timedelta(days=1))
    p1, p0 = str(t - timedelta(days=14)), str(t - timedelta(days=8))
    pct = lambda a, b: ("+" if a >= b else "") + (f"{(a-b)/b*100:.0f}%" if b else "новое")
    print(f"НЕДЕЛЯ {y1}…{y0} против {p1}…{p0}")
    # Метрика
    cur, prev = metrika_period(y1, y0, "ym:s:lastTrafficSource"), metrika_period(p1, p0, "ym:s:lastTrafficSource")
    tc, tp = cur["totals"], prev["totals"]
    print(f"Метрика: визиты {int(tc[0])} (было {int(tp[0])}, {pct(tc[0], tp[0])}), глубина {tc[1]:.2f} (было {tp[1]:.2f}), отказы {tc[2]:.0f}% (было {tp[2]:.0f}%)")
    pv = {x["dimensions"][0]["name"]: x["metrics"][0] for x in prev["data"]}
    print("  источники:", "; ".join(f"{x['dimensions'][0]['name']} {int(x['metrics'][0])} (было {int(pv.get(x['dimensions'][0]['name'], 0))})" for x in cur["data"]))
    ce, pe = metrika_period(y1, y0, "ym:s:searchEngineRoot"), metrika_period(p1, p0, "ym:s:searchEngineRoot")
    pev = {x["dimensions"][0]["name"]: x["metrics"][0] for x in pe["data"]}
    print("  поисковики:", "; ".join(f"{x['dimensions'][0]['name']} {int(x['metrics'][0])} (было {int(pev.get(x['dimensions'][0]['name'], 0))})" for x in ce["data"][:4]))
    # GSC: данные отстают на 2 дня
    g1, g0 = str(t - timedelta(days=9)), str(t - timedelta(days=3))
    h1, h0 = str(t - timedelta(days=16)), str(t - timedelta(days=10))
    for typ in ("web", "image"):
        c, p = gsc_pages(g1, g0, typ), gsc_pages(h1, h0, typ)
        ci, pi = sum(v[0] for v in c.values()), sum(v[0] for v in p.values())
        cc, pc = sum(v[1] for v in c.values()), sum(v[1] for v in p.values())
        print(f"GSC {typ} {g1}…{g0}: показы {int(ci)} (было {int(pi)}, {pct(ci, pi)}), клики {int(cc)} (было {int(pc)})")
        if typ == "web":
            keys = set(c) | set(p)
            d = sorted(((c.get(k, (0, 0, 0))[0] - p.get(k, (0, 0, 0))[0], k) for k in keys))
            print("  выросли:", "; ".join(f"{k} +{int(x)} (поз {c.get(k,(0,0,0))[2]:.1f})" for x, k in reversed(d[-6:]) if x > 0) or "—")
            def fell(k, x):
                if k not in c or not c[k][0]:
                    return f"{k} {int(x)} (выпала из выдачи, была поз {p[k][2]:.1f})"
                return f"{k} {int(x)} (поз {c[k][2]:.1f}, было {p.get(k,(0,0,0))[2]:.1f})"
            print("  упали:", "; ".join(fell(k, x) for x, k in d[:6] if x < 0) or "—")
            new = [k for k in c if k not in p and c[k][0] >= 3]
            if new: print("  новые в выдаче:", ", ".join(new[:10]))
    cq, pq = gsc_queries(g1, g0), gsc_queries(h1, h0)
    ups = sorted(((pq[q][2] - cq[q][2], q) for q in cq if q in pq and cq[q][0] >= 5), reverse=True)
    print("  запросы поднялись:", "; ".join(f"{q} {pq[q][2]:.1f}→{cq[q][2]:.1f}" for x, q in ups[:5] if x >= 1) or "—")
    print("  запросы опустились:", "; ".join(f"{q} {pq[q][2]:.1f}→{cq[q][2]:.1f}" for x, q in ups[::-1][:5] if x <= -1) or "—")
    # Вебмастер: снимок раз в неделю
    try:
        s = ywm("/summary")
        snap = {"date": str(t), "ywm_searchable": s.get("searchable_pages_count"),
                "ywm_excluded": s.get("excluded_pages_count"), "sqi": s.get("sqi")}
        hist = [json.loads(l) for l in SNAP.read_text(encoding="utf-8").splitlines()] if SNAP.exists() else []
        old = [h for h in hist if h["date"] <= str(t - timedelta(days=6))]
        o = old[-1] if old else None
        print(f"Вебмастер: в поиске {snap['ywm_searchable']}" + (f" (было {o['ywm_searchable']} на {o['date']})" if o else "") +
              f", исключено {snap['ywm_excluded']}, ИКС {snap['sqi']}" + (f" (было {o['sqi']})" if o else ""))
        if not hist or hist[-1]["date"] != snap["date"]:
            SNAP.parent.mkdir(parents=True, exist_ok=True)
            with SNAP.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(snap, ensure_ascii=False) + "\n")
    except SystemExit as e:
        print("Вебмастер недоступен:", e)


CMDS = {"check": cmd_check, "traffic": cmd_traffic, "landing": cmd_landing, "gsc": cmd_gsc,
        "gsc-queries": cmd_gsc_queries, "grow": cmd_grow, "inspect": cmd_inspect, "gindex": cmd_gindex, "ywm": cmd_ywm, "ga4": cmd_ga4, "week": cmd_week}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help") or sys.argv[1] not in CMDS:
        print(__doc__); sys.exit(0)
    CMDS[sys.argv[1]](*sys.argv[2:])
