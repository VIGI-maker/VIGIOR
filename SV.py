import streamlit as st
import pandas as pd
import os

# -------------------------------------
# INITIALISATION FICHIER
# -------------------------------------

DATA_FILE = "patients.csv"
if not os.path.exists(DATA_FILE):
    df_init = pd.DataFrame(columns=[
        "patient_id", "age", "sex", "smoker",
        "fragments", "gap_mm", "HSA_angle",
        "risk_necrosis", "risk_nonunion", "risk_stiffness",
        "recommended_treatment", "explanation"
    ])
    df_init.to_csv(DATA_FILE, index=False)

# -------------------------------------
# GENERATION DES IDS PATIENTS
# -------------------------------------
def generate_patient_id():
    df = pd.read_csv(DATA_FILE)
    if df.empty:
        return "H-001"
    else:
        last_id = df["patient_id"].iloc[-1]
        num = int(last_id.split("-")[1]) + 1
        return f"H-{num:03d}"

# -------------------------------------
# MODELES DE RISQUES (SIMPLIFIÉS)
# -------------------------------------
def compute_risks(age, fragments, gap_mm, HSA_angle, smoker):
    risk_necrosis = min(95, fragments * 12 + max(0, 120 - HSA_angle) + gap_mm * 2 + (10 if smoker == "Yes" else 0))
    risk_nonunion = min(80, fragments * 10 + gap_mm * 3 + (5 if smoker == "Yes" else 0))
    risk_stiffness = min(75, (age / 2) + fragments * 4 + gap_mm)
    return risk_necrosis, risk_nonunion, risk_stiffness

# -------------------------------------
# RECOMMANDATION THÉRAPEUTIQUE
# -------------------------------------
def propose_treatment(fragments, HSA_angle, gap_mm, age):
    if fragments >= 4 or HSA_angle < 120 or gap_mm > 8:
        return ("Arthroplastie",
                "Les fractures complexes, l'angle HSA réduit et un large gap inter-fragmentaire augmentent le risque de nécrose selon les données publiées.")
    elif fragments == 3 or gap_mm > 4:
        return ("Ostéosynthèse",
                "Les fractures à 3 fragments ou présentant un gap significatif bénéficient d'une fixation interne pour limiter la pseudarthrose.")
    else:
        return ("Traitement orthopédique",
                "Les fractures peu déplacées montrent de bons résultats fonctionnels avec traitement conservateur selon les méta-analyses récentes.")

# -------------------------------------
# CONFIG STREAMLIT
# -------------------------------------
st.set_page_config(page_title="VIGIOR", layout="centered")

# -------------------------------------
# MENU LATERAL SIMPLE
# -------------------------------------
page = st.sidebar.selectbox("Navigation", ["Home", "New Patient", "Research"])

# -------------------------------------
# PAGE HOME
# -------------------------------------
if page == "Home":
    st.title("🦾 VIGIOR")
    st.subheader("Predictive Orthopedic Assistant")

    st.write("")
    st.write("")

    if st.button("➕ New Patient", use_container_width=True):
        st.session_state["page"] = "New Patient"
        st.switch_page("New Patient")

    if st.button("📊 Research", use_container_width=True):
        st.session_state["page"] = "Research"
        st.switch_page("Research")

# -------------------------------------
# PAGE NEW PATIENT
# -------------------------------------
elif page == "New Patient":
    st.title("➕ New Patient")

    age = st.number_input("Âge", 18, 120, 55)
    sex = st.selectbox("Sexe", ["Male", "Female"])
    smoker = st.selectbox("Fumeur", ["No", "Yes"])
    fragments = st.number_input("Nombre de fragments", 1, 4, 2)
    gap_mm = st.number_input("Écart inter-fragmentaire (mm)", 0, 20, 2)

    HSA_angle = st.slider("Angle HSA (°)", 80, 160, 135)

    if st.button("Evaluate", type="primary"):
        risk_necrosis, risk_nonunion, risk_stiffness = compute_risks(
            age, fragments, gap_mm, HSA_angle, smoker
        )

        reco, explanation = propose_treatment(fragments, HSA_angle, gap_mm, age)

        st.session_state["result"] = {
            "age": age,
            "sex": sex,
            "smoker": smoker,
            "fragments": fragments,
            "gap_mm": gap_mm,
            "HSA_angle": HSA_angle,
            "risk_necrosis": risk_necrosis,
            "risk_nonunion": risk_nonunion,
            "risk_stiffness": risk_stiffness,
            "recommended_treatment": reco,
            "explanation": explanation
        }
        st.experimental_rerun()

    # AFFICHAGE DES RESULTATS
    if "result" in st.session_state:
        r = st.session_state["result"]

        st.subheader("Résultats")
        st.success(f"🔥 Risque de nécrose : **{r['risk_necrosis']}%**")
        st.warning(f"🦴 Risque de pseudarthrose : **{r['risk_nonunion']}%**")
        st.info(f"🔒 Risque de raideur : **{r['risk_stiffness']}%**")

        st.subheader("Proposition thérapeutique")
        st.write(f"**{r['recommended_treatment']}**")
        st.write(r["explanation"])

        if st.button("💾 Enregistrer Patient"):
            patient_id = generate_patient_id()
            df = pd.read_csv(DATA_FILE)

            new_row = {"patient_id": patient_id, **r}

            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            df.to_csv(DATA_FILE, index=False)

            st.success(f"Patient enregistré sous ID : **{patient_id}**")

# -------------------------------------
# PAGE RESEARCH
# -------------------------------------
elif page == "Research":
    st.title("📊 Research – Liste des patients")

    df = pd.read_csv(DATA_FILE)

    if df.empty:
        st.info("Aucun patient enregistré pour le moment.")
    else:
        query = st.text_input("🔍 Rechercher un patient (ID, âge, risque...)")

        if query:
            df = df[df.apply(lambda row: row.astype(str).str.contains(query, case=False).any(), axis=1)]

        st.dataframe(df)
