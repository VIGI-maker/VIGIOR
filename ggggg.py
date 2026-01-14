import streamlit as st
import pandas as pd
import os
import uuid
from datetime import datetime
import matplotlib.pyplot as plt

st.set_page_config(page_title="VIGIOR-H", layout="wide")

# -----------------------
# Constants / Files
# -----------------------
PATIENTS_CSV = "patients.csv"

RESEARCH_REFS = [
    {"title": "PHARON model (Goudie et al.) - predictors of nonunion/complications in PHF", "citation": "Goudie EB et al., JBJS, 2021"},
    {"title": "Systematic review/meta-analysis comparing treatments for PHF", "citation": "Hohmann E. et al., J Shoulder Elbow Surg, 2023"},
    {"title": "Comprehensive review of proximal humerus fractures", "citation": "Baker HP et al., J Clin Med, 2022"},
    {"title": "Bayesian network meta-analysis: RTSA vs ORIF vs HA (outcomes by age)", "citation": "Migliorini F., 2025"},
    {"title": "Comparative outcomes arthroplasty vs non-operative (recent review)", "citation": "Lai et al., Frontiers in Medicine, 2024"}
]

# -----------------------
# Session State & Data
# -----------------------
if "page" not in st.session_state:
    st.session_state.page = "Home"

if "patients" not in st.session_state:
    if os.path.exists(PATIENTS_CSV):
        st.session_state.patients = pd.read_csv(PATIENTS_CSV)
    else:
        st.session_state.patients = pd.DataFrame(columns=[
            "ID","Date","Age","Tabac","Comorbidities","BoneQuality",
            "Fragments","HSA","Gap","S_AVN","S_PSEU","S_FAIL_FIX","S_SURG",
            "Treatment","Justification","Notes"
        ])

if "Notes" not in st.session_state.patients.columns:
    st.session_state.patients["Notes"] = ""
    st.session_state.patients.to_csv(PATIENTS_CSV, index=False)

def save_patients():
    st.session_state.patients.to_csv(PATIENTS_CSV, index=False)

def generate_patient_id():
    return f"H-{str(uuid.uuid4())[:8].upper()}"

# -----------------------
# Language Switcher
# -----------------------
LANG = st.sidebar.radio("🔄 Language / Langue", options=["English", "Français"])

def tr(text_en, text_fr):
    return text_en if LANG == "English" else text_fr

# -----------------------
# Pages
# -----------------------
def page_home():
    st.title("VIGIOR-H")
    st.subheader(tr("Predictive Orthopedic Assistant — Proximal Humerus",
                    "Assistant Orthopédique Prédictif — Humérus proximal"))
    c1, c2 = st.columns([1,1])
    with c1:
        if st.button(tr("New Evaluation","Nouvelle évaluation"), use_container_width=True):
            st.session_state.page = "New Patient"
    with c2:
        if st.button(tr("Registered Patients","Patients enregistrés"), use_container_width=True):
            st.session_state.page = "Research"

def page_research():
    st.title(tr("Registered Patients","Patients enregistrés"))
    st.subheader(tr("Registered patients","Patients enregistrés"))

    q = st.text_input(tr("Search (ID, age, treatment...)","Rechercher (ID, âge, traitement...)"))
    df = st.session_state.patients.copy()
    if q:
        df = df[df.apply(lambda r: q.lower() in r.astype(str).str.lower().to_string(), axis=1)]

    st.dataframe(df, height=300)

    st.markdown("---")
    st.subheader(tr("Patient clinical notes","Notes cliniques du patient"))

    selected_id = st.selectbox(
        tr("Select patient ID","Sélectionner l’ID du patient"),
        df["ID"].tolist()
    )

    patient_row = df[df["ID"] == selected_id].iloc[0]

    notes = st.text_area(
        tr("Surgeon clinical notes","Notes cliniques du chirurgien"),
        value=patient_row.get("Notes",""),
        height=200
    )

    if st.button(tr("Save notes","Sauvegarder les notes")):
        st.session_state.patients.loc[
            st.session_state.patients["ID"] == selected_id, "Notes"
        ] = notes
        save_patients()
        st.success(tr("Notes saved","Notes sauvegardées"))

    # -----------------------
    # Analyse du registre
    # -----------------------
    st.markdown("---")
    st.subheader(tr("Registry analysis","Analyse du registre"))

    if len(df) > 0:
        col1, col2 = st.columns(2)

        with col1:
            fig, ax = plt.subplots()
            ax.hist(df["Age"].dropna(), bins=10)
            ax.set_title(tr("Age distribution","Distribution de l’âge"))
            st.pyplot(fig)

        with col2:
            fig, ax = plt.subplots()
            df["Fragments"].value_counts().sort_index().plot(kind="bar", ax=ax)
            ax.set_title(tr("Number of fragments","Nombre de fragments"))
            st.pyplot(fig)

        st.markdown(
            tr(
                f"**Mean HSA angle:** {round(df['HSA'].mean(),1)}°",
                f"**Angle HSA moyen :** {round(df['HSA'].mean(),1)}°"
            )
        )

        osteoporosis_rate = (df["BoneQuality"] == "poor").mean() * 100
        st.markdown(
            tr(
                f"**Osteoporosis:** {round(osteoporosis_rate,1)}%",
                f"**Ostéoporose :** {round(osteoporosis_rate,1)}%"
            )
        )

        notes_txt = df["Notes"].fillna("").str.lower()

        infection = notes_txt.str.contains("infection").sum()
        pseudarthrose = notes_txt.str.contains("pseudarthrose|nonunion").sum()
        necrose = notes_txt.str.contains("necrose|avn").sum()

        comp_df = pd.DataFrame({
            tr("Complication","Complication"): [
                tr("Infection","Infection"),
                tr("Nonunion","Pseudarthrose"),
                tr("Humeral head necrosis","Nécrose tête humérale")
            ],
            tr("Cases","Cas"): [infection, pseudarthrose, necrose]
        })

        fig, ax = plt.subplots()
        ax.bar(comp_df.iloc[:,0], comp_df.iloc[:,1])
        ax.set_title(tr("Complications from clinical notes",
                        "Complications issues des notes cliniques"))
        st.pyplot(fig)

    st.markdown("---")
    st.subheader(tr("Key References (archived)","Références clés (archivées)"))
    for r in RESEARCH_REFS:
        st.markdown(f"- **{r['title']}** — *{r['citation']}*")

    if st.button(tr("Back Home","Retour Home"), use_container_width=True):
        st.session_state.page = "Home"

# -----------------------
# Router
# -----------------------
if st.session_state.page == "Home":
    page_home()
elif st.session_state.page == "New Patient":
    page_new_patient()
elif st.session_state.page == "Research":
    page_research()
else:
    st.session_state.page = "Home"
