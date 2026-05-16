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
    treatment_done TEXT,
    outcome TEXT,
    follow_up TEXT
)
""")

conn.commit()

# =========================================================
# CONFIG
# =========================================================

st.set_page_config(page_title="VIGIOR AI", layout="wide")

st.title("🦴 VIGIOR AI")
st.subheader("Integrated Orthopaedic Decision Support System")

menu = st.sidebar.selectbox(
    "Navigation",
    ["Evaluate (AI)", "Register Patient", "Database & AI Learning"]
)

# =========================================================
# RISK MODEL
# =========================================================

def logistic(x):
    return 1 / (1 + math.exp(-x))


def compute_risks(age, diabetes, smoking, bmi, high_energy,
                  open_fracture, schatzker, soft_tissue,
                  blisters, compartment_signs, external_fixator,
                  surgical_delay):

    inf = 0
    comp = 0
    skin = 0

    if age > 60:
        inf += 1
        skin += 1

    if diabetes == "Yes":
        inf += 2

    if smoking == "Yes":
        inf += 2

    if bmi > 30:
        inf += 1

    if high_energy == "Yes":
        comp += 2
        skin += 2

    if open_fracture == "Yes":
        inf += 3
        skin += 2

    if schatzker in ["V", "VI"]:
        inf += 2
        comp += 2
        skin += 2

    if soft_tissue == "Moderate":
        skin += 2

    if soft_tissue == "Severe":
        inf += 2
        skin += 4

    if blisters == "Yes":
        skin += 3

    if compartment_signs == "Yes":
        comp += 5

    if external_fixator == "Yes":
        inf += 1

    if surgical_delay > 10:
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

    if skin > 80:
        return "Temporary External Fixation → Delayed ORIF / MIPO"

    elif comp > 75:
        return "Strict Monitoring ± Fasciotomy → Staged Fixation"

    elif inf > 60:
        return "MIPO (Biological fixation preferred)"

    elif skin > 55:
        return "Traction + Surveillance → Delayed Osteosynthesis"

    else:
        return "Early ORIF"

# =========================================================
# 1. EVALUATION (AI)
# =========================================================

if menu == "Evaluate (AI)":

    st.header("🧠 AI Evaluation")

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
            delay = st.slider("Surgical Delay", 0, 20, 5)

        submitted = st.form_submit_button("Evaluate")

    if submitted:

        inf, comp, skin = compute_risks(
            age, diabetes, smoking, bmi, high_energy,
            open_fracture, schatzker, soft_tissue,
            blisters, compartment, fixator, delay
        )

        plan = treatment_plan(inf, comp, skin)

        st.subheader("Risks")
        st.metric("Infection", f"{inf}%")
        st.metric("Compartment", f"{comp}%")
        st.metric("Skin", f"{skin}%")

        st.success(plan)

        st.session_state["last_eval"] = {
            "inf": inf,
            "comp": comp,
            "skin": skin,
            "plan": plan
        }

# =========================================================
# 2. REGISTER PATIENT
# =========================================================

elif menu == "Register Patient":

    st.header("💾 Patient Registration")

    if "last_eval" not in st.session_state:
        st.warning("Run evaluation first")
        st.stop()

    eval_data = st.session_state["last_eval"]

    with st.form("save_form"):

        patient_id = st.text_input("Patient Number")

        treatment_done = st.selectbox(
            "Treatment Performed",
            [
                "Early ORIF",
                "MIPO",
                "External Fixation + Delayed ORIF",
                "Traction + Surveillance",
                "Conservative"
            ]
        )

        outcome = st.selectbox("Outcome", ["A","B","C"])

        follow_up = st.text_area("Follow-up")

        submitted = st.form_submit_button("Save Patient")

    if submitted:

        pid = "VIG-" + str(uuid.uuid4())[:8]

        cursor.execute("""
        INSERT INTO patients VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            pid,
            str(datetime.now()),
            eval_data["inf"],
            eval_data["comp"],
            eval_data["skin"],
            eval_data["plan"],
            treatment_done,
            outcome,
            follow_up
        ))

        conn.commit()

        st.success(f"Saved patient {pid}")

# =========================================================
# 3. DATABASE + AI LEARNING
# =========================================================

elif menu == "Database & AI Learning":

    st.header("📊 Database + Learning AI")

    df = pd.read_sql_query("SELECT * FROM patients", conn)

    st.dataframe(df)

    if len(df) > 0:

        st.subheader("Statistics")

        st.metric("Patients", len(df))

        st.bar_chart(df["treatment_done"].value_counts())
        st.bar_chart(df["outcome"].value_counts())

        st.subheader("AI Learning")

        best = df.groupby("treatment_done")["outcome"].apply(
            lambda x: (x == "A").mean()
        ).idxmax()

        st.success(f"Best treatment in your data: {best}")
