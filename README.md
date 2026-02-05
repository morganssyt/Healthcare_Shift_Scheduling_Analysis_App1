# Pianificazione Turni - Croce Rossa

App web per generare la turnazione del personale sanitario su 5 settimane, con confronto scenari e export in più formati.

![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-red.svg)
![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

---

## Cosa fa

- **Genera turnazioni** rispettando vincoli (ore contrattuali, giorni consecutivi, riposo dopo notte)
- **Bilancia automaticamente** il carico tra dipendenti (mattini, pomeriggi, domeniche, notti)
- **Confronta scenari**: staff attuale vs. aggiunta di un nuovo dipendente (PT 28h o FT 38h)
- **Esporta** in CSV, Excel e PDF stampabile
- **Segnala carenze**: evidenzia quando serve "Volontario esperto" o turni scoperti

---

## Quick Start

```bash
cd rotazione_turni
pip install -r requirements.txt
streamlit run app.py
```

L'app si apre nel browser su `http://localhost:8501`

---

## Come usarlo

### 1. Configura

**Sidebar (sinistra):**
- Data inizio (deve essere un lunedì)
- Toggle "Usa Volontario esperto" (default ON)
- Toggle "Notte attiva" + giorni e minimo persone

**Sezione principale:**
- Modifica lo staff nella tabella (nome, ore, disponibilità notte/domenica)
- Imposta i vincoli di copertura (min persone per turno)

### 2. Confronta scenari (opzionale)

Compila "Nuovo dipendente" per generare automaticamente:
- **Versione A**: staff attuale
- **Versione B**: staff + nuovo con ore scelte
- **Versione C**: staff + nuovo con ore alternative (PT vs FT)

### 3. Genera e scarica

Clicca "Genera turnazione" per:
- Vedere la tabella comparativa
- Leggere il testo "Cosa cambia"
- Scaricare CSV/Excel/PDF per ogni versione

---

## Struttura progetto

```
├── app.py              # App Streamlit principale
├── core/
│   ├── __init__.py
│   ├── scheduler.py    # Algoritmo di scheduling
│   ├── exporters.py    # Export CSV, Excel, PDF
│   └── utils.py        # Validazioni e helpers
├── requirements.txt    # Dipendenze Python
└── README.md           # Questo file
```

---

## Regole di scheduling

| Regola | Descrizione |
|--------|-------------|
| Max 1 turno/giorno | Nessuno lavora mattino E pomeriggio lo stesso giorno |
| Max giorni consecutivi | Default 6, configurabile |
| Limite ore settimanali | Non si superano le ore contrattuali |
| Riposo dopo notte | Chi fa notte non lavora il giorno dopo |
| Domenica | Solo chi è disponibile |
| Notte | Solo chi è abilitato |

---

## Algoritmo di bilanciamento

Lo scheduler usa uno **scoring system** per scegliere chi assegnare:

1. Chi ha meno ore totali → priorità alta
2. Chi ha meno ore questa settimana → priorità
3. Chi ha meno turni di quel tipo (mattino/pomeriggio) → equilibrio
4. Chi ha meno domeniche → distribuzione equa
5. Penalità se vicino al limite consecutivi
6. Leggera penalità se ha lavorato ieri (alternanza)

---

## Deploy su Streamlit Community Cloud

### Preparazione repository

1. **Crea un repo GitHub** (pubblico o privato)

2. **Carica questi file**:
   ```
   app.py
   requirements.txt
   core/
   ├── __init__.py
   ├── scheduler.py
   ├── exporters.py
   └── utils.py
   ```

3. **Verifica requirements.txt**:
   ```
   streamlit>=1.30.0
   pandas>=2.0.0
   openpyxl>=3.1.0
   reportlab>=4.0.0
   ```

### Deploy

1. Vai su [share.streamlit.io](https://share.streamlit.io)
2. Accedi con GitHub
3. Clicca "New app"
4. Seleziona:
   - Repository: `tuouser/rotazione-turni`
   - Branch: `main`
   - Main file path: `app.py`
5. Clicca "Deploy"

Streamlit rileva automaticamente `app.py` e `requirements.txt`.

### Note importanti per il cloud

- **Nessun file locale**: l'app usa solo memoria (BytesIO), non scrive su disco
- **Nessun database**: tutto è calcolato on-the-fly
- **Session state**: i dati persistono solo durante la sessione browser
- **File temporanei**: gli export usano buffer in memoria, compatibili con il cloud

### Test locale prima del deploy

```bash
# Installa dipendenze
pip install -r requirements.txt

# Avvia in modalità "produzione"
streamlit run app.py --server.headless true

# Verifica che funzioni su http://localhost:8501
```

### Errori comuni e fix

| Errore | Causa | Soluzione |
|--------|-------|-----------|
| `ModuleNotFoundError: openpyxl` | Manca in requirements.txt | Aggiungi `openpyxl>=3.1.0` |
| `ModuleNotFoundError: reportlab` | Manca in requirements.txt | Aggiungi `reportlab>=4.0.0` |
| `No module named 'core'` | Struttura cartelle sbagliata | Verifica che `core/` sia nella root |
| App non si avvia | File path sbagliato | Main file deve essere `app.py` |
| Crash su download | Scrittura su disco | Usa solo BytesIO (già implementato) |

### URL finale

Dopo il deploy, l'app sarà disponibile su:
```
https://tuouser-rotazione-turni-app-xxxxx.streamlit.app
```

---

## Screenshot suggeriti

Per documentazione/portfolio, cattura:

1. **Schermata principale** con staff e vincoli
2. **Tabella comparativa** dopo generazione
3. **Sezione "Cosa cambia"** con raccomandazione
4. **Tab dettaglio** con calendario settimanale
5. **PDF esportato** (screenshot della prima pagina)

---

## Crediti

Sviluppato per Croce Rossa - Sistema Pianificazione Turni

**Tecnologie**: Python, Streamlit, Pandas, ReportLab, OpenPyXL

**Autore**: Morgan Germinario

---

*Ultimo aggiornamento: Febbraio 2026*
