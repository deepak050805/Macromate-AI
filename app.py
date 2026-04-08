import streamlit as st
import matplotlib.pyplot as plt

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="MacroMate", layout="centered")

# ---------------- CUSTOM STYLING ----------------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #0f172a, #020617);
    color: #e2e8f0;
}

.block-container {
    padding: 2.5rem;
}

h1 {
    font-weight: 700;
    letter-spacing: 1px;
}

/* Result card */
.result-card {
    padding: 20px;
    border-radius: 16px;
    background: rgba(255,255,255,0.05);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255,255,255,0.08);
    margin-top: 20px;
}

/* Clean human-style button */
.stButton > button {
    background-color: #111827;
    color: #e5e7eb;
    border: 1px solid #374151;
    border-radius: 8px;
    padding: 10px 16px;
    font-weight: 500;
}

.stButton > button:hover {
    background-color: #1f2937;
    border-color: #4b5563;
    transform: translateY(-1px);
    transition: 0.2s ease;
}
</style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------
st.title("MacroMate")
st.caption("A simple and effective tool for daily macro planning.")

# ---------------- INPUT ----------------
st.markdown("### Enter your details")

col1, col2 = st.columns(2)

with col1:
    weight = st.number_input("Weight (kg)", min_value=30, key="weight", placeholder="e.g. 65")

with col2:
    age = st.number_input("Age", min_value=10, key="age", placeholder="e.g. 20")

goal = st.selectbox("Goal", ["Fat Loss", "Maintain", "Weight Gain"], key="goal")

# ---------------- CALCULATION FUNCTION ----------------
def calculate_macros(weight, goal):
    maintenance = weight * 2.2 * 15

    if goal == "Fat Loss":
        calories = maintenance * 0.9
    elif goal == "Weight Gain":
        calories = maintenance * 1.1
    else:
        calories = maintenance

    protein = weight * 2
    fats = weight * 0.8
    carbs = (calories - (protein*4 + fats*9)) / 4

    return int(calories), int(protein), int(carbs), int(fats), int(maintenance)

# ---------------- BUTTON ----------------
if st.button("Calculate Plan"):

    calories, protein, carbs, fats, maintenance = calculate_macros(weight, goal)

    st.success("Plan generated successfully")

    # -------- RESULT CARD --------
    st.markdown("### Your Daily Plan")

    st.markdown(f"""
    <div class="result-card">
        <h3>Calories: {calories}</h3>
        <p>Maintenance: {maintenance}</p>
    </div>
    """, unsafe_allow_html=True)

    # -------- METRICS --------
    col1, col2, col3 = st.columns(3)

    col1.metric("Protein", f"{protein} g")
    col2.metric("Carbs", f"{carbs} g")
    col3.metric("Fats", f"{fats} g")

    # -------- CHART + FOOD --------
    col_left, col_right = st.columns([0.9, 1.1])

    with col_left:
        st.markdown("### Macro Distribution")

        labels = ['Protein', 'Carbs', 'Fats']
        values = [protein, carbs, fats]

        fig, ax = plt.subplots(figsize=(3, 3))
        ax.pie(values, labels=labels, autopct='%1.1f%%')
        ax.set_title("")

        st.pyplot(fig)

    with col_right:
        st.markdown("### Suggested Foods")

        if goal == "Fat Loss":
            st.write("• Paneer / Tofu")
            st.write("• Green vegetables")
            st.write("• Low oil meals")

        elif goal == "Weight Gain":
            st.write("• Rice / Roti")
            st.write("• Peanut butter")
            st.write("• Milk, Banana shake")

        else:
            st.write("• Balanced diet")
            st.write("• Maintain protein intake")

# ---------------- FOOTER ----------------
st.markdown("---")
st.markdown(
    "<p style='text-align:center; color:gray;'>MacroMate • Fitness-focused macro planning</p>",
    unsafe_allow_html=True
)

