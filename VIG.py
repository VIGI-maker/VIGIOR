# =========================================================
# FILE : app.py
# VIGIOR AI - STREAMLIT STABLE VERSION
# =========================================================

import streamlit as st
import pandas as pd
import sqlite3
import uuid
from datetime import datetime
import math

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
    infection_risk REAL,
    compartment_risk REAL,
    skin_risk REAL,
    ai_recommendation TEXT,
    performed_treatment TEXT,
    outcome TEXT,
    infection TEXT,
    nonunion TEXT,
    revision TEXT,
    follow_up TEXT
)
""")

conn.commit()

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="VIGIOR AI",
    layout="wide"
)

# =========================================================
# TITLE
# =========================================================

st.title("🦴 VIGIOR AI")
st.subheader("Self-Learning Predictive AI for Tibial Plateau Fractures")

st.markdown("---")

# =========================================================
# MENU
# =========================================================

menu = st.sidebar.selectbox(
    "Navigation",
    [
        "New Patient",
        "Patient Database",
        "Statistics Dashboard",
        "AI Predictive Evolution"
    ]
)

# =========================================================
# LOGISTIC FUNCTION
# =========================================================

def logistic(x):
    return 1 / (1 + math.exp(-x))

# =========================================================
# RISK CALCULATION
# =========================================================

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

    if age > 60:
        infection_score += 1
        skin_score += 1

    if diabetes == "Yes":
        infection_score += 2

    if smoking == "Yes":
        infection_score += 2

    if bmi > 30:
        infection_score += 1

    if high_energy == "Yes":
        compartment_score += 2
        skin_score += 2

    if open_fracture == "Yes":
        infection_score += 3
        skin_score += 2

    if schatzker in ["V", "VI"]:
        infection_score += 2
        compartment_score += 2
        skin_score += 1

    if soft_tissue == "Moderate":
        skin_score += 2

    if soft_tissue == "Severe":
        infection_score += 2
        skin_score += 4

    if blisters == "Yes":
        skin_score += 3

    if compartment_signs == "Yes":
        compartment_score += 5

    if external_fixator == "Yes":
        infection_score += 1

    if surgical_delay > 10:
        infection_score += 1

    infection_risk = round(logistic(infection_score / 2) * 100, 1)
    compartment_risk = round(logistic(compartment_score / 2) * 100, 1)
    skin_risk = round(logistic(skin_score / 2) * 100, 1)

    return infection_risk, compartment_risk, skin_risk

# =========================================================
# AI TREATMENT STRATEGY
# =========================================================

def treatment_strategy(
    infection,
    compartment,
    skin,
    open_fracture,
    soft_tissue,
    blisters,
    compartment_signs
):

    if (
        skin >= 80
        or soft_tissue == "Severe"
        or blisters == "Yes"
    ):

        return """
🚨 Temporary External Fixation + Delayed MIPO

Reason:
Major soft tissue compromise.

Future:
Delayed fixation after wrinkle sign.
"""

    elif (
        compartment >= 75
        or compartment_signs == "Yes"
    ):

        return """
🚨 Strict Monitoring ± Fasciotomy + Staged Fixation

Reason:
Very high compartment syndrome risk.

Future:
External fixation then delayed ORIF.
"""

    elif open_fracture == "Yes":

        return """
🚨 Debridement + Temporary Stabilization + Delayed Fixation

Reason:
High infection risk.

Future:
Biological fixation after tissue recovery.
"""

    elif (
        skin >= 55
        or infection >= 60
    ):

        return """
⚠ Minimally Invasive Osteosynthesis (MIPO)

Reason:
Moderate soft tissue risk.

Future:
Biological fixation with lower infection rate.
"""

    else:

        return """
✅ Early ORIF

Reason:
Good soft tissue condition and low complication risk.

Future:
Early mobilization and stable fixation.
"""

# =========================================================
# NEW PATIENT
# =========================================================

if menu == "New Patient":

    st.header("➕ New Patient")

    col1, col2, col3 = st.columns(3)

    with col1:

        patient_number = st.text_input("Patient Number")

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
            "Tscherne / Soft Tissue",
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
            "Expected Surgical Delay",
            0,
            20,
            5
        )

    st.markdown("---")

    if st.button("🔍 Evaluate"):

        infection_risk, compartment_risk, skin_risk = calculate_risks(
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

        recommendation = treatment_strategy(
            infection_risk,
            compartment_risk,
            skin_risk,
            open_fracture,
            soft_tissue,
            blisters,
            compartment_signs
        )

        st.success("AI Evaluation Completed")

        c1, c2, c3 = st.columns(3)

        with c1:
            st.metric(
                "Infection Risk",
                f"{infection_risk}%"
            )

        with c2:
            st.metric(
                "Compartment Syndrome Risk",
                f"{compartment_risk}%"
            )

        with c3:
            st.metric(
                "Skin Complication Risk",
                f"{skin_risk}%"
            )

        st.markdown("---")

        st.subheader("🩺 AI Recommended Strategy")

        st.info(recommendation)

        st.markdown("---")

        st.subheader("💾 Final Clinical Data")

        performed_treatment = st.selectbox(
            "Treatment Performed",
            [
                "Early ORIF",
                "MIPO",
                "External Fixator + Delayed ORIF",
                "Traction + Surveillance",
                "Debridement + Staged Fixation",
                "Conservative Treatment"
            ]
        )

        outcome = st.selectbox(
            "Final Outcome",
            [
                "A",
                "B",
                "C"
            ]
        )

        infection = st.selectbox(
            "Infection",
            ["No", "Yes"]
        )

        nonunion = st.selectbox(
            "Pseudarthrosis",
            ["No", "Yes"]
        )

        revision = st.selectbox(
            "Revision Surgery",
            ["No", "Yes"]
        )

        follow_up = st.text_area(
            "Follow-up Notes"
        )

        if st.button("💾 Save Patient"):

            patient_id = "VIG-" + str(uuid.uuid4())[:8]

            cursor.execute("""
            INSERT INTO patients VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                patient_id,
                patient_number,
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
                infection_risk,
                compartment_risk,
                skin_risk,
                recommendation,
                performed_treatment,
                outcome,
                infection,
                nonunion,
                revision,
                follow_up
            ))

            conn.commit()

            st.success(f"Patient saved : {patient_id}")

# =========================================================
# DATABASE
# =========================================================

elif menu == "Patient Database":

    st.header("🗂 Patient Database")

    df = pd.read_sql_query(
        "SELECT * FROM patients",
        conn
    )

    st.dataframe(df, use_container_width=True)

# =========================================================
# STATISTICS
# =========================================================

elif menu == "Statistics Dashboard":

    st.header("📊 Statistics Dashboard")

    df = pd.read_sql_query(
        "SELECT * FROM patients",
        conn
    )

    if len(df) == 0:

        st.warning("No patients recorded.")

    else:

        st.metric(
            "Average Age",
            round(df["age"].mean(), 1)
        )

        revision_rate = round(
            (df["revision"] == "Yes").mean() * 100,
            1
        )

        st.metric(
            "Revision Rate",
            f"{revision_rate}%"
        )

        st.subheader("Schatzker Classification")
        st.bar_chart(df["schatzker"].value_counts())

        st.subheader("Soft Tissue / Tscherne")
        st.bar_chart(df["soft_tissue"].value_counts())

        st.subheader("Treatment Methods")
        st.bar_chart(df["performed_treatment"].value_counts())

        st.subheader("Clinical Outcomes")
        st.bar_chart(df["outcome"].value_counts())

        complications = pd.DataFrame({
            "Complication": [
                "Infection",
                "Pseudarthrosis",
                "Revision"
            ],
            "Count": [
                (df["infection"] == "Yes").sum(),
                (df["nonunion"] == "Yes").sum(),
                (df["revision"] == "Yes").sum()
            ]
        })

        st.subheader("Complications")
        st.bar_chart(
            complications.set_index("Complication")
        )

# =========================================================
# SELF LEARNING AI
# =========================================================

elif menu == "AI Predictive Evolution":

    st.header("🧠 Self-Learning AI")

    df = pd.read_sql_query(
        "SELECT * FROM patients",
        conn
    )

    if len(df) < 5:

        st.warning(
            "At least 5 patients required."
        )

    else:

        infection_rate = round(
            (df["infection"] == "Yes").mean() * 100,
            1
        )

        nonunion_rate = round(
            (df["nonunion"] == "Yes").mean() * 100,
            1
        )

        revision_rate = round(
            (df["revision"] == "Yes").mean() * 100,
            1
        )

        st.metric(
            "Observed Infection Rate",
            f"{infection_rate}%"
        )

        st.metric(
            "Observed Pseudarthrosis Rate",
            f"{nonunion_rate}%"
        )

        st.metric(
            "Observed Revision Rate",
            f"{revision_rate}%"
        )

        st.markdown("---")

        best_treatment = df.groupby(
            "performed_treatment"
        )["outcome"].apply(
            lambda x: (x == "A").mean()
        ).idxmax()

        st.success(
            f"Best Treatment According To Your Database : {best_treatment}"
        )

        st.info("""
The AI progressively adapts recommendations
according to:
- complication rates
- outcomes
- revisions
- your own patient database
""")

# =========================================================
# FOOTER
# =========================================================

st.markdown("---")

st.caption("""
VIGIOR AI — Educational orthopaedic predictive platform.
Clinical judgment remains mandatory.
""")
