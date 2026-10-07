# Finance DBT Copilot

A screenshot-first, human-in-the-loop assistant for real dbt + Snowflake finance project work.

## Modules
1. Incremental Copilot
2. Macro Copilot
3. Snapshot Copilot
4. Data Quality Copilot
5. Lineage & Impact Copilot

## Start
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

## Optional AI
Set `OPENAI_API_KEY` in your environment. Do not hard-code it.

## Important
This version does not connect to your company repository or production Snowflake.
You manually provide screenshots/code/context that your company policy permits you to share.
Never provide passwords, tokens, customer PII, or confidential information unless explicitly approved.

## Next upgrades
- Vision screenshot understanding
- dbt manifest/catalog lineage
- project convention memory
- macro test-case generator
- compiled SQL preview
- Git diff / PR review
- Snowflake query-profile analysis
- redaction of sensitive values
