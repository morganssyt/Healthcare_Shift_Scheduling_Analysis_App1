# Domande Frequenti

---

### Il sistema decide al posto mio chi lavora e quando?

No. Il sistema propone una pianificazione che rispetta tutte le regole (ore contrattuali, giorni consecutivi, copertura minima). La decisione finale resta sempre del coordinatore, che può modificare manualmente il risultato.

---

### Posso cambiare un turno dopo che la pianificazione è stata generata?

Sì. La pianificazione è un punto di partenza, non un documento vincolante. Se serve uno scambio tra colleghi o una modifica dell'ultimo minuto, il coordinatore può intervenire. L'importante è che la modifica non crei buchi nella copertura.

---

### Come fa il sistema a sapere quante persone servono ogni giorno?

Lo legge dal file `demand.csv`, dove per ogni giorno e ogni turno è indicato il numero minimo di persone richieste. Attualmente: 2 persone mattino + 2 pomeriggio dal lunedì al sabato, 1 persona la domenica mattina.

---

### Perché le ore lavorate sono inferiori a quelle del contratto?

Perché il sistema deve rispettare contemporaneamente più vincoli: non superare i giorni consecutivi, non sovraccaricare i weekend, garantire la copertura minima. Questo porta a un utilizzo delle ore che è inferiore al massimo contrattuale. Con l'organico attuale, il margine è talmente ridotto che non si riesce a distribuire equamente il carico.

---

### Cosa vuol dire "copertura al 92,3%"?

Significa che su 65 posizioni da coprire in 5 settimane (turni × persone richieste), 60 sono coperte e 5 no. Le 5 posizioni scoperte corrispondono alle 5 domeniche mattina.

---

### Perché proprio la domenica è il problema?

Perché la domenica richiede comunque 1 persona al mattino, ma il margine settimanale è già consumato dai turni lunedì-sabato. Con 5 dipendenti e un surplus di sole 25 ore su 875, non c'è spazio per coprire anche la domenica senza violare qualche vincolo.

---

### Se un dipendente si ammala, cosa succede?

Con l'organico attuale (5 persone, surplus 2,9%), anche una singola assenza può creare buchi nella copertura. Con 6 dipendenti (surplus 24,6%), c'è margine sufficiente per assorbire un'assenza senza impatto sui turni.

---

### Il sistema tiene conto delle ferie?

Nella versione attuale, no. I periodi di ferie o indisponibilità vanno gestiti riducendo manualmente le ore disponibili del dipendente o escludendolo dalla pianificazione per le settimane interessate.

---

### Posso usare il sistema per un periodo diverso da 5 settimane?

Sì. Basta aggiornare i file `calendar.csv` e `demand.csv` con le nuove date. Il sistema si adatta alla durata indicata.

---

### Cosa sono gli "scenari"?

Sono simulazioni con organici diversi. Ad esempio: "scenario base" con 5 dipendenti, "scenario +1 full-time" con 6 dipendenti. Ogni scenario mostra la copertura risultante, le ore utilizzate e i turni scoperti. Servono per valutare concretamente l'impatto di un'assunzione.

---

### Il sistema funziona solo per la Croce Rossa?

No. I dati (dipendenti, turni, domanda) sono configurabili. Lo stesso sistema può essere adattato a qualsiasi contesto con turni da coprire: RSA, ambulatori, servizi di emergenza, cooperative.

---

### Chi ha accesso ai dati dei dipendenti?

I dati restano sul computer locale di chi usa il sistema. Non vengono inviati a nessun servizio esterno. L'applicazione funziona interamente in locale.
