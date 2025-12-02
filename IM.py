import streamlit as st
import pandas as pd
import os

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
    n = len(st.session_state.patients) + 1
    return f"H-{n:03d}"

def save_patients():
    st.session_state.patients.to_csv("patients.csv", index=False)

def compute_risks(age, tabac, fragments, HSA, gap):
    """Modèle simple simulé en attendant ton modèle statistique final"""

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

def propose_treatment(necrose, pseudo, raideur):
    """Proposition IA simple"""

    if necrose > 40 or fragments >= 4:
        return ("Arthroplastie",
                "Le risque nécrotique élevé et la complexité fracturaire favorisent une arthroplastie "
                "selon les données des méta-analyses de fractures complexes de l’humérus proximal.")

    if pseudo > 25 or gap > 6:
        return ("Ostéosynthèse",
                "Le risque de pseudarthrose est important : les données montrent qu'une fixation stable réduit "
                "significativement ce risque dans les fractures déplacées.")

    return ("Traitement orthopédique",
            "Les risques sont modérés ; les études montrent de bons résultats fonctionnels avec un traitement "
            "conservateur dans les fractures peu comminutives et peu déplacées.")

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
    fragments = st.number_input("Nombre de fragments", 2, 6, 3)
    HSA = st.slider("Angle HSA (°)", 80, 180, 130)
    gap = st.number_input("Écart interfragmentaire (mm)", 0, 20, 3)

    if st.button("🔍 Evaluate", use_container_width=True):

        necrose, pseudo, raideur = compute_risks(age, tabac, fragments, HSA, gap)

        st.subheader("📈 Risques estimés")
        st.write(f"**Risque de nécrose :** {necrose} %")
        st.write(f"**Risque de pseudarthrose :** {pseudo} %")
        st.write(f"**Risque de raideur :** {raideur} %")

        treatment, justification = propose_treatment(necrose, pseudo, raideur)

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

    if st.button("⬅️ Retour Home", use_container_width=True):
        st.session_state.page = "Home"
