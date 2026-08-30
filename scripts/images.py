#!/usr/bin/env python3
"""
images — генерация иллюстраций через Gemini Image API (Nano Banana 2) под контракт проекта.

Контракт: .jpg, 16:9, ровно 1200x675, фотореализм, естественный свет,
без текста, водяных знаков и людей. Имя файла точно как в статье.

Ключ: GEMINI_API_KEY или файл .gemini.token в корне (обязательно в .gitignore).
Модель: MD_IMAGE_MODEL, по умолчанию gemini-3.1-flash-image.

Идемпотентность: существующий файл не перегенерируется. Каждая картинка стоит денег,
повторный прогон статьи не должен их тратить.

  python3 scripts/images.py init  <слаг>   скелет промптов из frontmatter
  python3 scripts/images.py gen   <слаг>   сгенерировать недостающие
  python3 scripts/images.py check <слаг>   проверить файлы по контракту
  python3 scripts/images.py cost  <слаг>   сколько будет стоить прогон
"""
import sys, os, re, io, json, base64, time, signal, subprocess, urllib.request, urllib.error
from pathlib import Path

try:
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
except (AttributeError, ValueError):
    pass

ENDPOINT = ("https://generativelanguage.googleapis.com/v1beta/models/"
            "{model}:generateContent")
MODEL = os.environ.get("MD_IMAGE_MODEL", "gemini-3.1-flash-image")
W, H = 1200, 675
QUALITY = 86

# Ориентир стоимости 1K-картинки, август 2026. Только для оценки в `cost`.
PRICE = {"gemini-3.1-flash-image": 0.067, "gemini-3.1-flash-lite-image": 0.034}

# Контракт картинок проекта — приклеивается к каждому промпту.
# Так контракт не зависит от того, вспомнил ли о нём автор промпта.
STYLE = ("Photorealistic documentary photograph, natural daylight, realistic textures, "
         "shallow depth of field, shot on a 35mm lens, 16:9 aspect ratio. "
         "No people, no faces, no text, no letters, no labels, no watermarks, no logos, "
         "no illustration or 3D render look. Russian dacha / countryside context.")


def root() -> Path:
    try:
        return Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"],
                                            stderr=subprocess.DEVNULL, text=True).strip())
    except Exception:
        return Path.cwd()


ROOT = root()
ART = ROOT / "articles"
PROMPTS = ROOT / "prompts"


def key() -> str:
    k = os.environ.get("GEMINI_API_KEY")
    if k:
        return k.strip()
    p = ROOT / ".gemini.token"
    if p.exists():
        return p.read_text().strip()
    sys.exit("нет ключа: GEMINI_API_KEY или .gemini.token (обязательно в .gitignore)")


def article(slug: str) -> str:
    f = ART / f"{slug}.md"
    if not f.exists():
        sys.exit(f"нет статьи {f.name}")
    return f.read_text(encoding="utf-8")


def frontmatter_images(txt: str):
    m = re.match(r"\A---\s*\n(.*?)\n---\s*\n", txt, re.S)
    if not m:
        sys.exit("нет frontmatter")
    out, inside = [], False
    for line in m.group(1).splitlines():
        if re.match(r"^images:\s*$", line):
            inside = True
            continue
        if inside:
            mm = re.match(r"^\s*-\s*(\S+)", line)
            if mm:
                out.append(mm.group(1).strip("\"'"))
            elif line.strip() and not line.startswith((" ", "\t", "-")):
                break
    return out


def body_alts(txt: str):
    """alt-тексты из тела: путь → alt. Alt задаёт смысл кадра, промпт — его вид."""
    body = re.sub(r"\A---\s*\n.*?\n---\s*\n", "", txt, flags=re.S)
    return {p: a for a, p in re.findall(r"!\[(.*?)\]\((.*?)\)", body)}


def prompts_path(slug: str) -> Path:
    return PROMPTS / f"{slug}.json"


def load_prompts(slug: str):
    p = prompts_path(slug)
    if not p.exists():
        sys.exit(f"нет {p.relative_to(ROOT)} — сначала: images.py init {slug}")
    return json.loads(p.read_text(encoding="utf-8"))


# ---------------------------------------------------------------- команды


def cmd_init(slug):
    txt = article(slug)
    imgs = frontmatter_images(txt)
    if not imgs:
        sys.exit("в frontmatter нет списка images")
    alts = body_alts(txt)
    p = prompts_path(slug)
    old = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    old_by_file = {i["file"]: i.get("prompt", "") for i in old.get("images", [])}
    items = [{"file": f, "alt": alts.get(f, ""), "prompt": old_by_file.get(f, "")}
             for f in imgs]
    PROMPTS.mkdir(exist_ok=True)
    p.write_text(json.dumps({"slug": slug, "model": MODEL, "images": items},
                            ensure_ascii=False, indent=2), encoding="utf-8")
    empty = sum(1 for i in items if not i["prompt"])
    print(f"{p.relative_to(ROOT)}: {len(items)} кадров, пустых промптов {empty}")
    print("Заполни prompt по-английски: конкретный предмет + материал + ракурс + время суток.")
    print("Стиль дописывать не надо — приклеивается скриптом.")


def _generate(prompt: str, api_key: str) -> bytes:
    url = ENDPOINT.format(model=MODEL)
    payload = {"contents": [{"parts": [{"text": prompt + " " + STYLE}]}]}
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-goog-api-key": api_key})
    last = None
    for i in range(3):
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                data = json.loads(r.read().decode("utf-8"))
            for cand in data.get("candidates", []):
                for part in cand.get("content", {}).get("parts", []):
                    inline = part.get("inlineData") or part.get("inline_data")
                    if inline and inline.get("data"):
                        return base64.b64decode(inline["data"])
            raise RuntimeError(f"в ответе нет картинки: {json.dumps(data)[:400]}")
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:400]
            if e.code == 404:
                sys.exit(f"модель {MODEL} не найдена (404). Названия моделей у Google "
                         f"меняются — сверься с документацией, не подбирай наугад.\n{detail}")
            if e.code in (401, 403):
                sys.exit(f"ключ отклонён ({e.code}). Подписка Gemini не даёт доступа к API, "
                         f"нужен ключ из Google AI Studio.\n{detail}")
            last = RuntimeError(f"HTTP {e.code}: {detail}")
        except Exception as e:
            last = e
        time.sleep(3 * (i + 1))
    raise last


def _fit(raw: bytes) -> bytes:
    """Что бы модель ни вернула — кадрируем по центру в 16:9 и ресайзим в 1200x675."""
    from PIL import Image
    im = Image.open(io.BytesIO(raw))
    im = im.convert("RGB")
    tw, th = im.size
    target = W / H
    if tw / th > target:
        new_w = int(th * target)
        left = (tw - new_w) // 2
        im = im.crop((left, 0, left + new_w, th))
    else:
        new_h = int(tw / target)
        top = (th - new_h) // 2
        im = im.crop((0, top, tw, top + new_h))
    im = im.resize((W, H), Image.LANCZOS)
    # Новый объект без метаданных исходника — EXIF не переносится.
    clean = Image.new("RGB", im.size)
    clean.putdata(list(im.getdata()))
    buf = io.BytesIO()
    clean.save(buf, "JPEG", quality=QUALITY, optimize=True)
    return buf.getvalue()


def cmd_gen(slug):
    data = load_prompts(slug)
    api_key = key()
    made = skipped = 0
    for item in data["images"]:
        dest = ART / item["file"]
        if dest.exists():
            skipped += 1
            continue
        if not item.get("prompt"):
            print(f"  ПРОПУСК {item['file']}: пустой промпт")
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        print(f"  генерирую {item['file']} …", flush=True)
        raw = _generate(item["prompt"], api_key)
        dest.write_bytes(_fit(raw))
        made += 1
    price = PRICE.get(MODEL, 0.067)
    print(f"Сгенерировано {made}, уже было {skipped}. "
          f"Ориентировочно ${made * price:.2f} ({MODEL})")


def cmd_check(slug):
    from PIL import Image
    txt = article(slug)
    imgs = frontmatter_images(txt)
    bad = []
    for f in imgs:
        p = ART / f
        if not p.exists():
            bad.append(f"{f}: файла нет")
            continue
        if p.suffix.lower() not in (".jpg", ".jpeg"):
            bad.append(f"{f}: не JPEG")
        im = Image.open(p)
        if im.size != (W, H):
            bad.append(f"{f}: размер {im.size[0]}x{im.size[1]}, нужен {W}x{H}")
        if im.getexif():
            bad.append(f"{f}: остались метаданные EXIF")
        if p.stat().st_size > 400_000:
            bad.append(f"{f}: {p.stat().st_size // 1024} КБ — тяжеловато для страницы")
    alts = body_alts(txt)
    for f in imgs:
        if not alts.get(f, "").strip():
            bad.append(f"{f}: в теле статьи нет alt-текста")
    if bad:
        for b in bad:
            print("  -", b)
        sys.exit(1)
    print(f"OK — {len(imgs)} картинок, все по контракту {W}x{H} JPEG без метаданных.")


def cmd_cost(slug):
    data = load_prompts(slug)
    todo = [i for i in data["images"] if not (ART / i["file"]).exists() and i.get("prompt")]
    price = PRICE.get(MODEL, 0.067)
    print(f"К генерации {len(todo)} из {len(data['images'])}. "
          f"Ориентировочно ${len(todo) * price:.2f} при ${price}/кадр ({MODEL}).")
    print("Цена справочная — сверяйся с ai.google.dev/pricing.")


CMDS = {"init": cmd_init, "gen": cmd_gen, "check": cmd_check, "cost": cmd_cost}

if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] not in CMDS:
        print(__doc__)
        sys.exit(2)
    CMDS[sys.argv[1]](sys.argv[2])
