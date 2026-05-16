# =========================
# FILE : app.py
# VIGIOR AI - Advanced Version
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
# PAGE
# =========================

st.set_page_config(
    page_title="VIGIOR AI",
    layout="wide"
)

st.title("🦴 VIGIOR AI")
st.subheader("AI Predictive Assistant for Tibial Plateau Fractures")

st.markdown("---")

# =========================
# MENU
# =========================

menu = st.sidebar.selectbox(
    "Navigation",
    [
        "New Patient",
        "Patient Database"
    ]
)

# =========================
# LOGISTIC FUNCTION
# =========================

def logistic(x):
    return 1 / (1 + math.exp(-x))

# =========================
# RISK CALCULATION
# =========================

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

    # Age
    if age > 60:
        infection_score += 1
        skin_score += 1

    # Diabetes
    if diabetes == "Yes":
        infection_score += 2

    # Smoking
    if smoking == "Yes":
        infection_score += 2

    # BMI
    if bmi > 30:
        infection_score += 1

    # High-energy trauma
    if high_energy == "Yes":
        compartment_score += 2
        skin_score += 2

    # Open fracture
    if open_fracture == "Yes":
        infection_score += 3
        skin_score += 2

    # Schatzker
    if schatzker in ["V", "VI"]:
        infection_score += 2
        compartment_score += 2
        skin_score += 1

    # Soft tissue
    if soft_tissue == "Moderate":
        skin_score += 2

    if soft_tissue == "Severe":
        infection_score += 2
        skin_score += 4

    # Blisters
    if blisters == "Yes":
        skin_score += 3

    # Compartment syndrome
    if compartment_signs == "Yes":
        compartment_score += 5

    # External fixation
    if external_fixator == "Yes":
        infection_score += 1

    # Delay
    if surgical_delay > 10:
        infection_score += 1

    infection_risk = round(logistic(infection_score / 2) * 100, 1)
    compartment_risk = round(logistic(compartment_score / 2) * 100, 1)
    skin_risk = round(logistic(skin_score / 2) * 100, 1)

    return infection_risk, compartment_risk, skin_risk

# =========================
# TREATMENT ENGINE
# =========================

def treatment_strategy(
    infection,
    compartment,
    skin,
    schatzker,
    open_fracture,
    soft_tissue,
    blisters
):

    strategies = []

    # ---------------------
    # STANDARD ORIF
    # ---------------------

    if (
        infection < 50
        and skin < 50
        and compartment < 50
    ):

        strategies.append("""
### ✅ Early Open Reduction Internal Fixation (ORIF)

**Why?**
- Soft tissues acceptable
- Low infection risk
- Low compartment syndrome risk
- Allows anatomic reduction and stable fixation

**Goal**
- Early mobilization
- Articular restoration
- Better alignment
""")

    # ---------------------
    # MINIMALLY INVASIVE
    # ---------------------

    if (
        skin >= 50
        or soft_tissue == "Moderate"
    ):

        strategies.append("""
### ✅ Minimally Invasive Osteosynthesis (MIPO)

**Why?**
- Reduces additional soft tissue damage
- Preserves vascularization
- Decreases infection risk

**Goal**
- Biological fixation
- Less skin suffering
- Safer in swollen knees
""")

    # ---------------------
    # EXTERNAL FIXATION
    # ---------------------

    if (
        skin >= 70
        or blisters == "Yes"
        or soft_tissue == "Severe"
    ):

        strategies.append("""
### ✅ Temporary External Fixation

**Why?**
- Severe soft tissue compromise
- Important swelling or skin blisters
- Unsafe immediate ORIF

**Goal**
- Protect soft tissues
- Allow edema reduction
- Delay definitive surgery safely
""")

    # ---------------------
    # DELAYED ORIF
    # ---------------------

    if skin >= 70:

        strategies.append("""
### ✅ Delayed ORIF (7–14 days)

**Why?**
- High skin complication risk
- Better to wait for wrinkle sign
- Reduces necrosis and infection

**Goal**
- Safer definitive fixation
- Improved wound healing
""")

    # ---------------------
    # TRACTION
    # ---------------------

    if (
        skin >= 80
        and infection >= 70
    ):

        strategies.append("""
### ✅ Traction + Strict Monitoring

**Why?**
- Very high soft tissue risk
- Surgery initially dangerous

**Goal**
- Temporary alignment
- Pain control
- Soft tissue recovery before surgery
""")

    # ---------------------
    # COMPARTMENT
    # ---------------------

    if compartment >= 70:

        strategies.append("""
### ⚠ Compartment Syndrome Surveillance

**Why?**
- High predicted compartment syndrome risk

**Monitoring**
- Pain escalation
- Pain on passive stretch
- Tense compartments
- Neurologic signs

**Possible Action**
- Emergency fasciotomy if clinical syndrome confirmed
""")

    # ---------------------
    # OPEN FRACTURE
    # ---------------------

    if open_fracture == "Yes":

        strategies.append("""
### ⚠ Open Fracture Protocol

**Why?**
- Major infection risk

**Management**
- Urgent antibiotics
- Surgical debridement
- Irrigation
- Staged fixation if necessary
""")

    return "\n".join(strategies)

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

    if st.button("🔍 Predict Risks"):

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

        treatment = treatment_strategy(
            infection,
            compartment,
            skin,
            schatzker,
            open_fracture,
            soft_tissue,
            blisters
        )

        st.success("Prediction completed")

        c1, c2, c3 = st.columns(3)

        with c1:
            st.metric(
                "Infection Risk",
                f"{infection}%"
            )

        with c2:
            st.metric(
                "Compartment Syndrome Risk",
                f"{compartment}%"
            )

        with c3:
            st.metric(
                "Skin Complication Risk",
                f"{skin}%"
            )

        st.markdown("---")

        st.subheader("🩺 Suggested Management")

        st.markdown(treatment)

        st.markdown("---")

        follow_up = st.text_area(
            "Follow-up",
            placeholder="infection, pseudarthrosis, revision surgery..."
        )

        if st.button("💾 Save Patient"):

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
                treatment,
                follow_up
            ))

            conn.commit()

            st.success(f"Patient saved : {patient_id}")

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
Clinical judgment remains mandatory.
""")
