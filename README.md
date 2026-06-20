# mir-doma-content

Источник истины для статей сайта **mir-doma.pro**. Статьи лежат как `.md` файлы в папке `articles/`. Плагин на сайте сам забирает их из этого репозитория и создаёт черновики в WordPress.

## Что внутри

```
mir-doma-content/
├── articles/            ← сюда кладём статьи (.md)
│   └── primer-tlya.md   ← пример/образец
├── scripts/
│   └── validate.py      ← проверка статей
├── .github/workflows/
│   └── validate.yml     ← авто-проверка при пуше (CI)
├── SCHEMA.md            ← описание полей статьи
└── README.md
```

## Как залить репозиторий на GitHub (с нуля)

1. Создай на github.com новый репозиторий — например `mir-doma-content`. Можно приватный.
2. На своём компьютере открой терминал в этой папке и выполни по очереди:

```bash
git init
git add .
git commit -m "Старт: схема, пример статьи, CI"
git branch -M main
git remote add origin https://github.com/ТВОЙ_ЛОГИН/mir-doma-content.git
git push -u origin main
```

Если просит логин — пароль это не пароль от аккаунта, а **Personal Access Token** (GitHub → Settings → Developer settings → Tokens). Тот же токен потом вставишь в плагин, если репозиторий приватный.

## Как добавить новую статью

```bash
# положили новый файл articles/moya-statya.md, дальше:
git add articles/moya-statya.md
git commit -m "Статья: моя статья"
git push
```

После пуша GitHub сам прогонит проверку (вкладка Actions). Если проверка зелёная — плагин на сайте подхватит статью при следующей проверке и создаст черновик.

## Проверить статьи локально (необязательно)

```bash
python3 scripts/validate.py
```

## Правила статьи

Смотри `SCHEMA.md`. Кратко: файл начинается с frontmatter между `---`, обязательны `title` и `category`, `seo_title` ≤ 60 символов, `seo_description` ≤ 160, у каждой картинки должен быть alt-текст.
