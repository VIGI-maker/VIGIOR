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

RESEARCH_REFS = [
    {"title": "PHARON model (Goudie et al.) - predictors of nonunion/complications in PHF", "citation": "Goudie EB et al., JBJS, 2021"},
    {"title": "Systematic review/meta-analysis comparing treatments for PHF", "citation": "Hohmann E. et al., J Shoulder Elbow Surg, 2023"},
    {"title": "Comprehensive review of proximal humerus fractures", "citation": "Baker HP et al., J Clin Med, 2022"},
    {"title": "Bayesian network meta-analysis: RTSA vs ORIF vs HA (outcomes by age)", "citation": "Migliorini F., 2025"},
    {"title": "Comparative outcomes arthroplasty vs non-operative (recent review)", "citation": "Lai et al., Frontiers in Medicine, 2024"}
]

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

# Ensure Notes column exists (retro-compatibility)
if "Notes" not in st.session_state.patients.columns:
    st.session_state.patients["Notes"] = ""
    st.session_state.patients.to_csv(PATIENTS_CSV, index=False)

def save_patients():
    st.session_state.patients.to_csv(PATIENTS_CSV, index=False)

def generate_patient_id():
    return f"H-{str(uuid.uuid4())[:8].upper()}"

# -----------------------
# Language Switcher
# -----------------------
LANG = st.sidebar.radio("🔄 Language / Langue", options=["English", "Français"])

def tr(text_en, text_fr):
    return text_en if LANG == "English" else text_fr

# -----------------------
# Scoring functions
# -----------------------
def compute_scores(age, tabac, fragments, HSA, gap, bone_quality, comorbidities):
    I_age_gt_65 = 1 if age > 65 else 0
    I_age_gt_70 = 1 if age > 70 else 0
    I_tabac = 1 if tabac else 0
    I_bone_poor = 1 if bone_quality == "poor" else 0
    I_comorb = 1 if comorbidities >= 1 else 0

    S_AVN = 10 + 6 * I_age_gt_65 + 7 * I_tabac + 3 * fragments + 0.3 * (130 - HSA) + 1.5 * gap + 10 * I_bone_poor
    S_PSEU = 8 + 2 * fragments + 2 * gap + 4 * I_age_gt_70 + 5 * I_tabac + 8 * I_bone_poor
    S_FAIL_FIX = 5 + 4 * I_bone_poor + 3 * fragments + 2 * I_comorb + 1.5 * gap
    S_SURG = 0.4 * S_AVN + 0.35 * S_PSEU + 0.25 * S_FAIL_FIX

    def clip_round(x):
        return round(min(max(x, 0), 100), 1)

    return clip_round(S_AVN), clip_round(S_PSEU), clip_round(S_FAIL_FIX), clip_round(S_SURG)

# -----------------------
# Decision rules (UNCHANGED)
# -----------------------
def propose_treatment(S_AVN, S_PSEU, S_FAIL_FIX, age, fragments, gap, bone_quality, comorbidities):
    f = fragments

    if age >= 70 and bone_quality == "poor" and f <= 3 and gap <= 5 and S_AVN < 60 and S_PSEU < 50:
        return (tr("Conservative treatment","Traitement orthopédique (conservateur)"),
                tr("Elderly osteoporotic patient with minimally displaced fracture: meta-analyses show equivalent functional outcomes with fewer complications, conservative approach prioritized.",
                   "Patient âgé avec ostéoporose et fracture peu décalée : méta-analyses montrent des résultats fonctionnels équivalents au traitement chirurgical avec moins de complications — option conservatrice priorisée."))

    if S_AVN >= 50 or f >= 4 or (age >= 75 and bone_quality == "poor") or (0.4*S_AVN + 0.35*S_PSEU + 0.25*S_FAIL_FIX) >= 55:
        if age >= 75 or bone_quality == "poor" or comorbidities >= 1:
            return (tr("Arthroplasty (RTSA preferred)","Arthroplastie (RTSA préféré)"),
                    tr("High risk of reconstruction failure in elderly/osteoporotic patients — RTSA often preferred to restore function and reduce reoperation.",
                       "Risque élevé d'échec de reconstruction chez patient âgé/ostéoporotique — RTSA souvent préférable pour restaurer fonction et diminuer reprises."))
        else:
            return (tr("Arthroplasty (HA or RTSA as per-op)","Arthroplastie (HA ou RTSA selon per-op)"),
                    tr("High risk of mechanical complications or uncertain reconstruction; arthroplasty recommended.",
                       "Risque important de complications mécaniques ou reconstruction incertaine ; arthroplastie recommandée."))

    if S_PSEU >= 30 or S_FAIL_FIX >= 30 or f == 3:
        justific = tr("Open reduction internal fixation (ORIF) indicated: significant risk of nonunion/fixation failure but anatomy and bone quality allow reconstruction.",
                      "Ostéosynthèse foyer ouvert (ORIF) indiquée : risque de pseudarthrose/échec de fixation significatif mais anatomie et qualité osseuse permettant reconstruction.")
        if bone_quality == "poor" and age < 65:
            justific += " " + tr("Consider augmentation techniques (graft, cement).","Prévoir techniques d'augmentation (greffe, cimentage, renfort).")
        return (tr("Open reduction internal fixation (ORIF)","Ostéosynthèse foyer ouvert (ORIF)"), justific)

    if f <= 2 and S_FAIL_FIX < 30 and bone_quality != "poor":
        return (tr("Closed reduction internal fixation (IM nailing)","Ostéosynthèse foyer fermé (clou)"),
                tr("Minimally comminuted fracture and good bone quality: intramedullary nail suitable, minimal tissue trauma.",
                   "Fracture peu comminutive et bonne qualité osseuse : clou intramédullaire adapté, moindre traumatisme tissulaire."))

    if S_AVN < 25 and S_PSEU < 20 and f <= 2:
        return (tr("Conservative treatment","Traitement orthopédique (conservateur)"),
                tr("Low scores: good candidate for non-operative management.","Scores faibles : bon candidat pour traitement non opératoire."))

    return (tr("Conservative treatment","Traitement orthopédique (conservateur)"),
            tr("Default conservative choice.","Choix conservateur par défaut."))

# -----------------------
# Pages
# -----------------------
def page_home():
    st.title("VIGIOR-H")
    st.subheader(tr("Predictive Orthopedic Assistant — Proximal Humerus",
                    "Assistant Orthopédique Prédictif — Humérus proximal"))
    c1, c2 = st.columns([1,1])
    with c1:
        if st.button(tr("New Evaluation","Nouvelle évaluation"), use_container_width=True):
            st.session_state.page = "New Patient"
    with c2:
        if st.button(tr("Research & Database","Research & Base de données"), use_container_width=True):
            st.session_state.page = "Research"

def page_new_patient():
    st.title(tr("🧑‍⚕️ New Patient Evaluation","🧑‍⚕️ Nouvelle évaluation patient"))

    with st.form(key="form_eval"):
        col1, col2 = st.columns(2)
        with col1:
            age = st.number_input(tr("Age (years)","Âge (ans)"), min_value=18, max_value=110, value=70)
            tabac = st.checkbox(tr("Current smoker","Tabac actuel"))
            comorbidities = st.number_input(tr("Number of major comorbidities (0 if none)","Nombre de comorbidités majeures (0 si none)"), min_value=0, max_value=10, value=0)
            bone_quality = st.selectbox(tr("Bone quality","Qualité osseuse"), ["normal","poor"])
        with col2:
            fragments = st.selectbox(tr("Number of fragments","Nombre de fragments"), [2,3,4])
            HSA = st.slider(tr("HSA angle (°)","Angle HSA (°)"), 60, 180, 130)
            gap = st.number_input(tr("Interfragmentary gap (mm)","Gap interfragmentaire (mm)"), min_value=0, max_value=50, value=3)

        submitted = st.form_submit_button(tr("Evaluate","Évaluer"))

    if submitted:
        S_AVN, S_PSEU, S_FAIL_FIX, S_SURG = compute_scores(
            age, tabac, fragments, HSA, gap, bone_quality, comorbidities
        )

        treatment, justification = propose_treatment(
            S_AVN, S_PSEU, S_FAIL_FIX, age, fragments, gap, bone_quality, comorbidities
        )

        st.subheader(tr("Results","Résultats"))
        st.write(f"- S_AVN (avascular necrosis) : {S_AVN}%")
        st.write(f"- S_PSEU (nonunion) : {S_PSEU}%")
        st.write(f"- S_FAIL_FIX (fixation failure) : {S_FAIL_FIX}%")
        st.write(f"- S_SURG (composite) : {S_SURG}%")

        st.subheader(tr("Recommendation","Recommandation"))
        st.success(f"➡️ {treatment}")
        st.write(justification)

        patient_id = generate_patient_id()
        row = {
            "ID": patient_id,
            "Date": datetime.utcnow().isoformat(),
            "Age": age,
            "Tabac": "Yes" if tabac else "No",
            "Comorbidities": comorbidities,
            "BoneQuality": bone_quality,
            "Fragments": fragments,
            "HSA": HSA,
            "Gap": gap,
            "S_AVN": S_AVN,
            "S_PSEU": S_PSEU,
            "S_FAIL_FIX": S_FAIL_FIX,
            "S_SURG": S_SURG,
            "Treatment": treatment,
            "Justification": justification,
            "Notes": ""
        }

        st.session_state.patients = pd.concat(
            [st.session_state.patients, pd.DataFrame([row])],
            ignore_index=True
        )
        save_patients()
        st.success(tr(f"Patient saved: {patient_id}",f"Patient enregistré : {patient_id}"))

    if st.button(tr("Back Home","Retour Home"), use_container_width=True):
        st.session_state.page = "Home"

def page_research():
    st.title(tr("Research & Patients","Research & Patients"))
    st.subheader(tr("Registered patients","Patients enregistrés"))

    q = st.text_input(tr("Search (ID, age, treatment...)","Rechercher (ID, âge, traitement...)"))
    df = st.session_state.patients.copy()
    if q:
        df = df[df.apply(lambda r: q.lower() in r.astype(str).str.lower().to_string(), axis=1)]

    st.dataframe(df, height=300)

    st.markdown("---")
    st.subheader(tr("Patient clinical notes","Notes cliniques du patient"))

    selected_id = st.selectbox(
        tr("Select patient ID","Sélectionner l’ID du patient"),
        df["ID"].tolist()
    )

    patient_row = df[df["ID"] == selected_id].iloc[0]

    notes = st.text_area(
        tr("Surgeon clinical notes","Notes cliniques du chirurgien"),
        value=patient_row.get("Notes",""),
        height=200
    )

    if st.button(tr("Save notes","Sauvegarder les notes")):
        st.session_state.patients.loc[
            st.session_state.patients["ID"] == selected_id, "Notes"
        ] = notes
        save_patients()
        st.success(tr("Notes saved","Notes sauvegardées"))

    st.markdown("---")
    st.subheader(tr("Key References (archived)","Références clés (archivées)"))
    for r in RESEARCH_REFS:
        st.markdown(f"- **{r['title']}** — *{r['citation']}*")

    if st.button(tr("Back Home","Retour Home"), use_container_width=True):
        st.session_state.page = "Home"

# -----------------------
# Router
# -----------------------
if st.session_state.page == "Home":
    page_home()
elif st.session_state.page == "New Patient":
    page_new_patient()
elif st.session_state.page == "Research":
    page_research()
else:
    st.session_state.page = "Home"
