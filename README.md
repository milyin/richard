# RICHARD — lecture bilingue

PWA-приложение для чтения французского текста пьесы с раскрывающимся русским переводом и комментариями.

## Структура

- `richard_translation.tsv` — основной редактируемый источник: французский текст, перевод, комментарии.
- `pwa/` — статическое PWA-приложение.
- `pwa/build_data.py` — генерация `pwa/data.json` из TSV.
- `generate_pdf.py` — генерация PDF-версии из TSV.
- `source_extracted.txt` — извлечённый исходный текст.
- `RICHARD_modifs.docx` — исходный документ.
- `.github/workflows/pages.yml` — CI для генерации PWA и деплоя GitHub Pages.

## Как обновить текст

1. Отредактировать `richard_translation.tsv`.
2. Закоммитить и отправить изменения в `main`.
3. GitHub Actions автоматически пересоберёт `pwa/data.json` и обновит GitHub Pages.

Локально можно проверить так:

```bash
cd pwa
python3 build_data.py
python3 -m http.server 8765
```

После этого открыть `http://127.0.0.1:8765/`.
