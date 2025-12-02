import streamlit as st
import pandas as pd
import uuid
import os

# ------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------
st.set_page_config(page_title="VIGIOR", layout="wide")

DATAFILE = "vigior_data.csv"

# ------------------------------------------------------
# DATA MANAGEMENT
# ------------------------------------------------------

def load_data():
    if not os.path.exists(DATAFILE):
        df = pd.DataFrame()
        df.to_csv(DATAFILE, index=False)
        return df
    try:
        return pd.read_csv(DATAFILE)
    except:
        return pd.DataFrame()

def save_data(df):
    df.to_csv(DATAFILE, index=False)

def generate_patient_code(prefix="H"):
    number = str(len(load_data()) + 1).zfill(3)
    return f"{prefix}-{number}"

# ------------------------------------------------------
# RISK MODEL (placeholder)
# ------------------------------------------------------

def compute_risks(data):
    age = data["age"]
    neer = data["neer"]
    displacement = data["displacement"]

    necrose = min(90, 8 + age * 0.35 + neer * 10)
    pseudo = min(75, displacement * 3 + neer * 8)
    stiff = min(70, 5 + age * 0.25)

    score = (necrose + pseudo + stiff) / 3

    if neer >= 3:
        conduct = "Ostéosynthèse recommandée (ou prothèse selon âge et mobilité)."
        reason = "Fracture multi-fragmentaire avec risque élevé de complications."
    else:
        conduct = "Traitement conservateur envisageable."
        reason = "Fracture peu déplacée avec bon potentiel fonctionnel."

    return {
        "score": round(score, 1),
        "necrose": round(necrose, 1),
        "pseudoarthrose": round(pseudo, 1),
        "raideur": round(stiff, 1),
        "suggestion": conduct,
        "reason": reason
    }

# ------------------------------------------------------
# HOME PAGE WITH LARGE CARDS
# ------------------------------------------------------

def home():
    st.markdown("<h1 style='text-align:center; font-size:60px;'>VIGIOR</h1>", unsafe_allow_html=True)
    st.write("")

    col1, col2, col3 = st.columns([1,2,1])

    with col2:
        colA, colB = st.columns(2)

        with colA:
            if st.button("🧑‍⚕️ NEW PATIENT", use_container_width=True):
                st.session_state["page"] = "new_patient"

        with colB:
            if st.button("📚 RESEARCH", use_container_width=True):
                st.session_state["page"] = "research"

        st.markdown("""
            <style>
            button[kind="primary"] {
                font-size: 40px !important;
                height: 200px !important;
                border-radius: 20px !important;
            }
            </style>
        """, unsafe_allow_html=True)

# ------------------------------------------------------
# SKELETON SELECTION PAGE
# ------------------------------------------------------

def new_patient():
    st.markdown("<h1 style='text-align:center;'>Sélection anatomique</h1>", unsafe_allow_html=True)

    st.write("")
    st.write("### Cliquez sur l'épaule du squelette :")

    # SKELETON SVG WITH SHOULDER HOTSPOT BUTTON
    skeleton_svg = """
    <div style="text-align:center;">
        <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/8/8f/Human_skeleton_front.svg/480px-Human_skeleton_front.svg.png" width="300"/>
    </div>
    """
    st.markdown(skeleton_svg, unsafe_allow_html=True)

    st.write("")
    if st.button("👉 Cliquer ici si vous avez sélectionné l'épaule"):
        st.session_state["page"] = "shoulder"

# ------------------------------------------------------
# SHOULDER FORM
# ------------------------------------------------------

def shoulder_form():
    st.title("VIGIOR-H — Estimation des Risques et Conduite à Tenir")

    st.subheader("Données patient")
    col1, col2 = st.columns(2)
    with col1:
        age = st.number_input("Âge", 18, 100, 55)
        sexe = st.selectbox("Sexe", ["Homme", "Femme"])
        tabac = st.selectbox("Tabagisme", ["Non", "Oui"])
        diab = st.selectbox("Diabète", ["Non", "Oui"])
    with col2:
        osteo = st.selectbox("Ostéoporose connue", ["Non", "Oui"])
        comorb = st.text_input("Comorbidités majeures", "")

    st.subheader("Données fracture")
    col3, col4 = st.columns(2)
    with col3:
        neer = st.number_input("Classification de Neer", 1, 4, 2)
        displacement = st.number_input("Déplacement (mm)", 0, 40, 3)
    with col4:
        hsa = st.number_input("Angle HSA (°)", 80, 180, 135)
        mobility = st.selectbox("Mobilité antérieure", ["Bonne", "Moyenne", "Faible"])

    if st.button("Evaluate", type="primary"):
        data = {
            "age": age, "sexe": sexe, "tabac": tabac, "diab": diab, "osteo": osteo,
            "comorb": comorb, "neer": neer, "hsa": hsa, "displacement": displacement,
            "mobility": mobility
        }

        result = compute_risks(data)
        code = generate_patient_code()

        st.success(f"### Patient : **{code}**")

        st.metric("Score global", result["score"])
        st.metric("Risque de nécrose", f"{result['necrose']}%")
        st.metric("Risque de pseudarthrose", f"{result['pseudoarthrose']}%")
        st.metric("Risque de raideur", f"{result['raideur']}%")

        st.subheader("Conduite suggérée")
        st.write(result["suggestion"])
        st.caption(result["reason"])

        st.subheader("Notes cliniques")
        notes = st.text_area("Commentaires, évolution, traitement…", height=200)

        if st.button("💾 Save Patient", type="primary"):
            df = load_data()
            entry = data.copy()
            entry.update(result)
            entry["code"] = code
            entry["notes"] = notes

            df = pd.concat([df, pd.DataFrame([entry])], ignore_index=True)
            save_data(df)

            st.success("Patient enregistré avec succès !")

# ------------------------------------------------------
# RESEARCH PAGE
# ------------------------------------------------------

def research():
    df = load_data()
    st.title("Recherche — VIGIOR")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔎 Par P-Code"):
            st.session_state["research_mode"] = "pcode"
    with col2:
        if st.button("🧠 Par mot-clé"):
            st.session_state["research_mode"] = "keyword"

    mode = st.session_state.get("research_mode", None)

    if mode == "pcode":
        st.subheader("Recherche par code patient")
        code = st.text_input("Ex : H-001")
        if code and code in df.get("code", []):
            row = df[df["code"] == code].iloc[0]

            st.write(f"### Case Report : {code}")
            st.write(f"- Âge : {row['age']} ans, sexe {row['sexe']}")
            st.write(f"- Fracture Neer {row['neer']}, déplacement {row['displacement']} mm")
            st.write(f"- Risques : nécrose {row['necrose']} %, pseudoarthrose {row['pseudoarthrose']} %, raideur {row['raideur']} %")

            st.subheader("Notes cliniques")
            st.write(row["notes"])

    if mode == "keyword":
        st.subheader("Recherche par mots-clés")
        kw = st.text_input("Ex : infection, plaque...")
        if kw:
            matches = df[df.apply(lambda row: kw.lower() in str(row).lower(), axis=1)]
            st.write(f"### {len(matches)} patients trouvés")
            st.dataframe(matches)

            if st.button("Generate"):
                st.subheader("Analyse auto-générée")
                st.write(f"Nombre total de cas : {len(matches)}")
                st.write("Diagrammes et texte scientifique détaillé à ajouter.")

# ------------------------------------------------------
# PAGE ROUTER
# ------------------------------------------------------

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
