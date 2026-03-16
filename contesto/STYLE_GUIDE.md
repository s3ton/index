# Guida di Stile

## Python Naming Conventions
- **Classi**: PascalCase (es. `VolMktCapStrategy`).
- **Metodi/Variabili**: snake_case (es. `calculate_stats`).
- **Cartelle**: snake_case (es. `market_analytics`).

## Palette Colori Aziendale (Plotly)
- **Bitcoin (Benchmark)**: `#F7931A` (Arancione BTC).
- **Strategia Principale**: `#1f77b4` (Blu).
- **Linee di Ribilanciamento**: Verde con opacità 0.6, stile tratteggiato.
- **Heatmap**: Scala personalizzata da `#04114f` (Min) a `#ffffff` (Max).

## Requisiti dei Grafici
1. **Performance**: Deve sempre includere il confronto con il benchmark (BTC-USD).
2. **Pesi**: Utilizzare `stackgroup='one'` per i grafici di allocazione.
3. **Metrics**: Il file `metrics.json` deve essere generato per ogni strategia con le variazioni 24h, 7d e YTD.