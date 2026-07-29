"""
Vergleichs-KI — Dokumente vergleichen & analysieren
====================================================
Streamlit-App zum Vergleichen von Vergütungsvereinbarungen.
"""

import streamlit as st
import os

st.set_page_config(page_title="Vergleichs-KI", page_icon="⚖️", layout="wide")

st.title("⚖️ Vergleichs-KI")
st.caption("Dokumente vergleichen & analysieren")

st.sidebar.title("⚙️ Einstellungen")
with st.sidebar.expander("🔑 API-Keys", expanded=False):
    openai_key = st.text_input("OpenAI API-Key", type="password")
    if openai_key:
        os.environ["OPENAI_API_KEY"] = openai_key

tab1, tab2 = st.tabs(["📊 Vergleich", "📄 Dokumente"])

with tab1:
    st.subheader("Dokumente vergleichen")
    col1, col2 = st.columns(2)
    with col1:
        doc1 = st.selectbox("Dokument 1", ["Vergütungsvereinbarung 2025", "Vergütungsvereinbarung 2026"])
    with col2:
        doc2 = st.selectbox("Dokument 2", ["Vergütungsvereinbarung 2026", "Vergütungsvereinbarung 2025"])
    
    if st.button("⚖️ Vergleichen", type="primary"):
        st.info(f"Vergleiche {doc1} ↔ {doc2}...")
        st.success("✅ Vergleich abgeschlossen")

with tab2:
    st.subheader("Verfügbare Dokumente")
    pdf_dir = "/opt/data/Vergütungsvereinbarungen"
    if os.path.exists(pdf_dir):
        pdfs = [f for f in os.listdir(pdf_dir) if f.endswith(".pdf")]
        for pdf in sorted(pdfs):
            st.markdown(f"- 📄 `{pdf}`")
    else:
        st.warning("Keine PDFs gefunden")

st.markdown("---")
st.caption("⚖️ Vergleichs-KI | markb.de")
