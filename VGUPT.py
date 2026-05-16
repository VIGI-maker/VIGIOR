import streamlit as st
import pandas as pd
import sqlite3
import uuid
from datetime import datetime

# =========================================================
# DATABASE
# =========================================================

conn = sqlite3.connect("vigor.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS patients (
    id TEXT,
    patient_number TEXT,
    date TEXT,
    age INTEGER,
    schatzker TEXT,
    soft_tissue TEXT,
    risk REAL,
    treatment TEXT,
    outcome TEXT,
    infection TEXT,
    pseudarthrosis TEXT,
    revision TEXT
)
""")

conn.commit()

# =========================================================
# APP CONFIG
# =========================================================

st.set_page_config(page_title="VIGIOR AI", layout="wide")

st.title("🦴 VIGIOR AI")
st.subheader("Orthopaedic Predictive System (Stable Version)")

menu = st.sidebar.selectbox(
    "Navigation",
    ["New Patient", "Database", "Statistics", "AI Insight"]
)

# =========================================================
# SIMPLE RISK MODEL
# =========================================================

def compute_risk(age, schatzker, soft_tissue):

    risk = age / 3

    if schatzker in ["V", "VI"]:
        risk += 25

    if soft_tissue == "Moderate":
        risk += 10
    elif soft_tissue == "Severe":
        risk += 30

    return min(risk, 95)

# =========================================================
# TREATMENT LOGIC
# =========================================================

def treatment_decision(risk):

    if risk > 70:
        return "External Fixation + Delayed ORIF (Damage Control Strategy)"
    elif risk > 50:
        return "MIPO (Minimally Invasive Osteosynthesis)"
    else:
        return "Early ORIF"

# =========================================================
# NEW PATIENT
# =========================================================

if menu == "New Patient":

    st.header("➕ New Patient Entry")

    # FORM = STABLE STREAMLIT FIX
    with st.form("patient_form"):

        patient_number = st.text_input("Patient Number")

        age = st.number_input("Age", 18, 100, 40)

        schatzker = st.selectbox(
            "Schatzker Classification",
            ["I", "II", "III", "IV", "V", "VI"]
        )

        soft_tissue = st.selectbox(
            "Soft Tissue Condition",
            ["Mild", "Moderate", "Severe"]
        )

        st.markdown("---")
        st.subheader("Clinical Outcome (after treatment)")

        treatment = st.selectbox(
            "Treatment Performed",
            [
                "Early ORIF",
                "MIPO",
                "External Fixation + Delayed ORIF",
                "Traction + Monitoring",
                "Conservative"
            ]
        )

        outcome = st.selectbox("Outcome", ["A", "B", "C"])

        infection = st.selectbox("Infection", ["No", "Yes"])
        pseudarthrosis = st.selectbox("Pseudarthrosis", ["No", "Yes"])
        revision = st.selectbox("Revision Surgery", ["No", "Yes"])

        submitted = st.form_submit_button("Predict + Save Patient")

    # =====================================================
    # AFTER SUBMIT
    # =====================================================

    if submitted:

        risk = compute_risk(age, schatzker, soft_tissue)
        decision = treatment_decision(risk)

        st.metric("Predicted Risk (%)", f"{risk:.1f}%")

        st.success(f"Recommended Strategy: {decision}")

        st.markdown("---")

        # SAVE TO DATABASE
        patient_id = "VIG-" + str(uuid.uuid4())[:8]

        cursor.execute("""
        INSERT INTO patients VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            patient_id,
            patient_number,
            str(datetime.now()),
            age,
            schatzker,
            soft_tissue,
            risk,
            treatment,
            outcome,
            infection,
            pseudarthrosis,
            revision
        ))

        conn.commit()

        st.success(f"Patient saved successfully → {patient_id}")

# =========================================================
# DATABASE VIEW
# =========================================================

elif menu == "Database":

    st.header("📊 Patient Database")

    df = pd.read_sql_query("SELECT * FROM patients", conn)

    st.dataframe(df, use_container_width=True)

# =========================================================
# STATISTICS DASHBOARD
# =========================================================

elif menu == "Statistics":

    st.header("📈 Statistics")

    df = pd.read_sql_query("SELECT * FROM patients", conn)

    if len(df) == 0:
        st.warning("No data yet")
    else:

        st.metric("Total Patients", len(df))
        st.metric("Mean Age", round(df["age"].mean(), 1))

        st.subheader("Schatzker Distribution")
        st.bar_chart(df["schatzker"].value_counts())

        st.subheader("Treatment Distribution")
        st.bar_chart(df["treatment"].value_counts())

        st.subheader("Outcomes")
        st.bar_chart(df["outcome"].value_counts())

        st.subheader("Complications")

        st.bar_chart({
            "Infection": (df["infection"] == "Yes").sum(),
            "Pseudarthrosis": (df["pseudarthrosis"] == "Yes").sum(),
            "Revision": (df["revision"] == "Yes").sum()
        })

# =========================================================
# AI INSIGHT (SELF LEARNING SIMPLE)
# =========================================================

elif menu == "AI Insight":

    st.header("🧠 AI Learning from Your Data")

    df = pd.read_sql_query("SELECT * FROM patients", conn)

    if len(df) < 5:
        st.warning("Need at least 5 patients for AI learning")
    else:

        best = df.groupby("treatment")["outcome"].apply(
            lambda x: (x == "A").mean()
        ).idxmax()

        st.success(f"Best performing treatment in your dataset: {best}")

        st.info("""
AI concept:
- learns from your real cases
- compares treatment outcomes
- adapts recommendations over time
        """)
