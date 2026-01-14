import streamlit as st
import pandas as pd
import os
import uuid
from datetime import datetime

st.set_page_config(page_title="VIGIOR-H", layout="wide")

PATIENTS_CSV = "patients.csv"

# -----------------------
# Session State & Data
# -----------------------
if "page" not in st.session_state:
    st.session_state.page = "Home"

if "patients" not in st.session_state:
    if os.path.exists(PATIENTS_CSV):
        st.session_state.patients = pd.read_csv(PATIENTS_CSV)
    else:
        st.session_state.patients = pd.DataFrame(columns=[
            "ID","Date","Age","Tabac","Comorbidities","BoneQuality",
            "Fragments","HSA","Gap","S_AVN","S_PSEU","S_FAIL_FIX","S_SURG",
            "Treatment","Justification","Notes"
        ])

if "Notes" not in st.session_state.patients.columns:
    st.session_state.patients["Notes"] = ""
    st.session_state.patients.to_csv(PATIENTS_CSV, index=False)

def save_patients():
    st.session_state.patients.to_csv(PATIENTS_CSV, index=False)

def generate_patient_id():
    return f"H-{str(uuid.uuid4())[:8].upper()}"

# -----------------------
# Language
# -----------------------
LANG = st.sidebar.radio("🔄 Language / Langue", ["English", "Français"])

def tr(en, fr):
    return en if LANG == "English" else fr

# -----------------------
# Scores
# -----------------------
def compute_scores(age, tabac, fragments, HSA, gap, bone_quality, comorbidities):
    I_age_gt_65 = age > 65
    I_age_gt_70 = age > 70
    I_tabac = tabac
    I_bone_poor = bone_quality == "poor"
    I_comorb = comorbidities >= 1

    S_AVN = 10 + 6*I_age_gt_65 + 7*I_tabac + 3*fragments + 0.3*(130-HSA) + 1.5*gap + 10*I_bone_poor
    S_PSEU = 8 + 2*fragments + 2*gap + 4*I_age_gt_70 + 5*I_tabac + 8*I_bone_poor
    S_FAIL_FIX = 5 + 4*I_bone_poor + 3*fragments + 2*I_comorb + 1.5*gap
    S_SURG = 0.4*S_AVN + 0.35*S_PSEU + 0.25*S_FAIL_FIX

    return [round(min(max(x,0),100),1) for x in [S_AVN,S_PSEU,S_FAIL_FIX,S_SURG]]

# -----------------------
# Pages
# -----------------------
def page_home():
    st.title("VIGIOR-H")
    st.subheader(tr("Predictive Orthopedic Assistant — Proximal Humerus",
                    "Assistant Orthopédique Prédictif — Humérus proximal"))
    c1, c2 = st.columns(2)
    with c1:
        if st.button(tr("New Evaluation","Nouvelle évaluation"), use_container_width=True):
            st.session_state.page = "New Patient"
    with c2:
        if st.button(tr("Registered Patients","Patients enregistrés"), use_container_width=True):
            st.session_state.page = "Registered"

def page_registered():
    st.title(tr("Registered Patients","Patients enregistrés"))

    df = st.session_state.patients.copy()
    st.subheader(tr("Patient registry","Registre des patients"))
    st.dataframe(df, height=300)

    # ---------------- Notes ----------------
    st.markdown("---")
    st.subheader(tr("Patient clinical notes","Notes cliniques"))

    pid = st.selectbox("Patient ID", df["ID"])
    notes = st.text_area("Notes", df[df["ID"]==pid]["Notes"].values[0], height=150)

    if st.button(tr("Save notes","Sauvegarder les notes")):
        st.session_state.patients.loc[df["ID"]==pid,"Notes"] = notes
        save_patients()
        st.success(tr("Saved","Sauvegardé"))

    # ---------------- Analyse du registre ----------------
    st.markdown("---")
    st.subheader(tr("Registry analysis","Analyse du registre"))

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Age distribution**")
        st.bar_chart(df["Age"].value_counts().sort_index())

        st.markdown("**Fragments distribution**")
        st.bar_chart(df["Fragments"].value_counts().sort_index())

    with col2:
        mean_hsa = df["HSA"].mean()
        st.metric("Mean HSA angle (°)", round(mean_hsa,1))

        osteoporosis_rate = (df["BoneQuality"]=="poor").mean()*100
        st.metric("Osteoporosis (%)", round(osteoporosis_rate,1))

    # -------- Complications from notes --------
    st.markdown("### Complications (from clinical notes)")

    notes_lower = df["Notes"].str.lower().fillna("")

    complications = {
        "Infection": notes_lower.str.contains("infection|infected").sum(),
        "Pseudarthrosis": notes_lower.str.contains("pseudarthrose|nonunion").sum(),
        "Humeral head necrosis": notes_lower.str.contains("necrose|avn|osteonecrosis").sum()
    }

    comp_df = pd.DataFrame.from_dict(complications, orient="index", columns=["Cases"])
    st.bar_chart(comp_df)

    if st.button(tr("Back Home","Retour Home"), use_container_width=True):
        st.session_state.page = "Home"

# -----------------------
# Router
# -----------------------
if st.session_state.page == "Home":
    page_home()
elif st.session_state.page == "New Patient":
    page_new_patient()
elif st.session_state.page == "Registered":
    page_registered()
