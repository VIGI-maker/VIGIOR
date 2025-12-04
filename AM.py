import streamlit as st
import pandas as pd
import os
import uuid

# ---------------------------------------------
# INITIALISATION SESSION STATE
# ---------------------------------------------
if "page" not in st.session_state:
    st.session_state.page = "Home"

if "patients" not in st.session_state:
    # Dossier local pour enregistrer
    if os.path.exists("patients.csv"):
        st.session_state.patients = pd.read_csv("patients.csv")
    else:
        st.session_state.patients = pd.DataFrame(columns=[
            "ID", "Age", "Tabac", "Fragments", "HSA", "Gap",
            "Necrose", "Pseudo", "Raideur", "Treatment", "Justification"
        ])

# ---------------------------------------------
# FONCTION UTILITAIRE
# ---------------------------------------------
def generate_patient_id():
    return f"H-{str(uuid.uuid4())[:8]}"

def save_patients():
    st.session_state.patients.to_csv("patients.csv", index=False)

def compute_risks(age, tabac, fragments, HSA, gap):
    """Modèle simple simulé en attendant le modèle statistique final."""

    base_necrose = 10
    base_pseudo = 8
    base_raideur = 12

    # Facteurs plausibles inspirés de littérature
    necrose = base_necrose + fragments*3 + (HSA - 130)*0.3 + gap*1.5
    if tabac:
        necrose += 7
    if age > 65:
        necrose += 6

    pseudo = base_pseudo + gap*2 + fragments*2
    if age > 70:
        pseudo += 4

    raideur = base_raideur + fragments*1.5 + (HSA - 130)*0.2
    if age > 60:
        raideur += 3

    return round(necrose,1), round(pseudo,1), round(raideur,1)

def propose_treatment(necrose, pseudo, raideur, age, fragments, gap, bone_quality="normal"):
    """Proposition IA améliorée : inclut désormais l'ostéosynthèse et des règles basées sur la littérature.

    Règles (simplifiées) :
    - Arthroplastie (surtout RTSA) si risque nécrose très élevé, fracture très comminutive (>=4 fragments),
      ou patient âgé fragilisé (>75) avec tubérosités non réparables.
    - Ostéosynthèse (ORIF ou clou) si pseudarthrose/risque de non-union élevé mais anatomie réparables
      et qualité osseuse acceptable.
    - Traitement orthopédique si risques modérés/faibles et fracture peu déplacée.

    Cette fonction reste un prototype : le futur modèle statistique/ml intégrera poids et probabilités
    issus d'études publiées.
    """

    # Priorité aux signaux majeurs
    if necrose > 45 or fragments >= 4:
        # chez sujets âgés fragiles, préférer RTSA selon recommandations récentes
        if age >= 75 or bone_quality == "poor":
            return ("Arthroplastie (RTSA)",
                    "Risque élevé de nécrose / fracture très comminutive ; chez les sujets âgés ou en mauvaise qualité osseuse, "
                    "la reverse total shoulder arthroplasty (RTSA) donne des résultats fonctionnels supérieurs et moins de reprises.")
        else:
            return ("Arthroplastie (Hemi/RTSA selon indication)",
                    "Risque élevé de nécrose ou fracture 4-fragments ; arthroplastie indiquée lorsque la reconstruction de la tête/tubérosités est peu fiable.")

    # Si risque de pseudarthrose élevé ou gap important -> privilégier ostéosynthèse (fixation stable)
    if pseudo > 25 or gap >= 6 or fragments == 3:
        # si mauvaise qualité osseuse mais patient jeune -> tenter renforcement (grafting, techniques modernes)
        if bone_quality == "poor" and age < 65:
            justification = (
                "Risque de pseudarthrose élevé malgré mauvaise qualité osseuse : tenter ostéosynthèse "
                "avec techniques augmentées (greffe, cimentage local si nécessaire) et fixation robuste."
            )
        else:
            justification = (
                "Risque de pseudarthrose élevé ou écart interfragmentaire important ; une ostéosynthèse stable (ORIF ou clou intramédullaire) "
                "réduit le taux de non-union et améliore les chances d'une récupération fonctionnelle sans prothèse."
            )
        return ("Ostéosynthèse (ORIF / IM nailing)", justification)

    # Cas favorables au traitement conservateur
    if necrose <= 25 and pseudo <= 15 and raideur <= 20 and fragments <= 2:
        return ("Traitement orthopédique",
                "Risques faibles à modérés ; la littérature montre de bons résultats fonctionnels pour les fractures peu déplacées traitées de façon conservative.")

    # Cas intermédiaire : discussion multidisciplinaire
    return ("Indécis — Discussion MDT",
            "Cas intermédiaire : discuter en réunion pluridisciplinaire (ORIF vs RTSA vs conservative) en tenant compte de la demande fonctionnelle du patient, comorbidités et qualité osseuse.")

# ---------------------------------------------
# HOME PAGE
# ---------------------------------------------
if st.session_state.page == "Home":
    st.title("🦾 VIGIOR-H")
    st.subheader("Predictive Orthopedic Assistant")

    st.write("")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("➕ New Patient", use_container_width=True):
            st.session_state.page = "New Patient"

    with col2:
        if st.button("📊 Research", use_container_width=True):
            st.session_state.page = "Research"

# ---------------------------------------------
# NEW PATIENT PAGE
# ---------------------------------------------
elif st.session_state.page == "New Patient":

    st.title("🧑‍⚕️ New Patient Evaluation")

    age = st.number_input("Âge", 18, 100, 50)
    tabac = st.checkbox("Fumeur / tabagisme actuel")
    fragments = st.number_input("Nombre de fragments", 1, 6, 3)
    HSA = st.slider("Angle HSA (°)", 80, 180, 130)
    gap = st.number_input("Écart interfragmentaire (mm)", 0, 30, 3)
    bone_quality = st.selectbox("Qualité osseuse (estimation)", ["normal", "poor"])  # simple proxy

    if st.button("🔍 Evaluate", use_container_width=True):

        necrose, pseudo, raideur = compute_risks(age, tabac, fragments, HSA, gap)

        st.subheader("📈 Risques estimés")
        st.write(f"**Risque de nécrose :** {necrose} %")
        st.write(f"**Risque de pseudarthrose :** {pseudo} %")
        st.write(f"**Risque de raideur :** {raideur} %")

        treatment, justification = propose_treatment(necrose, pseudo, raideur, age, fragments, gap, bone_quality)

        st.subheader("🩺 Traitement proposé")
        st.write(f"**➡️ {treatment}**")

        st.write("### 🧠 Justification")
        st.write(justification)

        # Sauvegarde patient
        patient_id = generate_patient_id()

        new_row = pd.DataFrame([{
            "ID": patient_id,
            "Age": age,
            "Tabac": "Oui" if tabac else "Non",
            "Fragments": fragments,
            "HSA": HSA,
            "Gap": gap,
            "Necrose": necrose,
            "Pseudo": pseudo,
            "Raideur": raideur,
            "Treatment": treatment,
            "Justification": justification
        }])

        st.session_state.patients = pd.concat([st.session_state.patients, new_row], ignore_index=True)
        save_patients()

        st.success(f"Patient enregistré : **{patient_id}**")

    if st.button("⬅️ Retour Home", use_container_width=True):
        st.session_state.page = "Home"

# ---------------------------------------------
# RESEARCH PAGE
# ---------------------------------------------
elif st.session_state.page == "Research":

    st.title("📊 Patients enregistrés")

    query = st.text_input("🔎 Rechercher un patient (ID, âge, traitement…)", "")

    df = st.session_state.patients

    if query:
        df = df[df.apply(lambda row: query.lower() in row.astype(str).str.lower().to_string(), axis=1)]

    st.dataframe(df)

    st.markdown("---")
    st.markdown("### 🔬 Notes de recherche sauvegardées")
    st.markdown(
        "Les références clés et la logique de décision utilisées par VIGIOR-H sont enregistrées séparément pour assurer traçabilité et possibilité de révision."
    )

    if st.button("⬅️ Retour Home", use_container_width=True):
        st.session_state.page = "Home"
