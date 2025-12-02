import streamlit as st
import pandas as pd
import os
import uuid

# ---------------------------
# INITIALISATION DU FICHIER
# ---------------------------

DATA_FILE = "patients.csv"

if not os.path.exists(DATA_FILE):
    df_init = pd.DataFrame(columns=[
        "patient_id", "age", "sex", "smoker", "fragments",
        "HSA_angle", "treatment_planned",
        "risk_necrosis", "risk_nonunion", "risk_stiffness",
        "recommended_treatment", "explanation"
    ])
    df_init.to_csv(DATA_FILE, index=False)

# ---------------------------
# FONCTION : GENERER ID PATIENT
# ---------------------------

def generate_patient_id():
    df = pd.read_csv(DATA_FILE)
    if df.empty:
        return "H-001"
    else:
        last_id = df["patient_id"].iloc[-1]
        num = int(last_id.split("-")[1]) + 1
        return f"H-{num:03d}"

# ---------------------------
# FONCTION : MODELE DE RISQUES (SIMPLIFIÉ POUR DEMO)
# ---------------------------

def compute_risks(age, fragments, HSA_angle, smoker):
    # ► Ces formules seront remplacées par les données publiées (méta-analyses PubMed/Elsevier)
    risk_necrosis = min(95, (fragments * 15) + max(0, 120 - HSA_angle) + (10 if smoker == "Yes" else 0))
    risk_nonunion = min(85, fragments * 12 + (5 if smoker == "Yes" else 0))
    risk_stiffness = min(70, (age / 2) + fragments * 5)
    return risk_necrosis, risk_nonunion, risk_stiffness

# ---------------------------
# FONCTION : RECOMMANDATION TRAITEMENT
# ---------------------------

def propose_treatment(age, fragments, HSA_angle):
    if fragments >= 4 or HSA_angle < 120:
        return "Arthroplastie", "Les fractures complexes et les angles HSA faibles augmentent le risque de nécrose selon les méta-analyses récentes."
    elif fragments == 3:
        return "Ostéosynthèse", "Les fractures à 3 fragments obtiennent de meilleurs résultats fonctionnels avec fixation interne."
    else:
        return "Traitement orthopédique", "Les fractures peu déplacées ont de bons résultats avec traitement conservateur."
    
# ---------------------------
# INTERFACE STREAMLIT
# ---------------------------

st.set_page_config(page_title="VIGIOR", layout="centered")

# MENU PRINCIPAL
page = st.sidebar.selectbox("Navigation", ["Home", "New Patient", "Research"])

# --------------------------------------
# PAGE D’ACCUEIL
# --------------------------------------
if page == "Home":
    st.title("🦾 VIGIOR")
    st.subheader("Predictive Orthopedic Assistant")

    st.write("")

    if st.button("➕ New Patient", use_container_width=True):
        st.switch_page("New Patient")

    if st.button("📊 Research", use_container_width=True):
        st.switch_page("Research")

# --------------------------------------
# PAGE : NEW PATIENT
# --------------------------------------
elif page == "New Patient":
    st.title("➕ New Patient")

    age = st.number_input("Âge", 18, 120, 55)
    sex = st.selectbox("Sexe", ["Male", "Female"])
    smoker = st.selectbox("Fumeur", ["No", "Yes"])
    fragments = st.number_input("Nombre de fragments", 1, 4, 2)
    HSA_angle = st.number_input("Angle HSA", 80, 160, 135)
    treatment_planned = st.selectbox("Traitement prévu", ["Orthopédique", "Ostéosynthèse", "Arthroplastie"])

    if st.button("Evaluate", type="primary"):
        risk_necrosis, risk_nonunion, risk_stiffness = compute_risks(age, fragments, HSA_angle, smoker)
        reco, explanation = propose_treatment(age, fragments, HSA_angle)

        st.session_state["result"] = {
            "age": age,
            "sex": sex,
            "smoker": smoker,
            "fragments": fragments,
            "HSA_angle": HSA_angle,
            "treatment_planned": treatment_planned,
            "risk_necrosis": risk_necrosis,
            "risk_nonunion": risk_nonunion,
            "risk_stiffness": risk_stiffness,
            "recommended_treatment": reco,
            "explanation": explanation
        }
        st.experimental_rerun()

    # AFFICHAGE DES RÉSULTATS SI DISPONIBLES
    if "result" in st.session_state:
        r = st.session_state["result"]

        st.subheader("Résultats")

        st.success(f"🔥 Risque de nécrose : **{r['risk_necrosis']}%**")
        st.warning(f"🦴 Risque de pseudarthrose : **{r['risk_nonunion']}%**")
        st.info(f"🔒 Risque de raideur : **{r['risk_stiffness']}%**")

        st.subheader("Recommandation thérapeutique")
        st.write(f"**{r['recommended_treatment']}**")
        st.write(r["explanation"])

        if st.button("💾 Enregistrer Patient"):
            patient_id = generate_patient_id()
            df = pd.read_csv(DATA_FILE)

            new_row = {
                "patient_id": patient_id,
                **r
            }

            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            df.to_csv(DATA_FILE, index=False)

            st.success(f"Patient enregistré sous ID : **{patient_id}**")

# --------------------------------------
# PAGE : RESEARCH
# --------------------------------------
elif page == "Research":
    st.title("📊 Research – Liste des patients")

    df = pd.read_csv(DATA_FILE)

    if df.empty:
        st.info("Aucun patient enregistré pour le moment.")
    else:
        st.dataframe(df[["patient_id", "age", "fragments", "risk_necrosis", "risk_nonunion", "risk_stiffness", "recommended_treatment"]])
