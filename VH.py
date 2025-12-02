import streamlit as st
import pandas as pd
import uuid
import os

# ------------------------------------------------------
# PAGE CONFIG
# ------------------------------------------------------
st.set_page_config(
    page_title="VIGIOR",
    layout="wide",
)

DATAFILE = "vigior_data.csv"

# ------------------------------------------------------
# STYLE PREMIUM
# ------------------------------------------------------

CUSTOM_CSS = """
<style>

html, body, [class*="css"]  {
    font-family: 'Segoe UI', Roboto, sans-serif;
}

h1 {
    color: #003865;
    font-weight: 800;
}

.big-card {
    background: linear-gradient(135deg, #005A9C 0%, #0077C8 100%);
    padding: 40px;
    border-radius: 20px;
    text-align: center;
    color: white;
    font-size: 40px;
    font-weight: 700;
    cursor: pointer;
    transition: 0.2s;
    box-shadow: 0px 8px 20px rgba(0,0,0,0.25);
}
.big-card:hover {
    transform: scale(1.05);
    box-shadow: 0px 12px 26px rgba(0,0,0,0.4);
}

.skeleton-container {
    text-align: center;
    margin-top: 20px;
}

.shoulder-button {
    background-color: #00AEEF;
    color: white;
    padding: 12px 22px;
    border-radius: 12px;
    border: none;
    font-size: 22px;
    cursor: pointer;
    margin-top: 20px;
    transition: 0.2s;
}
.shoulder-button:hover {
    background-color: #008FCC;
    transform: scale(1.05);
}

.section-box {
    background: #F4F8FB;
    padding: 20px;
    border-radius: 14px;
    margin-bottom: 15px;
    border-left: 5px solid #0077C8;
}

</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

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
# RISK MODEL (placeholder logic)
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
# HOME PAGE — PREMIUM DESIGN
# ------------------------------------------------------

def home():
    st.markdown("<h1 style='text-align:center; font-size:70px;'>VIGIOR</h1>", unsafe_allow_html=True)
    st.write("")

    col1, col2, col3 = st.columns([2,3,2])

    with col2:
        colA, colB = st.columns(2)

        with colA:
            if st.button("🧑‍⚕️ NEW PATIENT", key="card1"):
                st.session_state["page"] = "new_patient"
            st.markdown('<div class="big-card" onclick="triggerClick(\'card1\')">🧑‍⚕️ NEW PATIENT</div>',
                        unsafe_allow_html=True)

        with colB:
            if st.button("📚 RESEARCH", key="card2"):
                st.session_state["page"] = "research"
            st.markdown('<div class="big-card" onclick="triggerClick(\'card2\')">📚 RESEARCH</div>',
                        unsafe_allow_html=True)

# ------------------------------------------------------
# SKELETON PAGE
# ------------------------------------------------------

def new_patient():
    st.markdown("<h1 style='text-align:center;'>Sélection anatomique</h1>", unsafe_allow_html=True)

    st.write("")
    st.subheader("Cliquez sur l'épaule du squelette pour commencer")

    st.markdown("""
    <div class="skeleton-container">
        <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/8/8f/Human_skeleton_front.svg/480px-Human_skeleton_front.svg.png"
             width="300"/>
    </div>
    """, unsafe_allow_html=True)

    st.write("")

    if st.button("👉 Sélectionner l'épaule", help="Continuer vers VIGIOR-H"):
        st.session_state["page"] = "shoulder"

# ------------------------------------------------------
# SHOULDER FORM — PREMIUM
# ------------------------------------------------------

def shoulder_form():
    st.markdown("<h1 style='text-align:center;'>VIGIOR-H</h1>", unsafe_allow_html=True)
    st.subheader("Estimation des risques • Fracture de l’humérus proximal")

    st.markdown('<div class="section-box">Données patient</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        age = st.number_input("Âge", 18, 100, 55)
        sexe = st.selectbox("Sexe", ["Homme", "Femme"])
        tabac = st.selectbox("Tabagisme", ["Non", "Oui"])
        diab = st.selectbox("Diabète", ["Non", "Oui"])
    with col2:
        osteo = st.selectbox("Ostéoporose connue", ["Non", "Oui"])
        comorb = st.text_input("Comorbidités majeures", "")

    st.markdown('<div class="section-box">Données de la fracture</div>', unsafe_allow_html=True)

    col3, col4 = st.columns(2)
    with col3:
        neer = st.number_input("Classification de Neer", 1, 4, 2)
        displacement = st.number_input("Déplacement (mm)", 0, 40, 3)
    with col4:
        hsa = st.number_input("Angle HSA (°)", 80, 180, 135)
        mobility = st.selectbox("Mobilité antérieure", ["Bonne", "Moyenne", "Faible"])

    if st.button("🔍 Évaluer", type="primary"):
        data = {
            "age": age, "sexe": sexe, "tabac": tabac, "diab": diab, "osteo": osteo,
            "comorb": comorb, "neer": neer, "hsa": hsa, "displacement": displacement,
            "mobility": mobility
        }

        result = compute_risks(data)
        code = generate_patient_code()

        st.success(f"### Patient : **{code}**")

        colA, colB, colC = st.columns(3)
        colA.metric("Score global", result["score"])
        colB.metric("Nécrose", f"{result['necrose']}%")
        colC.metric("Pseudarthrose", f"{result['pseudoarthrose']}%")

        st.metric("Raideur", f"{result['raideur']}%")

        st.subheader("Conduite recommandée")
        st.write(result["suggestion"])
        st.caption(result["reason"])

        st.subheader("Notes cliniques")
        notes = st.text_area("Ex : Ostéosynthèse par plaque DP, infection précoce traitée…", height=200)

        if st.button("💾 Enregistrer le patient"):
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
    st.markdown("<h1 style='text-align:center;'>Recherche clinique</h1>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔎 Par P-Code"):
            st.session_state["research_mode"] = "pcode"
    with col2:
        if st.button("🧠 Par mot-clé"):
            st.session_state["research_mode"] = "keyword"

    mode = st.session_state.get("research_mode", None)

    if mode == "pcode":
        st.subheader("Rechercher un patient")
        code = st.text_input("Ex : H-001")
        if code in df.get("code", []):
            row = df[df["code"] == code].iloc[0]

            st.write(f"### Case Report : {code}")
            st.write(f"- Âge : {row['age']} ans")
            st.write(f"- Sexe : {row['sexe']}")
            st.write(f"- Fracture Neer {row['neer']}, déplacement {row['displacement']} mm")
            st.write(f"- Risques : nécrose {row['necrose']}%, pseudoarthrose {row['pseudoarthrose']}%…")

            st.subheader("Notes cliniques")
            st.write(row["notes"])

    if mode == "keyword":
        st.subheader("Recherche par mots-clés")
        kw = st.text_input("Ex : infection, plaque…")
        if kw:
            matches = df[df.apply(lambda r: kw.lower() in str(r).lower(), axis=1)]
            st.write(f"### {len(matches)} patients trouvés")
            st.dataframe(matches)

# ------------------------------------------------------
# ROUTER
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
