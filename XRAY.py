import streamlit as st
from PIL import Image, ImageDraw
import numpy as np

st.title("🦴 VIGIOR - Détection simple de fracture")

st.write("Upload une radiographie : les zones suspectes seront encadrées.")

uploaded_file = st.file_uploader("Choisir une radiographie", type=["jpg", "png", "jpeg"])

if uploaded_file is not None:
    # Charger image en niveaux de gris
    image = Image.open(uploaded_file).convert("L")
    st.image(image, caption="Radiographie originale", use_column_width=True)

    # Convertir en array
    img_array = np.array(image)

    # Détection simple des contours (différence de pixels)
    edges = np.abs(np.diff(img_array, axis=0))

    # Seuil automatique
    threshold = edges.mean() + edges.std()
    mask = edges > threshold

    # Coordonnées des zones suspectes
    coords = np.column_stack(np.where(mask))

    # Dessiner rectangle
    image_color = image.convert("RGB")
    draw = ImageDraw.Draw(image_color)

    if len(coords) > 0:
        y_min, x_min = coords.min(axis=0)
        y_max, x_max = coords.max(axis=0)

        draw.rectangle([x_min, y_min, x_max, y_max], outline="red", width=3)

        st.image(image_color, caption="Zone suspecte encadrée", use_column_width=True)
        st.warning("⚠️ Zone suspecte détectée")
    else:
        st.image(image_color, caption="Aucune anomalie détectée", use_column_width=True)
        st.success("✅ Pas de zone suspecte")

    st.info("⚠️ Prototype simple - non validé médicalement")
