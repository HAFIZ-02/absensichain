import streamlit as st

def render_badge(percentage: float):
    if percentage >= 85:
        st.success("⭐⭐⭐ Badge: Si Rajin (>= 85%)")
    elif percentage >= 60:
        st.warning("⭐⭐ Badge: Si Pas-Pas (60% - 84%)")
    else:
        st.error("⭐ Badge: Si Malas (< 60%)")
