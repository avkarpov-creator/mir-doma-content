#!/usr/bin/env bash
# plugin-release.sh — релиз плагина mir-doma одной командой.
#
# Правило проекта: любое изменение PHP = бамп версии + запись в CHANGELOG
# (что / зачем / файлы) + логирование в рантайме. Скрипт ОТКАЗЫВАЕТ,
# если в изменённом PHP нет вызова логгера. Это не рекомендация, а механика.
#
#   ./scripts/plugin-release.sh patch "Что сделано" "Зачем"
#   ./scripts/plugin-release.sh minor "Что сделано" "Зачем"
#   ./scripts/plugin-release.sh major "Что сделано" "Зачем"
#
# Запускать из корня репозитория плагина (там, где лежит главный PHP-файл
# с заголовком «Version:»).

set -euo pipefail

BUMP="${1:-}"
WHAT="${2:-}"
WHY="${3:-}"

if [[ -z "$BUMP" || -z "$WHAT" || -z "$WHY" ]]; then
  echo "Использование: $0 {patch|minor|major} \"Что сделано\" \"Зачем\"" >&2
  exit 1
fi
case "$BUMP" in patch|minor|major) ;; *) echo "Неверный тип бампа: $BUMP" >&2; exit 1 ;; esac

# ---------------------------------------------------------------- главный файл

MAIN_FILE="$(grep -rlE '^\s*\*?\s*Version:\s*[0-9]' --include='*.php' . 2>/dev/null | head -1 || true)"
if [[ -z "$MAIN_FILE" ]]; then
  echo "Не найден PHP-файл с заголовком «Version:». Запусти из корня плагина." >&2
  exit 1
fi

CURRENT="$(grep -oE '^\s*\*?\s*Version:\s*[0-9]+\.[0-9]+\.[0-9]+' "$MAIN_FILE" \
           | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)"
if [[ -z "$CURRENT" ]]; then
  echo "Версия в $MAIN_FILE не в формате X.Y.Z — поправь вручную." >&2
  exit 1
fi

IFS='.' read -r MA MI PA <<< "$CURRENT"
case "$BUMP" in
  major) MA=$((MA+1)); MI=0; PA=0 ;;
  minor) MI=$((MI+1)); PA=0 ;;
  patch) PA=$((PA+1)) ;;
esac
NEW="$MA.$MI.$PA"

# ---------------------------------------------------------------- ЗАСТАВА: логирование

CHANGED="$(git diff --name-only HEAD -- '*.php'; git diff --cached --name-only -- '*.php'; \
           git ls-files --others --exclude-standard -- '*.php')"
CHANGED="$(echo "$CHANGED" | sort -u | sed '/^$/d')"

if [[ -z "$CHANGED" ]]; then
  echo "Нет изменённых PHP-файлов. Релизить нечего." >&2
  exit 1
fi

# Как выглядит вызов логгера в наших плагинах. Дополняй список, если появится новый.
LOGGER_RE='md_log|mir_doma_log|->log\(|error_log\(|\$this->logger'

MISSING=()
while IFS= read -r f; do
  [[ -f "$f" ]] || continue
  # Смотрим только добавленные строки диффа — новый код без логов нам и не нужен.
  ADDED="$(git diff HEAD -- "$f" | grep '^+' | grep -v '^+++' || true)"
  if [[ -z "$ADDED" ]]; then ADDED="$(cat "$f")"; fi
  if ! echo "$ADDED" | grep -qE "$LOGGER_RE"; then
    MISSING+=("$f")
  fi
done <<< "$CHANGED"

if (( ${#MISSING[@]} > 0 )); then
  echo "ОТКАЗ: в изменениях нет вызовов логгера." >&2
  for f in "${MISSING[@]}"; do echo "  - $f" >&2; done
  echo >&2
  echo "Правило проекта: логируем вход в функцию, ветвления и результат." >&2
  echo "Без логов отладка на боевом сайте идёт вслепую. Добавь и повтори." >&2
  exit 2
fi

# ---------------------------------------------------------------- бамп + CHANGELOG

sed -i.bak -E "s/(Version:[[:space:]]*)$CURRENT/\1$NEW/" "$MAIN_FILE" && rm -f "$MAIN_FILE.bak"

# Константа версии, если она объявлена в коде.
if grep -qE "define\(\s*'[A-Z_]*VERSION'" "$MAIN_FILE"; then
  sed -i.bak -E "s/($CURRENT)/$NEW/g" "$MAIN_FILE" && rm -f "$MAIN_FILE.bak"
fi

FILES_LINE="$(echo "$CHANGED" | tr '\n' ' ' | sed 's/ $//')"
DATE="$(date +%Y-%m-%d)"

ENTRY="## $NEW — $DATE

**Что:** $WHAT

**Зачем:** $WHY

**Файлы:** $FILES_LINE
"

if [[ -f CHANGELOG.md ]]; then
  printf '%s\n%s' "$ENTRY" "$(cat CHANGELOG.md)" > CHANGELOG.md.tmp
  mv CHANGELOG.md.tmp CHANGELOG.md
else
  printf '# CHANGELOG\n\n%s' "$ENTRY" > CHANGELOG.md
fi

echo "Версия: $CURRENT → $NEW  ($MAIN_FILE)"
echo "CHANGELOG обновлён."
echo "Логи найдены во всех изменённых файлах."
echo
echo "Дальше: git add -A && git commit -m \"v$NEW: $WHAT\""
