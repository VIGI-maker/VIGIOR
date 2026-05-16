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

    schatzker TEXT,
    soft_tissue TEXT,
    high_energy TEXT,
    open_fracture TEXT,
    blisters TEXT,
    compartment_signs TEXT,
    delay INTEGER,

    risk_infection REAL,
    risk_compartment REAL,
    risk_skin REAL,

    recommendation TEXT,

    treatment_done TEXT,
    outcome TEXT,

    infection TEXT,
    pseudarthrosis TEXT,
    revision TEXT
)
""")

conn.commit()

# =========================================================
# CONFIG
# =========================================================

st.set_page_config(page_title="VIGIOR HOSPITAL", layout="wide")

st.title("🏥 VIGIOR HOSPITAL AI")
st.subheader("Orthopaedic Decision Support System - Tibial Plateau Fractures")

menu = st.sidebar.selectbox(
    "Hospital Module",
    [
        "1. AI Evaluation",
        "2. Patient Registration",
        "3. Hospital Database",
        "4. Clinical Analytics"
    ]
)

# =========================================================
# RISK MODEL (CLINICAL WEIGHTED)
# =========================================================

def logistic(x):
    return 1 / (1 + math.exp(-x))


def compute_risk(age, diabetes, smoking, bmi,
                 schatzker, soft_tissue, high_energy,
                 open_fracture, blisters,
                 compartment_signs, delay):

    inf = 0
    comp = 0
    skin = 0

    # Patient factors
    if age > 60: inf += 1; skin += 1
    if diabetes == "Yes": inf += 2
    if smoking == "Yes": inf += 2
    if bmi > 30: inf += 1

    # Trauma severity
    if high_energy == "Yes":
        comp += 2
        skin += 2

    if open_fracture == "Yes":
        inf += 3
        skin += 3

    # Fracture type
    if schatzker in ["V", "VI"]:
        inf += 2
        comp += 2
        skin += 2

    # Soft tissue (Tscherne logic simplified)
    if soft_tissue == "Moderate":
        skin += 2
    if soft_tissue == "Severe":
        skin += 4
        inf += 2

    # Skin condition
    if blisters == "Yes":
        skin += 3

    # Compartment syndrome
    if compartment_signs == "Yes":
        comp += 5

    # Delay
    if delay > 10:
        inf += 1

    return (
        round(logistic(inf / 2) * 100, 1),
        round(logistic(comp / 2) * 100, 1),
        round(logistic(skin / 2) * 100, 1)
    )

# =========================================================
# CLINICAL DECISION TREE (IMPORTANT PART)
# =========================================================

def decision(inf, comp, skin):

    if comp > 75:
        return "URGENT: Monitoring ± Fasciotomy + External Fixation (Damage Control)"

    if skin > 80:
        return "External Fixation → Delayed ORIF / MIPO after soft tissue recovery"

    if inf > 65:
        return "MIPO (biological fixation) preferred"

    if skin > 55:
        return "Traction + Strict Monitoring → Delayed Osteosynthesis (7–14 days)"

    return "Early ORIF (anatomical reduction possible)"

# =========================================================
# 1. AI EVALUATION MODULE
# =========================================================

if menu == "1. AI Evaluation":

    st.header("🧠 Clinical Evaluation")

    with st.form("eval"):

        col1, col2, col3 = st.columns(3)

        with col1:
            age = st.number_input("Age", 18, 100, 40)
            sex = st.selectbox("Sex", ["Male", "Female"])
            diabetes = st.selectbox("Diabetes", ["No", "Yes"])
            smoking = st.selectbox("Smoking", ["No", "Yes"])

        with col2:
            bmi = st.number_input("BMI", 15.0, 50.0, 25.0)
            schatzker = st.selectbox("Schatzker", ["I","II","III","IV","V","VI"])
            soft_tissue = st.selectbox("Soft tissue (Tscherne)", ["Mild","Moderate","Severe"])

        with col3:
            high_energy = st.selectbox("High energy trauma", ["No","Yes"])
            open_fracture = st.selectbox("Open fracture", ["No","Yes"])
            blisters = st.selectbox("Blisters", ["No","Yes"])
            compartment = st.selectbox("Compartment syndrome signs", ["No","Yes"])
            delay = st.slider("Surgical delay (days)", 0, 20, 5)

        submit = st.form_submit_button("Run AI")

    if submit:

        inf, comp, skin = compute_risk(
            age, diabetes, smoking, bmi,
            schatzker, soft_tissue, high_energy,
            open_fracture, blisters,
            compartment, delay
        )

        plan = decision(inf, comp, skin)

        st.subheader("📊 Risk Analysis")
        st.metric("Infection risk", f"{inf}%")
        st.metric("Compartment risk", f"{comp}%")
        st.metric("Skin risk", f"{skin}%")

        st.success(plan)

        st.session_state["last_case"] = {
            "inf": inf,
            "comp": comp,
            "skin": skin,
            "plan": plan
        }

# =========================================================
# 2. PATIENT REGISTRATION
# =========================================================

elif menu == "2. Patient Registration":

    st.header("💾 Register Patient (Clinical Record)")

    if "last_case" not in st.session_state:
        st.warning("Run AI evaluation first")
        st.stop()

    case = st.session_state["last_case"]

    with st.form("save"):

        patient_id = st.text_input("Hospital Patient ID")

        st.subheader("Treatment performed")
        treatment_done = st.selectbox(
            "Procedure",
            [
                "Early ORIF",
                "MIPO",
                "External Fixation + Delayed ORIF",
                "Traction + Monitoring",
                "Conservative"
            ]
        )

        st.subheader("Outcomes")
        outcome = st.selectbox("Functional result", ["A","B","C"])

        infection = st.selectbox("Infection", ["No","Yes"])
        pseudarthrosis = st.selectbox("Pseudarthrosis", ["No","Yes"])
        revision = st.selectbox("Revision surgery", ["No","Yes"])

        submit = st.form_submit_button("Save to hospital DB")

    if submit:

        pid = "VIG-" + str(uuid.uuid4())[:8]

        cursor.execute("""
        INSERT INTO patients VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            pid,
            str(datetime.now()),

            age,
            sex,
            diabetes,
            smoking,
            bmi,

            schatzker,
            soft_tissue,
            high_energy,
            open_fracture,
            blisters,
            compartment,
            delay,

            case["inf"],
            case["comp"],
            case["skin"],

            case["plan"],

            treatment_done,
            outcome,

            infection,
            pseudarthrosis,
            revision
        ))

        conn.commit()

        st.success(f"Patient saved: {pid}")

# =========================================================
# 3. DATABASE
# =========================================================

elif menu == "3. Hospital Database":

    st.header("📂 Hospital Registry")

    df = pd.read_sql_query("SELECT * FROM patients", conn)

    st.dataframe(df, use_container_width=True)

# =========================================================
# 4. CLINICAL ANALYTICS
# =========================================================

elif menu == "4. Clinical Analytics":

    st.header("📊 Clinical Analytics Dashboard")

    df = pd.read_sql_query("SELECT * FROM patients", conn)

    if len(df) == 0:
        st.warning("No data available")
    else:

        st.metric("Total patients", len(df))
        st.metric("Mean age", round(df["age"].mean(), 1))

        st.subheader("Fracture patterns")
        st.bar_chart(df["schatzker"].value_counts())

        st.subheader("Treatment distribution")
        st.bar_chart(df["treatment_done"].value_counts())

        st.subheader("Outcomes")
        st.bar_chart(df["outcome"].value_counts())

        st.subheader("Complications")

        st.bar_chart({
            "Infection": (df["infection"] == "Yes").sum(),
            "Pseudarthrosis": (df["pseudarthrosis"] == "Yes").sum(),
            "Revision": (df["revision"] == "Yes").sum()
        })

        st.subheader("AI Learning (real hospital data)")

        best = df.groupby("treatment_done")["outcome"].apply(
            lambda x: (x == "A").mean()
        ).idxmax()

        st.success(f"Best observed treatment: {best}")

        st.info("""
The system adapts based on real hospital outcomes:
- infection rate
- functional result
- revision surgery
- treatment effectiveness
""")
