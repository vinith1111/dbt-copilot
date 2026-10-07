import os, re, json, textwrap
from pathlib import Path
import streamlit as st

st.set_page_config(page_title="Finance DBT Copilot", page_icon="🏦", layout="wide")

# ---------- access control ----------
# This app is intended for the owner's personal use.
# Configure the authorized email in Streamlit Secrets:
# ALLOWED_EMAIL = "your-login-email@example.com"
#
# Streamlit's native login is used so no password is stored in this repository.
if "ALLOWED_EMAIL" not in st.secrets:
    st.error("App access is not configured yet. Add ALLOWED_EMAIL in Streamlit Secrets.")
    st.stop()

if not st.user.is_logged_in:
    st.title("🔐 Finance DBT Copilot")
    st.caption("Private workspace. Sign in with your authorized account to continue.")
    if st.button("Sign in"):
        st.login()
    st.stop()

allowed_email = str(st.secrets["ALLOWED_EMAIL"]).strip().lower()
user_email = str(getattr(st.user, "email", "") or "").strip().lower()

if not user_email or user_email != allowed_email:
    st.error("🚫 Access denied")
    st.write("This Finance DBT Copilot is restricted to its authorized user.")
    if st.button("Sign out"):
        st.logout()
    st.stop()


st.title("🏦 Finance DBT Copilot")
st.caption("Screenshot-first assistant for dbt project work. Suggestions require human review.")

# ---------- helpers ----------
def ai(prompt, context=""):
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return None, "AI is not configured. Set OPENAI_API_KEY in your environment."
    try:
        from openai import OpenAI
        client = OpenAI(api_key=key)
        system = """You are a senior dbt + Snowflake engineer supporting a finance data project.
Be conservative. Never invent project conventions or unseen dependencies.
Clearly separate facts from assumptions.
For financial transformations, explicitly consider grain, duplicates, NULLs, precision/scale,
currency, date/time logic, late-arriving data, reconciliation, and downstream impact.
Do not execute or recommend production writes without human review."""
        r = client.responses.create(
            model=os.getenv("OPENAI_MODEL", "gpt-5.6"),
            input=[
                {"role":"system","content":system},
                {"role":"user","content":f"CONTEXT:\n{context}\n\nREQUEST:\n{prompt}"}
            ]
        )
        return r.output_text, None
    except Exception as e:
        return None, str(e)

def show_ai(prompt, context):
    answer, err = ai(prompt, context)
    if answer:
        st.markdown(answer)
    else:
        st.warning(err)
        st.info("You can still use the structured checklists without AI.")

def extract_text(upload):
    if not upload:
        return ""
    if upload.type.startswith("text/") or upload.name.endswith((".sql",".yml",".yaml",".md",".txt")):
        return upload.getvalue().decode("utf-8", errors="ignore")
    return f"[Image uploaded: {upload.name}. Use the AI vision-capable environment to analyze this screenshot.]"

# ---------- sidebar ----------
with st.sidebar:
    st.header("Project Context")
    st.write("Add only information approved by your company.")
    upload = st.file_uploader("Screenshot / SQL / YAML", type=["png","jpg","jpeg","webp","sql","yml","yaml","txt","md"])
    pasted = st.text_area("Paste project code or error", height=180)
    task = st.text_area("Task / Jira requirement", height=120, placeholder="Example: Add latest transaction status to the account model.")
    context = extract_text(upload) + "\n\n" + pasted + "\n\nTASK:\n" + task

    st.divider()
    st.caption("🔒 No repository connection. You control what is shared.")
    st.caption("⚠️ Do not provide passwords, tokens, customer PII or confidential data unless your company explicitly permits it.")

tabs = st.tabs([
    "🔄 Incremental",
    "🧩 Macros",
    "📸 Snapshots",
    "🧪 Data Quality",
    "🌳 Lineage & Impact"
])

# ---------- incremental ----------
with tabs[0]:
    st.header("🔄 Incremental Copilot")
    st.write("Use this before changing or creating an incremental model.")
    c1,c2 = st.columns(2)
    with c1:
        grain = st.text_input("Business grain", placeholder="One row per account + business_date")
        unique_key = st.text_input("Unique key", placeholder="account_id")
        strategy = st.selectbox("Incremental strategy", ["Unknown", "merge", "append", "delete+insert"])
    with c2:
        late = st.checkbox("Late-arriving data possible")
        updates = st.checkbox("Existing records can be corrected")
        deletes = st.checkbox("Deletes are possible")
        currency = st.checkbox("Money / multi-currency fields involved")

    if st.button("Analyze Incremental Logic"):
        checklist = f"""
Grain: {grain or 'Not provided'}
Unique key: {unique_key or 'Not provided'}
Strategy: {strategy}
Late arriving data: {late}
Corrections: {updates}
Deletes: {deletes}
Financial/currency data: {currency}
Code/context:
{context}
"""
        show_ai("""Review this incremental design. Identify likely duplicate, late-data, merge,
full-refresh, delete, precision, and reconciliation risks. If enough information exists,
propose robust dbt/Snowflake logic and tests. List assumptions explicitly.""", checklist)

# ---------- macros ----------
with tabs[1]:
    st.header("🧩 Macro Copilot")
    operation = st.selectbox("Macro task", [
        "Create a macro",
        "Explain an existing macro",
        "Convert SQL into a macro",
        "Debug a macro",
        "Review whether a macro is needed",
        "Refactor a macro"
    ])
    macro_request = st.text_area("Describe the macro task", height=140)
    if st.button("Run Macro Copilot"):
        prompt = f"""Macro operation: {operation}
User request: {macro_request}
Provide:
1. recommendation
2. macro code when appropriate
3. example usage
4. where it should live
5. edge cases
6. finance-specific risks
7. tests/checks
Do not create a macro merely for one-off logic."""
        show_ai(prompt, context)

# ---------- snapshots ----------
with tabs[2]:
    st.header("📸 Snapshot Copilot")
    st.write("For historical-change and slowly-changing-record problems.")
    snapshot_type = st.selectbox("What are you trying to track?", [
        "Unknown",
        "Row changes over time",
        "Status/history changes",
        "Financial/account attribute history",
        "Other"
    ])
    key = st.text_input("Business key", placeholder="account_id")
    change_col = st.text_input("Timestamp/change column", placeholder="updated_at")
    if st.button("Analyze Snapshot Design"):
        show_ai(f"""Evaluate this snapshot design:
Type: {snapshot_type}
Business key: {key}
Change/timestamp column: {change_col}
Recommend an appropriate dbt snapshot strategy, explain the generated historical fields,
and identify risks around late updates, corrections, deletes, timestamps and finance reporting.
Context: {context}""", context)

# ---------- quality ----------
with tabs[3]:
    st.header("🧪 Data Quality Copilot")
    st.write("Generate a practical test plan instead of blindly adding generic tests.")
    model_grain = st.text_input("Model grain", key="quality_grain", placeholder="One row per transaction")
    important_cols = st.text_area("Important columns", placeholder="transaction_id\naccount_id\namount\ncurrency\ntransaction_date")
    if st.button("Generate Test Plan"):
        show_ai(f"""Create a dbt data-quality test plan for this finance model.
Grain: {model_grain}
Columns:
{important_cols}
Include appropriate generic/custom tests and explain why each matters.
Pay special attention to uniqueness, not-null, accepted values, relationships, monetary
precision, currency consistency, date validity, duplicates, reconciliation and row-count anomalies.
Do not invent business rules; mark assumptions.""", context)

# ---------- lineage ----------
with tabs[4]:
    st.header("🌳 Lineage & Impact Copilot")
    st.write("Use before changing an existing model, macro or important column.")
    changed_item = st.text_input("What are you changing?", placeholder="dim_account.amount")
    change = st.text_area("What change are you considering?", height=120)
    if st.button("Analyze Impact"):
        show_ai(f"""Assess the likely impact of this dbt change.
Changed item: {changed_item}
Proposed change: {change}
Identify upstream/downstream dependencies that can be established from the supplied context,
what must be verified manually, tests to run, and potential finance/reporting risks.
Never claim complete lineage unless the context proves it.""", context)

st.divider()
st.subheader("🛡️ Finance safety checklist")
st.markdown("""
- **Grain:** What does one row represent?
- **Duplicates:** Can the transformation multiply rows?
- **Precision:** Are monetary fields using appropriate precision/scale?
- **Currency:** Are currencies consistent or converted explicitly?
- **Dates:** Are timezone and business-date rules correct?
- **Incremental:** Can late/corrected data be missed?
- **Reconciliation:** Can output be reconciled to the source?
- **Impact:** Which downstream models/reports could change?
- **Tests:** What proves the change is correct?
""")
