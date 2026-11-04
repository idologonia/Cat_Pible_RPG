# CAT & PIBBLE RPG

Піксельна Action RPG у браузері: котики й пібулі проти щурячої навали.

**Грати:** відкрий `cat-pibble-rpg.html` у браузері. Інтернет не потрібен.

**Збереження** лежать у браузері. Щоб перенести прогрес у нову версію файлу або на інший пристрій, відкрий «Меню → Перенести збереження» і скористайся експортом та імпортом (файл `.json` або код).

## Розробка з Claude Code

Інструкції для Claude — у `CLAUDE.md`, історія етапів — у `docs/CHANGELOG.md`.

```bash
pip install -r requirements.txt
python -m playwright install chromium
python tests/run_all.py
```
