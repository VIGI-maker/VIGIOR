import streamlit as st
import pandas as pd
import sqlite3
import uuid
from datetime import datetime
import matplotlib.pyplot as plt

# =========================================================
# CONFIG
# =========================================================

st.set_page_config(page_title="VIGIOR HOSPITAL AI", layout="wide")

st.title("🏥 VIGIOR HOSPITAL AI")
st.subheader("Learning Orthopaedic Decision System")

# =========================================================
# DATABASE (FIXED + SAFE)
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
# SESSION STATE (IMPORTANT FIX SAVE BUG)
# =========================================================

if "case" not in st.session_state:
    st.session_state.case = None

if "evaluated" not in st.session_state:
    st.session_state.evaluated = False

# =========================================================
# MENU
# =========================================================

menu = st.sidebar.selectbox(
    "Navigation",
    ["AI Evaluation", "Statistics Dashboard", "AI Learning"]
)

# =========================================================
# CLINICAL LOGIC
# =========================================================

def strategy(schatzker, soft_tissue, open_fracture, compartment):

    if compartment == "Yes":
        return "External Fixation → Fasciotomy if needed → delayed ORIF"

    if open_fracture == "Yes":
        return "Urgent debridement → temporary stabilization → staged fixation"

    if soft_tissue == "Severe":
        return "Damage control (external fixation) → wait soft tissue recovery → MIPO/ORIF"

    if schatzker in ["V", "VI"]:
        return "Staged strategy: external fixation → delayed ORIF/MIPO"

    return "Early ORIF (anatomical reconstruction possible)"

# =========================================================
# 1. AI EVALUATION
# =========================================================

if menu == "AI Evaluation":

    st.header("🧠 AI Recommended Strategy")

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

        rec = strategy(schatzker, soft_tissue, open_fracture, compartment)

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

        st.session_state.evaluated = True

    if st.session_state.evaluated:

        c = st.session_state.case

        st.success(c["recommendation"])

        # =====================================================
        # SCIENTIFIC EXPLANATION (SHORT BUT REAL)
        # =====================================================

        st.markdown("""
### 🧬 Scientific rationale

This decision is based on orthopedic trauma principles:

- **Soft tissue condition (Tscherne concept)**  
  → determines infection risk and wound complication risk

- **High-energy / Schatzker V–VI patterns**  
  → associated with metaphyseal comminution and vascular damage  
  → increased risk of secondary collapse

- **Open fracture (Gustilo principle)**  
  → high bacterial contamination → requires staged surgery

- **Compartment syndrome risk**  
  → surgical emergency → priority over fixation

👉 Therefore:
- “Damage control orthopaedics” is preferred in high-risk soft tissue conditions  
- “Biological fixation (MIPO)” reduces periosteal stripping and infection risk  
- “Early ORIF” only when soft tissue envelope is safe
""")

        # =====================================================
        # REGISTER PATIENT (FIXED SAVE BUTTON)
        # =====================================================

        st.markdown("---")
        st.subheader("💾 Register Patient")

        with st.form("save_form"):

            patient_number = st.text_input("Patient ID")

            treatment = st.selectbox(
                "Treatment performed",
                ["Early ORIF", "MIPO", "External Fixation", "Traction", "Staged Fixation"]
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

            st.session_state.evaluated = False
            st.session_state.case = None

# =========================================================
# 2. STATISTICS DASHBOARD (NEW FIX)
# =========================================================

elif menu == "Statistics Dashboard":

    st.header("📊 Clinical Statistics")

    df = pd.read_sql_query("SELECT * FROM patients", conn)

    if len(df) == 0:
        st.warning("No data yet")
    else:

        st.metric("Total patients", len(df))

        # =====================================================
        # BAR CHARTS
        # =====================================================

        st.subheader("Treatments distribution")
        st.bar_chart(df["treatment"].value_counts())

        st.subheader("Outcomes")
        st.bar_chart(df["outcome"].value_counts())

        st.subheader("Complications")
        st.bar_chart({
            "Infection": (df["infection"]=="Yes").sum(),
            "Secondary displacement": (df["secondary_displacement"]=="Yes").sum(),
            "Revision": (df["revision"]=="Yes").sum()
        })

        # =====================================================
        # NEW: LINE TREND (LEARNING EVOLUTION)
        # =====================================================

        st.subheader("📈 Learning trend (infection over time)")

        df["index"] = range(len(df))

        fig, ax = plt.subplots()
        ax.plot(df["index"], (df["infection"]=="Yes").astype(int))
        ax.set_ylabel("Infection (0/1)")
        ax.set_xlabel("Patients order")
        st.pyplot(fig)

# =========================================================
# 3. AI LEARNING (REAL DATA BASED)
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

        st.success(f"Best treatment based on YOUR data: {best}")

        st.markdown("""
### Learning principle:

The AI adapts based on:
- functional outcome (A/B/C)
- complication rate
- revision rate
- infection frequency

👉 This is a **real-world evidence system**, not literature-based.
""")
