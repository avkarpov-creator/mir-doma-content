#!/usr/bin/env bash
# ship.sh <слаг> [--yes] — полный цикл выпуска статьи.
#
# Семь шагов, останов на первой проблеме. Останов до пуша намеренный:
# чинить опубликованное дороже, чем не публиковать.
#
# Что делает пользователь до запуска:
#   1. mutagen.py pick "<фраза>" --min-freq=200 --max-strong=5
#   2. mdi.py dupe "<тема>" + mdi.py linkplan <слаг> "<Рубрика>" "<тема>"
#   3. mdi.py new <слаг> "<Рубрика>", написать текст, расставить ссылки в донорах
#   4. images.py init <слаг>, заполнить промпты
#   5. ./scripts/ship.sh <слаг>
#
# Что остаётся вручную после: в админке WordPress «Проверить GitHub сейчас»,
# затем ревью черновика и публикация.

set -euo pipefail

SLUG="${1:-}"
AUTO="${2:-}"
[ -n "$SLUG" ] || { echo "Использование: ./scripts/ship.sh <слаг> [--yes]"; exit 1; }
[ -d articles ] || { echo "Запусти из корня репозитория"; exit 1; }
[ -f "articles/$SLUG.md" ] || { echo "Нет articles/$SLUG.md"; exit 1; }

step() { echo; echo "── $1"; }

# --- 0. Токены не должны попасть в репозиторий ---------------------------
step "0/7 токены"
for t in .gemini.token .mutagen.token; do
  if git ls-files --error-unmatch "$t" >/dev/null 2>&1; then
    echo "СТОП: $t отслеживается git."
    echo "Выполни: git rm --cached $t && echo $t >> .gitignore"
    exit 1
  fi
done
echo "токены вне git — ок"

# --- 1. Индекс -----------------------------------------------------------
step "1/7 индекс"
python3 scripts/mdi.py index

# --- 2. Структура статьи и перелинковка ----------------------------------
step "2/7 структура статьи"
if ! python3 scripts/mdi.py check "$SLUG"; then
  echo
  echo "→ Почини замечания выше. Чаще всего это:"
  echo "  • нет входящих ссылок — без них страница не индексируется;"
  echo "    посмотри: python3 scripts/mdi.py linkplan $SLUG"
  echo "  • битый слаг — либо опечатка, либо статья создана вручную в WP;"
  echo "    во втором случае добавь слаг в external-slugs.txt"
  exit 1
fi

INC=$(python3 scripts/mdi.py in "$SLUG" | grep -c '←' || true)
if [ "$INC" -lt 2 ]; then
  echo "СТОП: входящих ссылок $INC, нужно минимум 2."
  echo "Без входящих страница не попадёт в индекс — это проверено на практике."
  echo "Кто может сослаться: python3 scripts/mdi.py linkplan $SLUG"
  exit 1
fi
echo "входящих ссылок: $INC"

# --- 3. Промпты ----------------------------------------------------------
step "3/7 промпты для картинок"
if [ ! -f "prompts/$SLUG.json" ]; then
  python3 scripts/images.py init "$SLUG"
  echo "→ Заполни поля prompt и запусти ship.sh снова."
  exit 1
fi
if grep -q '"prompt": ""' "prompts/$SLUG.json"; then
  echo "СТОП: в prompts/$SLUG.json остались пустые промпты."
  grep -B2 '"prompt": ""' "prompts/$SLUG.json" | grep '"file"' || true
  exit 1
fi
python3 scripts/images.py cost "$SLUG"

# --- 4. Генерация картинок ----------------------------------------------
step "4/7 генерация картинок"
python3 scripts/images.py gen "$SLUG"
if ! python3 scripts/images.py check "$SLUG"; then
  echo
  echo "→ Если файлы старые и не по контракту:"
  echo "  python3 scripts/optimize-images.py run"
  echo "→ Если файла нет — проверь, что имя в frontmatter совпадает с именем в prompts/."
  exit 1
fi

# --- 5. Финальная валидация ---------------------------------------------
step "5/7 финальная валидация"
python3 scripts/mdi.py index >/dev/null
python3 scripts/mdi.py check "$SLUG"

# --- 6. Что уходит в коммит ---------------------------------------------
step "6/7 состав коммита"
# Только файлы этой статьи. Чужие незакоммиченные правки в коммит не попадут —
# иначе статья уедет вперемешку с посторонними изменениями.
git add "articles/$SLUG.md" "prompts/$SLUG.json"
python3 - "$SLUG" <<'PY' | while read -r f; do [ -f "$f" ] && git add "$f"; done
import sys, re, pathlib
txt = pathlib.Path(f"articles/{sys.argv[1]}.md").read_text(encoding="utf-8")
m = re.match(r"\A---\s*\n(.*?)\n---\s*\n", txt, re.S)
inside = False
for line in (m.group(1).splitlines() if m else []):
    if re.match(r"^images:\s*$", line):
        inside = True; continue
    if inside:
        mm = re.match(r"^\s*-\s*(\S+)", line)
        if mm: print("articles/" + mm.group(1).strip("\"'"))
        elif line.strip() and not line.startswith((" ", "\t", "-")): break
PY
# Статьи-доноры, куда добавлены входящие ссылки.
git add -u articles 2>/dev/null || true

git diff --cached --stat | tail -12
CHANGED=$(git diff --cached --name-only | wc -l)
OTHER=$(git status --porcelain | grep -c '^ M\|^??' || true)
if [ "$OTHER" -gt 0 ]; then
  echo "(вне коммита остаётся $OTHER изменённых файлов — это нормально)"
fi
if [ "$CHANGED" -eq 0 ]; then
  echo "Нечего коммитить — всё уже в репозитории."
  exit 0
fi

# --- 7. Пуш --------------------------------------------------------------
step "7/7 коммит и пуш"
if [ "$AUTO" != "--yes" ]; then
  read -r -p "Запушить $CHANGED файлов? [y/N] " ans
  [ "$ans" = "y" ] || { echo "Отменено. Изменения остались в индексе."; exit 0; }
fi
git commit -qm "Статья: $SLUG"
git push -q
echo
echo "Готово. Дальше вручную:"
echo "  1. Админка WordPress → Настройки → Git Importer → «Проверить GitHub сейчас»"
echo "  2. Ревью черновика, проверить картинки и перелинковку глазами"
echo "  3. Публикация"
