import streamlit as st
import base64

def show_qr(qr_b64: str):
    img_bytes = base64.b64decode(qr_b64)
    st.image(img_bytes, caption="QR Code Absensi Privat", width=250)
    st.download_button("Unduh QR Code (PNG)", data=img_bytes, file_name="absenchain_qr.png", mime="image/png")
