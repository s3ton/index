from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
import yfinance as yf
import os
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import time

# ==========================================
# Genitore
# ==========================================
class BaseCryptoStrategy(ABC):
    """
    Classe genitore che gestisce il recupero dati e le statistiche.
    Le classi figlie devono implementare solo la logica di 'run_strategy' e 
    fornire un proprio metodo `plot_results` per visualizzare i risultati.
    """
    
    def __init__(self, portfolio_value = None):
        self.portfolio_value = portfolio_value
        self.data_dict = {}
        self.assets = []
        self.index_df = None
        self.benchmark_df = None  
        self.benchmark_ticker = 'BTC-USD' 
        self.rebalance_dates = [] # <-- Nuovo attributo per tracciare le date di ribilanciamento

    # ------------------------------------------------------------------
    # Grafici comuni e funzioni di esportazione
    # ------------------------------------------------------------------
    # ------------------------------------------------------------------
    # Grafici comuni e funzioni di esportazione
    # ------------------------------------------------------------------
    def _generate_performance_fig(self, title: str = None) -> go.Figure:
            """Costruisce la figura delle performance (senza mostrarla)."""
            if self.index_df is None:
                raise ValueError("Strategia non calcolata. Esegui run_strategy() prima.")

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=self.index_df.index,
                y=self.index_df['Valore Indice'],
                mode='lines',
                name='Indice Strategia',
                line=dict(color='#1f77b4', width=2)
            ))
            if self.benchmark_df is not None:
                common_idx = self.index_df.index.intersection(self.benchmark_df.index)
                if not common_idx.empty:
                    btc_prices = self.benchmark_df['Prezzo di Chiusura'].loc[common_idx]
                    btc_normalized = btc_prices
                    fig.add_trace(go.Scatter(
                        x=btc_normalized.index,
                        y=btc_normalized,
                        mode='lines',
                        name=f'{self.benchmark_ticker} (Benchmark)',
                        line=dict(color='#cc8306', width=2)
                    ))
            
            # --- MODIFICA GRAFICA LINEA INIZIALE ---
            fig.add_hline(
                y=self.portfolio_value,
                line_dash="dash",
                line_color="red",
                annotation_text=f"Capitale Iniziale ({self.portfolio_value:,.0f} $)",
                annotation_position="bottom right"
            )
            
            if self.rebalance_dates:
                for date in self.rebalance_dates:
                    fig.add_vline(
                        x=date,
                        line_width=1,
                        line_dash="dot",
                        line_color="green",
                        opacity=0.6
                    )
                fig.add_trace(go.Scatter(
                    x=[None], y=[None], mode='lines',
                    line=dict(color='green', dash='dot'),
                    name='Ribilanciamento'
                ))
                
            fig.update_xaxes(rangeslider_visible=True,
                            rangeselector=dict(
                                buttons=list([
                                    dict(count=6, label="6m", step="month", stepmode="backward"),
                                    dict(count=1, label="YTD", step="year", stepmode="todate"),
                                    dict(count=1, label="1y", step="year", stepmode="backward"),
                                    dict(step="all")
                                ])
                            ))
                            
            fig.update_layout(
                # TITOLO RIMOSSO QUI
                xaxis_title="Data",
                yaxis=dict(
                    title="Valore del Portafoglio ($)",
                    tickformat=",.0f",    # Formato asse Y (numero intero)
                    hoverformat=",.0f"    # Formato tooltip hover (numero intero)
                ),
                hovermode="x unified",
                template="plotly_white",
                legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
                font=dict(family="Times New Roman, serif", size=12),
                margin=dict(t=40) # Aggiunge un po' di margine superiore ora che non c'è il titolo
            )
            return fig

    def _generate_stats_fig(self, stats_df: pd.DataFrame, title: str = None) -> go.Figure:
        """Costruisce la tabella delle statistiche come figura Plotly."""
        fig_stats = go.Figure(go.Table(
            header=dict(values=["Metriche"] + list(stats_df.columns),
                        fill_color='paleturquoise', align='left'),
            cells=dict(values=[stats_df.index] + [stats_df[col] for col in stats_df.columns],
                       fill_color='lavender', align='left')
        ))
        
        # TITOLO RIMOSSO QUI
        fig_stats.update_layout(margin=dict(t=10, b=10)) 
        return fig_stats

    def _generate_weights_fig(self, title: str = None) -> go.Figure:
        """Costruisce il grafico dei pesi (stacked area) senza mostrarlo."""
        if not hasattr(self, 'weights_df') or self.weights_df is None:
            raise ValueError("Pesi non calcolati. Esegui run_strategy() prima di plottare i pesi.")

        fig = go.Figure()
        colors = px.colors.qualitative.Pastel
        active_assets = self.weights_df.columns[(self.weights_df > 0.001).any()]
        for idx, ticker in enumerate(active_assets):
            fig.add_trace(go.Scatter(
                x=self.weights_df.index,
                y=self.weights_df[ticker],
                mode='lines',
                name=ticker,
                stackgroup='one',
                line=dict(color=colors[idx % len(colors)], width=1)
            ))
        if hasattr(self, 'rebalance_dates') and self.rebalance_dates:
            for date in self.rebalance_dates:
                fig.add_vline(
                    x=date,
                    line_width=1,
                    line_dash="dot",
                    line_color="green",
                    opacity=0.6
                )
        fig.update_layout(
            # TITOLO RIMOSSO QUI
            xaxis_title="Data",
            yaxis_title="Percentuale di Allocazione",
            yaxis=dict(tickformat=".0%"),
            hovermode="x unified",
            template="plotly_white",
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=1.01),
            font=dict(family="Times New Roman, serif", size=12),
            margin=dict(t=40) # Aggiunge margine superiore
        )
        return fig

    def _generate_stats_fig(self, stats_df: pd.DataFrame, title: str = None) -> go.Figure:
        """Costruisce la tabella delle statistiche come figura Plotly."""
        fig_stats = go.Figure(go.Table(
            header=dict(values=["Metriche"] + list(stats_df.columns),
                        fill_color='paleturquoise', align='left'),
            cells=dict(values=[stats_df.index] + [stats_df[col] for col in stats_df.columns],
                       fill_color='lavender', align='left')
        ))
        stats_title = (f"Statistiche della Strategia - {title}") if title else "Statistiche della Strategia"
        fig_stats.update_layout(title_text=stats_title)
        return fig_stats

    def _generate_weights_fig(self, title: str = None) -> go.Figure:
        """Costruisce il grafico dei pesi (stacked area) senza mostrarlo."""
        if not hasattr(self, 'weights_df') or self.weights_df is None:
            raise ValueError("Pesi non calcolati. Esegui run_strategy() prima di plottare i pesi.")

        fig = go.Figure()
        colors = px.colors.qualitative.Pastel
        active_assets = self.weights_df.columns[(self.weights_df > 0.001).any()]
        for idx, ticker in enumerate(active_assets):
            fig.add_trace(go.Scatter(
                x=self.weights_df.index,
                y=self.weights_df[ticker],
                mode='lines',
                name=ticker,
                stackgroup='one',
                line=dict(color=colors[idx % len(colors)], width=1)
            ))
        if hasattr(self, 'rebalance_dates') and self.rebalance_dates:
            for date in self.rebalance_dates:
                fig.add_vline(
                    x=date,
                    line_width=1,
                    line_dash="dot",
                    line_color="green",
                    opacity=0.6
                )
        fig.update_layout(
            title= title if title is not None else "Evoluzione dell'Allocazione del Portafoglio nel Tempo",
            xaxis_title="Data",
            yaxis_title="Percentuale di Allocazione",
            yaxis=dict(tickformat=".0%"),
            hovermode="x unified",
            template="plotly_white",
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=1.01),
            font=dict(family="Times New Roman, serif", size=12)
        )
        return fig

    def save_charts_json(self, output_dir: str, title: str = None):
        """Genera tutti i grafici correlati alla strategia e li salva come file JSON.

        I file creati sono:
            performance.json, stats.json e weights.json
        """
        if self.index_df is None:
            raise ValueError("Strategia non calcolata. Esegui run_strategy() prima di salvare i grafici.")

        os.makedirs(output_dir, exist_ok=True)
        stats_df = self.print_stats()

        perf_fig = self._generate_performance_fig(title)
        perf_fig.write_json(os.path.join(output_dir, "performance.json"))

        stats_fig = self._generate_stats_fig(stats_df, title)
        stats_fig.write_json(os.path.join(output_dir, "stats.json"))

        try:
            weights_title = (f"{title} - Pesi") if title else None
            weights_fig = self._generate_weights_fig(weights_title)
            weights_fig.write_json(os.path.join(output_dir, "weights.json"))
        except ValueError:
            # se non ci sono pesi calcolati, saltiamo
            pass

    def import_data(self, assets: list, timeframe: str = "1y"):
        """Scarica e prepara i dati base (Prezzo, Volume, Circulating Supply) per la lista di asset."""
        print(f"Inizio download dati per il periodo '{timeframe}'...")
        self.assets = []
        
        for ticker_symbol in assets:
            try:
                ticker = yf.Ticker(ticker_symbol)
                df_raw = ticker.history(period=timeframe)
                
                if df_raw.empty:
                    print(f"Nessun dato per {ticker_symbol}. Salto.")
                    continue
                    
                # Tentativi per recuperare circulatingSupply (backoff semplice)
                circulating_supply = None
                for attempt in range(3):
                    try:
                        circulating_supply = ticker.info.get('circulatingSupply')
                        if circulating_supply:
                            break
                    except Exception:
                        time.sleep(1)
                if not circulating_supply:
                    print(f"Circulating Supply mancante per {ticker_symbol}. Salto.")
                    continue
                    
                df_final = df_raw[['Close', 'Volume']].copy()
                df_final['Circulating Supply'] = circulating_supply
                df_final.columns = ['Prezzo di Chiusura', 'Volume 24h', 'Circulating Supply']
                
                self.data_dict[ticker_symbol] = df_final
                self.assets.append(ticker_symbol)
                
            except Exception as e:
                print(f"Errore durante il recupero di {ticker_symbol}: {e}")

        # --- GESTIONE DEL BENCHMARK ---
        if self.benchmark_ticker in self.data_dict:
            self.benchmark_df = self.data_dict[self.benchmark_ticker]
        else:
            print(f"\n{self.benchmark_ticker} non presente nel dizionario. Avvio download in un df separato...")
            try:
                ticker_bench = yf.Ticker(self.benchmark_ticker)
                df_bench_raw = ticker_bench.history(period=timeframe)
                
                if not df_bench_raw.empty:
                    df_bench_final = df_bench_raw[['Close']].copy()
                    df_bench_final.columns = ['Prezzo di Chiusura']
                    self.benchmark_df = df_bench_final
                    print(f"Benchmark {self.benchmark_ticker} completato con successo.\n")
                else:
                    print(f"Nessun dato trovato per il benchmark {self.benchmark_ticker}.\n")
            except Exception as e:
                print(f"Errore durante il download del benchmark {self.benchmark_ticker}: {e}\n")

    @abstractmethod
    def run_strategy(self, **kwargs):
        """Metodo astratto: ogni classe figlia deve definire la propria logica di backtest."""
        pass


    def calculate_stats(self):
        """Calcola e restituisce le statistiche della strategia rispetto al benchmark."""
        if self.index_df is None:
            raise ValueError("Strategia non calcolata. Esegui run_strategy().")
        
        strat_returns = self.index_df['Valore Indice'].pct_change().dropna()
        stats = {'Strategia': self._compute_metrics(strat_returns)}
        
        if self.benchmark_df is not None:
            common_idx = self.index_df.index.intersection(self.benchmark_df.index)
            if not common_idx.empty:
                btc_prices = self.benchmark_df['Prezzo di Chiusura'].loc[common_idx]
                btc_returns = btc_prices.pct_change().dropna()
                stats[self.benchmark_ticker] = self._compute_metrics(btc_returns)
            
        return pd.DataFrame(stats).round(2)
    
    # --------------------------------------------------
    # utility per formattazione visiva delle statistiche
    # --------------------------------------------------
    def print_stats(self):
        """Stampa a schermo la tabella delle statistiche in modo leggibile.

        Usa ``tabulate`` se disponibile altrimenti si affida a ``DataFrame.to_string``.
        Restituisce anche il DataFrame per eventuali usi successivi (es. plot).
        """
        stats_df = self.calculate_stats()
        # formattiamo alcuni valori con il simbolo di percentuale per rendere più leggibile
        # lavoriamo su una copia di tipo object per evitare errori di conversione
        stats_to_show = stats_df.copy().astype(object)
        for metric in stats_to_show.index:
            for col in stats_to_show.columns:
                val = stats_to_show.at[metric, col]
                if isinstance(val, (int, float)):
                    if metric.lower().startswith('sharpe'):
                        stats_to_show.at[metric, col] = f"{val:.2f}"
                    else:
                        stats_to_show.at[metric, col] = f"{val:.2f}%"

        # Dopo la formattazione possiamo stampare la tabella formattata in console
        try:
            from tabulate import tabulate
            print(tabulate(stats_to_show, headers="keys", tablefmt="github"))
        except ImportError:
            print(stats_to_show.to_string())

        return stats_df

    def _compute_metrics(self, returns: pd.Series) -> dict:
        """Helper interno per il calcolo delle metriche finanziarie su 365 giorni."""
        trading_days = 365
        ann_return = returns.mean() * trading_days
        ann_volatility = returns.std() * np.sqrt(trading_days)
        sharpe_ratio = ann_return / ann_volatility if ann_volatility != 0 else 0
        
        cumulative_returns = (1 + returns).cumprod()
        peak = cumulative_returns.cummax()
        max_drawdown = ((cumulative_returns - peak) / peak).min()
        
        return {
            'Ritorno Annualizzato (%)': ann_return * 100,
            'Volatilità Annualizzata (%)': ann_volatility * 100,
            'Sharpe Ratio': sharpe_ratio,
            'Max Drawdown (%)': max_drawdown * 100
        }
    

# ==========================================
# Figlie
# ==========================================

# RIBALANCIAMENTO PERIODICO TOP X MARKET CAP

class RebalancedMarketCapStrategy(BaseCryptoStrategy):
    """
    Strategia figlia che seleziona dinamicamente le 10 crypto più capitalizzate.
    Effettua un ribilanciamento periodico (es. mensile): rivaluta l'intero universo
    di asset, estrae le nuove Top 10, ricalcola i pesi in base alla Mkt Cap 
    e rialloca il capitale accumulato fino a quel momento.
    Il valore iniziale del portafoglio è pari al prezzo di BTC nel giorno di partenza.
    """
    
    def run_strategy(self, rebalance_freq_days: int = 180, btc_ticker: str = 'BTC-USD', **kwargs):
        """
        rebalance_freq_days: Intervallo di ribilanciamento in giorni (int).
        Es. 30 = ribilanciamento ogni ~30 giorni.
        """
        if not self.data_dict:
            raise ValueError("Nessun dato disponibile. Esegui import_data() per primo.")
            
        print(f"\nAvvio backtest: Top Dinamica con ribilanciamento (ogni {rebalance_freq_days} giorni)...")
        
        df_prices = pd.DataFrame()
        df_mktcap = pd.DataFrame()
        
        # 1. Allineamento dati e calcolo della Market Cap (uso nome 'Market Cap' coerente)
        for ticker in self.assets:
            df = self.data_dict[ticker].copy()
            df['Market Cap'] = df['Prezzo di Chiusura'] * df['Circulating Supply']
            
            df.index = pd.to_datetime(df.index)
            df_prices[ticker] = df['Prezzo di Chiusura']
            df_mktcap[ticker] = df['Market Cap']
            
        # riempimento e controllo dati
        df_prices.ffill(inplace=True)
        df_mktcap.ffill(inplace=True)
        df_prices.dropna(how='all', inplace=True)
        
        if df_prices.empty:
            raise ValueError("Dopo l'allineamento i prezzi sono vuoti. Controlla i dati sorgente.")
        
        dates = df_prices.index
        first_date = dates[0]
        
        # 2. Identificazione dei giorni di ribilanciamento (usando intervalli in giorni)
        if not isinstance(rebalance_freq_days, int) or rebalance_freq_days <= 0:
            raise ValueError(f"Parametro rebalance_freq_days non valido: {rebalance_freq_days}")

        rebalance_dates = []
        start = first_date
        end = dates[-1]
        current_target = start

        # Per ogni target date (start + n * rebalance_freq_days) troviamo la prima data di trading >= target
        while current_target <= end:
            idx = dates.searchsorted(current_target)
            if idx < len(dates):
                candidate = dates[idx]
                if not rebalance_dates or candidate != rebalance_dates[-1]:
                    rebalance_dates.append(candidate)
            current_target = current_target + pd.Timedelta(days=rebalance_freq_days)

        # salvo le date per il plotting
        self.rebalance_dates = rebalance_dates
        
        # --- MODIFICA CHIAVE: Valore iniziale = Prezzo di BTC indipendente ---
        if btc_ticker in df_prices.columns:
            btc_initial_price = df_prices.loc[first_date, btc_ticker]
        else:
            print(f"Recupero il prezzo storico di {btc_ticker} per impostare il capitale iniziale...")
            try:
                yf_ticker = btc_ticker if "-" in btc_ticker else f"{btc_ticker}-USD"
                ticker_obj = yf.Ticker(yf_ticker)
                
                # Aggiungiamo qualche giorno di margine per assicurarci di pescare il dato
                end_date = first_date + pd.Timedelta(days=3)
                btc_data = ticker_obj.history(start=first_date, end=end_date)
                
                if btc_data.empty:
                    raise ValueError(f"Dati non trovati su yfinance per {yf_ticker} nella data {first_date}.")
                
                btc_initial_price = float(btc_data['Close'].iloc[0])
            except Exception as e:
                raise ValueError(f"Impossibile recuperare il prezzo di {btc_ticker} al {first_date}: {e}")
                
        if pd.isna(btc_initial_price) or btc_initial_price <= 0:
            raise ValueError(f"Il prezzo di {btc_ticker} il primo giorno ({first_date.strftime('%Y-%m-%d')}) non è valido: {btc_initial_price}")
            
        portfolio_value = float(btc_initial_price)
        self.portfolio_value = portfolio_value
        print(f"Valore iniziale del portafoglio impostato al prezzo di {btc_ticker} in data {first_date.strftime('%Y-%m-%d')}: {portfolio_value:.2f} USD")
        # ---------------------------------------------------------------------

        shares = {}
        current_top = []
        index_values = []
        last_top = []
        last_weights = {}
        last_top_mktcap = None
        
        # DIZIONARIO PER TRACCIARE I PESI GIORNALIERI
        daily_weights_history = {}
        
        # 3. Loop giornaliero: simulazione day-by-day
        for current_date in dates:
            
            # --- A. AGGIORNAMENTO VALORE PORTAFOGLIO ---
            if shares:
                # Calcolo robusto: ignoro prezzi NaN e ticker non presenti
                pv = 0.0
                for ticker in current_top:
                    price = df_prices.loc[current_date, ticker]
                    if pd.isna(price):
                        continue
                    pv += shares.get(ticker, 0.0) * price
                portfolio_value = pv
            
            index_values.append(portfolio_value)
            
            # --- SALVATAGGIO PESI GIORNALIERI (basati su shares correnti) ---
            current_actual_weights = {}
            for ticker in self.assets:
                price = df_prices.loc[current_date, ticker] if ticker in df_prices.columns else np.nan
                price = price if not pd.isna(price) else 0
                asset_value = shares.get(ticker, 0.0) * price
                current_actual_weights[ticker] = asset_value / portfolio_value if portfolio_value > 0 else 0
            daily_weights_history[current_date] = current_actual_weights
            
            # --- B. CONTROLLO RIBILANCIAMENTO ---
            # Ribilanciamo se è il primo giorno assoluto o se è una data di ribilanciamento
            if current_date == first_date or current_date in rebalance_dates:
                
                # Prende la Mkt Cap di TUTTE le crypto in questa specifica data
                daily_mktcap = df_mktcap.loc[current_date].dropna()
                
                if daily_mktcap.empty:
                    # non ci sono market cap validi in questa data => skip
                    continue
                
                # Seleziona le NUOVE Top 10 (il tuo codice originale prendeva le top 5, lascio intatto)
                top = daily_mktcap.nlargest(5)
                current_top = top.index.tolist()
                
                total_mktcap = top.sum()
                if total_mktcap == 0:
                    continue # Evita divisioni per zero se i dati sono corrotti
                
                # Ricalcola i nuovi pesi
                weights = (top / total_mktcap).to_dict()
                
                # Salvo stato valido per eventuale stampa finale
                last_top = current_top.copy()
                last_weights = weights.copy()
                last_top_mktcap = top.copy()
                
                # Vende tutto e ricompra: ricalcola le quote esatte per le nuove Top
                shares = {}
                for ticker in current_top:
                    price = df_prices.loc[current_date, ticker]
                    if pd.isna(price) or price <= 0:
                        shares[ticker] = 0.0
                        continue
                    allocated_capital = portfolio_value * weights[ticker]
                    shares[ticker] = allocated_capital / price
                    
        # 4. Salvataggio della serie storica
        self.index_df = pd.DataFrame({'Date': dates, 'Valore Indice': index_values})
        self.index_df.set_index('Date', inplace=True)

        # SALVATAGGIO STORICO PESI IN UN DATAFRAME
        self.weights_df = pd.DataFrame.from_dict(daily_weights_history, orient='index')
        
        print(f"Backtest completato. Composizione FINALE del portafoglio al {dates[-1].strftime('%Y-%m-%d')}:")
        if last_top and last_weights and last_top_mktcap is not None:
            for ticker in last_top:
                print(f"- {ticker}: {last_weights[ticker]:.2%} (Mkt Cap: {last_top_mktcap[ticker]:,.0f})")
        else:
            print("Nessuna composizione finale valida calcolata.")

    def plot_weights(self, title: str = None, save_json_dir: str = None, return_fig: bool = False):
        fig = self._generate_weights_fig(title)

        if save_json_dir:
            os.makedirs(save_json_dir, exist_ok=True)
            fig.write_json(os.path.join(save_json_dir, "weights.json"))

        if return_fig:
            return fig

        fig.show()

    def plot_results(self, title: str = None, save_json_dir: str = None, return_fig: bool = False):
        if self.index_df is None:
            raise ValueError("Strategia non calcolata. Esegui run_strategy() prima di plottare.")
        stats_df = self.print_stats()

        perf_fig = self._generate_performance_fig(title)
        stats_fig = self._generate_stats_fig(stats_df, title)

        if save_json_dir:
            os.makedirs(save_json_dir, exist_ok=True)
            perf_fig.write_json(os.path.join(save_json_dir, "performance.json"))
            stats_fig.write_json(os.path.join(save_json_dir, "stats.json"))

        perf_fig.show()
        stats_fig.show()

        weights_fig = None
        try:
            weights_title = (f"{title} - Pesi") if title else None
            weights_fig = self.plot_weights(weights_title, save_json_dir=save_json_dir, return_fig=True)
        except Exception:
            pass

        if return_fig:
            return perf_fig, stats_fig, weights_fig
# STRATEGIA TOP X MARKET CAP, RIBILANCIAMENTO VOLUME/MARKET CAP 

class VolMktCapStrategy(BaseCryptoStrategy):
    """
    Strategia figlia che seleziona i Top N asset per Market Cap tra quelli con dati sufficienti,
    e pondera il portafoglio in base al rapporto Volume/MarketCap.
    Il valore iniziale del portafoglio è pari al prezzo di BTC al termine del periodo di warm-up.
    """
    
    def run_strategy(self, rebalance_freq_days: int = 180, top_n: int = 5, btc_ticker: str = 'BTC-USD'):
        if not self.data_dict:
            raise ValueError("Nessun dato disponibile. Esegui import_data() per primo.")
            
        print(f"\nAvvio backtest con ribilanciamento ogni {rebalance_freq_days} giorni.")

        df_prices = pd.DataFrame()
        df_vol_mktcap = pd.DataFrame()
        df_mktcap = pd.DataFrame()
        
        # Allineamento dati
        for ticker in self.assets:
            df = self.data_dict[ticker].copy()
            df['Market Cap'] = df['Circulating Supply'] * df['Prezzo di Chiusura']
            df['vol/mktcap'] = df['Volume 24h'] / df['Market Cap']
            df.index = pd.to_datetime(df.index)
            
            df_prices[ticker] = df['Prezzo di Chiusura']
            df_vol_mktcap[ticker] = df['vol/mktcap']
            df_mktcap[ticker] = df['Market Cap']
            
        df_prices.dropna(how='all', inplace=True)
        df_vol_mktcap.dropna(how='all', inplace=True)
        df_mktcap.dropna(how='all', inplace=True)
        
        df_prices.ffill(inplace=True)
        df_vol_mktcap.ffill(inplace=True)
        df_mktcap.ffill(inplace=True)
        
        dates = df_prices.index
        
        if len(dates) <= rebalance_freq_days:
            raise ValueError(f"Dati storici insufficienti. Servono più di {rebalance_freq_days} giorni.")
            
        warmup_vol = df_vol_mktcap.iloc[:rebalance_freq_days]
        warmup_mktcap = df_mktcap.iloc[:rebalance_freq_days]

        warmup_start = warmup_vol.index[0].strftime('%Y-%m-%d')
        warmup_end = warmup_vol.index[-1].strftime('%Y-%m-%d')
        print(f"Periodo di warm-up ({rebalance_freq_days} giorni): dal {warmup_start} al {warmup_end}")

        valid_assets_initial = warmup_vol.columns[warmup_vol.notna().all()].tolist()
        
        if not valid_assets_initial:
            raise ValueError("Nessun asset ha dati sufficienti nel periodo di warm-up iniziale.")

        last_warmup_date = warmup_mktcap.index[-1]
        top_assets = df_mktcap.loc[last_warmup_date, valid_assets_initial].nlargest(top_n).index.tolist()
        print(f"Asset iniziali validi selezionati: {top_assets}")

        initial_avg = warmup_vol[top_assets].mean()
        total_initial_avg = initial_avg.sum()
        
        weights = {ticker: 0.0 for ticker in self.assets}
        if total_initial_avg > 0:
            for ticker in top_assets:
                weights[ticker] = initial_avg[ticker] / total_initial_avg
        else:
            for ticker in top_assets:
                weights[ticker] = 1.0 / len(top_assets)
            
        backtest_dates = dates[rebalance_freq_days:]
        first_trading_date = backtest_dates[0]
        
        # --- MODIFICA: Valore iniziale = Prezzo di BTC indipendente DOPO il warm-up ---
        if btc_ticker in df_prices.columns:
            btc_initial_price = df_prices.loc[first_trading_date, btc_ticker]
        else:
            print(f"Recupero il prezzo storico di {btc_ticker} al termine del warm-up per impostare il capitale iniziale...")
            try:
                yf_ticker = btc_ticker if "-" in btc_ticker else f"{btc_ticker}-USD"
                ticker_obj = yf.Ticker(yf_ticker)
                
                # Aggiungiamo qualche giorno di margine per assicurarci di pescare il dato
                end_date = first_trading_date + pd.Timedelta(days=3)
                btc_data = ticker_obj.history(start=first_trading_date, end=end_date)
                
                if btc_data.empty:
                    raise ValueError(f"Dati non trovati su yfinance per {yf_ticker} nella data {first_trading_date}.")
                
                btc_initial_price = float(btc_data['Close'].iloc[0])
            except Exception as e:
                raise ValueError(f"Impossibile recuperare il prezzo di {btc_ticker} al {first_trading_date}: {e}")
                
        if pd.isna(btc_initial_price) or btc_initial_price <= 0:
            raise ValueError(f"Il prezzo di {btc_ticker} nel primo giorno di trading ({first_trading_date.strftime('%Y-%m-%d')}) non è valido: {btc_initial_price}")
            
        portfolio_value = float(btc_initial_price)
        self.portfolio_value = portfolio_value
        print(f"Valore iniziale del portafoglio impostato al prezzo di {btc_ticker} in data {first_trading_date.strftime('%Y-%m-%d')}: {portfolio_value:.2f} USD")
        # ------------------------------------------------------------------------------
        
        shares = {ticker: 0.0 for ticker in self.assets}
        for ticker in top_assets:
            shares[ticker] = (portfolio_value * weights[ticker]) / df_prices.loc[first_trading_date, ticker]
            
        index_values = []
        last_rebalance_date = first_trading_date
        self.rebalance_dates = [] 
        
        # DIZIONARIO PER TRACCIARE I PESI GIORNALIERI
        daily_weights_history = {}
        
        for current_date in backtest_dates:
            # 1. Calcolo del valore del portafoglio corrente
            current_portfolio_value = sum(
                shares[ticker] * (df_prices.loc[current_date, ticker] if not pd.isna(df_prices.loc[current_date, ticker]) else 0) 
                for ticker in self.assets
            )
            index_values.append(current_portfolio_value)
            
            # 2. Salvataggio dei pesi EFFETTIVI per il giorno corrente
            current_actual_weights = {}
            for ticker in self.assets:
                price = df_prices.loc[current_date, ticker] if not pd.isna(df_prices.loc[current_date, ticker]) else 0
                asset_value = shares[ticker] * price
                current_actual_weights[ticker] = asset_value / current_portfolio_value if current_portfolio_value > 0 else 0
            
            daily_weights_history[current_date] = current_actual_weights
            
            # 3. Controllo Ribilanciamento
            if (current_date - last_rebalance_date).days >= rebalance_freq_days:
                self.rebalance_dates.append(current_date)
                
                past_data_vol = df_vol_mktcap.loc[last_rebalance_date:current_date]
                valid_assets = past_data_vol.columns[past_data_vol.notna().all()].tolist()
                
                if not valid_assets:
                    last_rebalance_date = current_date
                    continue
                
                current_top_assets = df_mktcap.loc[current_date, valid_assets].nlargest(top_n).index.tolist()
                
                past_data_filtered = past_data_vol[current_top_assets]
                avg_vol_mktcap = past_data_filtered.mean()
                total_avg = avg_vol_mktcap.sum()
                
                weights = {ticker: 0.0 for ticker in self.assets}
                if total_avg > 0:
                    for ticker in current_top_assets:
                        weights[ticker] = avg_vol_mktcap[ticker] / total_avg
                else:
                    for ticker in current_top_assets:
                        weights[ticker] = 1.0 / len(current_top_assets)
                        
                # Aggiornamento shares con i nuovi pesi target
                for ticker in self.assets:
                    if ticker in current_top_assets:
                        shares[ticker] = (current_portfolio_value * weights[ticker]) / df_prices.loc[current_date, ticker]
                    else:
                        shares[ticker] = 0.0 
                        
                last_rebalance_date = current_date
                
        self.index_df = pd.DataFrame({'Date': backtest_dates, 'Valore Indice': index_values})
        self.index_df.set_index('Date', inplace=True)
        
        # SALVATAGGIO STORICO PESI IN UN DATAFRAME
        self.weights_df = pd.DataFrame.from_dict(daily_weights_history, orient='index')
        
        print("Backtest completato con successo su tutto il periodo storico disponibile.")

    def plot_weights(self, title: str = None, save_json_dir: str = None, return_fig: bool = False):
        """Mostra o salva il grafico dei pesi per VolMktCapStrategy."""
        fig = self._generate_weights_fig(title)

        if save_json_dir:
            os.makedirs(save_json_dir, exist_ok=True)
            fig.write_json(os.path.join(save_json_dir, "weights.json"))

        if return_fig:
            return fig

        fig.show()

    def plot_results(self, title: str = None, save_json_dir: str = None, return_fig: bool = False):
        """Mostra o salva i grafici relativi alla strategia VolMktCap."""
        if self.index_df is None:
            raise ValueError("Strategia non calcolata. Esegui run_strategy() prima di plottare.")
        stats_df = self.print_stats()

        perf_fig = self._generate_performance_fig(title)
        stats_fig = self._generate_stats_fig(stats_df, title)

        if save_json_dir:
            os.makedirs(save_json_dir, exist_ok=True)
            perf_fig.write_json(os.path.join(save_json_dir, "performance.json"))
            stats_fig.write_json(os.path.join(save_json_dir, "stats.json"))

        perf_fig.show()
        stats_fig.show()

        weights_fig = None
        try:
            weights_title = (f"{title} - Pesi") if title else None
            weights_fig = self.plot_weights(weights_title, save_json_dir=save_json_dir, return_fig=True)
        except Exception:
            pass

        if return_fig:
            return perf_fig, stats_fig, weights_fig

        try:
            weights_title = (f"{title} - Pesi") if title else None
            self.plot_weights(weights_title)
        except Exception:
            pass

# STRATEGIA TOP X MARKET CAP, RIBILANCIAMENTO SOGLIA MINIMA MKT CAP


class MarketCapThresholdStrategy(BaseCryptoStrategy):
    """
    Strategia figlia che utilizza l'intera lista di asset fornita
    e ribilancia periodicamente il portafoglio sulla base
    delle capitalizzazioni di mercato (Market Cap).
    Solo gli asset con una Market Cap superiore a una soglia
    definita (default 1 miliardo) vengono inclusi nel paniere.
    Il valore iniziale del portafoglio è pari al prezzo di BTC nel giorno di partenza.
    """

    def run_strategy(self, rebalance_freq_days: int = 180, min_mktcap: float = 1_000_000_000, btc_ticker: str = 'BTC-USD'):
        if not self.data_dict:
            raise ValueError("Nessun dato disponibile. Esegui import_data() per primo.")

        print(f"\nAvvio backtest: ribilanciamento ogni {rebalance_freq_days} giorni, soglia MktCap {min_mktcap:,}.")

        df_prices = pd.DataFrame()
        df_mktcap = pd.DataFrame()

        # raccolgo prezzi e market cap per ogni asset
        for ticker in self.assets:
            df = self.data_dict[ticker].copy()
            df['Market Cap'] = df['Prezzo di Chiusura'] * df['Circulating Supply']
            df.index = pd.to_datetime(df.index)

            df_prices[ticker] = df['Prezzo di Chiusura']
            df_mktcap[ticker] = df['Market Cap']

        df_prices.ffill(inplace=True)
        df_mktcap.ffill(inplace=True)
        df_prices.dropna(how='all', inplace=True)

        dates = df_prices.index
        if dates.empty:
            raise ValueError("Dopo l'allineamento i prezzi sono vuoti.")

        # generazione delle date di ribilanciamento
        rebalance_dates = []
        start = dates[0]
        end = dates[-1]
        current_target = start
        while current_target <= end:
            idx = dates.searchsorted(current_target)
            if idx < len(dates):
                candidate = dates[idx]
                if not rebalance_dates or candidate != rebalance_dates[-1]:
                    rebalance_dates.append(candidate)
            current_target += pd.Timedelta(days=rebalance_freq_days)
        self.rebalance_dates = rebalance_dates

        first_date = dates[0]

        # --- MODIFICA: Valore iniziale = Prezzo di BTC indipendente ---
        if btc_ticker in df_prices.columns:
            btc_initial_price = df_prices.loc[first_date, btc_ticker]
        else:
            print(f"Recupero il prezzo storico di {btc_ticker} per impostare il capitale iniziale...")
            try:
                # Usa yfinance per scaricare il prezzo del giorno di partenza
                yf_ticker = btc_ticker if "-" in btc_ticker else f"{btc_ticker}-USD"
                ticker_obj = yf.Ticker(yf_ticker)
                
                # Aggiungiamo qualche giorno di margine per assicurarci di pescare il dato
                end_date = first_date + pd.Timedelta(days=3)
                btc_data = ticker_obj.history(start=first_date, end=end_date)
                
                if btc_data.empty:
                    raise ValueError(f"Dati non trovati su yfinance per {yf_ticker} nella data {first_date}.")
                
                btc_initial_price = float(btc_data['Close'].iloc[0])
            except Exception as e:
                raise ValueError(f"Impossibile recuperare il prezzo di {btc_ticker} al {first_date}: {e}")
                
        if pd.isna(btc_initial_price) or btc_initial_price <= 0:
            raise ValueError(f"Il prezzo di {btc_ticker} il primo giorno ({first_date.strftime('%Y-%m-%d')}) non è valido: {btc_initial_price}")
            
        portfolio_value = float(btc_initial_price)
        self.portfolio_value = portfolio_value
        print(f"Valore iniziale del portafoglio impostato al prezzo di {btc_ticker} in data {first_date.strftime('%Y-%m-%d')}: {portfolio_value:.2f} USD")
        # --------------------------------------------------------------

        shares = {}
        index_values = []
        last_weights = {}
        last_basket = None
        daily_weights_history = {}

        current_basket = []

        for current_date in dates:
            if shares:
                pv = 0.0
                for ticker in current_basket:
                    price = df_prices.loc[current_date, ticker]
                    if pd.isna(price):
                        continue
                    pv += shares.get(ticker, 0.0) * price
                portfolio_value = pv

            index_values.append(portfolio_value)

            current_actual_weights = {}
            for ticker in self.assets:
                price = df_prices.loc[current_date, ticker] if ticker in df_prices.columns else np.nan
                price = price if not pd.isna(price) else 0
                asset_value = shares.get(ticker, 0.0) * price
                current_actual_weights[ticker] = asset_value / portfolio_value if portfolio_value > 0 else 0
            daily_weights_history[current_date] = current_actual_weights

            if current_date == first_date or current_date in rebalance_dates:
                daily_mktcap = df_mktcap.loc[current_date].dropna()
                valid = daily_mktcap[daily_mktcap > min_mktcap]
                if valid.empty:
                    current_basket = []
                    shares = {}
                    continue

                current_basket = valid.index.tolist()
                total_mktcap = valid.sum()
                weights = (valid / total_mktcap).to_dict()

                last_weights = weights.copy()
                last_basket = valid.copy()

                shares = {}
                for ticker in current_basket:
                    price = df_prices.loc[current_date, ticker]
                    if pd.isna(price) or price <= 0:
                        shares[ticker] = 0.0
                        continue
                    alloc = portfolio_value * weights[ticker]
                    shares[ticker] = alloc / price

        self.index_df = pd.DataFrame({'Date': dates, 'Valore Indice': index_values})
        self.index_df.set_index('Date', inplace=True)
        self.weights_df = pd.DataFrame.from_dict(daily_weights_history, orient='index')

        print(f"Backtest completato. Composizione finale al {dates[-1].strftime('%Y-%m-%d')}:" )
        if last_basket is not None and last_weights:
            for ticker in last_weights:
                print(f"- {ticker}: {last_weights[ticker]:.2%} (Mkt Cap: {last_basket[ticker]:,.0f})")
        else:
            print("Nessuna composizione valida calculata.")

    def plot_weights(self, title: str = None, save_json_dir: str = None, return_fig: bool = False):
        """Mostra o salva il grafico dei pesi per MarketCapThresholdStrategy."""
        fig = self._generate_weights_fig(title)

        if save_json_dir:
            os.makedirs(save_json_dir, exist_ok=True)
            fig.write_json(os.path.join(save_json_dir, "weights.json"))

        if return_fig:
            return fig

        fig.show()

    def plot_results(self, title: str = None, save_json_dir: str = None,
                     return_fig: bool = False):
        """Mostra o salva i grafici per MarketCapThresholdStrategy."""
        if self.index_df is None:
            raise ValueError("Strategia non calcolata. Esegui run_strategy() prima di plottare.")
        stats_df = self.print_stats()

        perf_fig = self._generate_performance_fig(title)
        stats_fig = self._generate_stats_fig(stats_df, title)

        if save_json_dir:
            os.makedirs(save_json_dir, exist_ok=True)
            perf_fig.write_json(os.path.join(save_json_dir, "performance.json"))
            stats_fig.write_json(os.path.join(save_json_dir, "stats.json"))

        perf_fig.show()
        stats_fig.show()

        weights_fig = None
        try:
            weights_title = (f"{title} - Pesi") if title else None
            weights_fig = self.plot_weights(weights_title,
                                           save_json_dir=save_json_dir,
                                           return_fig=True)
        except Exception:
            pass

        if return_fig:
            return perf_fig, stats_fig, weights_fig

        try:
            weights_title = (f"{title} - Pesi") if title else None
            self.plot_weights(weights_title)
        except Exception:
            pass

# STRATEGIA EQUAL WEIGHT CON RIBILANCIAMENTO MENSILE

class EqualWeightThresholdStrategy(BaseCryptoStrategy):
    """
    Strategia figlia che utilizza l'intera lista di asset fornita
    e ribilancia periodicamente il portafoglio.
    Solo gli asset con una Market Cap superiore a una soglia
    definita (default 1 miliardo) vengono inclusi nel paniere.
    
    A differenza della strategia basata sulla Market Cap, qui
    l'allocazione è EQUAL WEIGHT: il capitale viene diviso in
    parti uguali tra tutti gli asset validi al momento del ribilanciamento.
    Il valore iniziale del portafoglio è pari al prezzo di BTC nel giorno di partenza.
    """

    def run_strategy(self, rebalance_freq_days: int = 180, min_mktcap: float = 1_000_000_000, btc_ticker: str = 'BTC-USD'):
        if not self.data_dict:
            raise ValueError("Nessun dato disponibile. Esegui import_data() per primo.")

        print(f"\nAvvio backtest: ribilanciamento ogni {rebalance_freq_days} giorni, soglia MktCap {min_mktcap:,}. Metodo: Equal Weight.")

        df_prices = pd.DataFrame()
        df_mktcap = pd.DataFrame()

        # Raccolgo prezzi e calcolo la market cap per ogni asset (serve per il filtro)
        for ticker in self.assets:
            df = self.data_dict[ticker].copy()
            df['Market Cap'] = df['Prezzo di Chiusura'] * df['Circulating Supply']
            df.index = pd.to_datetime(df.index)

            df_prices[ticker] = df['Prezzo di Chiusura']
            df_mktcap[ticker] = df['Market Cap']

        df_prices.ffill(inplace=True)
        df_mktcap.ffill(inplace=True)
        df_prices.dropna(how='all', inplace=True)

        dates = df_prices.index
        if dates.empty:
            raise ValueError("Dopo l'allineamento i prezzi sono vuoti.")

        # Generazione delle date di ribilanciamento
        rebalance_dates = []
        start = dates[0]
        end = dates[-1]
        current_target = start
        while current_target <= end:
            idx = dates.searchsorted(current_target)
            if idx < len(dates):
                candidate = dates[idx]
                if not rebalance_dates or candidate != rebalance_dates[-1]:
                    rebalance_dates.append(candidate)
            current_target += pd.Timedelta(days=rebalance_freq_days)
        self.rebalance_dates = rebalance_dates

        first_date = dates[0]

        # --- MODIFICA CHIAVE: Valore iniziale = Prezzo di BTC ---
        if btc_ticker not in df_prices.columns:
            raise ValueError(f"Ticker '{btc_ticker}' non trovato nei dati. Impossibile determinare il valore iniziale.")
            
        btc_initial_price = df_prices.loc[first_date, btc_ticker]
        
        if pd.isna(btc_initial_price) or btc_initial_price <= 0:
            raise ValueError(f"Il prezzo di {btc_ticker} il primo giorno ({first_date.strftime('%Y-%m-%d')}) non è valido: {btc_initial_price}")
            
        portfolio_value = float(btc_initial_price)
        self.portfolio_value = portfolio_value
        print(f"Valore iniziale del portafoglio impostato al prezzo di {btc_ticker} in data {first_date.strftime('%Y-%m-%d')}: {portfolio_value:.2f}")
        # --------------------------------------------------------

        shares = {}
        index_values = []
        last_weights = {}
        last_basket = None
        daily_weights_history = {}

        current_basket = []

        for current_date in dates:
            # Aggiornamento del valore del portafoglio basato sulle quote attuali
            if shares:
                pv = 0.0
                for ticker in current_basket:
                    price = df_prices.loc[current_date, ticker]
                    if pd.isna(price):
                        continue
                    pv += shares.get(ticker, 0.0) * price
                portfolio_value = pv

            index_values.append(portfolio_value)

            # Salvataggio pesi giornalieri effettivi (fluttuano con i prezzi)
            current_actual_weights = {}
            for ticker in self.assets:
                price = df_prices.loc[current_date, ticker] if ticker in df_prices.columns else np.nan
                price = price if not pd.isna(price) else 0
                asset_value = shares.get(ticker, 0.0) * price
                current_actual_weights[ticker] = asset_value / portfolio_value if portfolio_value > 0 else 0
            daily_weights_history[current_date] = current_actual_weights

            # Ribilanciamento
            if current_date == first_date or current_date in rebalance_dates:
                daily_mktcap = df_mktcap.loc[current_date].dropna()
                valid = daily_mktcap[daily_mktcap > min_mktcap]
                
                if valid.empty:
                    current_basket = []
                    shares = {}
                    continue

                current_basket = valid.index.tolist()
                
                # --- EQUAL WEIGHT ---
                # Contiamo quanti asset hanno superato la soglia e diamo a ciascuno lo stesso peso
                num_assets = len(current_basket)
                equal_weight = 1.0 / num_assets
                weights = {ticker: equal_weight for ticker in current_basket}
                # --------------------

                last_weights = weights.copy()
                last_basket = valid.copy()

                # Ricalcolo quote (shares) per il nuovo paniere
                shares = {}
                for ticker in current_basket:
                    price = df_prices.loc[current_date, ticker]
                    if pd.isna(price) or price <= 0:
                        shares[ticker] = 0.0
                        continue
                    alloc = portfolio_value * weights[ticker]
                    shares[ticker] = alloc / price

        # Salvataggio risultati nella classe
        self.index_df = pd.DataFrame({'Date': dates, 'Valore Indice': index_values})
        self.index_df.set_index('Date', inplace=True)
        self.weights_df = pd.DataFrame.from_dict(daily_weights_history, orient='index')

        print(f"Backtest completato. Composizione finale al {dates[-1].strftime('%Y-%m-%d')}:" )
        if last_basket is not None and last_weights:
            for ticker in last_weights:
                print(f"- {ticker}: {last_weights[ticker]:.2%} (Mkt Cap reale: {last_basket[ticker]:,.0f})")
        else:
            print("Nessuna composizione valida calcolata.")


    def plot_weights(self, title: str = None, save_json_dir: str = None, return_fig: bool = False):
        """Mostra o salva il grafico dei pesi per EqualWeightThresholdStrategy."""
        fig = self._generate_weights_fig(title)

        if save_json_dir:
            os.makedirs(save_json_dir, exist_ok=True)
            fig.write_json(os.path.join(save_json_dir, "weights.json"))

        if return_fig:
            return fig

        fig.show()

    def plot_results(self, title: str = None, save_json_dir: str = None, return_fig: bool = False):
        """Mostra o salva i grafici per EqualWeightThresholdStrategy."""
        if self.index_df is None:
            raise ValueError("Strategia non calcolata. Esegui run_strategy() prima di plottare.")
        stats_df = self.print_stats()

        perf_fig = self._generate_performance_fig(title)
        stats_fig = self._generate_stats_fig(stats_df, title)

        if save_json_dir:
            os.makedirs(save_json_dir, exist_ok=True)
            perf_fig.write_json(os.path.join(save_json_dir, "performance.json"))
            stats_fig.write_json(os.path.join(save_json_dir, "stats.json"))

        perf_fig.show()
        stats_fig.show()

        weights_fig = None
        try:
            weights_title = (f"{title} - Pesi") if title else None
            weights_fig = self.plot_weights(weights_title, save_json_dir=save_json_dir, return_fig=True)
        except Exception:
            pass

        if return_fig:
            return perf_fig, stats_fig, weights_fig

        try:
            weights_title = (f"{title} - Pesi") if title else None
            self.plot_weights(weights_title)
        except Exception:
            pass