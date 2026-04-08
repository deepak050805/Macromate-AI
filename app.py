import streamlit as st

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

.result-card {
    padding: 20px;
    border-radius: 16px;
    background: rgba(255,255,255,0.05);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255,255,255,0.08);
    margin-top: 20px;
}

.stButton>button {
    background: linear-gradient(90deg, #6366f1, #8b5cf6);
    color: white;
    border-radius: 10px;
    padding: 10px 18px;
    border: none;
    font-weight: 500;
}

.stButton>button:hover {
    transform: translateY(-2px);
    transition: 0.2s ease;
}
</style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------
st.title("💪 MacroMate")
st.caption("Simple. Smart. Fitness.")

# ---------------- INPUT ----------------
st.markdown("### Enter your details")

col1, col2 = st.columns(2)

with col1:
    weight = st.number_input("Weight (kg)", min_value=30, placeholder="e.g. 65")

with col2:
    age = st.number_input("Age", min_value=10, placeholder="e.g. 20")

goal = st.selectbox("Goal", ["Fat Loss", "Maintain", "Weight Gain"])

# ---------------- CALCULATION FUNCTION ----------------
def calculate_macros(weight, goal):
    # Maintenance calories
    maintenance = weight * 2.2 * 15

    if goal == "Fat Loss":
        calories = maintenance * 0.9   # -10%
    elif goal == "Weight Gain":
        calories = maintenance * 1.1   # +10%
    else:
        calories = maintenance

    protein = weight * 2
    fats = weight * 0.8
    carbs = (calories - (protein*4 + fats*9)) / 4

    return int(calories), int(protein), int(carbs), int(fats), int(maintenance)

# ---------------- BUTTON ----------------
if st.button("Calculate Plan 🔥"):

    calories, protein, carbs, fats, maintenance = calculate_macros(weight, goal)

    st.markdown("### Your Daily Plan")

    st.markdown(f"""
    <div class="result-card">
        <h3>🔥 Calories: {calories}</h3>
        <p>⚖️ Maintenance Calories: {maintenance}</p>
        <p>🥩 Protein: {protein} g</p>
        <p>🍚 Carbs: {carbs} g</p>
        <p>🥑 Fats: {fats} g</p>
    </div>
    """, unsafe_allow_html=True)

    # Human-style feedback
    if goal == "Fat Loss":
        st.info("Stay consistent with your calorie deficit and keep protein high.")
    elif goal == "Weight Gain":
        st.info("Focus on progressive overload and sufficient calorie surplus.")
    else:
        st.info("Maintain your routine and stay consistent.")

# ---------------- FOOTER ----------------
st.markdown("---")
st.markdown(
    "<p style='text-align:center; color:gray;'>MacroMate AI • Designed for real fitness tracking</p>",
    unsafe_allow_html=True
)