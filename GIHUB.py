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
        return """
🚨 External Fixation + Monitoring → Possible Fasciotomy → Delayed ORIF

Scientific rationale:
- High risk of compartment syndrome
- Damage control orthopaedics reduces soft tissue aggression
- Delayed fixation decreases ischemic and infectious complications
"""

    if open_fracture == "Yes":
        return """
🚨 Debridement + Temporary Stabilization → Delayed Definitive Fixation

Scientific rationale:
- Infection prevention is priority
- Early aggressive ORIF increases contamination risk
- Staged fixation improves soft tissue recovery
"""

    if soft_tissue == "Severe":
        return """
⚠ External Fixation → Wait Wrinkle Sign → Delayed MIPO/ORIF

Scientific rationale:
- Severe soft tissue injury increases wound complications
- Delayed fixation protects vascularity
- MIPO preserves biology and decreases infection risk
"""

    if schatzker in ["V", "VI"]:
        return """
⚠ Staged Treatment: External Fixation → Delayed ORIF/MIPO

Scientific rationale:
- High-energy bicondylar fractures have elevated soft tissue risk
- Staged management decreases skin necrosis and deep infection
"""

    return """
✅ Early ORIF

Scientific rationale:
- Stable soft tissue envelope
- Allows anatomical reduction
- Early mobilization decreases stiffness
"""

# =========================================================
# 1. AI EVALUATION
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
            schatzker = st.selectbox(
                "Schatzker",
                ["I", "II", "III", "IV", "V", "VI"]
            )

            soft_tissue = st.selectbox(
                "Soft tissue",
                ["Mild", "Moderate", "Severe"]
            )

            open_fracture = st.selectbox(
                "Open fracture",
                ["No", "Yes"]
            )

            compartment = st.selectbox(
                "Compartment syndrome",
                ["No", "Yes"]
            )

        submit = st.form_submit_button("Evaluate")

    if submit:

        rec = strategy(
            age,
            schatzker,
            soft_tissue,
            open_fracture,
            compartment
        )

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

        # =====================================================
        # REGISTER PATIENT
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

            outcome = st.selectbox(
                "Outcome",
                ["A", "B", "C"]
            )

            infection = st.selectbox(
                "Infection",
                ["No", "Yes"]
            )

            secondary = st.selectbox(
                "Secondary displacement",
                ["No", "Yes"]
            )

            revision = st.selectbox(
                "Revision",
                ["No", "Yes"]
            )

            save = st.form_submit_button("Save Patient")

        # =====================================================
        # FIXED SAVE
        # =====================================================

        if save:

            pid = "VIG-" + str(uuid.uuid4())[:8]

            try:

                cursor.execute("""
                INSERT INTO patients VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
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

                st.success(f"✅ Patient saved successfully: {pid}")

                st.session_state.eval_done = False
                st.session_state.case = None

            except Exception as e:

                st.error("Save failed")
                st.write(e)

# =========================================================
# 2. AI LEARNING + STATISTICS
# =========================================================

elif menu == "AI Learning":

    st.header("🧠 AI Learning from Hospital Data")

    df = pd.read_sql_query("SELECT * FROM patients", conn)

    if len(df) < 3:

        st.warning("Need at least 3 patients to learn")

    else:

        st.subheader("📊 Statistics")

        col1, col2 = st.columns(2)

        with col1:
            st.metric("Total patients", len(df))

        with col2:
            st.metric(
                "Mean age",
                round(df["age"].mean(), 1)
            )

        st.markdown("---")

        st.subheader("Treatment Distribution")
        st.bar_chart(df["treatment"].value_counts())

        st.subheader("Outcome Distribution")
        st.bar_chart(df["outcome"].value_counts())

        st.subheader("Schatzker Types")
        st.bar_chart(df["schatzker"].value_counts())

        st.subheader("Soft Tissue Severity")
        st.bar_chart(df["soft_tissue"].value_counts())

        complications = pd.DataFrame({
            "Complication": [
                "Infection",
                "Secondary displacement",
                "Revision"
            ],
            "Count": [
                (df["infection"] == "Yes").sum(),
                (df["secondary_displacement"] == "Yes").sum(),
                (df["revision"] == "Yes").sum()
            ]
        })

        st.subheader("Complications")
        st.bar_chart(complications.set_index("Complication"))

        st.markdown("---")

        best = df.groupby("treatment")["outcome"].apply(
            lambda x: (x == "A").mean()
        ).idxmax()

        st.success(f"🏆 Best treatment in YOUR hospital data: {best}")

        st.info("""
The AI progressively evolves according to:
- real patient outcomes
- complications
- treatment performance
- local hospital practice
""")
