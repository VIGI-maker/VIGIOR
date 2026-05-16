import streamlit as st
import pandas as pd
import sqlite3
import uuid
from datetime import datetime

# =========================================================
# CONFIG
# =========================================================

st.set_page_config(page_title="VIGIOR HOSPITAL AI", layout="wide")

st.title("🏥 VIGIOR HOSPITAL AI")
st.subheader("Learning Orthopaedic Decision System")

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
# SESSION MEMORY
# =========================================================

if "eval_done" not in st.session_state:
    st.session_state.eval_done = False

if "case" not in st.session_state:
    st.session_state.case = None

# =========================================================
# MENU
# =========================================================

menu = st.sidebar.selectbox(
    "Navigation",
    ["AI Evaluation", "AI Learning"]
)

# =========================================================
# SIMPLE CLINICAL STRATEGY ENGINE
# =========================================================

def strategy(age, schatzker, soft_tissue, open_fracture, compartment):

    if compartment == "Yes":
        return "External Fixation + Monitoring → possible fasciotomy → delayed ORIF"

    if open_fracture == "Yes":
        return "Debridement + Temporary Fixation → delayed definitive fixation"

    if soft_tissue == "Severe":
        return "External Fixation → wait wrinkle sign → delayed MIPO/ORIF"

    if schatzker in ["V", "VI"]:
        return "Staged treatment: External fixation → delayed ORIF/MIPO"

    return "Early ORIF (anatomical reduction possible)"

# =========================================================
# 1. AI EVALUATION (STRATEGY ONLY)
# =========================================================

if menu == "AI Evaluation":

    st.header("🧠 AI Evaluation")

    with st.form("eval_form"):

        col1, col2 = st.columns(2)

        with col1:
            age = st.number_input("Age", 18, 100, 40)
            sex = st.selectbox("Sex", ["Male", "Female"])
            diabetes = st.selectbox("Diabetes", ["No", "Yes"])
            smoking = st.selectbox("Smoking", ["No", "Yes"])

        with col2:
            schatzker = st.selectbox("Schatzker", ["I","II","III","IV","V","VI"])
            soft_tissue = st.selectbox("Soft tissue", ["Mild","Moderate","Severe"])
            open_fracture = st.selectbox("Open fracture", ["No","Yes"])
            compartment = st.selectbox("Compartment syndrome", ["No","Yes"])

        submit = st.form_submit_button("Evaluate")

    if submit:

        rec = strategy(age, schatzker, soft_tissue, open_fracture, compartment)

        st.session_state.case = {
            "age": age,
            "sex": sex,
            "diabetes": diabetes,
            "smoking": smoking,
            "schatzker": schatzker,
            "soft_tissue": soft_tissue,
            "open_fracture": open_fracture,
            "compartment": compartment,
            "recommendation": rec
        }

        st.session_state.eval_done = True

    if st.session_state.eval_done:

        c = st.session_state.case

        st.subheader("🩺 AI Recommended Strategy")

        st.success(c["recommendation"])

        st.markdown("""
### Why this strategy?

This decision is based on:
- soft tissue condition
- fracture severity (Schatzker)
- infection risk context (open fracture)
- compartment syndrome risk

### Clinical principle:
👉 protect soft tissue first  
👉 delay definitive fixation if necessary  
👉 prioritize biological fixation when needed
""")

        # =====================================================
        # REGISTER PATIENT (INSIDE SAME FLOW)
        # =====================================================

        st.markdown("---")
        st.subheader("💾 Register Patient")

        with st.form("register_form"):

            patient_number = st.text_input("Patient ID")

            treatment = st.selectbox(
                "Treatment performed",
                [
                    "Early ORIF",
                    "MIPO",
                    "External Fixation",
                    "Traction + Monitoring",
                    "Debridement + Staged Fixation"
                ]
            )

            outcome = st.selectbox("Outcome", ["A","B","C"])
            infection = st.selectbox("Infection", ["No","Yes"])
            secondary = st.selectbox("Secondary displacement", ["No","Yes"])
            revision = st.selectbox("Revision", ["No","Yes"])

            save = st.form_submit_button("Save Patient")

        if save:

            pid = "VIG-" + str(uuid.uuid4())[:8]

            cursor.execute("""
            INSERT INTO patients VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                pid,
                patient_number,
                str(datetime.now()),
                c["age"],
                c["sex"],
                c["diabetes"],
                c["smoking"],
                25,
                c["schatzker"],
                c["soft_tissue"],
                c["open_fracture"],
                c["compartment"],
                c["recommendation"],
                treatment,
                outcome,
                infection,
                secondary,
                revision
            ))

            conn.commit()

            st.success(f"Patient saved: {pid}")

            st.session_state.eval_done = False
            st.session_state.case = None

# =========================================================
# 2. AI LEARNING (BASED ONLY ON YOUR DATA)
# =========================================================

elif menu == "AI Learning":

    st.header("🧠 AI Learning from Hospital Data")

    df = pd.read_sql_query("SELECT * FROM patients", conn)

    if len(df) < 3:
        st.warning("Need at least 3 patients to learn")
    else:

        # BEST STRATEGY BASED ON OUTCOME A
        best = df.groupby("treatment")["outcome"].apply(
            lambda x: (x == "A").mean()
        ).idxmax()

        st.success(f"Best treatment in YOUR hospital data: {best}")

        st.subheader("Learning summary")

        st.write(df.groupby("treatment")["outcome"].value_counts())

        st.info("""
👉 The AI now evolves based ONLY on YOUR patients:
- outcome A/B/C
- complications
- treatment choice
- real hospital feedback
""")
