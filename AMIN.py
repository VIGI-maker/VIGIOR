# app_final.py
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
            "Treatment","Justification"
        ])

def save_patients():
    st.session_state.patients.to_csv(PATIENTS_CSV, index=False)

def generate_patient_id():
    return f"H-{str(uuid.uuid4())[:8].upper()}"

# -----------------------
# Scoring functions (detailed formulas)
# -----------------------
def compute_scores(age, tabac, fragments, HSA, gap, bone_quality, comorbidities):
    """
    Retourne S_AVN, S_PSEU, S_FAIL_FIX, S_SURG
    Formules calibrées sur nos approximations basées sur PHARON / méta-analyses.
    """
    # Binary indicators
    I_age_gt_65 = 1 if age > 65 else 0
    I_age_gt_70 = 1 if age > 70 else 0
    I_tabac = 1 if tabac else 0
    I_bone_poor = 1 if bone_quality == "poor" else 0
    I_comorb = 1 if comorbidities >= 1 else 0

    # --- S_AVN ---
    S_AVN = 10
    S_AVN += 6 * I_age_gt_65
    S_AVN += 7 * I_tabac
    S_AVN += 3 * fragments
    S_AVN += 0.3 * (130 - HSA)    # if HSA <130 increases risk; if HSA>130 decreases
    S_AVN += 1.5 * gap
    S_AVN += 10 * I_bone_poor

    # --- S_PSEU ---
    S_PSEU = 8
    S_PSEU += 2 * fragments
    S_PSEU += 2 * gap
    S_PSEU += 4 * I_age_gt_70
    S_PSEU += 5 * I_tabac
    S_PSEU += 8 * I_bone_poor

    # --- S_FAIL_FIX ---
    S_FAIL_FIX = 5
    S_FAIL_FIX += 4 * I_bone_poor
    S_FAIL_FIX += 3 * fragments
    S_FAIL_FIX += 2 * I_comorb
    S_FAIL_FIX += 1.5 * gap

    # Composite
    S_SURG = 0.4 * S_AVN + 0.35 * S_PSEU + 0.25 * S_FAIL_FIX

    # Clip and round
    def clip_round(x):
        if x < 0: x = 0
        if x > 100: x = 100
        return round(x,1)

    return clip_round(S_AVN), clip_round(S_PSEU), clip_round(S_FAIL_FIX), clip_round(S_SURG)

# -----------------------
# Decision rules (with Orthopédique priority for elderly osteoporotic)
# -----------------------
def propose_treatment(S_AVN, S_PSEU, S_FAIL_FIX, age, fragments, gap, bone_quality, comorbidities):
    """
    Retourne (treatment_label, justification).
    Modalités exclusives :
      - Traitement orthopédique
      - Ostéosynthèse foyer fermé (IM nailing)
      - Ostéosynthèse foyer ouvert (ORIF)
      - Arthroplastie (HA / RTSA selon indication)
    """

    # Map fragments to numeric (if user provided numeric)
    # Here fragments expected as integer (2,3,4)
    f = fragments

    # PRIORITÉ ORTHOPÉDIQUE (nouvelle règle demandée)
    # Si âge élevé + os pauvre + fracture peu déplacée (gap <=5, fragments <=3) + risques modérés -> orthopédique
    if age >= 70 and bone_quality == "poor" and f <= 3 and gap <= 5 and S_AVN < 60 and S_PSEU < 50:
        return ("Traitement orthopédique (conservateur)",
                "Patient âgé avec ostéoporose et fracture peu décalée : méta-analyses montrent des résultats fonctionnels équivalents au traitement chirurgical avec moins de complications — option conservatrice priorisée.")

    # Arthroplastie criteria (high AVN risk, 4 fragments, elderly with poor bone or high composite)
    if (S_AVN >= 50) or (f >= 4) or (age >= 75 and bone_quality == "poor") or (S_SURG := 0.4*S_AVN + 0.35*S_PSEU + 0.25*S_FAIL_FIX) >= 55:
        # prefer RTSA for elderly/poor bone/comorbid
        if age >= 75 or bone_quality == "poor" or comorbidities >= 1:
            return ("Arthroplastie (RTSA preferred)",
                    "Risque élevé d'échec de reconstruction chez patient âgé/ostéoporotique — RTSA souvent préférable pour restaurer fonction et diminuer reprises.")
        else:
            return ("Arthroplastie (HA or RTSA selon per-op)",
                    "Risque important de complications mécaniques ou reconstruction incertaine ; arthroplastie recommandée.")

    # ORIF criteria
    if (S_PSEU >= 30 or S_FAIL_FIX >= 30 or f == 3) and not (bone_quality == "poor" and age >= 75):
        justific = ("Ostéosynthèse foyer ouvert (ORIF) indiquée : risque de pseudarthrose/échec de fixation significatif mais anatomie et qualité osseuse permettant reconstruction.")
        if bone_quality == "poor" and age < 65:
            justific += " Prévoir techniques d'augmentation (greffe, cimentage, renfort)."
        return ("Ostéosynthèse foyer ouvert (ORIF)", justific)

    # IM nailing (closed)
    if f <= 2 and S_FAIL_FIX < 30 and bone_quality != "poor":
        return ("Ostéosynthèse foyer fermé (IM nailing)",
                "Fracture peu comminutive et bonne qualité osseuse : clou intramédullaire adapté, moindre traumatisme tissulaire.")

    # Conservative fallback for low risk
    if S_AVN < 25 and S_PSEU < 20 and f <= 2:
        return ("Traitement orthopédique (conservateur)",
                "Scores faibles : bon candidat pour traitement non opératoire.")

    # Dernier recours : choisir selon priorités (Arthroplastie si plusieurs signaux de risque; sinon ORIF)
    if S_AVN >= 40 or f >= 3:
        if age >= 75 or bone_quality == "poor":
            return ("Arthroplastie (type selon per-op)", "Signal de risque élevé; arthroplastie privilégiée en raison du profil du patient.")
        else:
            return ("Ostéosynthèse foyer ouvert (ORIF)", "Signal de risque modéré-élevé mais patient jeune/osseux correct -> tenter reconstruction.")

    # Par défaut, conservative
    return ("Traitement orthopédique (conservateur)", "Choix conservateur par défaut pour cas intermédiaire ou patient à risque.")

# -----------------------
# Pages
# -----------------------
def page_home():
    st.title("VIGIOR-H")
    st.subheader("Predictive Orthopedic Assistant — Proximal Humerus")
    c1, c2 = st.columns([1,1])
    with c1:
        if st.button("Nouvelle évaluation", use_container_width=True):
            st.session_state.page = "New Patient"
    with c2:
        if st.button("Research & Database", use_container_width=True):
            st.session_state.page = "Research"

def page_new_patient():
    st.title("🧑‍⚕️ Nouvelle évaluation patient")

    with st.form(key="form_eval"):
        col1, col2, col3 = st.columns(3)
        with col1:
            age = st.number_input("Âge (ans)", min_value=18, max_value=110, value=70)
            tabac = st.checkbox("Tabac actuel")
            comorbidities = st.number_input("Nombre de comorbidités majeures (0 si none)", min_value=0, max_value=10, value=0)
            bone_quality = st.selectbox("Qualité osseuse", ["normal", "poor"])
        with col2:
            fragments = st.selectbox("Nombre de fragments", [2,3,4])
            HSA = st.slider("Angle HSA (°)", 60, 180, 130)
            gap = st.number_input("Gap interfragmentaire (mm)", min_value=0, max_value=50, value=3)
        with col3:
            displacement = st.selectbox("Déplacement (subjectif)", ["Faible","Modéré","Sévère"])
            # note clinical and tuberosities removed per request
            # submit button (single click)
            submitted = st.form_submit_button("Évaluer")

    if submitted:
        # compute numeric fragments int
        f = fragments
        S_AVN, S_PSEU, S_FAIL_FIX, S_SURG = compute_scores(age, tabac, f, HSA, gap, bone_quality, comorbidities)
        treatment, justification = propose_treatment(S_AVN, S_PSEU, S_FAIL_FIX, age, f, gap, bone_quality, comorbidities)

        # Results display
        st.subheader("Résultats")
        st.write(f"- **S_AVN (nécrose)** : {S_AVN} %")
        st.write(f"- **S_PSEU (pseudarthrose)** : {S_PSEU} %")
        st.write(f"- **S_FAIL_FIX (échec fixation)** : {S_FAIL_FIX} %")
        st.write(f"- **S_SURG (composite)** : {S_SURG}")

        st.subheader("Recommandation")
        st.success(f"➡️ {treatment}")
        st.write(justification)

        # Save patient
        patient_id = generate_patient_id()
        now = datetime.utcnow().isoformat()
        row = {
            "ID": patient_id,
            "Date": now,
            "Age": age,
            "Tabac": "Oui" if tabac else "Non",
            "Comorbidities": comorbidities,
            "BoneQuality": bone_quality,
            "Fragments": f,
            "HSA": HSA,
            "Gap": gap,
            "S_AVN": S_AVN,
            "S_PSEU": S_PSEU,
            "S_FAIL_FIX": S_FAIL_FIX,
            "S_SURG": S_SURG,
            "Treatment": treatment,
            "Justification": justification
        }
        st.session_state.patients = pd.concat([st.session_state.patients, pd.DataFrame([row])], ignore_index=True)
        save_patients()
        st.success(f"Patient enregistré : {patient_id}")

    if st.button("Retour Home", use_container_width=True):
        st.session_state.page = "Home"

def page_research():
    st.title("Research & Patients")
    st.subheader("Patients enregistrés")
    q = st.text_input("Rechercher (ID, âge, traitement...)")
    df = st.session_state.patients.copy()
    if q:
        df = df[df.apply(lambda r: q.lower() in r.astype(str).str.lower().to_string(), axis=1)]
    st.dataframe(df, height=300)

    st.markdown("---")
    st.subheader("Références clés (archivées)")
    for r in RESEARCH_REFS:
        st.markdown(f"- **{r['title']}** — *{r['citation']}*")

    st.markdown("**Conseils d'archivage** : versionner le dépôt (GitHub), archiver sur Zenodo (DOI), stocker PDFs dans `research/` et sauvegarder la DB régulièrement.")

    if st.button("Retour Home", use_container_width=True):
        st.session_state.page = "Home"

# Router
if st.session_state.page == "Home":
    page_home()
elif st.session_state.page == "New Patient":
    page_new_patient()
elif st.session_state.page == "Research":
    page_research()
else:
    st.session_state.page = "Home"
    page_home()
