import streamlit as st

# -------------------------------
# Language System
# -------------------------------
def translate(text, lang):
    """Simple bilingual translation system for orthopedic terminology."""
    dictionary = {
        "Age": {"FR": "Âge"},
        "Bone quality": {"FR": "Qualité osseuse"},
        "Comorbidities": {"FR": "Comorbidités"},
        "Number of fragments": {"FR": "Nombre de fragments"},
        "HSA angle (°)": {"FR": "Angle HSA (°)"},
        "Interfragmentary gap (mm)": {"FR": "Écart interfragmentaire (mm)"},
        "Evaluate": {"FR": "Évaluer"},
        "Estimated risks": {"FR": "Risques estimés"},
        "Risk of avascular necrosis": {"FR": "Risque de nécrose"},
        "Risk of nonunion": {"FR": "Risque de pseudarthrose"},
        "Risk of stiffness": {"FR": "Risque de raideur"},
        "Treatment recommendation": {"FR": "Recommandation thérapeutique"},
        "Proposed option": {"FR": "Option proposée"},
    }

    if lang == "EN":
        return text
    if text in dictionary:
        return dictionary[text]["FR"]
    return text


st.set_page_config(page_title="VIGIOR-H", layout="wide")

# -------------------------------
# UI Language
# -------------------------------
lang = st.toggle("FR / EN", value=False)
LANG = "FR" if lang else "EN"

# -------------------------------
# Title
# -------------------------------
st.title("🦾 VIGIOR-H — Proximal Humerus Decision Support System")

# -------------------------------
# INPUTS
# -------------------------------
st.subheader(translate("Age", LANG))
age = st.number_input("", min_value=18, max_value=100, value=65)

st.subheader(translate("Bone quality", LANG))
bone_quality = st.selectbox(
    "",
    ["Good", "Moderate", "Poor"]
)

st.subheader(translate("Comorbidities", LANG))
comorbid = st.selectbox("", ["None", "Significant"])

st.subheader(translate("Number of fragments", LANG))
nb_frag = st.selectbox(
    "",
    ["2-part", "3-part", "4-part"]
)

st.subheader(translate("HSA angle (°)", LANG))
HSA = st.slider("", 80, 180, 130)

st.subheader(translate("Interfragmentary gap (mm)", LANG))
gap = st.slider("", 0, 20, 3)

# -------------------------------
# RISK MODEL
# -------------------------------
def compute_risks(age, bone_quality, comorbid, nb_frag, HSA, gap):
    nec = 8
    nonunion = 6
    stiff = 10

    # Age effect
    if age >= 70:
        nec += 6
        nonunion += 5
        stiff += 7
    if age >= 80:
        nec += 4
        nonunion += 4

    # Bone quality
    if bone_quality == "Moderate":
        nonunion += 4
    if bone_quality == "Poor":
        nec += 6
        nonunion += 12
        stiff += 6

    # Comorbidities
    if comorbid == "Significant":
        nonunion += 5
        stiff += 4

    # Fragments
    if nb_frag == "3-part":
        nec += 6
    if nb_frag == "4-part":
        nec += 12
        nonunion += 10

    # Radiologic parameters
    if HSA < 120:
        nec += 10
        stiff += 5
    if gap > 6:
        nonunion += 12
    if gap > 12:
        nec += 8

    return min(nec, 90), min(nonunion, 90), min(stiff, 90)


if st.button(translate("Evaluate", LANG)):
    nec, nonunion, stiff = compute_risks(age, bone_quality, comorbid, nb_frag, HSA, gap)

    st.subheader("📊 " + translate("Estimated risks", LANG))
    st.write(f"● {translate('Risk of avascular necrosis', LANG)} : **{nec}%**")
    st.write(f"● {translate('Risk of nonunion', LANG)} : **{nonunion}%**")
    st.write(f"● {translate('Risk of stiffness', LANG)} : **{stiff}%**")

    # -------------------------------
    # Treatment decision tree
    # -------------------------------
    def recommend(age, bone_quality, nb_frag, HSA, gap):
        # Elderly + Poor Bone → Nonoperative unless catastrophic pattern
        if age >= 70 and bone_quality == "Poor":
            if nb_frag in ["2-part", "3-part"] and gap <= 6 and HSA >= 120:
                return ("Non-operative treatment",
                        "High-level evidence (PROFHER, Cochrane) demonstrates equivalent outcomes "
                        "to surgery with fewer complications in elderly osteoporotic patients.")
            else:
                return ("Arthroplasty",
                        "Severely displaced or 4-part fractures in osteoporotic elderly patients "
                        "show superior outcomes with arthroplasty.")

        # Young + 4-part
        if nb_frag == "4-part":
            if bone_quality == "Good":
                return ("Open reduction internal fixation",
                        "Young patients with reconstructible 4-part fractures benefit from anatomical ORIF.")
            else:
                return ("Arthroplasty",
                        "Poor bone stock limits fixation reliability; arthroplasty is recommended.")

        # 3-part
        if nb_frag == "3-part":
            if gap > 6 or HSA < 120:
                return ("Open reduction internal fixation",
                        "Marked displacement or varus malalignment requires open anatomical reduction.")
            else:
                return ("Closed reduction internal fixation",
                        "Stable 3-part patterns without major displacement can be managed with CRIF.")

        # 2-part
        if nb_frag == "2-part":
            if gap <= 6 and HSA >= 120:
                return ("Non-operative treatment",
                        "Minimally displaced 2-part fractures show excellent outcomes with conservative care.")
            else:
                return ("Closed reduction internal fixation",
                        "A significant gap or malalignment justifies CRIF.")

        return ("Non-operative treatment", "Default safe-mode.")

    treatment, justification = recommend(age, bone_quality, nb_frag, HSA, gap)

    st.subheader("🩺 " + translate("Treatment recommendation", LANG))
    st.success(f"### {translate('Proposed option', LANG)} : **{treatment}**")
    st.write(justification)
