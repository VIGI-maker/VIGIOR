import streamlit as st
import pandas as pd
import sqlite3
import uuid
from datetime import datetime

# =========================================================
# CONFIG
# =========================================================

st.set_page_config(page_title="VIGIOR FIX", layout="wide")

st.title("🏥 VIGIOR FIX SAVE VERSION")

# =========================================================
# DATABASE SAFE RESET FIX
# =========================================================

conn = sqlite3.connect("vigor.db", check_same_thread=False)
cursor = conn.cursor()

# 🔥 IMPORTANT FIX: DROP OLD TABLE (avoids mismatch crash)
cursor.execute("DROP TABLE IF EXISTS patients")

cursor.execute("""
CREATE TABLE patients (
    id TEXT,
    patient_number TEXT,
    date TEXT,

    age INTEGER,
    sex TEXT,
    diabetes TEXT,
    smoking TEXT,
    bmi REAL,

    schatzker TEXT,
    soft_tissue TEXT,
    open_fracture TEXT,
    compartment TEXT,

    recommendation TEXT,

    treatment TEXT,
    outcome TEXT,
    infection TEXT,
    secondary TEXT,
    revision TEXT
)
""")

conn.commit()

# =========================================================
# SIMPLE STRATEGY
# =========================================================

def strategy(schatzker, soft_tissue, open_fracture, compartment):

    if compartment == "Yes":
        return "External fixation → fasciotomy if needed → delayed ORIF"

    if open_fracture == "Yes":
        return "Debridement → temporary fixation → staged ORIF"

    if soft_tissue == "Severe":
        return "External fixation → delayed MIPO/ORIF"

    if schatzker in ["V", "VI"]:
        return "Staged strategy (ExFix → ORIF)"

    return "Early ORIF"

# =========================================================
# SESSION STATE
# =========================================================

if "case" not in st.session_state:
    st.session_state.case = None

# =========================================================
# UI
# =========================================================

menu = st.sidebar.selectbox("Menu", ["AI Evaluation"])

if menu == "AI Evaluation":

    st.header("🧠 AI Evaluation")

    with st.form("form"):

        col1, col2 = st.columns(2)

        with col1:
            age = st.number_input("Age", 18, 100, 40)
            sex = st.selectbox("Sex", ["Male", "Female"])
            diabetes = st.selectbox("Diabetes", ["No", "Yes"])
            smoking = st.selectbox("Smoking", ["No", "Yes"])
            bmi = st.number_input("BMI", 15.0, 50.0, 25.0)

        with col2:
            schatzker = st.selectbox("Schatzker", ["I","II","III","IV","V","VI"])
            soft_tissue = st.selectbox("Soft tissue", ["Mild","Moderate","Severe"])
            open_fracture = st.selectbox("Open fracture", ["No","Yes"])
            compartment = st.selectbox("Compartment", ["No","Yes"])

        submit = st.form_submit_button("Evaluate")

    if submit:

        rec = strategy(schatzker, soft_tissue, open_fracture, compartment)

        st.session_state.case = {
            "age": age,
            "sex": sex,
            "diabetes": diabetes,
            "smoking": smoking,
            "bmi": bmi,
            "schatzker": schatzker,
            "soft_tissue": soft_tissue,
            "open_fracture": open_fracture,
            "compartment": compartment,
            "rec": rec
        }

    if st.session_state.case:

        c = st.session_state.case

        st.success(c["rec"])

        st.markdown("---")
        st.subheader("💾 Register Patient")

        with st.form("save"):

            patient_number = st.text_input("Patient ID")

            treatment = st.selectbox(
                "Treatment performed",
                ["Early ORIF", "MIPO", "External Fixation", "Traction", "Staged ORIF"]
            )

            outcome = st.selectbox("Outcome", ["A","B","C"])
            infection = st.selectbox("Infection", ["No","Yes"])
            secondary = st.selectbox("Secondary displacement", ["No","Yes"])
            revision = st.selectbox("Revision", ["No","Yes"])

            save = st.form_submit_button("Save Patient")

        if save:

            pid = "VIG-" + str(uuid.uuid4())[:8]

            # ✅ FIX: EXPLICIT COLUMN INSERT (NO MORE SQLITE ERROR)
            cursor.execute("""
            INSERT INTO patients (
                id, patient_number, date,
                age, sex, diabetes, smoking, bmi,
                schatzker, soft_tissue, open_fracture, compartment,
                recommendation,
                treatment, outcome, infection, secondary, revision
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                pid,
                patient_number,
                str(datetime.now()),
                c["age"],
                c["sex"],
                c["diabetes"],
                c["smoking"],
                c["bmi"],
                c["schatzker"],
                c["soft_tissue"],
                c["open_fracture"],
                c["compartment"],
                c["rec"],
                treatment,
                outcome,
                infection,
                secondary,
                revision
            ))

            conn.commit()

            st.success(f"Patient saved → {pid}")

            st.session_state.case = None
