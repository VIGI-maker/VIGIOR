# =========================
# FILE : app.py
# VIGIOR AI - Tibial Plateau Fracture Predictor
# Ready for GitHub + Streamlit Cloud
# =========================

import streamlit as st
import pandas as pd
import sqlite3
import uuid
from datetime import datetime
import math

# =========================
# DATABASE
# =========================

conn = sqlite3.connect("vigor.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS patients (
    id TEXT,
    date TEXT,
    age INTEGER,
    sex TEXT,
    diabetes TEXT,
    smoking TEXT,
    bmi REAL,
    high_energy TEXT,
    open_fracture TEXT,
    schatzker TEXT,
    soft_tissue TEXT,
    blisters TEXT,
    compartment_signs TEXT,
    external_fixator TEXT,
    surgical_delay INTEGER,
    infection REAL,
    compartment REAL,
    skin REAL,
    recommendation TEXT,
    follow_up TEXT
)
""")

conn.commit()

# =========================
# PAGE CONFIG
# =========================

st.set_page_config(
    page_title="VIGIOR AI",
    layout="wide"
)

# =========================
# TITLE
# =========================

st.title("🦴 VIGIOR AI")
st.subheader("Predictive AI for Tibial Plateau Fractures")

st.markdown("---")

# =========================
# SIDEBAR
# =========================

menu = st.sidebar.selectbox(
    "Menu",
    [
        "New Patient",
        "Patient Database"
    ]
)

# =========================
# RISK CALCULATOR
# =========================

def logistic(x):
    return 1 / (1 + math.exp(-x))

def calculate_risks(
    age,
    diabetes,
    smoking,
    bmi,
    high_energy,
    open_fracture,
    schatzker,
    soft_tissue,
    blisters,
    compartment_signs,
    external_fixator,
    surgical_delay
):

    infection_score = 0
    compartment_score = 0
    skin_score = 0

    # AGE
    if age > 60:
        infection_score += 1
        skin_score += 1

    # DIABETES
    if diabetes == "Yes":
        infection_score += 2

    # SMOKING
    if smoking == "Yes":
        infection_score += 2

    # BMI
    if bmi > 30:
        infection_score += 1

    # HIGH ENERGY
    if high_energy == "Yes":
        compartment_score += 2
        skin_score += 2

    # OPEN FRACTURE
    if open_fracture == "Yes":
        infection_score += 3
        skin_score += 2

    # SCHATZKER
    if schatzker in ["V", "VI"]:
        infection_score += 2
        compartment_score += 2

    # SOFT TISSUE
    if soft_tissue == "Severe":
        infection_score += 2
        skin_score += 3

    # BLISTERS
    if blisters == "Yes":
        skin_score += 3

    # COMPARTMENT SIGNS
    if compartment_signs == "Yes":
        compartment_score += 4

    # EXTERNAL FIXATOR
    if external_fixator == "Yes":
        infection_score += 1

    # DELAY
    if surgical_delay > 10:
        infection_score += 1

    # LOGISTIC
    infection_risk = round(logistic(infection_score / 2) * 100, 1)
    compartment_risk = round(logistic(compartment_score / 2) * 100, 1)
    skin_risk = round(logistic(skin_score / 2) * 100, 1)

    return infection_risk, compartment_risk, skin_risk

# =========================
# RECOMMENDATION ENGINE
# =========================

def recommendation_engine(
    infection,
    compartment,
    skin
):

    recommendation = []

    if skin > 70:
        recommendation.append(
            "⚠ Delay ORIF until soft tissue improvement (7-14 days)"
        )

    if compartment > 70:
        recommendation.append(
            "⚠ Strict compartment syndrome surveillance"
        )

    if infection > 70:
        recommendation.append(
            "⚠ Consider minimally invasive fixation strategy"
        )

    if infection < 50 and skin < 50:
        recommendation.append(
            "✅ Standard ORIF possible"
        )

    if skin > 60:
        recommendation.append(
            "✅ Consider temporary external fixation"
        )

    return "\n".join(recommendation)

# =========================
# NEW PATIENT
# =========================

if menu == "New Patient":

    st.header("➕ New Patient")

    col1, col2, col3 = st.columns(3)

    with col1:

        age = st.number_input("Age", 18, 100, 40)

        sex = st.selectbox(
            "Sex",
            ["Male", "Female"]
        )

        diabetes = st.selectbox(
            "Diabetes",
            ["No", "Yes"]
        )

        smoking = st.selectbox(
            "Smoking",
            ["No", "Yes"]
        )

    with col2:

        bmi = st.number_input(
            "BMI",
            15.0,
            50.0,
            25.0
        )

        high_energy = st.selectbox(
            "High Energy Trauma",
            ["No", "Yes"]
        )

        open_fracture = st.selectbox(
            "Open Fracture",
            ["No", "Yes"]
        )

        schatzker = st.selectbox(
            "Schatzker Type",
            ["I", "II", "III", "IV", "V", "VI"]
        )

    with col3:

        soft_tissue = st.selectbox(
            "Soft Tissue Injury",
            ["Mild", "Moderate", "Severe"]
        )

        blisters = st.selectbox(
            "Skin Blisters",
            ["No", "Yes"]
        )

        compartment_signs = st.selectbox(
            "Compartment Syndrome Signs",
            ["No", "Yes"]
        )

        external_fixator = st.selectbox(
            "Temporary External Fixator",
            ["No", "Yes"]
        )

        surgical_delay = st.slider(
            "Expected Surgical Delay (days)",
            0,
            20,
            5
        )

    st.markdown("---")

    if st.button("🔍 Calculate Risks"):

        infection, compartment, skin = calculate_risks(
            age,
            diabetes,
            smoking,
            bmi,
            high_energy,
            open_fracture,
            schatzker,
            soft_tissue,
            blisters,
            compartment_signs,
            external_fixator,
            surgical_delay
        )

        recommendation = recommendation_engine(
            infection,
            compartment,
            skin
        )

        st.success("AI Prediction Completed")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Infection Risk",
                f"{infection}%"
            )

        with col2:
            st.metric(
                "Compartment Syndrome Risk",
                f"{compartment}%"
            )

        with col3:
            st.metric(
                "Skin Complication Risk",
                f"{skin}%"
            )

        st.markdown("---")

        st.subheader("📋 AI Recommendations")

        st.info(recommendation)

        st.markdown("---")

        st.subheader("💾 Save Patient")

        follow_up = st.text_area(
            "Future Follow-up",
            placeholder="infection, pseudarthrosis, revision surgery..."
        )

        if st.button("Save Patient"):

            patient_id = "VIG-" + str(uuid.uuid4())[:8]

            cursor.execute("""
            INSERT INTO patients VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                patient_id,
                str(datetime.now()),
                age,
                sex,
                diabetes,
                smoking,
                bmi,
                high_energy,
                open_fracture,
                schatzker,
                soft_tissue,
                blisters,
                compartment_signs,
                external_fixator,
                surgical_delay,
                infection,
                compartment,
                skin,
                recommendation,
                follow_up
            ))

            conn.commit()

            st.success(f"Patient Saved : {patient_id}")

# =========================
# DATABASE
# =========================

if menu == "Patient Database":

    st.header("🗂 Patient Database")

    df = pd.read_sql_query(
        "SELECT * FROM patients",
        conn
    )

    st.dataframe(df, use_container_width=True)

    csv = df.to_csv(index=False).encode("utf-8")

    st.download_button(
        "⬇ Download CSV",
        csv,
        "vigor_patients.csv",
        "text/csv"
    )

# =========================
# FOOTER
# =========================

st.markdown("---")

st.caption("""
VIGIOR AI - Educational predictive tool for orthopaedic surgery.
Not intended to replace medical judgment.
""")
