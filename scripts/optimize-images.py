#!/usr/bin/env python3
"""
optimize-images — привести уже загруженные картинки к контракту проекта.

В репозитории 716 файлов на 1,2 ГБ, в среднем 1,7 МБ на кадр, размеры вразнобой
(1360x768, 1376x768, 1792x1008, 1024x1024...). На странице шесть картинок — это
около 10 МБ веса, что рушит LCP и мобильную выдачу.

  python3 scripts/optimize-images.py report          что сейчас, без изменений
  python3 scripts/optimize-images.py run --dry       что будет сделано
  python3 scripts/optimize-images.py run             сделать
  python3 scripts/optimize-images.py run --min=500   только файлы тяжелее 500 КБ

Идемпотентно: файл, уже соответствующий контракту, не трогается.
Оригиналы не сохраняются — они есть в истории git до коммита.
"""
import sys, io, signal, subprocess, collections
from pathlib import Path

try:
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
except (AttributeError, ValueError):
    pass

W, H, QUALITY = 1200, 675, 86


def root() -> Path:
    try:
        return Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"],
                                            stderr=subprocess.DEVNULL, text=True).strip())
    except Exception:
        return Path.cwd()


IMG = root() / "articles" / "images"


def files():
    return sorted(list(IMG.glob("*.jpg")) + list(IMG.glob("*.jpeg")) + list(IMG.glob("*.png")))


def convert(p: Path) -> bytes:
    from PIL import Image
    im = Image.open(p).convert("RGB")
    tw, th = im.size
    target = W / H
    if tw / th > target:
        nw = int(th * target)
        left = (tw - nw) // 2
        im = im.crop((left, 0, left + nw, th))
    else:
        nh = int(tw / target)
        top = (th - nh) // 2
        im = im.crop((0, top, tw, top + nh))
    im = im.resize((W, H), Image.LANCZOS)
    clean = Image.new("RGB", im.size)
    clean.paste(im)                      # новый объект — метаданные не переносятся
    buf = io.BytesIO()
    clean.save(buf, "JPEG", quality=QUALITY, optimize=True)
    return buf.getvalue()


def cmd_report(args):
    from PIL import Image
    fs = files()
    if not fs:
        sys.exit(f"нет картинок в {IMG}")
    sizes, total, heavy, ok = collections.Counter(), 0, 0, 0
    for p in fs:
        total += p.stat().st_size
        if p.stat().st_size > 1_000_000:
            heavy += 1
        try:
            s = Image.open(p).size
            sizes[s] += 1
            if s == (W, H) and p.suffix.lower() in (".jpg", ".jpeg"):
                ok += 1
        except Exception:
            sizes[("битый", "")] += 1
    print(f"Файлов {len(fs)}, суммарно {total/1024/1024:.0f} МБ, "
          f"в среднем {total/len(fs)/1024:.0f} КБ")
    print(f"Тяжелее 1 МБ: {heavy} ({heavy*100//len(fs)}%). "
          f"Уже по контракту {W}x{H}: {ok}")
    print("Размеры:")
    for s, n in sizes.most_common(8):
        ratio = f"{s[0]/s[1]:.3f}" if isinstance(s[1], int) and s[1] else "—"
        print(f"  {n:>4}  {s[0]}x{s[1]}  ({ratio})")


def cmd_run(args):
    from PIL import Image
    dry = "--dry" in args
    minkb = 0
    for a in args:
        if a.startswith("--min="):
            minkb = int(a.split("=")[1])
    done = skipped = 0
    before = after = 0
    for p in files():
        sz = p.stat().st_size
        if sz < minkb * 1024:
            skipped += 1
            continue
        try:
            same = Image.open(p).size == (W, H)
        except Exception:
            print(f"  БИТЫЙ {p.name}")
            continue
        if same and p.suffix.lower() in (".jpg", ".jpeg") and sz < 400_000:
            skipped += 1
            continue
        new = convert(p)
        before += sz
        after += len(new)
        done += 1
        if not dry:
            if p.suffix.lower() == ".png":
                # имя файла указано в статьях — расширение менять нельзя,
                # поэтому JPEG кладём под прежним именем.
                p.write_bytes(new)
            else:
                p.write_bytes(new)
    verb = "будет обработано" if dry else "обработано"
    print(f"{verb} {done}, пропущено {skipped}")
    if done:
        print(f"{before/1024/1024:.0f} МБ → {after/1024/1024:.0f} МБ "
              f"(−{100 - after*100//before}%)")
    if dry:
        print("Это сухой прогон. Убери --dry, чтобы применить.")
    else:
        print("Проверь глазами несколько файлов, затем коммить.")


CMDS = {"report": cmd_report, "run": cmd_run}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in CMDS:
        print(__doc__)
        sys.exit(2)
    CMDS[sys.argv[1]](sys.argv[2:])
