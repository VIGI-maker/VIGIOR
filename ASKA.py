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
    secondary_displacement TEXT,
    revision TEXT
)
""")

conn.commit()

# =========================================================
# SESSION MEMORY (IMPORTANT FOR LEARNING AI)
# =========================================================

if "eval" not in st.session_state:
    st.session_state.eval = None

# =========================================================
# SIMPLE MENU
# =========================================================

menu = st.sidebar.selectbox(
    "Navigation",
    ["AI Evaluation", "Register Patient", "AI Learning"]
)

st.title("🦴 VIGIOR AI - LEARNING SYSTEM")

# =========================================================
# 1. AI EVALUATION (STRATEGY ONLY)
# =========================================================

if menu == "AI Evaluation":

    st.header("🧠 AI Recommended Strategy")

    with st.form("eval"):

        col1, col2 = st.columns(2)

        with col1:
            age = st.number_input("Age", 18, 100, 40)
            schatzker = st.selectbox("Schatzker", ["I","II","III","IV","V","VI"])
            soft_tissue = st.selectbox("Soft tissue", ["Mild","Moderate","Severe"])

        with col2:
            open_fracture = st.selectbox("Open fracture", ["No","Yes"])
            compartment = st.selectbox("Compartment signs", ["No","Yes"])
            smoking = st.selectbox("Smoking", ["No","Yes"])

        submit = st.form_submit_button("Generate Strategy")

    if submit:

        # =================================================
        # SIMPLE LOGIC (NO RISK DISPLAY)
        # =================================================

        if compartment == "Yes":
            strategy = """
🚨 STRATEGY: External Fixation + Monitoring

WHY:
- suspected compartment syndrome
- risk of muscle ischemia

NEXT STEP:
- possible fasciotomy
- delayed definitive fixation
"""

        elif open_fracture == "Yes":
            strategy = """
🚨 STRATEGY: Debridement + Temporary Stabilization

WHY:
- open fracture contamination risk

NEXT STEP:
- staged ORIF after infection control
"""

        elif soft_tissue == "Severe":
            strategy = """
⚠ STRATEGY: External Fixation → Delayed ORIF/MIPO

WHY:
- severe soft tissue condition

NEXT STEP:
- wait for swelling reduction (wrinkle sign)
"""

        else:
            strategy = """
✅ STRATEGY: Early ORIF

WHY:
- acceptable soft tissue conditions
- stable fracture pattern

NEXT STEP:
- early anatomical reduction + fixation
"""

        st.success(strategy)

        # SAVE TEMP IN MEMORY
        st.session_state.eval = {
            "age": age,
            "schatzker": schatzker,
            "soft_tissue": soft_tissue,
            "open_fracture": open_fracture,
            "compartment": compartment,
            "smoking": smoking,
            "recommendation": strategy
        }

# =========================================================
# 2. REGISTER PATIENT
# =========================================================

elif menu == "Register Patient":

    st.header("💾 Patient Registration")

    if st.session_state.eval is None:
        st.warning("Run AI Evaluation first")
        st.stop()

    d = st.session_state.eval

    with st.form("save"):

        patient_id = st.text_input("Patient ID")

        st.subheader("Treatment performed")
        treatment = st.selectbox(
            "Treatment",
            ["Early ORIF", "MIPO", "External Fixation", "Traction", "Conservative"]
        )

        st.subheader("Outcomes")
        outcome = st.selectbox("Functional result", ["A","B","C"])
        infection = st.selectbox("Infection", ["No","Yes"])
        secondary = st.selectbox("Secondary displacement", ["No","Yes"])
        revision = st.selectbox("Revision surgery", ["No","Yes"])

        save = st.form_submit_button("Save Patient")

    if save:

        pid = "VIG-" + str(uuid.uuid4())[:8]

        cursor.execute("""
        INSERT INTO patients VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            pid,
            str(datetime.now()),

            d["age"],
            "Unknown",
            "No",
            d["smoking"],
            25,

            d["schatzker"],
            d["soft_tissue"],
            d["open_fracture"],
            d["compartment"],

            d["recommendation"],

            treatment,
            outcome,

            infection,
            secondary,
            revision
        ))

        conn.commit()

        st.success(f"Saved patient {pid}")

        st.session_state.eval = None

# =========================================================
# 3. SIMPLE LEARNING AI (BASED ON ONLY 3+ PATIENTS)
# =========================================================

elif menu == "AI Learning":

    st.header("🧠 Self Learning AI (Prototype)")

    df = pd.read_sql_query("SELECT * FROM patients", conn)

    if len(df) < 3:
        st.warning("Need at least 3 patients to learn")
    else:

        # =================================================
        # SIMPLE LEARNING RULE
        # =================================================

        # Best treatment = one with most "A" outcomes
        best = df.groupby("treatment")["outcome"].apply(
            lambda x: (x == "A").mean()
        ).idxmax()

        # Infection rate per treatment
        infection_rate = df.groupby("treatment")["infection"].apply(
            lambda x: (x == "Yes").mean()
        )

        st.success(f"Best performing treatment: {best}")

        st.subheader("Learning from real data")

        st.write("Infection rates per treatment:")
        st.dataframe(infection_rate)

        st.info("""
AI logic:
- compares treatments
- learns from outcomes
- adapts recommendation over time
(very simplified prototype version)
""")
