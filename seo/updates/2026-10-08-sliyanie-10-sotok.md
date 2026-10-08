# Слияние кластера «10 соток» — 2026-10-08

Две статьи слиты в пиллар `planirovka-uchastka-10-sotok`. Обе Google просканировал,
но в индекс не взял («Crawled — currently not indexed»): он видел в них повтор пиллара.

| Старый URL | Что перенесено в пиллар |
|---|---|
| /planirovka-uchastka-10-sotok-pod-stroitelstvo/ | раздел «Если участок пустой: планировка под строительство дома» + FAQ про грунт |
| /zonirovanie-uchastka-10-sotok/ | разделы «Схемы зонирования» (таблица 4 схем) и «Чем разделить зоны» + 2 FAQ |

Внутренние ссылки на старые URL уже переставлены на пиллар (6 статей).

## Что сделать владельцу

1. Git Importer → «Проверить GitHub сейчас» — подтянется обновлённый пиллар
   и правки в статьях со ссылками.
2. **301-редиректы** (там же, где делали 301 для дублей `-2`), напрямую на URL со слешем,
   чтобы не было цепочки:
   - `/planirovka-uchastka-10-sotok-pod-stroitelstvo/` → `https://mir-doma.pro/planirovka-uchastka-10-sotok/`
   - `/zonirovanie-uchastka-10-sotok/` → `https://mir-doma.pro/planirovka-uchastka-10-sotok/`
3. Обе старые записи — в черновик или корзину **после** того, как редирект заработает.
4. Проверка: `curl -sI https://mir-doma.pro/zonirovanie-uchastka-10-sotok/` → `301`,
   `location: https://mir-doma.pro/planirovka-uchastka-10-sotok/`.

Файлы статей удалены из репозитория. Импортёр записи в WordPress не удаляет,
поэтому до редиректа старые страницы продолжают открываться.
