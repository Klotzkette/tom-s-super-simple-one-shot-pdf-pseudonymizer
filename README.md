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

## LM Studio einrichten – Schritt für Schritt

### Schritt 1 – LM Studio installieren

[LM Studio herunterladen](https://lmstudio.ai/) und installieren (Windows, macOS oder Linux).

---

### Schritt 2 – Qwen-Modell herunterladen

1. LM Studio öffnen
2. Oben auf **„Search"** (Lupe) klicken
3. In die Suchleiste **`Qwen3`** eingeben
4. Ein Modell auswählen – Empfehlung je nach verfügbarem RAM/VRAM:

| Modell (Suchbegriff in LM Studio) | RAM/VRAM | Qualität |
|---|---|---|
| `Qwen3-14B` | ~10 GB | Sehr gut |
| `Qwen3-8B` | ~6 GB | Gut |
| `Qwen3-4B` | ~3 GB | Ausreichend |

5. Auf **„Download"** klicken und warten bis der Download abgeschlossen ist

> **Tipp:** Wenn kein Qwen3 verfügbar ist, funktioniert auch `Qwen2.5-7B-Instruct` oder `Qwen2.5-14B-Instruct`.

---

### Schritt 3 – Modell in LM Studio laden

1. Im linken Menü auf **„My Models"** (oder „Chat") klicken
2. Das heruntergeladene Qwen-Modell auswählen und auf **„Load"** klicken
3. Warten bis das Modell vollständig geladen ist (Statusanzeige unten)

---

### Schritt 4 – Lokalen API-Server starten

1. Im linken Menü auf **„Local Server"** klicken (Symbol: `<->` oder „Developer")
2. Sicherstellen dass der Port auf **`1234`** eingestellt ist
3. Auf **„Start Server"** klicken
4. Der Server läuft, wenn unten grün **„Server running"** erscheint

Der Server ist jetzt erreichbar unter: `http://127.0.0.1:1234/v1`

> **Wichtig:** LM Studio muss laufen und das Modell geladen sein, **bevor** Sie ein PDF verarbeiten.

---

### Schritt 5 – Modellnamen herausfinden

Der exakte Modellname wird im PDF-Anonymizer benötigt. So finden Sie ihn:

- In LM Studio: Unter „Local Server" sehen Sie unter **„Model loaded"** den genauen Modellnamen
- Alternativ: `http://127.0.0.1:1234/v1/models` im Browser öffnen → dort steht der `id`-Wert

Typische Modellnamen:
```
qwen3-14b
qwen3-8b
qwen2.5-7b-instruct
lmstudio-community/Qwen3-14B-GGUF
```

---

### Schritt 6 – PDF-Anonymizer konfigurieren

1. PDF-Anonymizer starten
2. Oben rechts auf **⚙ Einstellungen** klicken
3. Folgendes eintragen:
   - **Base URL**: `http://127.0.0.1:1234/v1` (Standardwert, normalerweise unverändert lassen)
   - **Modellname**: den exakten Namen aus Schritt 5 (z. B. `qwen3-14b`)
4. Auf **✓ Speichern** klicken

Fertig – jetzt können Sie PDFs per Drag & Drop anonymisieren.

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
