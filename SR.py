# app.py
import streamlit as st
import pandas as pd
import os
from datetime import datetime

# -------------------------
# Config & Data file
# -------------------------
st.set_page_config(page_title="VIGIOR", layout="centered")
DATA_FILE = "patients.csv"

# Create data file if missing
if not os.path.exists(DATA_FILE):
    df_init = pd.DataFrame(columns=[
        "patient_id", "timestamp", "age", "sex", "smoker",
        "fragments", "gap_mm", "HSA_angle",
        "risk_necrosis", "risk_nonunion", "risk_stiffness",
        "recommended_treatment", "justification"
    ])
    df_init.to_csv(DATA_FILE, index=False)

# -------------------------
# Helpers
# -------------------------
def generate_patient_id():
    df = pd.read_csv(DATA_FILE)
    if df.empty:
        return "H-001"
    else:
        # take last patient_id, increment numeric part
        try:
            last_id = df["patient_id"].iloc[-1]
            num = int(last_id.split("-")[1]) + 1
        except Exception:
            num = len(df) + 1
        return f"H-{num:03d}"

def compute_risks(age, fragments, gap_mm, HSA_angle, smoker):
    """
    Retourne trois risques (en pourcentages) : nécrose, pseudarthrose, raideur.
    Formules heuristiques (demo) : pondération des facteurs cliniques.
    """
    # base selon nombre de fragments
    base_frag = fragments * 12.0  # chaque fragment augmente le risque
    # HSA impact (plus bas = plus de risque de nécrose)
    hsa_penalty = max(0, 120 - HSA_angle) * 0.9
    # gap increases nonunion and necrosis slightly
    gap_penalty_nec = gap_mm * 2.0
    gap_penalty_non = gap_mm * 3.0
    # age mostly contributes to stiffness
    age_penalty = max(0, (age - 50) * 0.6)
    # smoking
    smoke_pen = 10.0 if smoker == "Yes" else 0.0

    risk_necrosis = min(95.0, base_frag + hsa_penalty + gap_penalty_nec + smoke_pen)
    risk_nonunion = min(95.0, fragments * 9.0 + gap_penalty_non + (5.0 if smoker == "Yes" else 0.0))
    risk_stiffness = min(95.0, 10.0 + age_penalty + fragments * 4.0 + gap_mm * 0.8)

    # round to one decimal for display / storage
    return round(risk_necrosis, 1), round(risk_nonunion, 1), round(risk_stiffness, 1)

def propose_treatment_and_justification(age, fragments, gap_mm, HSA_angle, risks):
    """
    Règles heuristiques pour proposer un traitement et justifier le choix.
    Le texte de justification explique le raisonnement (facteurs majeurs).
    """
    necrosis, nonunion, stiffness = risks

    # Decision rules (heuristiques)
    if necrosis >= 50 or fragments >= 4 or HSA_angle < 120:
        reco = "Arthroplastie"
        reason = (
            "Raisonnement : risque élevé de nécrose (facteurs : grand nombre de fragments, "
            "HSA bas, ou score de nécrose élevé). L'arthroplastie est proposée car elle évite "
            "les complications liées à la nécrose tête humérale et donne une solution fiable "
            "chez les patients âgés ou à os de mauvaise qualité."
        )
    elif nonunion >= 40 or gap_mm > 6 or fragments == 3:
        reco = "Ostéosynthèse"
        reason = (
            "Raisonnement : risque notable de pseudarthrose (gap inter-fragmentaire important, "
            "fracture comminutive). L'ostéosynthèse vise à restaurer l'anatomie et la stabilité "
            "pour réduire le risque de non-union."
        )
    else:
        reco = "Traitement orthopédique (conservateur)"
        reason = (
            "Raisonnement : risques modérés/faibles ; fracture peu déplacée ou faible gap. "
            "Le traitement conservateur limite les complications chirurgicales et peut donner "
            "de bons résultats fonctionnels si la réduction est acceptable."
        )

    # Add short bullet points of contributing factors
    factors = []
    if age > 65:
        factors.append("âge élevé → risque accru de raideur et mauvaise qualité osseuse")
    if fragments >= 3:
        factors.append("nombre de fragments élevé → risque de complication mécanique")
    if HSA_angle < 120:
        factors.append("HSA bas → perfusion tête humérale compromise → risque nécrose")
    if gap_mm > 5:
        factors.append("écart inter-fragmentaire important → risque de pseudarthrose")
    if smoker == "Yes":
        factors.append("tabagisme → altère la consolidation osseuse")

    if factors:
        reason += "\n\nFacteurs contribuant :\n- " + "\n- ".join(factors)

    # append numeric risks summary
    reason += f"\n\nRisques estimés : nécrose {necrosis}%, pseudarthrose {nonunion}%, raideur {stiffness}%."

    return reco, reason

# -------------------------
# Navigation (single-file)
# -------------------------
if "page" not in st.session_state:
    st.session_state["page"] = "Home"

def go_to(p):
    st.session_state["page"] = p
    st.experimental_rerun()

page = st.session_state["page"]

# -------------------------
# HOME
# -------------------------
if page == "Home":
    st.title("🦾 VIGIOR")
    st.caption("Predictive Orthopedic Assistant — simple & efficace")

    st.write("")  # spacing

    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕  New Patient", use_container_width=True):
            go_to("New Patient")
    with col2:
        if st.button("📊  Research", use_container_width=True):
            go_to("Research")

    st.markdown("---")
    st.markdown("Interface simple : cliquez sur **New Patient** pour évaluer un cas, ou **Research** pour consulter la base.")

# -------------------------
# NEW PATIENT
# -------------------------
elif page == "New Patient":
    st.header("➕ New Patient — Saisie clinique")

    with st.form("form_new_patient"):
        age = st.number_input("Âge (années)", min_value=18, max_value=120, value=65, step=1)
        sex = st.selectbox("Sexe", ["Male", "Female"])
        smoker = st.selectbox("Fumeur ?", ["No", "Yes"])
        fragments = st.number_input("Nombre de fragments (Neer)", min_value=1, max_value=4, value=2, step=1)
        gap_mm = st.number_input("Écart inter-fragmentaire (mm)", min_value=0, max_value=50, value=0, step=1)
        # HSA slider (horizontal)
        HSA_angle = st.slider("Angle HSA (°)", min_value=80, max_value=160, value=135, step=1)

        submitted = st.form_submit_button("Evaluate")

    if submitted:
        # compute risks
        risks = compute_risks(age, fragments, gap_mm, HSA_angle, smoker)
        reco, justification = propose_treatment_and_justification(age, fragments, gap_mm, HSA_angle, risks)

        # store current evaluation in session for display and saving
        st.session_state["current_eval"] = {
            "timestamp": datetime.utcnow().isoformat(),
            "age": age,
            "sex": sex,
            "smoker": smoker,
            "fragments": fragments,
            "gap_mm": gap_mm,
            "HSA_angle": HSA_angle,
            "risk_necrosis": risks[0],
            "risk_nonunion": risks[1],
            "risk_stiffness": risks[2],
            "recommended_treatment": reco,
            "justification": justification
        }
        st.experimental_rerun()

    # If there is a current evaluation, show results and save option
    if "current_eval" in st.session_state:
        r = st.session_state["current_eval"]
        st.markdown("---")
        st.subheader("📋 Résultats (évaluation)")
        colA, colB, colC = st.columns(3)
        colA.metric("Risque nécrose", f"{r['risk_necrosis']} %")
        colB.metric("Risque pseudarthrose", f"{r['risk_nonunion']} %")
        colC.metric("Risque raideur", f"{r['risk_stiffness']} %")

        st.markdown("### ✅ Recommandation de traitement")
        st.write(f"**{r['recommended_treatment']}**")
        st.markdown("**Justification (raisonnement de l'IA) :**")
        st.write(r['justification'])

        # save option
        if st.button("💾 Enregistrer patient"):
            # assign id and save to CSV
            patient_id = generate_patient_id()
            row = {
                "patient_id": patient_id,
                "timestamp": r["timestamp"],
                "age": r["age"],
                "sex": r["sex"],
                "smoker": r["smoker"],
                "fragments": r["fragments"],
                "gap_mm": r["gap_mm"],
                "HSA_angle": r["HSA_angle"],
                "risk_necrosis": r["risk_necrosis"],
                "risk_nonunion": r["risk_nonunion"],
                "risk_stiffness": r["risk_stiffness"],
                "recommended_treatment": r["recommended_treatment"],
                "justification": r["justification"]
            }
            df = pd.read_csv(DATA_FILE)
            df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
            df.to_csv(DATA_FILE, index=False)
            st.success(f"Patient enregistré : {patient_id}")
            # clear current eval or keep it if you prefer
            # del st.session_state["current_eval"]

# -------------------------
# RESEARCH
# -------------------------
elif page == "Research":
    st.header("📊 Research — Base des patients")
    df = pd.read_csv(DATA_FILE)

    if df.empty:
        st.info("Aucun patient enregistré.")
    else:
        # simple filter box
        q = st.text_input("🔎 Rechercher (ID, âge, risque, traitement...)", value="")
        if q:
            # filter rows where any cell (stringified) contains q (case-insensitive)
            mask = df.apply(lambda row: row.astype(str).str.contains(q, case=False).any(), axis=1)
            df_display = df[mask].copy()
        else:
            df_display = df.copy()

        # show summary table with important columns
        st.dataframe(df_display[[
            "patient_id", "timestamp", "age", "sex", "smoker",
            "fragments", "gap_mm", "HSA_angle",
            "risk_necrosis", "risk_nonunion", "risk_stiffness",
            "recommended_treatment"
        ]].sort_values("patient_id").reset_index(drop=True), height=420)

        # Option: inspect a single patient
        st.markdown("---")
        st.write("Afficher une fiche patient détaillée :")
        sel = st.selectbox("Choisir patient ID", options=[""] + df_display["patient_id"].tolist())
        if sel:
            row = df[df["patient_id"] == sel].iloc[-1]  # latest
            st.subheader(f"Fiche — {sel}")
            st.write(f"- Date : {row['timestamp']}")
            st.write(f"- Âge : {row['age']}  •  Sexe : {row['sex']}  •  Fumeur : {row['smoker']}")
            st.write(f"- Fragments : {row['fragments']}  •  Gap (mm) : {row['gap_mm']}  •  HSA : {row['HSA_angle']}°")
            st.write(f"- Risque nécrose : {row['risk_necrosis']}%")
            st.write(f"- Risque pseudarthrose : {row['risk_nonunion']}%")
            st.write(f"- Risque raideur : {row['risk_stiffness']}%")
            st.write(f"- Recommandation : **{row['recommended_treatment']}**")
            st.markdown("**Justification**")
            st.write(row["justification"])

# -------------------------
# Footer: quick nav
# -------------------------
st.markdown("---")
c1, c2, c3 = st.columns([1,1,1])
with c1:
    if st.button("◀ Home"):
        go_to("Home")
with c2:
    if st.button("➕ New Patient (nav)"):
        go_to("New Patient")
with c3:
    if st.button("📊 Research (nav)"):
        go_to("Research")
