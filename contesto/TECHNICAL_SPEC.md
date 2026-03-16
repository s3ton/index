# Specifiche Tecniche

## Architettura del Codice
Il motore di calcolo è basato su OOP in Python:
- **Classe Base (`BaseCryptoStrategy`)**: Gestisce l'importazione dati, il calcolo delle statistiche (Sharpe, Drawdown) e l'esportazione dei grafici in formato JSON.
- **Classi Figlie**: Implementano la logica specifica del backtest nel metodo `run_strategy`.

## Flusso dei Dati
1. **Input**: File JSON in `data/historical/`. Ogni file rappresenta una moneta (es. `btc.json`) con date e prezzi di chiusura.
2. **Processamento**: Pandas per manipolazione serie temporali e calcolo pesi/rendimenti.
3. **Output**: File JSON in `charts/` (suddivisi per categoria: `market_analytics`, `DeFiMktCap_TH`, etc.).

## Standard di Esportazione (Plotly)
- I grafici devono essere salvati tramite `fig.write_json()`.
- Il front-end legge questi file tramite **JavaScript**.
- **Layout**: 
    - Sfondi trasparenti (`paper_bgcolor="rgba(0,0,0,0)"`).
    - Font: Times New Roman o Serif per uniformità aziendale.
    - Hovermode: `x unified`.

## Ottimizzazione
- Minimizzare i cicli `for` sulle righe dei DataFrame (usare logica vettorializzata di Pandas).
- Gestire i dati mancanti con `ffill()` e `dropna()` prima del calcolo dei pesi.