# Blood on the Clocktower Streamlit App

This project has been migrated to **Python + Streamlit** so you can run and deploy it quickly without a Node/Vite toolchain.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Community Cloud

1. Push this repo to GitHub.
2. In Streamlit Community Cloud, create a new app.
3. Set:
   - **Main file path**: `app.py`
   - **Python version**: 3.11+ (recommended)
4. Deploy.

## Features

- 12-seat default roster with editable player details.
- Alignment / alive status / suspicion tracker.
- Quick tags and long-form notes.
- Reminder toggles (poisoned, drunk, safe, etc.).
- Up to 3 possible roles per player with confidence + reasoning.
- Fuzzy search across names, tags, notes, and role possibilities.
- Import/export game state as JSON.
