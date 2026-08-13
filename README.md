# ⚖️ Vergleichs-KI — Dokumentenvergleich SGB V

[![Python](https://img.shields.io/badge/Python-3.12+-blue?logo=python)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.40+-red?logo=streamlit)](https://streamlit.io)
[![PyMuPDF](https://img.shields.io/badge/PDF-PyMuPDF-orange)](https://pymupdf.readthedocs.io)
[![Deployed](https://img.shields.io/badge/Deployed-vergleichs--ki.markb.de-brightgreen)](https://vergleichs-ki.markb.de)

**Automatischer Vergleich von Vergütungsvereinbarungen nach SGB V.** Lädt PDFs, extrahiert Text, findet Unterschiede deterministisch per String-Vergleich und Levenshtein-Distanz in Textblöcken, Beträgen, Paragraphen und Begriffen — live per Streamlit. Eine KI-Zusammenfassung kann optional nachgelagert über die bereits berechneten Unterschiede laufen.

---

## ✨ Features

- **📄 PDF-Verarbeitung:** Automatische Textextraktion mit PyMuPDF (fitz)
- **⚖️ Side-by-Side-Vergleich:** Zwei Dokumente auswählen und Unterschiede sofort sehen
- **💰 Betrags-Analyse:** Neue, entfernte und geänderte Euro-Beträge automatisch erkennen
- **📜 Paragraphen-Tracking:** Welche Paragraphen wurden hinzugefügt oder gestrichen?
- **🔤 Begriffs-Diff:** Neue und entfernte Fachbegriffe im Vergleich
- **🔍 Detailsuche:** Gezielte Volltextsuche mit Zeilennummern
- **📤 Persistenter Mehrfach-PDF-Upload:** Zwei oder mehr eigene PDFs hochladen, dauerhaft im PDF-Ordner speichern und direkt vergleichen
- **🧮 Deterministischer Text-Diff:** String-Vergleich von Textblöcken inklusive Levenshtein-Distanz vor jeder KI-Auswertung
- **🤖 Optionale KI-Zusammenfassung:** KI fasst nur die deterministisch gefundenen Unterschiede zusammen, wenn `OPENAI_API_KEY` gesetzt ist
- **💡 Suchvorschläge:** Detailsuche zeigt häufige Fachbegriffe und ähnliche Vorschläge

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
streamlit run app/app.py
```

Die App läuft auf **Port 8501** und ist deployed unter [vergleichs-ki.markb.de](https://vergleichs-ki.markb.de).

### Workflow

1. **Dokumente laden:** PDFs rekursiv aus `/opt/data/Vergütungsvereinbarungen/` laden oder mehrere PDFs per Upload dauerhaft unter `_uploads/` speichern
2. **Vergleichen:** Dokument A und B auswählen → „Deterministisch vergleichen"
3. **Ergebnisse analysieren:** Levenshtein-Distanz, geänderte Textblöcke, neue/entfernte Beträge und Paragraphen prüfen
4. **Optional KI nutzen:** Nur bei gesetztem `OPENAI_API_KEY` eine Zusammenfassung der deterministischen Unterschiede erzeugen
5. **Detailsuche:** Vorschläge nutzen und gezielt nach „Basisfallwert", „Punktwert", „§37" etc. suchen

---

## 🧱 Tech-Stack

| Komponente | Technologie |
|---|---|
| **Frontend** | Streamlit |
| **PDF** | PyMuPDF (fitz) |
| **Textanalyse** | Python Regex, difflib, Levenshtein-Distanz |
| **KI optional** | OpenAI API nach deterministischem Vergleich |
| **Sprache** | Python 3.12+ |

---

## 📁 Projektstruktur

```
vergleichs-ki/
├── app/app.py                # Streamlit-App
└── .venv/                    # Virtuelle Umgebung
```

---

## 👤 Autor

**Mark Baumann** — [GitHub](https://github.com/mark-baumann) · [markb.de](https://markb.de)
