import streamlit as st

st.set_page_config(page_title="MacroMate", layout="centered")

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #0f172a, #020617);
    color: #e2e8f0;
}
.block-container {
    padding: 2.5rem;
}
.result-card {
    padding: 20px;
    border-radius: 16px;
    background: rgba(255,255,255,0.05);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255,255,255,0.08);
}
</style>
""", unsafe_allow_html=True)

st.title("💪 MacroMate")
st.caption("Simple. Smart. Fitness.")

st.markdown("### Enter your details")

col1, col2 = st.columns(2)

with col1:
    weight = st.number_input("Weight (kg)", min_value=30, key="weight")

with col2:
    age = st.number_input("Age", min_value=10, key="age")

goal = st.selectbox("Goal", ["Fat Loss", "Maintain", "Weight Gain"], key="goal")

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

if st.button("Calculate Plan 🔥"):

    calories, protein, carbs, fats, maintenance = calculate_macros(weight, goal)

    st.markdown("### Your Daily Plan")

    st.markdown(f"""
    <div class="result-card">
        <h3>🔥 Calories: {calories}</h3>
        <p>⚖️ Maintenance: {maintenance}</p>
        <p>🥩 Protein: {protein} g</p>
        <p>🍚 Carbs: {carbs} g</p>
        <p>🥑 Fats: {fats} g</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")
st.markdown(
    "<p style='text-align:center; color:gray;'>MacroMate AI • Designed for real fitness tracking</p>",
    unsafe_allow_html=True
)