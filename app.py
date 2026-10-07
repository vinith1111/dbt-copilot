import re
import streamlit as st

st.set_page_config(page_title="Finance DBT Copilot", page_icon="🏦", layout="wide")
st.title("🏦 Finance DBT Copilot")
st.caption("Offline dbt workbench. No AI or API key required.")

def cols(value):
    return [x.strip() for x in re.split(r"[,\\n]+", value or "") if x.strip()]

def incremental_code(strategy, key):
    s = strategy if strategy != "Unknown" else "merge"
    k = cols(key)
    uk = "'" + k[0] + "'" if len(k) == 1 else (str(k) if k else "'REPLACE_WITH_UNIQUE_KEY'")
    return """{{ config(
    materialized='incremental',
    incremental_strategy='""" + s + """',
    unique_key=""" + uk + """
) }}

select *
from {{ ref('source_model') }}

{% if is_incremental() %}
-- Add your project-approved lookback/incremental filter here.
{% endif %}"""

def quality_tests(grain, important):
    c=cols(important); out=[]
    if grain: out.append("Grain: "+grain)
    if c:
        out.append("Review NOT NULL for required columns: "+", ".join(c))
        out.append("Apply UNIQUE only where it matches the declared grain.")
    out += ["Relationships: validate foreign-key-style dimensions.","Accepted values: validate controlled status/type/currency fields.","Financial: check precision/scale, signs, rounding and currency consistency.","Dates: check invalid/future dates and timezone/business-date rules.","Reconciliation: compare source/output row counts and important financial totals."]
    return out

with st.sidebar:
    st.header("Project Context")
    st.caption("Inputs are used only for the current app session. Nothing is committed to GitHub.")
    st.file_uploader("Screenshot / SQL / YAML",type=["png","jpg","jpeg","webp","sql","yml","yaml","txt","md"])
    st.text_area("Paste project code or error",height=160)
    st.text_area("Task / Jira requirement",height=100)

tabs=st.tabs(["🔄 Incremental","🧩 Macros","📸 Snapshots","🧪 Data Quality","🌳 Lineage & Impact"])

with tabs[0]:
    st.header("🔄 Incremental Workbench")
    st.write("Generate a starting configuration and identify design risks.")
    grain=st.text_input("Business grain",placeholder="One row per account + business_date")
    key=st.text_input("Unique key",placeholder="account_id")
    strategy=st.selectbox("Incremental strategy",["Unknown","merge","append","delete+insert"])
    late=st.checkbox("Late-arriving data possible")
    updates=st.checkbox("Existing records can be corrected")
    deletes=st.checkbox("Deletes are possible")
    currency=st.checkbox("Money / multi-currency fields involved")
    if st.button("Generate Incremental Design"):
        st.subheader("model.sql starter"); st.code(incremental_code(strategy,key),language="sql")
        if not grain: st.warning("Define the business grain.")
        if not key and strategy!="append": st.warning("Define a reliable unique key.")
        if strategy=="append" and (updates or deletes): st.warning("Append may be unsafe when records are corrected or deleted.")
        if late: st.warning("Late-arriving data needs a documented lookback/capture strategy.")
        if currency: st.warning("Validate monetary precision, scale, currency and rounding.")
        st.info("Replace source_model and add the incremental filter according to your project rules.")

with tabs[1]:
    st.header("🧩 Macro Workbench")
    operation=st.selectbox("Macro task",["Create a macro","Convert SQL into a macro","Debug a macro","Review whether a macro is needed","Refactor a macro"])
    name=st.text_input("Macro name",placeholder="format_amount")
    request=st.text_area("What should it do?",height=120)
    if st.button("Generate Macro Template"):
        macro=name.strip() or "my_macro"
        st.code("""{% macro """+macro+"""(column_name) %}
    -- Add reusable parameterized logic here.
    {{ column_name }}
{% endmacro %}""",language="jinja")
        st.write("Checklist: put reusable macros in the project's macros/ directory; avoid macros for one-off SQL; test representative inputs and edge cases.")
        if request: st.write("Requested behavior:",request)

with tabs[2]:
    st.header("📸 Snapshot Workbench")
    st.write("Generate a standard dbt snapshot starting point.")
    key2=st.text_input("Business key",placeholder="account_id")
    updated=st.text_input("Updated timestamp",placeholder="updated_at")
    if st.button("Generate Snapshot Template"):
        k=key2.strip() or "business_key"; u=updated.strip() or "updated_at"
        st.code("""{% snapshot account_history %}

{{ config(
    target_schema='snapshots',
    unique_key='"""+k+"""',
    strategy='timestamp',
    updated_at='"""+u+"""'
) }}

select *
from {{ ref('source_model') }}

{% endsnapshot %}""",language="sql")
        st.warning("Verify the key is unique at the snapshot grain and the timestamp is reliable.")

with tabs[3]:
    st.header("🧪 Data Quality Workbench")
    grain2=st.text_input("Model grain",key="qgrain",placeholder="One row per transaction")
    important=st.text_area("Important columns",key="qcols",placeholder="transaction_id\\naccount_id\\namount\\ncurrency\\ntransaction_date")
    if st.button("Generate Test Plan"):
        for x in quality_tests(grain2,important): st.write("☐ "+x)
        st.subheader("schema.yml starter")
        st.code("version: 2\\n\\nmodels:\\n  - name: your_model\\n    columns:\\n"+''.join("      - name: "+c+"\\n        # Add approved tests\\n" for c in cols(important)),language="yaml")

with tabs[4]:
    st.header("🌳 Lineage & Impact Workbench")
    item=st.text_input("What are you changing?",placeholder="dim_account.amount")
    change=st.text_area("What change are you considering?",height=100)
    if st.button("Generate Impact Checklist"):
        for x in ["Search dbt refs and sources for direct dependencies.","Search downstream models, exposures and reports.","Compile affected models and inspect generated SQL.","Run affected model tests.","Compare row counts and important financial totals before/after.","Check incremental and full-refresh behavior.","Check schema/column compatibility for downstream consumers."]: st.write("☐ "+x)
        st.info("Complete lineage cannot be inferred without your project/catalog. This is a checklist, not an automatic lineage scan.")

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
