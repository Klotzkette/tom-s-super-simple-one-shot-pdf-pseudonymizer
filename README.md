# PDF Anonymizer – LM Studio Edition

KI-gestütztes Tool zur automatischen Anonymisierung personenbezogener Daten in PDF-Dokumenten – **vollständig lokal**, kein Internet erforderlich.

## Funktionsweise

1. **LM Studio starten** – LM Studio öffnen und ein Qwen-Modell laden (z. B. Qwen3-14B)
2. **Server aktivieren** – In LM Studio den lokalen Server starten (Standard: `http://127.0.0.1:1234`)
3. **Programm starten** – `PDFAnonymizer.exe` (Windows) oder `python src/main.py`
4. **Einstellungen prüfen** – Über ⚙ Einstellungen die LM Studio URL und den Modellnamen hinterlegen
5. **PDF laden** – Per Drag & Drop oder über „PDF auswählen"
6. **Speicherort wählen** – Das anonymisierte PDF wird dort abgelegt
7. **Fertig** – Das Tool erkennt automatisch alle PII-Daten und ersetzt sie

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

- **Das PDF muss bereits Texterkennung (OCR) enthalten.** Gescannte Bilder ohne eingebetteten Text können nicht verarbeitet werden (Fallback auf Tesseract OCR möglich).
- **LM Studio** mit einem laufenden lokalen Modell:
  - Empfohlen: **Qwen3-14B** oder neueres Qwen-Modell
  - Standard-URL: `http://127.0.0.1:1234/v1`
  - Kein API-Key erforderlich

## LM Studio einrichten

1. [LM Studio herunterladen](https://lmstudio.ai/) und installieren
2. Ein Qwen3-Modell im Model Hub suchen und herunterladen (z. B. `qwen3-14b`)
3. Das Modell laden und den **lokalen Server starten** (Tab „Local Server" → „Start Server")
4. Im PDF-Anonymizer unter ⚙ Einstellungen:
   - **Base URL**: `http://127.0.0.1:1234/v1`
   - **Modellname**: exakt so wie in LM Studio angezeigt (z. B. `qwen3-14b`)

## Installation & Build (Windows EXE)

### Voraussetzungen

- Python 3.10 oder neuer
- pip
- [LM Studio](https://lmstudio.ai/) mit geladenem Modell

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

## Einstellungen (GUI)

| Einstellung | Beschreibung | Standard |
|---|---|---|
| Base URL | LM Studio Server-Adresse | `http://127.0.0.1:1234/v1` |
| Modellname | Name des geladenen Modells | `qwen3-14b` |

## Unterstützte Modelle

Jedes in LM Studio ladbare Modell mit Chat-Unterstützung funktioniert. Empfehlungen:

| Modell | Qualität | VRAM-Bedarf |
|---|---|---|
| Qwen3-14B | ★★★★★ | ~10 GB |
| Qwen3-8B | ★★★★☆ | ~6 GB |
| Qwen2.5-7B-Instruct | ★★★★☆ | ~5 GB |
| Qwen2.5-14B-Instruct | ★★★★★ | ~10 GB |

## Datenschutz

Der Text des PDFs wird **ausschließlich lokal** verarbeitet. Es findet **keine Übertragung** an externe Server statt. LM Studio läuft vollständig auf Ihrem Gerät.
