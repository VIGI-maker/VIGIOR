import streamlit as st
import pandas as pd
import uuid
import os

st.set_page_config(page_title="VIGIOR-H — Risques post-fracture humérus proximal", layout="centered")
st.title("🦾 VIGIOR-H — Évaluation des Risques après Fracture Proximale de l’Humérus")
st.write("Remplissez les données cliniques pour estimer les risques selon les options thérapeutiques.")

# --- Formulaire patient ---
with st.form("vigiorh_form"):
    age = st.number_input("Âge (années)", min_value=18, max_value=100, step=1)
    sexe = st.selectbox("Sexe", ["Homme", "Femme"])
    fumeur = st.radio("Fumeur ?", ["Non", "Oui"])
    pa = st.slider("Pack-Years (PA) si fumeur", 0, 100, step=1)
    n_fragments = st.slider("Nombre de fragments (Neer)", 2, 4, step=1)
    hsa = st.slider("Angle HSA (°)", 90, 160, step=1)
    ecart = st.radio("Écart inter-fragmentaire > 5 mm", ["Non", "Oui"])
    luxation = st.radio("Luxation associée ?", ["Non", "Oui"])
    osteoporosis = st.radio("Ostéoporose connue ?", ["Non", "Oui"])
    submitted = st.form_submit_button("Évaluer les risques")

if submitted:
    # Score brut par option thérapeutique
    base_score = 0
    if age > 65: base_score += 2
    if fumeur == "Oui" and pa > 10: base_score += 2
    if n_fragments >= 4: base_score += 3
    if hsa < 120 or hsa > 145: base_score += 2
    if ecart == "Oui": base_score += 2
    if luxation == "Oui": base_score += 2
    if osteoporosis == "Oui": base_score += 2

    # Risques par stratégie (les pourcentages sont fictifs pour l'exemple)
    ortho_necrose = min(5 + base_score * 2, 95)
    ortho_pseudo = min(8 + base_score * 1.5, 95)
    ortho_raideur = min(10 + base_score * 2.5, 95)

    chir_necrose = min(15 + base_score * 1.2, 95)
    chir_pseudo = min(10 + base_score * 1.0, 90)
    chir_raideur = min(7 + base_score * 2.0, 90)

    st.markdown("---")
    st.subheader("📋 Résultats par option thérapeutique")

    st.markdown("### 🧍‍ Traitement Orthopédique")
    st.markdown(f"➡️ Risque de nécrose : **{ortho_necrose:.1f}%**")
    st.markdown(f"➡️ Risque de pseudarthrose : **{ortho_pseudo:.1f}%**")
    st.markdown(f"➡️ Risque de raideur : **{ortho_raideur:.1f}%**")

    st.markdown("### 🛠️ Réduction chirurgicale (ostéosynthèse)")
    st.markdown(f"➡️ Risque de nécrose : **{chir_necrose:.1f}%**")
    st.markdown(f"➡️ Risque de pseudarthrose : **{chir_pseudo:.1f}%**")
    st.markdown(f"➡️ Risque de raideur : **{chir_raideur:.1f}%**")

    st.markdown("### 🦾 Traitement radical (arthroplastie)")
    st.info("✅ Option privilégiée si : \n- >75 ans \n- fracture en 4 fragments avec luxation \n- ostéoporose sévère \n- mauvais os pour fixation")

    # Génération code patient + sauvegarde CSV
    code_patient = f"VIGH-{str(uuid.uuid4())[:8].upper()}"

    st.code(f"🆔 Code patient : {code_patient}", language='markdown')

    # Sauvegarde
    data = {
        'code_patient': code_patient,
        'age': age,
        'sexe': sexe,
        'fumeur': fumeur,
        'PA': pa if fumeur == "Oui" else 0,
        'n_fragments': n_fragments,
        'HSA': hsa,
        'ecart_interfragmentaire': ecart,
        'luxation': luxation,
        'osteoporose': osteoporosis,
        'risque_necrose_ortho': ortho_necrose,
        'risque_pseudo_ortho': ortho_pseudo,
        'risque_raideur_ortho': ortho_raideur,
        'risque_necrose_chir': chir_necrose,
        'risque_pseudo_chir': chir_pseudo,
        'risque_raideur_chir': chir_raideur
    }

    df_new = pd.DataFrame([data])
    if os.path.exists("vigior_humerus_db.csv"):
        df_old = pd.read_csv("vigior_humerus_db.csv")
        df = pd.concat([df_old, df_new], ignore_index=True)
    else:
        df = df_new

    df.to_csv("vigior_humerus_db.csv", index=False)
    st.success("✅ Données sauvegardées")
