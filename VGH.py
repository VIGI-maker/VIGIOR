import streamlit as st
import pandas as pd
import os
import uuid
from datetime import datetime

st.set_page_config(page_title="VIGIOR-H", layout="wide")

# -----------------------
# File
# -----------------------
PATIENTS_CSV = "patients.csv"

# -----------------------
# Session state
# -----------------------
if "page" not in st.session_state:
    st.session_state.page = "Home"

if "selected_patient" not in st.session_state:
    st.session_state.selected_patient = None

# -----------------------
# Load data
# -----------------------
if os.path.exists(PATIENTS_CSV):
    st.session_state.patients = pd.read_csv(PATIENTS_CSV)
else:
    st.session_state.patients = pd.DataFrame(columns=[
        "Patient ID","Date",
        "Age","Smoking status","Number of comorbidities","Bone quality",
        "Number of fracture fragments","HSA angle","Interfragmentary gap",
        "Risk of avascular necrosis (%)",
        "Risk of nonunion (%)",
        "Risk of fixation failure (%)",
        "Recommended treatment",
        "Recommendation justification",
        "Surgeon notes"
    ])

def save_patients():
    st.session_state.patients.to_csv(PATIENTS_CSV, index=False)

def generate_patient_id():
    return f"H-{str(uuid.uuid4())[:8].upper()}"

# -----------------------
# Language
# -----------------------
LANG = st.sidebar.radio("Language", ["English","Français"])

def tr(en, fr):
    return en if LANG == "English" else fr

# -----------------------
# Scoring
# -----------------------
def compute_scores(age, smoking, fragments, HSA, gap, bone_quality, comorbidities):
    I_age_65 = 1 if age > 65 else 0
    I_age_70 = 1 if age > 70 else 0
    I_smoking = 1 if smoking else 0
    I_poor_bone = 1 if bone_quality == "poor" else 0
    I_comorb = 1 if comorbidities >= 1 else 0

    risk_avn = 10 + 6*I_age_65 + 7*I_smoking + 3*fragments + 0.3*(130-HSA) + 1.5*gap + 10*I_poor_bone
    risk_nonunion = 8 + 2*fragments + 2*gap + 4*I_age_70 + 5*I_smoking + 8*I_poor_bone
    risk_fix_failure = 5 + 4*I_poor_bone + 3*fragments + 2*I_comorb + 1.5*gap

    def clip(x): return round(min(max(x,0),100),1)

    return clip(risk_avn), clip(risk_nonunion), clip(risk_fix_failure)

# -----------------------
# Recommendation logic (UNCHANGED)
# -----------------------
def propose_treatment(risk_avn, risk_nonunion, risk_fix_failure, age, fragments, gap, bone_quality, comorbidities):

    if age >= 70 and bone_quality == "poor" and fragments <= 3 and gap <= 5 and risk_avn < 60:
        return tr(
            "Non-operative (conservative) treatment",
            "Traitement orthopédique (conservateur)"
        ), tr(
            "Elderly patient with osteoporotic bone and limited displacement. Current evidence shows comparable functional outcomes with fewer complications using conservative management.",
            "Patient âgé, os ostéoporotique et fracture peu déplacée. Les données actuelles montrent des résultats fonctionnels comparables avec moins de complications par traitement conservateur."
        )

    if risk_avn >= 50 or fragments >= 4 or (age >= 75 and bone_quality == "poor"):
        return tr(
            "Primary arthroplasty (RTSA preferred)",
            "Arthroplastie primaire (RTSA privilégiée)"
        ), tr(
            "High risk of humeral head ischemia or mechanical failure makes reconstruction unreliable.",
            "Risque élevé de souffrance céphalique ou d’échec mécanique rendant la reconstruction peu fiable."
        )

    if risk_nonunion >= 30 or risk_fix_failure >= 30 or fragments == 3:
        return tr(
            "Open reduction and internal fixation (ORIF)",
            "Ostéosynthèse à foyer ouvert"
        ), tr(
            "Moderate to high risk of nonunion or fixation failure, but bone stock and patient profile allow reconstruction.",
            "Risque modéré à élevé de pseudarthrose ou d’échec de fixation, avec un terrain permettant une reconstruction."
        )

    return tr(
        "Non-operative treatment",
        "Traitement orthopédique"
    ), tr(
        "Low predicted complication risks support conservative management.",
        "Faible risque prédictif de complications, en faveur d’un traitement conservateur."
    )

# -----------------------
# Pages
# -----------------------
def page_home():
    st.title("VIGIOR-H")
    c1, c2 = st.columns(2)
    with c1:
        if st.button(tr("New evaluation","Nouvelle évaluation"), use_container_width=True):
            st.session_state.page = "New"
    with c2:
        if st.button(tr("Registered patients","Patients enregistrés"), use_container_width=True):
            st.session_state.page = "Registry"

# -----------------------
def page_new_patient():
    st.title(tr("New patient evaluation","Nouvelle évaluation patient"))

    with st.form("evaluation"):
        col1, col2 = st.columns(2)
        with col1:
            age = st.number_input(tr("Age","Âge"),18,110,70)
            smoking = st.checkbox(tr("Current smoker","Tabagisme actif"))
            comorbidities = st.number_input(tr("Number of comorbidities","Nombre de comorbidités"),0,10,0)
            bone_quality = st.selectbox(tr("Bone quality","Qualité osseuse"),["normal","poor"])
        with col2:
            fragments = st.selectbox(tr("Number of fracture fragments","Nombre de fragments"),[2,3,4])
            HSA = st.slider(tr("Head–shaft angle (degrees)","Angle tête-diaphyse (°)"),60,180,130)
            gap = st.number_input(tr("Interfragmentary gap (mm)","Écart interfragmentaire (mm)"),0,50,3)

        submitted = st.form_submit_button(tr("Evaluate","Évaluer"))

    if submitted:
        risk_avn, risk_nonunion, risk_fix_failure = compute_scores(
            age, smoking, fragments, HSA, gap, bone_quality, comorbidities)

        treatment, justification = propose_treatment(
            risk_avn, risk_nonunion, risk_fix_failure,
            age, fragments, gap, bone_quality, comorbidities)

        st.subheader(tr("Predicted complication risks","Risques prédictifs de complications"))
        st.write(f"• Avascular necrosis risk: **{risk_avn}%**")
        st.write(f"• Nonunion risk: **{risk_nonunion}%**")
        st.write(f"• Fixation failure risk: **{risk_fix_failure}%**")

        st.subheader(tr("Recommended strategy","Stratégie recommandée"))
        st.success(treatment)
        st.write(justification)

        st.subheader(tr("Clinical interpretation","Interprétation clinique"))
        st.markdown(tr(
            "- These risk estimates are based on published prognostic factors.\n"
            "- They are intended to support — not replace — clinical judgment.\n"
            "- Patient-specific factors and surgeon experience remain essential.",
            "- Ces estimations sont basées sur des facteurs pronostiques publiés.\n"
            "- Elles visent à aider la décision sans se substituer au jugement clinique.\n"
            "- Le contexte patient et l’expérience du chirurgien restent déterminants."
        ))

        pid = generate_patient_id()
        row = {
            "Patient ID": pid,
            "Date": datetime.utcnow().isoformat(),
            "Age": age,
            "Smoking status": smoking,
            "Number of comorbidities": comorbidities,
            "Bone quality": bone_quality,
            "Number of fracture fragments": fragments,
            "HSA angle": HSA,
            "Interfragmentary gap": gap,
            "Risk of avascular necrosis (%)": risk_avn,
            "Risk of nonunion (%)": risk_nonunion,
            "Risk of fixation failure (%)": risk_fix_failure,
            "Recommended treatment": treatment,
            "Recommendation justification": justification,
            "Surgeon notes": ""
        }

        st.session_state.patients = pd.concat(
            [st.session_state.patients, pd.DataFrame([row])],
            ignore_index=True)

        save_patients()
        st.success(tr(f"Patient saved: {pid}","Patient enregistré : ") + pid)

    if st.button(tr("Back to home","Retour accueil")):
        st.session_state.page = "Home"

# -----------------------
def page_registry():
    st.title(tr("Registered patients","Patients enregistrés"))

    df = st.session_state.patients
    st.dataframe(df, height=300)

    st.markdown("---")
    pid = st.selectbox(tr("Select a patient","Sélectionner un patient"), df["Patient ID"].tolist())
    patient = df[df["Patient ID"] == pid].iloc[0]

    st.subheader(tr("Surgeon clinical notes","Notes cliniques du chirurgien"))
    notes = st.text_area("", value=patient["Surgeon notes"], height=200)

    if st.button(tr("Save notes","Sauvegarder les notes")):
        st.session_state.patients.loc[
            st.session_state.patients["Patient ID"] == pid,
            "Surgeon notes"
        ] = notes
        save_patients()
        st.success(tr("Notes saved","Notes sauvegardées"))

    if st.button(tr("Back to home","Retour accueil")):
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
