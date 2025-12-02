# app.py
import streamlit as st
import pandas as pd
import uuid
import os
from datetime import datetime

# ========== Page config ==========
st.set_page_config(page_title="VIGIOR-H — Épaule interactive", layout="wide", initial_sidebar_state="auto")

# ========== Styles (CSS) ==========
st.markdown(
    """
    <style>
    /* Font + base */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    html, body, [class*="css"]  { font-family: 'Inter', sans-serif; }

    /* Page background & card */
    .bg {
        background: linear-gradient(180deg,#f6fbff 0%, #ffffff 60%);
        padding: 28px;
        border-radius: 14px;
        box-shadow: 0 6px 30px rgba(16,24,40,0.06);
    }

    .card {
        background: linear-gradient(180deg, rgba(255,255,255,0.9), rgba(250,250,255,0.85));
        padding: 18px;
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(16,24,40,0.04);
        transition: transform 0.18s ease, box-shadow 0.18s ease;
    }
    .card:hover { transform: translateY(-4px); box-shadow: 0 10px 30px rgba(16,24,40,0.07); }

    /* Buttons */
    .btn {
        background: linear-gradient(90deg,#2563eb,#4f46e5);
        color: white;
        padding: 10px 18px;
        border-radius: 12px;
        border: none;
        font-weight: 600;
        cursor: pointer;
        box-shadow: 0 6px 18px rgba(79,70,229,0.18);
        transition: transform 0.12s ease;
    }
    .btn:active { transform: translateY(1px); }

    /* Secondary */
    .btn-ghost {
        background: transparent;
        color: #0f172a;
        border: 1px solid rgba(15,23,42,0.06);
        padding: 8px 14px;
        border-radius: 10px;
        font-weight: 600;
        cursor: pointer;
    }

    /* SVG container */
    .svg-wrap {
        display:flex;
        align-items:center;
        justify-content:center;
        padding: 12px;
    }

    /* pulse animation on shoulder */
    @keyframes pulse {
      0% { r: 10px; opacity: 0.6; transform: scale(1.0);}
      50% { r: 14px; opacity: 0.12; transform: scale(1.08);}
      100% { r: 10px; opacity: 0.6; transform: scale(1.0);}
    }
    .shoulder-pulse { animation: pulse 1.6s ease-in-out infinite; transform-origin:center; }

    /* form layout */
    .form-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
    @media (max-width:800px) { .form-grid { grid-template-columns: 1fr; } }

    /* subtle transitions */
    .fade-in { animation: fadeIn 0.36s ease-out; }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(6px);} to { opacity: 1; transform: translateY(0);} }

    </style>
    """, unsafe_allow_html=True
)

# ========== Header ==========
st.markdown("<div class='bg'><h1 style='margin:0 0 8px 0'>🦾 VIGIOR-H — Évaluation (interface interactive)</h1>"
            "<p style='margin:0;color:#334155'>Clique sur l'épaule (ou le bouton) pour commencer l'évaluation — design minimaliste et réactif.</p></div>",
            unsafe_allow_html=True)

st.write("")  # spacing

# ========== Layout: Left (visual) / Right (controls) ==========
left_col, right_col = st.columns([1.1, 1])

with left_col:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<h3 style='margin:6px 0 12px 0'>Sélectionner l'épaule</h3>", unsafe_allow_html=True)

    # Inline SVG minimal flat design torso + highlighted shoulder
    svg_html = """
    <div class="svg-wrap">
    <svg width="360" height="360" viewBox="0 0 360 360" xmlns="http://www.w3.org/2000/svg">
      <!-- Torso -->
      <rect x="120" y="60" rx="30" ry="30" width="120" height="140" fill="#e6f0ff" stroke="#c7ddff" />
      <!-- neck -->
      <rect x="155" y="30" width="50" height="40" rx="10" fill="#f8fbff" stroke="#dbeeff"/>
      <!-- head -->
      <circle cx="180" cy="8" r="22" fill="#fff" stroke="#e0efff"/>

      <!-- left humerus (stylized) -->
      <path d="M120 110 C80 120, 70 170, 100 200 C120 220, 140 215, 145 200" fill="none" stroke="#b6c9ff" stroke-width="10" stroke-linecap="round"/>
      <!-- right humerus (stylized) -->
      <path d="M240 110 C280 120, 290 170, 260 200 C240 220, 220 215, 215 200" fill="none" stroke="#b6c9ff" stroke-width="10" stroke-linecap="round"/>

      <!-- shoulder highlight (right) - interactive target -->
      <g id="shoulder-target" style="cursor:pointer;">
        <circle cx="260" cy="150" r="14" fill="#2563eb" opacity="0.98" />
        <circle class="shoulder-pulse" cx="260" cy="150" r="10" fill="#2563eb" opacity="0.18" />
      </g>

      <!-- small label -->
      <text x="230" y="184" font-family="Inter, sans-serif" font-size="12" fill="#0f172a">Épaule (prox. humérus)</text>
    </svg>
    </div>
    """
    st.markdown(svg_html, unsafe_allow_html=True)

    st.markdown("<div style='display:flex; gap:10px; margin-top:10px'>", unsafe_allow_html=True)
    # Buttons near image: clickable shoulder or clear selection
    if st.button("🖱️ Cliquer l'épaule", key="click_shoulder", help="Simule le clic sur l'épaule"):
        st.session_state['shoulder_clicked'] = True
        # small visual feedback
        st.experimental_rerun()

    if st.button("🔄 Réinitialiser sélection", key="reset_shoulder"):
        st.session_state['shoulder_clicked'] = False
        st.experimental_rerun()
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with right_col:
    # Card: résumé / actions
    st.markdown("<div class='card fade-in'>", unsafe_allow_html=True)
    st.markdown("<h3 style='margin:6px 0 8px 0'>Flux d'utilisation</h3>", unsafe_allow_html=True)
    st.markdown("""
    - Clique sur l'épaule (ou le bouton).  
    - Le formulaire s'ouvre dans une carte fluide.  
    - Remplis les données → app calcule et sauvegarde.  
    """, unsafe_allow_html=True)

    st.markdown("---")
    # Show status of selection
    clicked = st.session_state.get('shoulder_clicked', False)
    if clicked:
        st.success("✅ Épaule sélectionnée — formulaire disponible ci-dessous")
    else:
        st.info("ℹ️ Aucune épaule sélectionnée — clique pour commencer")

    st.markdown("</div>", unsafe_allow_html=True)

# ========== Main form : shown only if shoulder clicked ==========
if st.session_state.get('shoulder_clicked', False):
    st.write("")
    st.markdown("<div class='card fade-in'>", unsafe_allow_html=True)
    st.markdown("<h3 style='margin:6px 0 10px 0'>Formulaire d'évaluation — VIGIOR-H</h3>", unsafe_allow_html=True)

    with st.form("vigiorh_form", clear_on_submit=False):
        # Grid layout
        st.markdown("<div class='form-grid'>", unsafe_allow_html=True)

        age = st.number_input("Âge (années)", min_value=18, max_value=100, step=1, value=72)
        sexe = st.selectbox("Sexe", ["Homme", "Femme"])
        fumeur = st.radio("Fumeur ?", ["Non", "Oui"], index=0, horizontal=True)

        if fumeur == "Oui":
            pa = st.slider("Pack-years (PA)", 0, 100, step=1, value=15)
        else:
            pa = 0

        n_fragments = st.slider("Nombre de fragments (Neer)", 2, 4, step=1, value=3)
        hsa = st.slider("Angle HSA (°)", 90, 160, step=1, value=130)
        ecart = st.radio("Écart inter-fragmentaire > 5 mm", ["Non", "Oui"], horizontal=True)
        luxation = st.radio("Luxation associée ?", ["Non", "Oui"], horizontal=True)
        osteoporosis = st.radio("Ostéoporose connue ?", ["Non", "Oui"], horizontal=True)

        st.markdown("</div>", unsafe_allow_html=True)  # close grid

        st.markdown("<div style='display:flex; gap:12px; margin-top:12px'>", unsafe_allow_html=True)
        submit = st.form_submit_button("Évaluer les risques", use_container_width=False)
        st.markdown("</div>", unsafe_allow_html=True)

    # Process submission
    if submit:
        # small "processing" animation
        with st.spinner("Analyse en cours…"):
            # compute base score (same logic que ton modèle)
            base_score = 0
            base_score += 2 if age > 65 else 0
            base_score += 2 if (fumeur == "Oui" and pa > 10) else 0
            base_score += 3 if n_fragments == 4 else 0
            base_score += 2 if (hsa < 120 or hsa > 145) else 0
            base_score += 2 if ecart == "Oui" else 0
            base_score += 2 if luxation == "Oui" else 0
            base_score += 2 if osteoporosis == "Oui" else 0

            # Risks (fictifs / demo)
            ortho_necrose = min(5 + base_score * 2, 95)
            ortho_pseudo = min(8 + base_score * 1.5, 95)
            ortho_raideur = min(10 + base_score * 2.5, 95)

            chir_necrose = min(15 + base_score * 1.2, 95)
            chir_pseudo = min(10 + base_score * 1.0, 90)
            chir_raideur = min(7 + base_score * 2.0, 90)

        # show results in two-column cards
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown("### 🧍‍ Traitement orthopédique")
            st.write(f"- Risque nécrose : **{ortho_necrose:.1f}%**")
            st.write(f"- Risque pseudarthrose : **{ortho_pseudo:.1f}%**")
            st.write(f"- Risque raideur : **{ortho_raideur:.1f}%**")
            st.markdown("</div>", unsafe_allow_html=True)

        with c2:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown("### 🛠️ Réduction chirurgicale")
            st.write(f"- Risque nécrose : **{chir_necrose:.1f}%**")
            st.write(f"- Risque pseudarthrose : **{chir_pseudo:.1f}%**")
            st.write(f"- Risque raideur : **{chir_raideur:.1f}%**")
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div style='margin-top:12px'/>", unsafe_allow_html=True)

        # Recommendation card
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("### 🦾 Recommandation (heuristique)")
        st.info("Arthroplastie recommandée si : >75 ans, 4 fragments avec luxation, ostéoporose sévère, mauvais os pour fixation.")
        st.markdown("</div>", unsafe_allow_html=True)

        # Generate patient code and save
        code_patient = f"VIGH-{uuid.uuid4().hex[:8].upper()}"
        st.success(f"🆔 Code patient : **{code_patient}**")

        # build dataframe row
        data = {
            'timestamp': datetime.utcnow().isoformat(),
            'code_patient': code_patient,
            'age': age,
            'sexe': sexe,
            'fumeur': fumeur,
            'PA': pa,
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
        file_path = "vigior_humerus_db.csv"
        if os.path.exists(file_path):
            df_old = pd.read_csv(file_path)
            df = pd.concat([df_old, df_new], ignore_index=True)
        else:
            df = df_new

        df.to_csv(file_path, index=False)
        st.success("📁 Données sauvegardées localement.")

        # small download link
        st.markdown("---")
        st.download_button("📥 Télécharger la ligne (CSV)", df_new.to_csv(index=False).encode('utf-8'),
                           file_name=f"{code_patient}.csv", mime="text/csv")

    st.markdown("</div>", unsafe_allow_html=True)  # close card

# ========== Footer: tips / next steps ==========
st.write("")
st.markdown("<div style='opacity:0.9; margin-top:18px'>"
            "<small>Astuce : tu peux remplacer le SVG par une image fournie et conserver la logique « cliquer l'épaule ».</small></div>",
            unsafe_allow_html=True)
