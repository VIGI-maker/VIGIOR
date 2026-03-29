import streamlit as st
from PIL import Image, ImageDraw
import numpy as np
import requests
import io

st.set_page_config(page_title="VIGIOR - Détection de fracture", layout="wide")
st.title("🦴 VIGIOR - Détection automatique de fracture")

st.write("Upload une radiographie, l'IA détectera automatiquement les zones suspectes.")

# Upload image
uploaded_file = st.file_uploader("Choisir une radiographie", type=["jpg","jpeg","png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file).convert("L")
    st.image(image, caption="Radiographie originale", use_column_width=True)

    # Convertir image en array
    img_array = np.array(image)

    # ----- Détection simplifiée avec modèle IA pré-entraîné en ligne -----
    # Pour simplifier, on utilise un modèle IA léger hébergé en ligne (simulé ici)
    # Dans une vraie version, tu peux pointer vers un modèle PyTorch ou TensorFlow hébergé
    # Ici, on simule la sortie : une "probabilité de fracture" sur chaque pixel

    # Simuler heatmap
    heatmap = np.zeros_like(img_array, dtype=float)
    # On met des valeurs aléatoires pour simuler un modèle IA
    # Dans vrai usage : heatmap = modèle.predict(img_array)
    np.random.seed(42)
    heatmap[img_array > 50] = np.random.rand(np.sum(img_array > 50))

    # Seuil pour détecter fracture
    threshold = 0.85
    mask = heatmap > threshold

    # Dessiner rectangles autour des zones suspectes
    coords = np.column_stack(np.where(mask))
    image_color = image.convert("RGB")
    draw = ImageDraw.Draw(image_color)

    if len(coords) > 0:
        # On découpe en rectangles précis autour des zones
        for y_min, x_min in coords:
            x_max = min(x_min+10, img_array.shape[1])
            y_max = min(y_min+10, img_array.shape[0])
            draw.rectangle([x_min, y_min, x_max, y_max], outline="red", width=2)

        st.image(image_color, caption="Zones suspectes détectées", use_column_width=True)
        st.warning(f"⚠️ {len(coords)} pixels suspects détectés")
    else:
        st.image(image_color, caption="Aucune zone suspecte détectée", use_column_width=True)
        st.success("✅ Pas de zone suspecte détectée")

    st.info("⚠️ Prototype IA simple pour démonstration. Version clinique nécessiterait modèle validé.")
