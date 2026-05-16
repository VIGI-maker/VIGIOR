# =========================================================
# FILE : app.py
# VIGIOR AI - DEFINITIVE VERSION
# Predictive AI for Tibial Plateau Fractures
# Ready for GitHub + Streamlit Cloud
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
st.subheader("Predictive AI Assistant for Tibial Plateau Fractures")

st.markdown("---")

# =========================================================
# SIDEBAR
# =========================================================

menu = st.sidebar.selectbox(
    "Navigation",
    [
        "New Patient",
        "Patient Database"
    ]
)

# =========================================================
# LOGISTIC FUNCTION
# =========================================================

def logistic(x):
    return 1 / (1 + math.exp(-x))

# =========================================================
# RISK CALCULATOR
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

    # AGE
    if age > 60:
        infection_score += 1
        skin_score += 1

    # DIABETES
    if diabetes == "Yes":
        infection_score += 2

    # SMOKING
    if smoking == "Yes":
        infection_score += 2

    # BMI
    if bmi > 30:
        infection_score += 1

    # HIGH ENERGY
    if high_energy == "Yes":
        compartment_score += 2
        skin_score += 2

    # OPEN FRACTURE
    if open_fracture == "Yes":
        infection_score += 3
        skin_score += 2

    # SCHATZKER
    if schatzker in ["V", "VI"]:
        infection_score += 2
        compartment_score += 2
        skin_score += 1

    # SOFT TISSUE
    if soft_tissue == "Moderate":
        skin_score += 2

    if soft_tissue == "Severe":
        infection_score += 2
        skin_score += 4

    # BLISTERS
    if blisters == "Yes":
        skin_score += 3

    # COMPARTMENT
    if compartment_signs == "Yes":
        compartment_score += 5

    # EXTERNAL FIXATOR
    if external_fixator == "Yes":
        infection_score += 1

    # DELAY
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
    schatzker,
    open_fracture,
    soft_tissue,
    blisters,
    compartment_signs,
    high_energy
):

    # =====================================================
    # VERY HIGH SOFT TISSUE RISK
    # =====================================================

    if (
        skin >= 80
        or soft_tissue == "Severe"
        or blisters == "Yes"
    ):

        return f"""
# 🚨 Recommended Strategy
## Temporary External Fixation + Delayed Minimally Invasive Osteosynthesis

### Why this strategy?

This fracture presents a major soft tissue risk profile:

- Skin complication risk : {skin}%
- Infection risk : {infection}%
- Severe edema or skin suffering probable
- Immediate aggressive ORIF may cause:
  - skin necrosis
  - wound dehiscence
  - deep infection

### Immediate Treatment

✅ Temporary spanning external fixation

Purpose:
- restore alignment
- maintain limb length
- stabilize fracture
- protect soft tissues

✅ Strict elevation and edema control

✅ Daily soft tissue evaluation

### Definitive Surgery

➡ Delayed osteosynthesis after soft tissue recovery
(usually 7–14 days)

Definitive surgery should ideally wait for:
- wrinkle sign
- edema regression
- skin improvement

### Preferred Technique

✅ Minimally invasive osteosynthesis (MIPO)

Reason:
- preserves vascularity
- decreases infection risk
- minimizes soft tissue aggression

### Future Risks

⚠ Deep infection  
⚠ Skin necrosis  
⚠ Delayed union  
⚠ Knee stiffness
"""

    # =====================================================
    # COMPARTMENT SYNDROME RISK
    # =====================================================

    elif (
        compartment >= 75
        or compartment_signs == "Yes"
    ):

        return f"""
# 🚨 Recommended Strategy
## Strict Compartment Monitoring ± Emergency Fasciotomy + Staged Osteosynthesis

### Why this strategy?

This patient presents a very high risk of compartment syndrome:

- Compartment syndrome risk : {compartment}%
- High-energy trauma mechanism
- Severe swelling probable

### Immediate Priorities

✅ Repeated clinical monitoring

Monitor:
- pain increase
- pain on passive stretch
- tense compartments
- neurologic signs

### If compartment syndrome confirmed

➡ Emergency fasciotomy mandatory

### Fracture Stabilization

✅ Temporary external fixation initially recommended

Reason:
- damage control strategy
- minimizes secondary soft tissue injury
- safer delayed fixation

### Definitive Treatment

➡ Delayed ORIF after soft tissue stabilization

### Future Risks

⚠ Infection  
⚠ Muscle necrosis  
⚠ Neurologic deficit  
⚠ Knee stiffness
"""

    # =====================================================
    # OPEN FRACTURE
    # =====================================================

    elif open_fracture == "Yes":

        return f"""
# 🚨 Recommended Strategy
## Urgent Debridement + Temporary Stabilization + Delayed Internal Fixation

### Why this strategy?

This is an open fracture with high contamination risk:

- Infection risk : {infection}%
- Soft tissue vulnerability probable

### Immediate Treatment

✅ Urgent antibiotics

✅ Surgical irrigation and debridement

✅ Temporary stabilization
(external fixation if necessary)

### Why avoid immediate aggressive ORIF?

Because immediate definitive fixation may increase:
- deep infection
- wound complications
- fixation failure

### Definitive Surgery

➡ Delayed internal fixation after:
- infection control
- soft tissue improvement

### Preferred Technique

✅ Biological fixation / MIPO if feasible

### Future Risks

⚠ Deep infection  
⚠ Nonunion  
⚠ Multiple revision surgeries
"""

    # =====================================================
    # MODERATE SOFT TISSUE RISK
    # =====================================================

    elif (
        skin >= 55
        or infection >= 60
        or soft_tissue == "Moderate"
    ):

        return f"""
# ⚠ Recommended Strategy
## Minimally Invasive Osteosynthesis (MIPO)

### Why this strategy?

This fracture presents a moderate soft tissue risk:

- Infection risk : {infection}%
- Skin complication risk : {skin}%

### Why MIPO?

Compared with large open ORIF:
- less periosteal stripping
- preserves blood supply
- decreases soft tissue aggression
- lower infection probability

### Surgical Goal

✅ Stable fixation with biological preservation

### Timing

➡ Surgery after partial edema reduction

### Future Risks

⚠ Infection  
⚠ Secondary displacement  
⚠ Delayed union
"""

    # =====================================================
    # LOW RISK
    # =====================================================

    else:

        return f"""
# ✅ Recommended Strategy
## Early Open Reduction and Internal Fixation (ORIF)

### Why this strategy?

Current evaluation suggests:

- acceptable soft tissue condition
- low complication risk profile
- Infection risk : {infection}%
- Skin complication risk : {skin}%

### Why immediate ORIF?

Early fixation allows:
- anatomical joint restoration
- stable fixation
- early mobilization
- reduction of secondary displacement

### Surgical Goal

✅ Restore:
- joint congruence
- alignment
- knee stability

### Future Monitoring

⚠ Infection surveillance  
⚠ Knee stiffness prevention  
⚠ Secondary osteoarthritis
"""

# =========================================================
# NEW PATIENT PAGE
# =========================================================

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
            blisters,
            compartment_signs,
            high_energy
        )

        st.success("AI Prediction Completed")

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

        st.subheader("🩺 Recommended Management")

        st.markdown(treatment)

        st.markdown("---")

        st.subheader("💾 Follow-up")

        follow_up = st.text_area(
            "Future evolution",
            placeholder="infection, pseudarthrosis, revision surgery..."
        )

        if st.button("Save Patient"):

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

# =========================================================
# DATABASE PAGE
# =========================================================

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

# =========================================================
# FOOTER
# =========================================================

st.markdown("---")

st.caption("""
VIGIOR AI — Educational predictive tool for orthopaedic surgery.
Clinical judgment remains mandatory.
""")
