import streamlit as st
from features import skill_matching

# Page config
st.set_page_config(page_title="Job Consultant AI", layout="wide")

# Header
st.markdown("""
<div style="border: 2px solid #4a90e2; padding: 10px; border-radius: 5px; text-align: center; margin-bottom: 20px;">
<h3 style="color: #000; margin: 0;">Job Consultation AI</h3>
</div>
""", unsafe_allow_html=True,
)

# Run Skill Matching feature directly on the main page
skill_matching.app()

















