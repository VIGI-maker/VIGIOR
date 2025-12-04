# app.py
import streamlit as st
import pandas as pd
import os
import uuid
from datetime import datetime

# -------------------------
# CONFIG / INIT
# -------------------------
st.set_page_config(page_title="VIGIOR-H", layout="wide")

if "page" not in st.session_state:
    st.session_state.page = "Home"

PATIENTS_CSV = "patients.csv"

# Load or initialize patients dataframe
if "patients" not in st.session_state:
    if os.path.exists(PATIENTS_CSV):
        st.session_state.patients = pd.read_csv(PATIENTS_CSV)
    else:
        st.session_state.patients = pd.DataFrame(columns=[
            "ID", "Date", "Age", "Tabac", "Comorbidities", "BoneQuality",
            "Fragments", "HSA", "Gap", "Tuberosities_Irreparable",
            "S_AVN", "S_PSEU", "S_FAIL_FIX", "S_SURG",
            "Treatment", "Justification"
        ])

# -------------------------
# RESEARCH REFERENCES (ENREGISTRÉES)
# -------------------------
RESEARCH_REFS = [
    {
        "title": "PHARON model (Goudie et al.) - predictors of nonunion/complications in PHF",
        "citation": "Goudie EB et al., JBJS, 2021"
    },
    {
        "title": "Systematic review/meta-analysis comparing treatments for PHF",
        "citation": "Hohmann E. et al., J Shoulder Elbow Surg, 2023"
    },
    {
        "title": "Comprehensive review of proximal humerus fractures",
        "citation": "Baker HP et al., J Clin Med, 2022"
    },
    {
        "title": "Bayesian network meta-analysis: RTSA vs ORIF vs HA (outcomes by age)",
        "citation": "Migliorini F., 2025"
    },
    {
        "title": "Comparative outcomes arthroplasty vs non-operative (recent review)",
        "citation": "Lai et al., Frontiers in Medicine, 2024"
    }
]
# NOTE: stocke aussi les PDFs localement dans research/ si tu veux archivage long terme.

# -------------------------
# UTILS
# -------------------------
def generate_patient_id():
    return f"H-{str(uuid.uuid4())[:8].upper()}"

def save_patients():
    st.session_state.patients.to_csv(PATIENTS_CSV, index=False)

# -------------------------
# SCORE CALCULS (FORMULES)
# -------------------------
def compute_scores(age, tabac, fragments, HSA, gap, bone_quality, comorbidities, tuberosities_irreparable):
    """
    Retourne S_AVN, S_PSEU, S_FAIL_FIX, S_SURG (tous arrondis à 1 décimale)
    Formules décrites dans la spécification du projet (poids inspirés des méta-analyses / PHARON).
    """
    # Binary indicators
    I_age_gt_65 = 1 if age > 65 else 0
    I_age_gt_70 = 1 if age > 70 else 0
    I_tabac = 1 if tabac else 0
    I_bone_poor = 1 if bone_quality == "poor" else 0
    I_comorb = 1 if comorbidities >= 1 else 0
    # S_AVN: probabilité relative de nécrose
    S_AVN = 10
    S_AVN += 6 * I_age_gt_65
    S_AVN += 7 * I_tabac
    S_AVN += 3 * fragments
    # HSA effect: lower HSA (below 130) increases risk; if HSA>130 effect negative
    # We use (130 - HSA) so positive when HSA < 130, negative otherwise
    S_AVN += 0.3 * (130 - HSA)
    S_AVN += 1.5 * gap
    S_AVN += 10 * I_bone_poor
    # Tuberosities irreparable increases chance arthroplastie, add to AVN as surrogate risk
    if tuberosities_irreparable:
        S_AVN += 6

    # S_PSEU: pseudarthrose / non-union risk
    S_PSEU = 8
    S_PSEU += 2 * fragments
    S_PSEU += 2 * gap
    S_PSEU += 4 * I_age_gt_70
    S_PSEU += 5 * I_tabac
    S_PSEU += 8 * I_bone_poor

    # S_FAIL_FIX: risque d'échec de fixation / perte de réduction
    S_FAIL_FIX = 5
    S_FAIL_FIX += 4 * I_bone_poor
    S_FAIL_FIX += 3 * fragments
    S_FAIL_FIX += 2 * I_comorb
    S_FAIL_FIX += 1.5 * gap

    # Composite surgical score (pondération)
    S_SURG = 0.4 * S_AVN + 0.35 * S_PSEU + 0.25 * S_FAIL_FIX

    # Clip to reasonable bounds (0..100)
    for varname in ["S_AVN", "S_PSEU", "S_FAIL_FIX", "S_SURG"]:
        val = locals()[varname]
        if val < 0: val = 0
        if val > 100: val = 100
        locals()[varname] = round(val, 1)

    return round(S_AVN,1), round(S_PSEU,1), round(S_FAIL_FIX,1), round(S_SURG,1)

# -------------------------
# DECISION RULES (propose_treatment)
# -------------------------
def propose_treatment(score_avn, score_pseu, score_fail_fix, age, fragments, gap, bone_quality, comorbidities, tuberosities_irreparable):
    """
    Retourne (treatment_label, justification_text)
    Modalités exclusives :
      - Traitement orthopédique (conservateur)
      - Ostéosynthèse foyer fermé (IM nailing)
      - Ostéosynthèse foyer ouvert (ORIF)
      - Arthroplastie (HA ou RTSA selon indication)
    Règles basées sur scores et variables cliniques.
    """
    # Priority: Arthroplastie > ORIF > IM nailing > Conservative
    # 1) Criteria for arthroplastie (RTSA favored for elderly/comorbid/poor bone/tuberosities irreparable)
    if (score_avn >= 50) or (fragments >= 4) or (age >= 75 and bone_quality == "poor") or tuberosities_irreparable:
        # Choose RTSA vs HA: if age >=75 or poor bone or comorbidities -> RTSA
        if age >= 75 or bone_quality == "poor" or comorbidities >= 1:
            treatment = "Arthroplastie (RTSA preferred)"
            justification = (
                "Risque élevé de nécrose / fracture très comminutive / tubérosités irréparables. "
                "Chez les patients âgés ou en mauvaise qualité osseuse, la RTSA offre souvent de meilleurs "
                "résultats fonctionnels et réduit les reprises par rapport à une fixation incertaine."
            )
        else:
            treatment = "Arthroplastie (HA or RTSA selon tubérosités)"
            justification = (
                "Risque élevé de complications mécaniques ou anatomiques rendant la reconstruction peu fiable ; "
                "arthroplastie est indiquée, type exact à décider en per-op selon tubérosités."
            )
        return treatment, justification

    # 2) Criteria for ORIF (ostéosynthèse foyer ouvert)
    # Indiqué quand risque de non-union / échec fixation modéré à élevé mais anatomie réparables et qualité osseuse acceptable
    if (score_pseu >= 30 or score_fail_fix >= 30 or fragments == 3) and not (bone_quality == "poor" and age >= 75):
        treatment = "Ostéosynthèse foyer ouvert (ORIF - plaque et vis / technique adaptée)"
        justification = (
            "Risque de pseudarthrose ou d'échec de fixation significatif mais anatomie et qualité osseuse permettant "
            "une reconstruction ouverte. ORIF permet réduction anatomique, réparation des tubérosités et fixation stable."
        )
        # If bone poor but younger, suggest augmentation
        if bone_quality == "poor" and age < 65:
            justification += " Prévoir augmentation (greffe osseuse, cimentage local, ou techniques de renforcement)."
        return treatment, justification

    # 3) Criteria for IM nailing (ostéosynthèse foyer fermé)
    if fragments <= 2 and score_fail_fix < 30 and bone_quality != "poor":
        treatment = "Ostéosynthèse foyer fermé (IM nailing)"
        justification = (
            "Fracture peu comminutive, qualité osseuse acceptable et risque d'échec faible : "
            "clou intramédullaire permet fixation fermée, moindre traumatisme tissulaire et bonne stabilité si indication adaptée."
        )
        return treatment, justification

    # 4) Conservative
    if score_avn < 25 and score_pseu < 20 and fragments <= 2:
        treatment = "Traitement orthopédique (conservateur)"
        justification = (
            "Faibles scores de nécrose et non-union, fracture peu comminutive : la littérature montre de bons résultats fonctionnels "
            "avec prise en charge conservatrice pour ces profils."
        )
        return treatment, justification

    # Fallback (if multiple critères proches) -- apply priority but try to be explicit
    # We already removed "indecis" option; apply priority order by re-evaluating most concerning signal
    # If any major signal persists, escalate according to priority
    # re-check: if score_avn or fragments suggest surgery -> ORIF or Arthroplasty depending on age/bone
    if score_avn >= 40 or fragments >= 3:
        # if elderly/poor bone -> arthroplastie else ORIF
        if age >= 75 or bone_quality == "poor":
            treatment = "Arthroplastie (type selon per-op)"
            justification = "Signal élevé de complication + patient à risque -> arthroplastie à privilégier."
            return treatment, justification
        else:
            treatment = "Ostéosynthèse foyer ouvert (ORIF)"
            justification = "Signal élevé mais patient relativement jeune et os corrects -> tentative de reconstruction."
            return treatment, justification

    # If none matched strictly, default to ORIF when surgical risk acceptable, else conservative
    if age < 80 and comorbidities < 2:
        return ("Ostéosynthèse foyer ouvert (ORIF)", "Choix par défaut pour cas intermédiaire où fixation anatomique est envisageable.")
    else:
        return ("Traitement orthopédique (conservateur)", "Patient à risque chirurgical élevé ; privilégier conservateur ou discussion locale.")

# -------------------------
# PAGES
# -------------------------
def page_home():
    st.title("🦾 VIGIOR-H")
    st.subheader("Predictive Orthopedic Assistant — Proximal Humerus Fractures")
    col1, col2 = st.columns([1,1])
    with col1:
        if st.button("➕ New Patient", use_container_width=True):
            st.session_state.page = "New Patient"
    with col2:
        if st.button("📊 Research", use_container_width=True):
            st.session_state.page = "Research"

def page_new_patient():
    st.title("🧑‍⚕️ New Patient Evaluation")

    with st.form(key="patient_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            age = st.number_input("Âge (ans)", min_value=18, max_value=110, value=60)
            tabac = st.checkbox("Tabac (actuel)")
            comorbidities = st.number_input("Comorbidités majeures (0=no, 1=oui)", min_value=0, max_value=10, value=0)
            bone_quality = st.selectbox("Qualité osseuse (estimation)", ["normal", "poor"])
        with col2:
            fragments = st.number_input("Nombre de fragments", min_value=1, max_value=6, value=3)
            HSA = st.slider("Angle HSA (°)", min_value=60, max_value=180, value=130)
            gap = st.number_input("Gap interfragmentaire (mm)", min_value=0, max_value=50, value=3)
        with col3:
            tuberosities_irreparable = st.checkbox("Tubérosités irréparables (oui/non)")
            notes = st.text_area("Notes cliniques (optionnel)", height=120)

        submitted = st.form_submit_button("🔍 Evaluate")

    if submitted:
        # compute scores
        S_AVN, S_PSEU, S_FAIL_FIX, S_SURG = compute_scores(
            age, tabac, fragments, HSA, gap, bone_quality, comorbidities, tuberosities_irreparable
        )

        # propose treatment
        treatment, justification = propose_treatment(
            S_AVN, S_PSEU, S_FAIL_FIX, age, fragments, gap, bone_quality, comorbidities, tuberosities_irreparable
        )

        # Display results
        st.subheader("📈 Scores estimés")
        st.metric("S_AVN (nécrose prob.)", f"{S_AVN} %")
        st.metric("S_PSEU (pseudarthrose prob.)", f"{S_PSEU} %")
        st.metric("S_FAIL_FIX (échec fixation)", f"{S_FAIL_FIX} %")
        st.metric("S_SURG (composite)", f"{S_SURG}")

        st.subheader("🩺 Traitement proposé")
        st.write(f"**➡️ {treatment}**")
        st.write("### 🧠 Justification")
        st.write(justification)
        if notes:
            st.markdown("**Notes cliniques :**")
            st.write(notes)

        # Save patient
        patient_id = generate_patient_id()
        now = datetime.utcnow().isoformat()
        new_row = {
            "ID": patient_id,
            "Date": now,
            "Age": age,
            "Tabac": "Oui" if tabac else "Non",
            "Comorbidities": comorbidities,
            "BoneQuality": bone_quality,
            "Fragments": fragments,
            "HSA": HSA,
            "Gap": gap,
            "Tuberosities_Irreparable": "Oui" if tuberosities_irreparable else "Non",
            "S_AVN": S_AVN,
            "S_PSEU": S_PSEU,
            "S_FAIL_FIX": S_FAIL_FIX,
            "S_SURG": S_SURG,
            "Treatment": treatment,
            "Justification": justification
        }
        st.session_state.patients = pd.concat([st.session_state.patients, pd.DataFrame([new_row])], ignore_index=True)
        save_patients()
        st.success(f"Patient enregistré : **{patient_id}**")

    if st.button("⬅️ Retour Home", use_container_width=True):
        st.session_state.page = "Home"

def page_research():
    st.title("📚 Research & Patients")
    st.subheader("Patients enregistrés")
    query = st.text_input("🔎 Rechercher (ID, âge, traitement…)", "")
    df = st.session_state.patients.copy()
    if query:
        df = df[df.apply(lambda row: query.lower() in row.astype(str).str.lower().to_string(), axis=1)]
    st.dataframe(df, height=300)

    st.markdown("---")
    st.subheader("🔬 Références clés utilisées par VIGIOR-H")
    for r in RESEARCH_REFS:
        st.markdown(f"- **{r['title']}** — *{r['citation']}*")

    st.markdown("**Notes d'archivage** :")
    st.markdown(
        "- Archive les PDFs dans `research/` avec métadonnées (DOI, titre, auteurs, date).\n"
        "- Versionne le dépôt (GitHub) et crée un snapshot (Zenodo) pour pérenniser la version du modèle.\n"
        "- Pour production: migrer CSV -> PostgreSQL et mettre en place backups & contrôles d'accès."
    )

    if st.button("⬅️ Retour Home", use_container_width=True):
        st.session_state.page = "Home"

# -------------------------
# ROUTING
# -------------------------
if st.session_state.page == "Home":
    page_home()
elif st.session_state.page == "New Patient":
    page_new_patient()
elif st.session_state.page == "Research":
    page_research()
else:
    st.session_state.page = "Home"
    page_home()
