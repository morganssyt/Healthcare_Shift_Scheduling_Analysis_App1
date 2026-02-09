# Come si usa il sistema

## Panoramica

Il sistema di pianificazione turni è un'applicazione web che permette di generare, visualizzare e confrontare pianificazioni dei turni. Non servono competenze tecniche per usarlo: basta aprirlo nel browser e seguire i passaggi.

---

## Avvio

1. Aprire il terminale (o il prompt dei comandi)
2. Navigare nella cartella del progetto
3. Lanciare il comando:
   ```
   streamlit run app.py
   ```
4. Si apre automaticamente una pagina nel browser

---

## Cosa si trova nell'interfaccia

### Dati di partenza
Il sistema carica automaticamente:
- **Lista dipendenti** con tipo di contratto e ore settimanali
- **Definizione turni** (mattino 07:00–14:00, pomeriggio 14:00–21:00)
- **Domanda di copertura** per ogni giorno della settimana

Questi dati si trovano nella cartella `data/` e possono essere modificati prima dell'avvio.

### Generazione della pianificazione
- Il sistema costruisce la pianificazione rispettando tutti i vincoli operativi
- Mostra il risultato in formato tabellare (chi lavora dove e quando)
- Evidenzia eventuali turni scoperti

### Confronto scenari
- Si può confrontare lo scenario base (5 dipendenti) con scenari alternativi (es. +1 full-time)
- Per ogni scenario si vedono: copertura percentuale, ore utilizzate, turni scoperti

### Report e grafici
- Grafici a barre: ore lavorate vs. ore contrattuali per dipendente
- Distribuzione weekend: quanti weekend lavora ciascuno
- Heatmap calendario: visione d'insieme su 5 settimane
- Confronto capacità tra scenari

---

## Come modificare i dati

### Aggiungere un dipendente
Aprire il file `data/employees.csv` e aggiungere una riga:
```
Nome Cognome,full_time,38
```
oppure per un part-time:
```
Nome Cognome,part_time,28
```

### Cambiare la copertura richiesta
Aprire il file `data/demand.csv` e modificare il numero di persone richieste per turno e giorno.

### Cambiare il periodo
Aggiornare il file `data/calendar.csv` con le nuove date e i numeri di settimana corrispondenti.

---

## Esportazione risultati

Il sistema produce automaticamente:
- **File CSV** nella cartella `output/` (pianificazione, KPI, analisi copertura)
- **Grafici PNG** nella cartella `figures/` (pronti per presentazioni o stampa)
- **Report PDF** generabile dallo script `scripts/generate_pdf.py`

---

## In caso di problemi

| Problema | Cosa fare |
|----------|-----------|
| L'applicazione non si avvia | Verificare che Python e Streamlit siano installati |
| I dati non si caricano | Controllare che i file CSV nella cartella `data/` siano presenti e formattati correttamente |
| La pianificazione ha buchi | È normale se l'organico è insufficiente — confrontare con lo scenario +1 dipendente |
| I grafici non si generano | Verificare che la cartella `figures/` esista |
