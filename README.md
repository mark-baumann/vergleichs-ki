# ⚖️ Vergleichs-KI — Dokumentenvergleich SGB V

[![Python](https://img.shields.io/badge/Python-3.12+-blue?logo=python)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.40+-red?logo=streamlit)](https://streamlit.io)
[![PyMuPDF](https://img.shields.io/badge/PDF-PyMuPDF-orange)](https://pymupdf.readthedocs.io)
[![Deployed](https://img.shields.io/badge/Deployed-vergleichs--ki.markb.de-brightgreen)](https://vergleichs-ki.markb.de)

**Automatischer Vergleich von Vergütungsvereinbarungen nach SGB V.** Lädt PDFs, extrahiert Text, findet Unterschiede in Beträgen, Paragraphen und Begriffen — live per Streamlit.

---

## ✨ Features

- **📄 PDF-Verarbeitung:** Automatische Textextraktion mit PyMuPDF (fitz)
- **⚖️ Side-by-Side-Vergleich:** Zwei Dokumente auswählen und Unterschiede sofort sehen
- **💰 Betrags-Analyse:** Neue, entfernte und geänderte Euro-Beträge automatisch erkennen
- **📜 Paragraphen-Tracking:** Welche Paragraphen wurden hinzugefügt oder gestrichen?
- **🔤 Begriffs-Diff:** Neue und entfernte Fachbegriffe im Vergleich
- **🔍 Detailsuche:** Gezielte Volltextsuche mit Zeilennummern
- **📤 PDF-Upload:** Eigene PDFs hochladen und vergleichen

---

## 🚀 Installation

```bash
git clone https://github.com/mark-baumann/vergleichs-ki.git
cd vergleichs-ki
python3 -m venv .venv && source .venv/bin/activate
pip install streamlit pymupdf
```

---

## 🖥️ Nutzung

```bash
streamlit run app.py
```

Die App läuft auf **Port 8501** und ist deployed unter [vergleichs-ki.markb.de](https://vergleichs-ki.markb.de).

### Workflow

1. **Dokumente laden:** PDFs aus `/opt/data/Vergütungsvereinbarungen/` oder per Upload
2. **Vergleichen:** Dokument A und B auswählen → „Jetzt vergleichen"
3. **Ergebnisse analysieren:** Betrags-Änderungen, neue/entfernte Paragraphen, Begriffs-Diff
4. **Detailsuche:** Gezielt nach „Basisfallwert", „Punktwert", „§37" etc. suchen

---

## 🧱 Tech-Stack

| Komponente | Technologie |
|---|---|
| **Frontend** | Streamlit |
| **PDF** | PyMuPDF (fitz) |
| **Textanalyse** | Python Regex, Collections |
| **Sprache** | Python 3.12+ |

---

## 📁 Projektstruktur

```
vergleichs-ki/
├── app.py                    # Streamlit-App (203 Zeilen)
└── .venv/                    # Virtuelle Umgebung
```

---

## 👤 Autor

**Mark Baumann** — [GitHub](https://github.com/mark-baumann) · [markb.de](https://markb.de)
