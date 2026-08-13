"""
Vergleichs-KI — Dokumente vergleichen & analysieren
====================================================
Vergleicht Vergütungsvereinbarungen (SGB V) deterministisch auf Textunterschiede.
Optional kann danach eine KI-Zusammenfassung über die bereits ermittelten Unterschiede laufen.
"""

import difflib
import json
import os
import re
import tempfile
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="Vergleichs-KI", page_icon="⚖️", layout="wide")

DEFAULT_PDF_DIR = "/opt/data/Vergütungsvereinbarungen"
MAX_DIFF_ITEMS = 80


# ── Text-Normalisierung & deterministische Metriken ──────────────────────────
def normalize_text(text: str) -> str:
    """Macht PDF-Text vergleichbarer, ohne Inhalte semantisch zu verändern."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_units(text: str) -> list[str]:
    """Teilt Text in stabile Vergleichseinheiten (Absätze, notfalls Zeilen)."""
    normalized = normalize_text(text)
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", normalized) if p.strip()]
    if len(paragraphs) < 2:
        paragraphs = [line.strip() for line in normalized.split("\n") if line.strip()]
    return paragraphs


def levenshtein_distance(a: str, b: str) -> int:
    """Berechnet die Levenshtein-Distanz deterministisch mit O(min(n,m)) Speicher."""
    if a == b:
        return 0
    if len(a) < len(b):
        a, b = b, a
    previous = list(range(len(b) + 1))
    for i, char_a in enumerate(a, start=1):
        current = [i]
        for j, char_b in enumerate(b, start=1):
            insert = current[j - 1] + 1
            delete = previous[j] + 1
            replace = previous[j - 1] + (char_a != char_b)
            current.append(min(insert, delete, replace))
        previous = current
    return previous[-1]


def similarity_ratio(a: str, b: str) -> float:
    if not a and not b:
        return 1.0
    max_len = max(len(a), len(b), 1)
    return 1 - (levenshtein_distance(a, b) / max_len)


# ── PDF-Text extrahieren ─────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def extract_pdf_texts(pdf_dir: str) -> dict:
    import fitz

    docs = {}
    pdf_path = Path(pdf_dir)
    if not pdf_path.exists():
        return docs

    # Rekursiv suchen, damit gemountete Unterordner ebenfalls angezeigt werden.
    for pdf_file in sorted(pdf_path.rglob("*.pdf"), key=lambda p: str(p).lower()):
        try:
            doc = fitz.open(pdf_file)
            text = "".join(page.get_text() for page in doc)
            display_name = str(pdf_file.relative_to(pdf_path))
            docs[display_name] = {
                "text": normalize_text(text),
                "pages": len(doc),
                "source": str(pdf_file),
            }
            doc.close()
        except Exception as e:
            docs[pdf_file.name] = {"text": f"FEHLER: {e}", "pages": 0, "source": str(pdf_file)}
    return docs


def extract_uploaded_pdf(uploaded_file) -> dict:
    import fitz

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.getvalue())
        tmp_path = tmp.name
    try:
        doc = fitz.open(tmp_path)
        text = "".join(page.get_text() for page in doc)
        pages = len(doc)
        doc.close()
        return {"text": normalize_text(text), "pages": pages, "source": "Upload"}
    finally:
        Path(tmp_path).unlink(missing_ok=True)


# ── Differenz-Analyse ───────────────────────────────────────────────────────
def find_amounts(text: str) -> set[str]:
    amount_pattern = r"(?:EUR\s*)?\d{1,3}(?:\.\d{3})*(?:,\d{2})\s*(?:€|Euro)?|\d+[.,]\d{2}\s*(?:€|Euro)"
    return {match.strip() for match in re.findall(amount_pattern, text, flags=re.IGNORECASE) if re.search(r"\d", match)}


def build_deterministic_diff(text_a: str, text_b: str) -> dict:
    units_a = split_units(text_a)
    units_b = split_units(text_b)
    matcher = difflib.SequenceMatcher(a=units_a, b=units_b, autojunk=False)

    inserted, removed, changed = [], [], []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        if tag == "delete":
            removed.extend({"index_a": i + 1, "text": units_a[i]} for i in range(i1, i2))
        elif tag == "insert":
            inserted.extend({"index_b": j + 1, "text": units_b[j]} for j in range(j1, j2))
        elif tag == "replace":
            block_a = units_a[i1:i2]
            block_b = units_b[j1:j2]
            for offset in range(max(len(block_a), len(block_b))):
                old = block_a[offset] if offset < len(block_a) else ""
                new = block_b[offset] if offset < len(block_b) else ""
                changed.append({
                    "index_a": i1 + offset + 1 if old else None,
                    "index_b": j1 + offset + 1 if new else None,
                    "old": old,
                    "new": new,
                    "levenshtein": levenshtein_distance(old, new),
                    "similarity": similarity_ratio(old, new),
                })

    words_a = set(re.findall(r"\b\w{4,}\b", text_a.lower()))
    words_b = set(re.findall(r"\b\w{4,}\b", text_b.lower()))
    paragraphs_a = set(re.findall(r"§\s*\d+[a-z]?", text_a, flags=re.IGNORECASE))
    paragraphs_b = set(re.findall(r"§\s*\d+[a-z]?", text_b, flags=re.IGNORECASE))
    amounts_a = find_amounts(text_a)
    amounts_b = find_amounts(text_b)

    aggregate_distance = sum(item["levenshtein"] for item in changed)
    aggregate_distance += sum(len(item["text"]) for item in inserted + removed)
    aggregate_length = max(len(text_a), len(text_b), 1)

    return {
        "units_a": len(units_a),
        "units_b": len(units_b),
        "len_a": len(text_a),
        "len_b": len(text_b),
        "levenshtein": aggregate_distance,
        "similarity": 1 - min(aggregate_distance / aggregate_length, 1),
        "inserted": inserted,
        "removed": removed,
        "changed": changed,
        "only_a": words_a - words_b,
        "only_b": words_b - words_a,
        "new_amounts": amounts_b - amounts_a,
        "removed_amounts": amounts_a - amounts_b,
        "common_amounts": amounts_a & amounts_b,
        "new_paragraphs": paragraphs_b - paragraphs_a,
        "removed_paragraphs": paragraphs_a - paragraphs_b,
        "common_paragraphs": paragraphs_a & paragraphs_b,
    }


def build_search_suggestions(docs: dict, query: str = "") -> list[str]:
    words = []
    domain_terms = ["basisfallwert", "punktwert", "vergütung", "entgelt", "pauschale", "anlage", "laufzeit", "kündigung", "§"]
    for data in docs.values():
        words.extend(re.findall(r"\b[A-Za-zÄÖÜäöüß][\wÄÖÜäöüß-]{4,}\b", data["text"].lower()))
    from collections import Counter

    frequent = [word for word, _ in Counter(words).most_common(40)]
    candidates = list(dict.fromkeys(domain_terms + frequent))
    if query:
        close = difflib.get_close_matches(query.lower(), candidates, n=10, cutoff=0.25)
        contains = [term for term in candidates if query.lower() in term]
        return list(dict.fromkeys(contains + close))[:10]
    return candidates[:12]


def render_diff_item(item: dict, index: int):
    title = f"Änderung {index} · Levenshtein {item['levenshtein']} · Ähnlichkeit {item['similarity']:.1%}"
    with st.expander(title):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Alt (Einheit {item['index_a']})**")
            st.code(item["old"][:3000])
        with col2:
            st.markdown(f"**Neu (Einheit {item['index_b']})**")
            st.code(item["new"][:3000])


def summarize_with_ai(diff_payload: dict) -> str:
    """Fasst deterministisch gefundene Unterschiede optional mit OpenAI zusammen."""
    from openai import OpenAI

    client = OpenAI()
    compact = {
        "dokument_a": diff_payload["doc_a"],
        "dokument_b": diff_payload["doc_b"],
        "kennzahlen": {
            "levenshtein": diff_payload["result"]["levenshtein"],
            "similarity": diff_payload["result"]["similarity"],
            "changed_blocks": len(diff_payload["result"]["changed"]),
            "inserted_blocks": len(diff_payload["result"]["inserted"]),
            "removed_blocks": len(diff_payload["result"]["removed"]),
            "new_amounts": sorted(diff_payload["result"]["new_amounts"]),
            "removed_amounts": sorted(diff_payload["result"]["removed_amounts"]),
            "new_paragraphs": sorted(diff_payload["result"]["new_paragraphs"]),
            "removed_paragraphs": sorted(diff_payload["result"]["removed_paragraphs"]),
        },
        "beispiel_aenderungen": diff_payload["result"]["changed"][:12],
        "neue_textbloecke": diff_payload["result"]["inserted"][:8],
        "entfernte_textbloecke": diff_payload["result"]["removed"][:8],
    }
    response = client.responses.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        input=(
            "Du bist eine Vergleichs-KI für deutsche Vergütungsvereinbarungen. "
            "Fasse ausschließlich die folgenden deterministisch berechneten Unterschiede zusammen. "
            "Kennzeichne Beträge, Paragraphen, Laufzeiten und materielle Änderungen.\n\n"
            + json.dumps(compact, ensure_ascii=False)
        ),
    )
    return response.output_text


# ── Haupt-App ────────────────────────────────────────────────────────────────
st.title("⚖️ Vergleichs-KI")
st.caption("Deterministischer Vergleich von Vergütungsvereinbarungen — KI optional nachgelagert")

pdf_dir = st.sidebar.text_input("PDF-Ordner", value=os.getenv("PDF_DIR", DEFAULT_PDF_DIR))
if st.sidebar.button("🔄 PDF-Ordner neu einlesen"):
    extract_pdf_texts.clear()

if "uploaded_docs" not in st.session_state:
    st.session_state.uploaded_docs = {}

docs = {**extract_pdf_texts(pdf_dir), **st.session_state.uploaded_docs}

tab1, tab2, tab3 = st.tabs(["📊 Vergleich", "📄 Dokumente", "🔍 Detailsuche"])

with tab1:
    st.subheader("📊 Zwei Vergütungsvereinbarungen vergleichen")
    if len(docs) >= 2:
        doc_names = list(docs.keys())
        col1, col2 = st.columns(2)
        with col1:
            doc_a = st.selectbox("Dokument A", doc_names, key="doc_a")
        with col2:
            doc_b = st.selectbox("Dokument B", doc_names, index=min(1, len(doc_names) - 1), key="doc_b")

        if doc_a == doc_b:
            st.info("Bitte zwei unterschiedliche Dokumente auswählen.")
        elif st.button("⚖️ Deterministisch vergleichen", type="primary", use_container_width=True):
            result = build_deterministic_diff(docs[doc_a]["text"], docs[doc_b]["text"])
            st.session_state.last_diff = {"doc_a": doc_a, "doc_b": doc_b, "result": result}

        if "last_diff" in st.session_state:
            result = st.session_state.last_diff["result"]
            st.markdown("### 📊 Deterministische Übersicht")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Levenshtein-Distanz (Blöcke)", f"{result['levenshtein']:,}")
            col2.metric("Textähnlichkeit", f"{result['similarity']:.1%}")
            col3.metric("Geänderte Textblöcke", len(result["changed"]))
            col4.metric("Neu/Entfernt", f"{len(result['inserted'])}/{len(result['removed'])}")

            st.markdown("---")
            st.subheader("💰 Beträge & 📜 Paragraphen")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Neue Beträge", len(result["new_amounts"]))
            col2.metric("Entfernte Beträge", len(result["removed_amounts"]))
            col3.metric("Neue Paragraphen", len(result["new_paragraphs"]))
            col4.metric("Entfernte Paragraphen", len(result["removed_paragraphs"]))
            if result["new_amounts"]:
                st.info("Neue Beträge: " + ", ".join(sorted(result["new_amounts"])[:25]))
            if result["removed_amounts"]:
                st.warning("Entfernte Beträge: " + ", ".join(sorted(result["removed_amounts"])[:25]))

            st.markdown("---")
            st.subheader("🧾 Textunterschiede per String-Vergleich")
            for idx, item in enumerate(result["changed"][:MAX_DIFF_ITEMS], start=1):
                render_diff_item(item, idx)
            if result["inserted"]:
                with st.expander(f"🆕 Neue Textblöcke ({len(result['inserted'])})"):
                    for item in result["inserted"][:MAX_DIFF_ITEMS]:
                        st.markdown(f"**Neu Einheit {item['index_b']}**")
                        st.code(item["text"][:2000])
            if result["removed"]:
                with st.expander(f"🗑️ Entfernte Textblöcke ({len(result['removed'])})"):
                    for item in result["removed"][:MAX_DIFF_ITEMS]:
                        st.markdown(f"**Alt Einheit {item['index_a']}**")
                        st.code(item["text"][:2000])

            with st.expander("🤖 KI-Zusammenfassung optional nach deterministischem Vergleich"):
                st.write("Die KI ist bewusst nachgelagert: Grundlage sind ausschließlich die oben berechneten Unterschiede.")
                if os.getenv("OPENAI_API_KEY"):
                    if st.button("🤖 KI-Zusammenfassung erzeugen"):
                        with st.spinner("KI fasst deterministische Unterschiede zusammen …"):
                            st.markdown(summarize_with_ai(st.session_state.last_diff))
                else:
                    st.warning("OPENAI_API_KEY ist nicht gesetzt. Der deterministische Vergleich funktioniert weiterhin ohne KI.")
    else:
        st.warning(f"Mindestens 2 PDFs nötig. Aktueller Ordner: {pdf_dir}")

with tab2:
    st.subheader("📄 Verfügbare Dokumente")
    st.caption(f"Quelle: {pdf_dir} — rekursive PDF-Suche inklusive Unterordner")

    uploaded = st.file_uploader("Eine oder mehrere PDFs zum Vergleich hochladen", type="pdf", accept_multiple_files=True)
    if uploaded:
        for file in uploaded:
            st.session_state.uploaded_docs[f"Upload/{file.name}"] = extract_uploaded_pdf(file)
        st.success(f"✅ {len(uploaded)} PDF(s) geladen. Sie können jetzt im Vergleich ausgewählt werden.")
        docs = {**extract_pdf_texts(pdf_dir), **st.session_state.uploaded_docs}

    if docs:
        for name, data in docs.items():
            with st.expander(f"📄 {name} ({data['pages']} Seiten, {len(data['text']):,} Zeichen)"):
                st.caption(data.get("source", ""))
                st.text_area("Volltext", data["text"][:3000], height=250, key=f"text_{hash(name)}")
    else:
        st.warning(f"Keine PDFs in {pdf_dir}. Prüfen Sie den gemounteten Ordner oder laden Sie oben zwei PDFs hoch.")

with tab3:
    st.subheader("🔍 Detailsuche mit Vorschlägen")
    if docs:
        suggestions = build_search_suggestions(docs)
        selected_suggestion = st.selectbox("Vorschläge", [""] + suggestions, format_func=lambda x: "Vorschlag wählen …" if x == "" else x)
        search_term = st.text_input("Suchbegriff", value=selected_suggestion, placeholder="z.B. Basisfallwert, Punktwert, §37…")
        if search_term:
            suggested = build_search_suggestions(docs, search_term)
            if suggested:
                st.caption("Ähnliche Vorschläge: " + ", ".join(suggested))
            search_doc = st.selectbox("Dokument", list(docs.keys()), key="search_doc")
            text = docs[search_doc]["text"]
            lines = text.split("\n")
            matches = [(i, line) for i, line in enumerate(lines) if search_term.lower() in line.lower()]
            if matches:
                st.success(f"**{len(matches)} Treffer** in {search_doc}")
                for i, line in matches[:30]:
                    st.markdown(f"**Zeile {i + 1}:** {line.strip()[:300]}")
            else:
                st.warning("Keine Treffer. Nutzen Sie die Vorschläge oder probieren Sie einen kürzeren Suchbegriff.")
    else:
        st.info("Für die Detailsuche bitte zuerst PDFs bereitstellen oder hochladen.")

st.markdown("---")
st.caption("⚖️ Vergleichs-KI | markb.de | SGB V Vergütungsvereinbarungen")
