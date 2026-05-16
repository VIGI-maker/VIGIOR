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
# DATABASE (FIXED STRUCTURE)
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
    secondary TEXT,
    revision TEXT
)
""")

conn.commit()

# =========================================================
# SESSION STATE
# =========================================================

if "case" not in st.session_state:
    st.session_state.case = None

if "done" not in st.session_state:
    st.session_state.done = False

# =========================================================
# MENU
# =========================================================

menu = st.sidebar.selectbox(
    "Navigation",
    ["AI Evaluation", "Statistics", "AI Learning"]
)

# =========================================================
# CLINICAL STRATEGY (IMPROVED SCIENTIFIC LOGIC)
# =========================================================

def strategy(schatzker, soft_tissue, open_fracture, compartment):

    if compartment == "Yes":
        return "Damage Control Orthopaedics: External fixation → fasciotomy if needed → delayed ORIF (avoid early closure due to muscle ischemia risk)"

    if open_fracture == "Yes":
        return "Gustilo-based staged management: urgent debridement → temporary fixation → delayed definitive fixation (infection control priority)"

    if soft_tissue == "Severe":
        return "Tscherne C3 pattern: external fixation → soft tissue recovery → MIPO/biological ORIF (avoid wound complications)"

    if schatzker in ["V", "VI"]:
        return "High-energy fracture: staged protocol (external fixation → delayed ORIF/MIPO) due to metaphyseal comminution & vascular risk"

    return "Early ORIF: acceptable soft tissue envelope allows anatomical reduction and stable fixation"

# =========================================================
# 1. AI EVALUATION
# =========================================================

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
            compartment = st.selectbox("Compartment syndrome", ["No","Yes"])

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

        st.session_state.done = True

    if st.session_state.done:

        c = st.session_state.case

        st.success(c["rec"])

        st.markdown("""
### 🧬 Scientific rationale

- **Soft tissue status (Tscherne classification)** → main predictor of infection & wound breakdown  
- **Open fracture (Gustilo-Anderson principle)** → contamination → staged surgery mandatory  
- **Schatzker V–VI fractures** → high-energy trauma → metaphyseal instability → biological fixation preferred  
- **Compartment syndrome risk** → surgical emergency → takes priority over fixation  

👉 Principle: **Damage control orthopaedics + biological fixation**
""")

        # =====================================================
        # REGISTER PATIENT (FIXED SAVE)
        # =====================================================

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

            st.session_state.done = False
            st.session_state.case = None

# =========================================================
# 2. STATISTICS DASHBOARD (NEW)
# =========================================================

elif menu == "Statistics":

    st.header("📊 Statistics Dashboard")

    df = pd.read_sql_query("SELECT * FROM patients", conn)

    if len(df) == 0:
        st.warning("No patients yet")
    else:

        st.metric("Total patients", len(df))

        st.subheader("Treatments distribution")
        st.bar_chart(df["treatment"].value_counts())

        st.subheader("Outcomes")
        st.bar_chart(df["outcome"].value_counts())

        st.subheader("Complications")

        st.bar_chart({
            "Infection": (df["infection"] == "Yes").sum(),
            "Secondary displacement": (df["secondary"] == "Yes").sum(),
            "Revision": (df["revision"] == "Yes").sum()
        })

        # Trend simple
        df["index"] = range(len(df))
        df["infection_bin"] = df["infection"].apply(lambda x: 1 if x == "Yes" else 0)

        st.subheader("Infection trend")
        st.line_chart(df[["index", "infection_bin"]].set_index("index"))

# =========================================================
# 3. AI LEARNING (REAL DATA)
# =========================================================

elif menu == "AI Learning":

    st.header("🧠 AI Learning from YOUR patients")

    df = pd.read_sql_query("SELECT * FROM patients", conn)

    if len(df) < 3:
        st.warning("Need at least 3 patients")
    else:

        best = df.groupby("treatment")["outcome"].apply(
            lambda x: (x == "A").mean()
        ).idxmax()

        st.success(f"Best treatment in YOUR data: {best}")

        st.write(df.groupby("treatment")["outcome"].value_counts())
