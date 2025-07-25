import streamlit as st
import pandas as pd
import os
import uuid

st.set_page_config(page_title="VIGIOR Simple", layout="centered")

st.title("🦾 VIGIOR — Évaluation du Risque de Syndrome de Loges")
st.write("Entrez les données du patient pour estimer le risque de syndrome de loges après fracture du plateau tibial.")

# --- Formulaire principal ---
with st.form("vigior_form"):
    age = st.number_input("Âge", 0, 120, step=1)
    sexe = st.selectbox("Sexe", ["Homme", "Femme"])
    schatzker = st.selectbox("Type de fracture (classification de Schatzker)", [1, 2, 3, 4, 5, 6])
    n_fragments = st.number_input("Nombre de fragments", 1, 10, step=1)
    largeur = st.slider("Largeur de la fracture (en mm)", 0, 100, step=1)
    ratio = st.slider("Ratio muscle / graisse (scanner)", 0.0, 2.0, step=0.01)
    submitted = st.form_submit_button("Évaluer le risque")

if submitted:
    # --- Calcul du score ---
    score = 0
    if age < 40: score += 2
    elif age < 60: score += 1
    if sexe == "Homme": score += 1
    if schatzker >= 5: score += 3
    if n_fragments >= 3: score += 2
    if largeur >= 30: score += 2
    if ratio < 1.0: score += 3

    risque = round((score / 15) * 100, 1)

    # --- Recommandation ---
    if score <= 5:
        recommandation = "Surveillance simple"
    elif score <= 10:
        recommandation = "Fixateur externe + surveillance"
    else:
        recommandation = "Fasciotomie initiale recommandée"

    # --- Générer un code unique patient ---
    code_patient = f"VIG-{str(uuid.uuid4())[:8].upper()}"

    # Affichage résultats
    st.success(f"🧠 Score total : {score} / 15")
    st.info(f"📊 Risque estimé : {risque} %")
    st.warning(f"🩺 Recommandation : **{recommandation}**")
    st.code(f"🆔 Code patient : {code_patient}", language='markdown')

    # --- Sauvegarde dans CSV ---
    data = {
        'code_patient': code_patient,
        'age': age,
        'sexe': sexe,
        'schatzker': schatzker,
        'n_fragments': n_fragments,
        'largeur_fracture_mm': largeur,
        'ratio_muscle_graisse': ratio,
        'score_total': score,
        'risque_estimé': risque,
        'prise_en_charge_proposée': recommandation,
        'outcome_reel': None
    }

    df_new = pd.DataFrame([data])
    if os.path.exists("vigior_database.csv"):
        df_old = pd.read_csv("vigior_database.csv")
        df = pd.concat([df_old, df_new], ignore_index=True)
    else:
        df = df_new
    df.to_csv("vigior_database.csv", index=False)

# --- Section ajout retour clinique ---
st.markdown("---")
st.subheader("🔁 Ajouter un retour clinique")
with st.form("retour_form"):
    code = st.text_input("Code patient (ex: VIG-XXXXXX)")
    retour = st.text_area("Retour clinique (ex: pas de syndrome après fasciotomie)")
    retour_submitted = st.form_submit_button("Ajouter le retour")

if retour_submitted:
    if os.path.exists("vigior_database.csv"):
        df = pd.read_csv("vigior_database.csv")
        if code in df['code_patient'].values:
            df.loc[df['code_patient'] == code, 'outcome_reel'] = retour
            df.to_csv("vigior_database.csv", index=False)
            st.success(f"✅ Retour ajouté pour le patient {code}")
        else:
            st.error("❌ Code patient introuvable.")
    else:
        st.error("❌ Base de données introuvable.")
