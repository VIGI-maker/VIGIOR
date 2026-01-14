import streamlit as st
import pandas as pd
import os
import uuid
from datetime import datetime

st.set_page_config(page_title="VIGIOR-H", layout="wide")

# -----------------------
# Constants / Files
# -----------------------
PATIENTS_CSV = "patients.csv"

# -----------------------
# Session State & Data
# -----------------------
if "page" not in st.session_state:
    st.session_state.page = "Home"

if "selected_patient" not in st.session_state:
    st.session_state.selected_patient = None

if os.path.exists(PATIENTS_CSV):
    patients_df = pd.read_csv(PATIENTS_CSV)
else:
    patients_df = pd.DataFrame(columns=[
        "ID","Date","Age","Tabac","Comorbidities","BoneQuality",
        "Fragments","HSA","Gap",
        "S_AVN","S_PSEU","S_FAIL_FIX","S_SURG",
        "Treatment","Justification","Notes"
    ])

st.session_state.patients = patients_df


def save_patients():
    st.session_state.patients.to_csv(PATIENTS_CSV, index=False)


def generate_patient_id():
    return f"H-{str(uuid.uuid4())[:8].upper()}"

# -----------------------
# Language
# -----------------------
LANG = st.sidebar.radio("🔄 Language", ["English","Français"])

def tr(en, fr):
    return en if LANG == "English" else fr

# -----------------------
# Scores
# -----------------------
def compute_scores(age, tabac, fragments, HSA, gap, bone_quality, comorbidities):
    I_age_gt_65 = 1 if age > 65 else 0
    I_age_gt_70 = 1 if age > 70 else 0
    I_tabac = 1 if tabac else 0
    I_bone_poor = 1 if bone_quality == "poor" else 0
    I_comorb = 1 if comorbidities >= 1 else 0

    S_AVN = 10 + 6*I_age_gt_65 + 7*I_tabac + 3*fragments + 0.3*(130-HSA) + 1.5*gap + 10*I_bone_poor
    S_PSEU = 8 + 2*fragments + 2*gap + 4*I_age_gt_70 + 5*I_tabac + 8*I_bone_poor
    S_FAIL_FIX = 5 + 4*I_bone_poor + 3*fragments + 2*I_comorb + 1.5*gap
    S_SURG = 0.4*S_AVN + 0.35*S_PSEU + 0.25*S_FAIL_FIX

    def clip(x): return round(min(max(x,0),100),1)
    return clip(S_AVN), clip(S_PSEU), clip(S_FAIL_FIX), clip(S_SURG)

# -----------------------
# Pages
# -----------------------
def page_home():
    st.title("VIGIOR-H")

    c1, c2 = st.columns(2)
    with c1:
        if st.button(tr("New Evaluation","Nouvelle évaluation"), use_container_width=True):
            st.session_state.page = "New"
    with c2:
        if st.button(tr("Registered Patients","Patients enregistrés"), use_container_width=True):
            st.session_state.page = "Registry"

# -----------------------
def page_new_patient():
    st.title(tr("🧑‍⚕️ New Evaluation","🧑‍⚕️ Nouvelle évaluation"))

    with st.form("eval"):
        age = st.number_input(tr("Age","Âge"), 18, 110, 70)
        tabac = st.checkbox(tr("Smoker","Tabac"))
        comorbidities = st.number_input(tr("Comorbidities","Comorbidités"),0,10,0)
        bone_quality = st.selectbox(tr("Bone quality","Qualité osseuse"),["normal","poor"])
        fragments = st.selectbox(tr("Fragments","Fragments"),[2,3,4])
        HSA = st.slider("HSA",60,180,130)
        gap = st.number_input(tr("Gap (mm)","Gap (mm)"),0,50,3)

        submitted = st.form_submit_button(tr("Evaluate","Évaluer"))

    if submitted:
        S_AVN,S_PSEU,S_FAIL_FIX,S_SURG = compute_scores(
            age,tabac,fragments,HSA,gap,bone_quality,comorbidities)

        st.subheader("Scores")
        st.write(S_AVN,S_PSEU,S_FAIL_FIX,S_SURG)

        # Save
        pid = generate_patient_id()
        row = {
            "ID": pid,
            "Date": datetime.utcnow().isoformat(),
            "Age": age,
            "Tabac": tabac,
            "Comorbidities": comorbidities,
            "BoneQuality": bone_quality,
            "Fragments": fragments,
            "HSA": HSA,
            "Gap": gap,
            "S_AVN": S_AVN,
            "S_PSEU": S_PSEU,
            "S_FAIL_FIX": S_FAIL_FIX,
            "S_SURG": S_SURG,
            "Treatment": "",
            "Justification": "",
            "Notes": ""
        }

        st.session_state.patients = pd.concat(
            [st.session_state.patients, pd.DataFrame([row])],
            ignore_index=True)

        save_patients()
        st.success(f"Patient saved: {pid}")

        # 🔍 Similar patients
        st.markdown("---")
        st.subheader(tr("Similar registered patients","Patients similaires enregistrés"))

        similar = st.session_state.patients[
            (abs(st.session_state.patients["Age"] - age) <= 5) &
            (st.session_state.patients["Fragments"] == fragments)
        ]

        if len(similar) == 0:
            st.info(tr("No similar patient found","Aucun patient similaire"))
        else:
            for _, r in similar.iterrows():
                if st.button(f"📁 {r['ID']}"):
                    st.session_state.selected_patient = r["ID"]
                    st.session_state.page = "Registry"

    if st.button(tr("Back","Retour")):
        st.session_state.page = "Home"

# -----------------------
def page_registry():
    st.title(tr("📁 Registered Patients","📁 Patients enregistrés"))

    df = st.session_state.patients
    st.dataframe(df[["ID","Age","Fragments","S_SURG"]], height=250)

    st.markdown("---")

    pid = st.selectbox(
        tr("Select patient","Sélectionner patient"),
        df["ID"].tolist(),
        index=df["ID"].tolist().index(st.session_state.selected_patient)
        if st.session_state.selected_patient in df["ID"].tolist()
        else 0
    )

    patient = df[df["ID"] == pid].iloc[0]

    st.subheader(f"📝 Notes – {pid}")
    notes = st.text_area(
        tr("Clinical notes","Notes cliniques"),
        value=patient["Notes"],
        height=200
    )

    if st.button(tr("Save notes","Sauvegarder notes")):
        st.session_state.patients.loc[
            st.session_state.patients["ID"] == pid, "Notes"
        ] = notes
        save_patients()
        st.success(tr("Notes saved","Notes sauvegardées"))

    if st.button(tr("Back Home","Retour accueil")):
        st.session_state.page = "Home"

# -----------------------
# Router
# -----------------------
if st.session_state.page == "Home":
    page_home()
elif st.session_state.page == "New":
    page_new_patient()
elif st.session_state.page == "Registry":
    page_registry()
