import streamlit as st
import uuid
import pandas as pd
import os

DATAFILE = "vigior_data.csv"

# -----------------------------------------------------
# UTILITIES
# -----------------------------------------------------

def load_data():
    if not os.path.exists(DATAFILE):
        return pd.DataFrame()
    return pd.read_csv(DATAFILE)

def save_data(df):
    df.to_csv(DATAFILE, index=False)

def generate_patient_code(prefix="H"):
    number = str(len(load_data()) + 1).zfill(3)
    return f"{prefix}-{number}"

# Basic mock “risk model” – replace later with real meta-analysis data
def compute_risks(data):
    age = data["age"]
    neer = data["neer"]
    displacement = data["displacement"]

    # Mock logic
    necrose = min(95, 10 + age * 0.4 + neer * 8)
    pseudoarthrose = min(80, 5 + displacement * 4 + neer * 5)
    raideur = min(70, 10 + age * 0.2)

    global_score = (necrose + pseudoarthrose + raideur) / 3

    # Suggested management (mock rules)
    if neer >= 3 or displacement > 5:
        suggestion = "Traitement chirurgical recommandé (ostéosynthèse ou prothèse selon âge et mobilité)."
        reason = "Fragments multiples / déplacement important → risque élevé d’échec conservateur."
    else:
        suggestion = "Traitement conservateur envisageable."
        reason = "Fracture peu déplacée avec bon profil fonctionnel."

    return {
        "score": round(global_score, 2),
        "necrose": round(necrose, 1),
        "pseudoarthrose": round(pseudoarthrose, 1),
        "raideur": round(raideur, 1),
        "suggestion": suggestion,
        "reason": reason
    }


# -----------------------------------------------------
# MAIN APP
# -----------------------------------------------------

st.set_page_config(page_title="VIGIOR", layout="wide")

# Home page
def home():
    st.markdown("<h1 style='text-align: center;'>VIGIOR</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([2,2,2])

    with col1:
        if st.button("RESEARCH", use_container_width=True):
            st.session_state["page"] = "research"

    with col3:
        if st.button("NEW PATIENT", use_container_width=True):
            st.session_state["page"] = "new_patient"


# -----------------------------------------------------
# NEW PATIENT — Skeleton screen
# -----------------------------------------------------

def new_patient():
    st.title("Sélection anatomique")

    st.write("Cliquez sur l'épaule pour commencer :")

    # Simple ASCII/SVG skeleton
    with st.container(border=True):
        st.markdown(
            """
            <div style="text-align:center; font-size:60px; cursor:pointer;">
                🦴<br>
                <span style="font-size:40px;">👆 Épaule</span>
            </div>
            """,
            unsafe_allow_html=True
        )

    if st.button("➡️ Aller à l'épaule"):
        st.session_state["page"] = "shoulder"


# -----------------------------------------------------
# SHOULDER FORM — VIGIOR-H
# -----------------------------------------------------

def shoulder_form():
    st.title("VIGIOR-H — Estimation des Risques et Conduite à Tenir")

    st.subheader("Données patient")

    age = st.number_input("Âge", 18, 100, 55)
    sexe = st.selectbox("Sexe", ["Homme", "Femme"])
    tabac = st.selectbox("Tabagisme", ["Non", "Oui"])
    diab = st.selectbox("Diabète", ["Non", "Oui"])
    osteo = st.selectbox("Ostéoporose connue", ["Non", "Oui"])
    comorb = st.text_input("Comorbidités majeures")

    st.subheader("Données fracture")

    neer = st.number_input("Classification de Neer (nombre de fragments)", 1, 4, 2)
    hsa = st.number_input("Angle HSA (°)", 80, 180, 135)
    displacement = st.number_input("Déplacement inter-fragmentaire (mm)", 0, 40, 3)
    mobility = st.selectbox("Mobilité antérieure du patient", ["Bonne", "Moyenne", "Faible"])

    if st.button("Evaluate", type="primary"):
        data = {
            "age": age,
            "sexe": sexe,
            "tabac": tabac,
            "diab": diab,
            "osteo": osteo,
            "comorb": comorb,
            "neer": neer,
            "hsa": hsa,
            "displacement": displacement,
            "mobility": mobility
        }

        result = compute_risks(data)
        code = generate_patient_code()

        st.success(f"Code Patient : **{code}**")
        st.metric("Score global", result["score"])
        st.metric("Risque de nécrose", f"{result['necrose']}%")
        st.metric("Risque de pseudarthrose", f"{result['pseudoarthrose']}%")
        st.metric("Risque de raideur", f"{result['raideur']}%")

        st.subheader("Conduite suggérée")
        st.write(result["suggestion"])
        st.caption(result["reason"])

        st.subheader("Note clinique")
        notes = st.text_area("Compte-rendu / évolution clinique", height=200)

        if st.button("Save patient"):
            df = load_data()
            entry = data.copy()
            entry.update(result)
            entry["code"] = code
            entry["notes"] = notes
            df = pd.concat([df, pd.DataFrame([entry])], ignore_index=True)
            save_data(df)
            st.success("Patient enregistré.")


# -----------------------------------------------------
# RESEARCH PAGE
# -----------------------------------------------------

def research():
    st.title("Recherche — VIGIOR")

    colA, colB = st.columns(2)

    with colA:
        if st.button("P-Code"):
            st.session_state["research_mode"] = "pcode"

    with colB:
        if st.button("Keyword"):
            st.session_state["research_mode"] = "keyword"

    df = load_data()

    # ----- PCODE MODE -----
    if st.session_state.get("research_mode") == "pcode":
        st.subheader("Recherche par Code Patient")
        code = st.text_input("Code (ex: H-001)")
        if code and code in df["code"].values:
            row = df[df["code"] == code].iloc[0]
            st.write("### Case Report Auto-généré")
            st.write(f"**Patient {code}**, {row['age']} ans, sexe {row['sexe']}.")
            st.write(f"Fracture de l’humérus proximal type Neer {row['neer']} avec déplacement de {row['displacement']} mm.")
            st.write(f"Risques : nécrose {row['necrose']} %, pseudarthrose {row['pseudoarthrose']} %, raideur {row['raideur']} %.")    
            st.write("#### Notes cliniques")
            st.write(row["notes"])

    # ----- KEYWORD MODE -----
    if st.session_state.get("research_mode") == "keyword":
        st.subheader("Recherche par mots-clés")
        kw = st.text_input("Mot-clé (ex: infection, plaque, ostéosynthèse...)")
        if kw:
            matches = df[df.apply(lambda r: kw.lower() in str(r).lower(), axis=1)]
            st.write(f"**{len(matches)} patients trouvés**")
            st.dataframe(matches[["code", "age", "neer", "displacement", "notes"]])

        if st.button("Generate"):
            st.subheader("Texte scientifique auto-généré")
            st.write("### Série de cas — Résultats")
            st.write(f"Nombre total de patients : {len(df)}")
            st.write(f"Nombre correspondant au filtre : {len(matches) if kw else 0}")
            st.write("Analyse automatique + diagrammes à ajouter ultérieurement.")


# -----------------------------------------------------
# ROUTER
# -----------------------------------------------------

if "page" not in st.session_state:
    st.session_state["page"] = "home"

if st.session_state["page"] == "home":
    home()
elif st.session_state["page"] == "new_patient":
    new_patient()
elif st.session_state["page"] == "shoulder":
    shoulder_form()
elif st.session_state["page"] == "research":
    research()
