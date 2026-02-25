# PDF Anonymizer

KI-gestütztes Tool zur automatischen Anonymisierung personenbezogener Daten in PDF-Dokumenten.

## Funktionsweise

1. **Programm starten** – `PDFAnonymizer.exe` (Windows) oder `python src/main.py`
2. **API-Key hinterlegen** – Über ⚙ Einstellungen den Key für OpenAI, Anthropic oder Google Gemini eingeben
3. **PDF laden** – Per Drag & Drop oder über „PDF auswählen"
4. **Speicherort wählen** – Das anonymisierte PDF wird dort abgelegt
5. **Fertig** – Das Tool erkennt automatisch alle PII-Daten und ersetzt sie

## Was wird anonymisiert?

| Kategorie | Beispiel | Variable |
|---|---|---|
| Vornamen | Max → | `VBX01` |
| Nachnamen | Mustermann → | `VBX02` |
| Straßen | Musterstraße → | `VBX03` |
| Hausnummern | 42 → | `VBX04` |
| Städte | Berlin → | `VBX05` |
| Postleitzahlen | 10115 → | `VBX06` |
| Kontonummern / IBAN | DE89 3704 ... → | `VBX07` |
| E-Mail-Adressen | max@example.com → | `VBX08` |
| Krypto-Adressen | 1A1zP1... → | `VBX09` |
| Unternehmensnamen | Muster GmbH → | `VBX10` |
| Grundstücksangaben | Flur 3, Flurstück 42 → | `VBX11` |
| Telefonnummern | +49 30 12345 → | `VBX12` |
| Geburtsdaten | 01.01.1990 → | `VBX13` |
| Steuernummern | DE123456789 → | `VBX14` |

Gleiche Entitäten erhalten immer dieselbe Variable (z. B. „Max" ist überall `VBX01`).

Die anonymisierten Stellen werden **türkis** überdeckt, die Variable wird in weißer Schrift darauf angezeigt.

## Voraussetzungen

- **Das PDF muss bereits Texterkennung (OCR) enthalten.** Gescannte Bilder ohne eingebetteten Text können nicht verarbeitet werden.
- Ein gültiger API-Key für mindestens einen der unterstützten KI-Anbieter:
  - **OpenAI** (ChatGPT) – `sk-...`
  - **Anthropic** (Claude) – `sk-ant-...`
  - **Google Gemini** – `AI...`

## Installation & Build (Windows EXE)

### Voraussetzungen

- Python 3.10 oder neuer
- pip

### Schritte

```bash
# 1. Abhängigkeiten installieren
pip install -r requirements.txt

# 2. Direkt starten (ohne Build)
python src/main.py

# 3. Oder als EXE bauen
build.bat
# Ergebnis: dist\PDFAnonymizer\PDFAnonymizer.exe
```

### Alternativ mit PyInstaller direkt

```bash
pip install -r requirements.txt
pyinstaller build.spec
```

## Unterstützte KI-Anbieter

| Anbieter | Modell | Kosten |
|---|---|---|
| OpenAI | GPT-4o | nach Verbrauch |
| Anthropic | Claude Sonnet | nach Verbrauch |
| Google | Gemini 2.0 Flash | nach Verbrauch |

## Datenschutz

Der Text des PDFs wird an den gewählten KI-Anbieter gesendet, um die personenbezogenen Daten zu erkennen. Stellen Sie sicher, dass dies mit Ihren Datenschutzanforderungen vereinbar ist.
