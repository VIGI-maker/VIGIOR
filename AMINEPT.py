# =========================================================
# VIGIOR HOSPITAL AI - FINAL STABLE VERSION
# =========================================================

import streamlit as st
import pandas as pd
import sqlite3
import uuid
from datetime import datetime
import math

# =========================================================
# CONFIG
# =========================================================

st.set_page_config(page_title="VIGIOR HOSPITAL AI", layout="wide")

st.title("🏥 VIGIOR HOSPITAL AI")
st.subheader("Predictive & Learning System for Tibial Plateau Fractures")

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
    recommendation TEXT,
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
# MENU
# =========================================================

menu = st.sidebar.selectbox(
    "Navigation",
    ["AI Evaluation", "Register Patient", "Database", "Statistics", "AI Learning"]
)

# =========================================================
# LOGISTIC
# =========================================================

def logistic(x):
    return 1 / (1 + math.exp(-x))

# =========================================================
# RISK MODEL
# =========================================================

def calculate_risks(age, diabetes, smoking, bmi,
                     high_energy, open_fracture,
                     schatzker, soft_tissue,
                     blisters, compartment_signs,
                     external_fixator, delay):

    inf = 0
    comp = 0
    skin = 0

    if age > 60:
        inf += 1; skin += 1
    if diabetes == "Yes":
        inf += 2
    if smoking == "Yes":
        inf += 2
    if bmi > 30:
        inf += 1
    if high_energy == "Yes":
        comp += 2; skin += 2
    if open_fracture == "Yes":
        inf += 3; skin += 2
    if schatzker in ["V", "VI"]:
        inf += 2; comp += 2; skin += 2
    if soft_tissue == "Moderate":
        skin += 2
    if soft_tissue == "Severe":
        inf += 2; skin += 4
    if blisters == "Yes":
        skin += 3
    if compartment_signs == "Yes":
        comp += 5
    if external_fixator == "Yes":
        inf += 1
    if delay > 10:
        inf += 1

    return (
        round(logistic(inf / 2) * 100, 1),
        round(logistic(comp / 2) * 100, 1),
        round(logistic(skin / 2) * 100, 1)
    )

# =========================================================
# TREATMENT DECISION
# =========================================================

def treatment_plan(inf, comp, skin):

    if comp > 75:
        return "🚨 Fasciotomy ± External Fixation + Staged ORIF"

    if skin > 80:
        return "🚨 External Fixation → Delayed ORIF/MIPO"

    if inf > 65:
        return "⚠ MIPO (biological fixation preferred)"

    if skin > 55:
        return "⚠ Traction + Monitoring → Delayed ORIF"

    return "✅ Early ORIF"

# =========================================================
# SESSION STATE FIX (IMPORTANT)
# =========================================================

if "evaluation_done" not in st.session_state:
    st.session_state.evaluation_done = False

if "last_data" not in st.session_state:
    st.session_state.last_data = {}

# =========================================================
# 1. AI EVALUATION (NO RESET BUG)
# =========================================================

if menu == "AI Evaluation":

    st.header("🧠 Clinical Evaluation")

    with st.form("eval_form"):

        col1, col2, col3 = st.columns(3)

        with col1:
            age = st.number_input("Age", 18, 100, 40)
            sex = st.selectbox("Sex", ["Male", "Female"])
            diabetes = st.selectbox("Diabetes", ["No", "Yes"])
            smoking = st.selectbox("Smoking", ["No", "Yes"])

        with col2:
            bmi = st.number_input("BMI", 15.0, 50.0, 25.0)
            high_energy = st.selectbox("High Energy", ["No", "Yes"])
            open_fracture = st.selectbox("Open Fracture", ["No", "Yes"])
            schatzker = st.selectbox("Schatzker", ["I","II","III","IV","V","VI"])

        with col3:
            soft_tissue = st.selectbox("Soft Tissue", ["Mild","Moderate","Severe"])
            blisters = st.selectbox("Blisters", ["No","Yes"])
            compartment = st.selectbox("Compartment signs", ["No","Yes"])
            fixator = st.selectbox("External Fixator", ["No","Yes"])
            delay = st.slider("Delay (days)", 0, 20, 5)

        submit = st.form_submit_button("Evaluate")

    if submit:

        inf, comp, skin = calculate_risks(
            age, diabetes, smoking, bmi,
            high_energy, open_fracture,
            schatzker, soft_tissue,
            blisters, compartment,
            fixator, delay
        )

        plan = treatment_plan(inf, comp, skin)

        st.session_state.evaluation_done = True
        st.session_state.last_data = {
            "age": age,
            "sex": sex,
            "diabetes": diabetes,
            "smoking": smoking,
            "bmi": bmi,
            "high_energy": high_energy,
            "open_fracture": open_fracture,
            "schatzker": schatzker,
            "soft_tissue": soft_tissue,
            "blisters": blisters,
            "compartment": compartment,
            "fixator": fixator,
            "delay": delay,
            "inf": inf,
            "comp": comp,
            "skin": skin,
            "plan": plan
        }

    if st.session_state.evaluation_done:

        d = st.session_state.last_data

        st.subheader("📊 Risks")
        st.metric("Infection", f"{d['inf']}%")
        st.metric("Compartment", f"{d['comp']}%")
        st.metric("Skin", f"{d['skin']}%")

        st.success(d["plan"])

# =========================================================
# 2. REGISTER PATIENT (NO RESET BUG FIXED)
# =========================================================

elif menu == "Register Patient":

    st.header("💾 Register Patient")

    if not st.session_state.evaluation_done:
        st.warning("Run AI Evaluation first")
        st.stop()

    d = st.session_state.last_data

    with st.form("save_form"):

        patient_number = st.text_input("Patient ID")

        performed_treatment = st.selectbox(
            "Treatment performed",
            [
                "Early ORIF",
                "MIPO",
                "External Fixation + Delayed ORIF",
                "Traction + Monitoring",
                "Conservative"
            ]
        )

        outcome = st.selectbox("Outcome", ["A","B","C"])
        infection = st.selectbox("Infection", ["No","Yes"])
        nonunion = st.selectbox("Nonunion", ["No","Yes"])
        revision = st.selectbox("Revision", ["No","Yes"])
        follow_up = st.text_area("Follow-up")

        save = st.form_submit_button("Save Patient")

    if save:

        pid = "VIG-" + str(uuid.uuid4())[:8]

        cursor.execute("""
        INSERT INTO patients VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            pid,
            patient_number,
            str(datetime.now()),
            d["age"],
            d["sex"],
            d["diabetes"],
            d["smoking"],
            d["bmi"],
            d["high_energy"],
            d["open_fracture"],
            d["schatzker"],
            d["soft_tissue"],
            d["blisters"],
            d["compartment"],
            d["fixator"],
            d["delay"],
            d["inf"],
            d["comp"],
            d["skin"],
            d["plan"],
            performed_treatment,
            outcome,
            infection,
            nonunion,
            revision,
            follow_up
        ))

        conn.commit()

        st.success(f"Patient saved → {pid}")

        # RESET AFTER SAVE (IMPORTANT FIX)
        st.session_state.evaluation_done = False

# =========================================================
# 3. DATABASE
# =========================================================

elif menu == "Database":

    st.header("📂 Patients Database")

    df = pd.read_sql_query("SELECT * FROM patients", conn)

    st.dataframe(df, use_container_width=True)

# =========================================================
# 4. STATISTICS
# =========================================================

elif menu == "Statistics":

    st.header("📊 Statistics")

    df = pd.read_sql_query("SELECT * FROM patients", conn)

    if len(df) > 0:

        st.metric("Patients", len(df))
        st.metric("Mean age", round(df["age"].mean(),1))

        st.subheader("Treatments")
        st.bar_chart(df["performed_treatment"].value_counts())

        st.subheader("Outcomes")
        st.bar_chart(df["outcome"].value_counts())

        st.subheader("Complications")
        st.bar_chart({
            "Infection": (df["infection"]=="Yes").sum(),
            "Nonunion": (df["nonunion"]=="Yes").sum(),
            "Revision": (df["revision"]=="Yes").sum()
        })

# =========================================================
# 5. AI LEARNING
# =========================================================

elif menu == "AI Learning":

    st.header("🧠 AI Learning from Your Data")

    df = pd.read_sql_query("SELECT * FROM patients", conn)

    if len(df) < 5:
        st.warning("Need more patients")
    else:

        best = df.groupby("performed_treatment")["outcome"].apply(
            lambda x: (x=="A").mean()
        ).idxmax()

        st.success(f"Best treatment in YOUR dataset: {best}")
