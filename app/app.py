"""
Vergleichs-KI — Dokumente vergleichen & analysieren
====================================================
Vergleicht Vergütungsvereinbarungen (SGB V) auf Unterschiede.
"""

import streamlit as st
import os
import re
from pathlib import Path
from collections import Counter

st.set_page_config(page_title="Vergleich-Agenten", page_icon="⚖️", layout="wide")

# ── PDF-Text extrahieren ──
@st.cache_data
def extract_pdf_texts(pdf_dir: str) -> dict:
    import fitz
    docs = {}
    pdf_path = Path(pdf_dir)
    if not pdf_path.exists():
        return docs
    for pdf_file in sorted(pdf_path.glob("*.pdf")):
        try:
            doc = fitz.open(pdf_file)
            text = "".join(page.get_text() for page in doc)
            docs[pdf_file.name] = {"text": text, "pages": len(doc)}
            doc.close()
        except Exception as e:
            docs[pdf_file.name] = {"text": f"FEHLER: {e}", "pages": 0}
    return docs

# ── Differenz-Analyse ──
def compare_documents(text_a: str, text_b: str, name_a: str, name_b: str) -> dict:
    """Vergleicht zwei Dokumente und findet Unterschiede."""
    # Absätze
    paras_a = [p.strip() for p in text_a.split("\n\n") if len(p.strip()) > 20]
    paras_b = [p.strip() for p in text_b.split("\n\n") if len(p.strip()) > 20]

    # Wörter
    words_a = set(re.findall(r'\b\w{4,}\b', text_a.lower()))
    words_b = set(re.findall(r'\b\w{4,}\b', text_b.lower()))

    # Beträge
    def find_amounts(text):
        amounts = []
        for pat in [r'(\d+[.,]\d{2})\s*€', r'(\d+[.,]\d{2})\s*Euro', r'EUR\s*(\d+[.,]\d{2})']:
            amounts.extend(re.findall(pat, text))
        return set(amounts)

    amts_a = find_amounts(text_a)
    amts_b = find_amounts(text_b)

    # Paragraphen
    paragraphs_a = set(re.findall(r'§\s*\d+[a-z]?', text_a))
    paragraphs_b = set(re.findall(r'§\s*\d+[a-z]?', text_b))

    return {
        "paras_a": len(paras_a), "paras_b": len(paras_b),
        "common_words": len(words_a & words_b),
        "only_a": words_a - words_b,
        "only_b": words_b - words_a,
        "new_amounts": amts_b - amts_a,
        "removed_amounts": amts_a - amts_b,
        "changed_amounts": amts_a & amts_b,
        "new_paragraphs": paragraphs_b - paragraphs_a,
        "removed_paragraphs": paragraphs_a - paragraphs_b,
        "common_paragraphs": paragraphs_a & paragraphs_b,
        "len_a": len(text_a), "len_b": len(text_b),
    }

# ── Haupt-App ──
st.title("⚖️ Vergleich-Agenten")
st.caption("Vergütungsvereinbarungen SGB V — automatisch vergleichen")

pdf_dir = "/opt/data/Vergütungsvereinbarungen"
docs = extract_pdf_texts(pdf_dir)

tab1, tab2, tab3 = st.tabs(["📊 Vergleich", "📄 Dokumente", "🔍 Detailsuche"])

with tab1:
    st.subheader("📊 Dokumente vergleichen")

    if len(docs) >= 2:
        doc_names = list(docs.keys())
        col1, col2 = st.columns(2)
        with col1:
            doc_a = st.selectbox("Dokument A", doc_names, key="doc_a")
        with col2:
            doc_b = st.selectbox("Dokument B", doc_names, index=min(1, len(doc_names)-1), key="doc_b")

        if st.button("⚖️ Jetzt vergleichen", type="primary", use_container_width=True):
            text_a = docs[doc_a]["text"]
            text_b = docs[doc_b]["text"]
            result = compare_documents(text_a, text_b, doc_a, doc_b)

            # Übersicht
            st.markdown("### 📊 Übersicht")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric(f"Länge {doc_a[:15]}", f"{result['len_a']:,} Zeichen")
            with col2:
                st.metric(f"Länge {doc_b[:15]}", f"{result['len_b']:,} Zeichen")
            with col3:
                delta = result['len_b'] - result['len_a']
                st.metric("Differenz", f"{delta:+,} Zeichen")
            with col4:
                st.metric("Gemeinsame Wörter", result['common_words'])

            # Beträge
            st.markdown("---")
            st.subheader("💰 Betrags-Änderungen")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Gleiche Beträge", len(result['changed_amounts']))
            with col2:
                st.metric(f"🆕 Neu in {doc_b[:20]}", len(result['new_amounts']))
            with col3:
                st.metric(f"🗑️ Entfernt aus {doc_a[:20]}", len(result['removed_amounts']))

            if result['new_amounts']:
                st.markdown(f"**Neue Beträge:** {', '.join(sorted(result['new_amounts'])[:15])} €")
            if result['removed_amounts']:
                st.markdown(f"**Entfernte Beträge:** {', '.join(sorted(result['removed_amounts'])[:15])} €")

            # Paragraphen
            st.markdown("---")
            st.subheader("📜 Paragraphen-Änderungen")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Gleiche Paragraphen", len(result['common_paragraphs']))
            with col2:
                st.metric("Neue Paragraphen", len(result['new_paragraphs']))
            with col3:
                st.metric("Entfernte Paragraphen", len(result['removed_paragraphs']))

            if result['new_paragraphs']:
                st.info(f"🆕 **Neu:** {', '.join(sorted(result['new_paragraphs']))}")
            if result['removed_paragraphs']:
                st.warning(f"🗑️ **Entfernt:** {', '.join(sorted(result['removed_paragraphs']))}")

            # Neue/entfernte Begriffe
            st.markdown("---")
            st.subheader("🔤 Neue & entfernte Begriffe")

            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Nur in {doc_a[:20]}** ({len(result['only_a'])} Begriffe)")
                st.text(", ".join(sorted(list(result['only_a']))[:30]))
            with col2:
                st.markdown(f"**Nur in {doc_b[:20]}** ({len(result['only_b'])} Begriffe)")
                st.text(", ".join(sorted(list(result['only_b']))[:30]))

            st.success("✅ Vergleich abgeschlossen")
    else:
        st.warning("Mindestens 2 PDFs nötig. Erwartet: /opt/data/Vergütungsvereinbarungen/")

with tab2:
    st.subheader("📄 Verfügbare Dokumente")

    if docs:
        for name, data in docs.items():
            with st.expander(f"📄 {name} ({data['pages']} Seiten, {len(data['text']):,} Zeichen)"):
                st.text_area("Volltext", data["text"][:3000], height=250, key=f"text_{hash(name)}")
    else:
        st.warning(f"Keine PDFs in {pdf_dir}")

    st.markdown("---")
    st.subheader("📤 PDF hochladen")
    uploaded = st.file_uploader("Zusätzliche PDF zum Vergleich", type="pdf")
    if uploaded:
        import tempfile, fitz
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded.read())
            doc = fitz.open(tmp.name)
            text = "".join(page.get_text() for page in doc)
            docs[uploaded.name] = {"text": text, "pages": len(doc)}
            doc.close()
        st.success(f"✅ {uploaded.name} geladen ({len(text):,} Zeichen)")

with tab3:
    st.subheader("🔍 Gezielte Suche")

    if docs:
        search_doc = st.selectbox("Dokument", list(docs.keys()), key="search_doc")
        search_term = st.text_input("Suchbegriff", placeholder="z.B. Basisfallwert, Punktwert, §37...")

        if search_term and st.button("🔍 Suchen", key="search_btn"):
            text = docs[search_doc]["text"]
            lines = text.split("\n")
            matches = [(i, line) for i, line in enumerate(lines) if search_term.lower() in line.lower()]

            if matches:
                st.success(f"**{len(matches)} Treffer** in {search_doc}")
                for i, line in matches[:20]:
                    st.markdown(f"**Zeile {i+1}:** {line.strip()[:200]}")
            else:
                st.warning("Keine Treffer.")

st.markdown("---")
st.caption("⚖️ Vergleich-Agenten | markb.de | SGB V Vergütungsvereinbarungen")
