from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
import pickle
from pathlib import Path

# Mapping da ticker a nomi delle cryptocurrency per esteso
CRYPTO_NAMES = {
    'BTC-USD': 'Bitcoin',
    'ETH-USD': 'Ethereum',
    'XRP-USD': 'XRP',
    'SOL-USD': 'Solana',
    'DOGE-USD': 'Dogecoin',
    'ADA-USD': 'Cardano',
    'LINK-USD': 'Chainlink',
    'AVAX-USD': 'Avalanche',
    'DOT-USD': 'Polkadot',
    'UNI7083-USD': 'Uniswap',
    'SKY33038-USD': 'Sky',
    'NEAR-USD': 'Near',
    'ATOM-USD': 'Cosmos',
    'POL28321-USD': 'Polygon',
    'ALGO-USD': 'Algorand',
    'APT21794-USD': 'Aptos',
    'ARB11841-USD': 'Arbitrum',
    'STX4847-USD': 'Stacks',
    'INJ-USD': 'Injective',
    'TIA-USD': 'Celestia',
    'GRT6719-USD': 'The Graph',
    'OP-USD': 'Optimism',
    'SUI20947-USD': 'Sui',
    'XLM-USD': 'Stellar Lumens',
    'XPL-USD': 'XPL',
    'ONDO-USD': 'Ondo',
    'HBAR-USD': 'Hedera',
    'FIL-USD': 'Filecoin',
    'AAVE-USD': 'Aave',
    'NIGHT39064-USD': 'Nyx',
    'ETC-USD': 'Ethereum Classic',
    'LTC-USD': 'Litecoin',
}

# ==========================================
# Genitore
# ==========================================
class BaseCryptoStrategy(ABC):
    """
    Classe genitore che gestisce il recupero dati, le statistiche e i grafici interattivi.
    Le classi figlie devono implementare solo la logica di 'run_strategy'.
    """
    
    def __init__(self, initial_value: float = 10000.0):
        self.initial_value = initial_value
        self.data_dict = {}
        self.assets = []
        self.index_df = None
        self.benchmark_df = None  
        self.benchmark_ticker = 'BTC-USD' 
        self.rebalance_dates = [] # <-- Nuovo attributo per tracciare le date di ribilanciamento
        self.cache_dir = Path('./data_cache')
        self.cache_dir.mkdir(exist_ok=True)

    def _get_cache_path(self, ticker: str, timeframe: str) -> Path:
        """Ritorna il percorso del file cache per un ticker e timeframe."""
        return self.cache_dir / f"{ticker}_{timeframe}.pkl"

    def _load_cache(self, ticker: str, timeframe: str):
        """Carica i dati dal cache se disponibili. Ritorna None se non trovati."""
        cache_path = self._get_cache_path(ticker, timeframe)
        if cache_path.exists():
            try:
                with open(cache_path, 'rb') as f:
                    return pickle.load(f)
            except Exception as e:
                print(f"Errore nel caricamento cache per {ticker}: {e}")
                return None
        return None

    def _save_cache(self, ticker: str, timeframe: str, data):
        """Salva i dati nel cache."""
        cache_path = self._get_cache_path(ticker, timeframe)
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(data, f)
        except Exception as e:
            print(f"Errore nel salvataggio cache per {ticker}: {e}")

    def import_data(self, assets: list, timeframe: str = "1y", use_cache: bool = True, refresh_cache: bool = False):
        """Scarica e prepara i dati base (Prezzo, Volume, Circulating Supply) per la lista di asset."""
        print(f"Inizio download dati per il periodo '{timeframe}'...")
        self.assets = []
        
        for ticker_symbol in assets:
            try:
                # Gestione cache
                if use_cache and not refresh_cache:
                    cached_data = self._load_cache(ticker_symbol, timeframe)
                    if cached_data is not None:
                        try:
                            # Tenta di unpacking come tupla (nuovo formato)
                            df_raw, circulating_supply = cached_data
                            print(f"  {ticker_symbol}: caricato dalla cache")
                            df_final = df_raw[['Close', 'Volume']].copy()
                            df_final['Circulating Supply'] = circulating_supply
                            df_final.columns = ['Prezzo di Chiusura', 'Volume 24h', 'Circulating Supply']
                            self.data_dict[ticker_symbol] = df_final
                            self.assets.append(ticker_symbol)
                            continue
                        except (ValueError, TypeError):
                            # Formato cache vecchio o corrotto, scarica di nuovo
                            pass
                
                # Download da yfinance
                ticker = yf.Ticker(ticker_symbol)
                df_raw = ticker.history(period=timeframe)
                
                if df_raw.empty:
                    print(f"Nessun dato per {ticker_symbol}. Salto.")
                    continue
                    
                circulating_supply = ticker.info.get('circulatingSupply')
                if not circulating_supply:
                    print(f"Circulating Supply mancante per {ticker_symbol}. Salto.")
                    continue
                
                # Salva nel cache
                if use_cache:
                    self._save_cache(ticker_symbol, timeframe, (df_raw, circulating_supply))
                    
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
                # Gestione cache per benchmark
                if use_cache and not refresh_cache:
                    cached_data = self._load_cache(self.benchmark_ticker, timeframe)
                    if cached_data is not None:
                        try:
                            df_bench_raw, _ = cached_data
                            print(f"Benchmark {self.benchmark_ticker} caricato dalla cache.\n")
                            df_bench_final = df_bench_raw[['Close']].copy()
                            df_bench_final.columns = ['Prezzo di Chiusura']
                            self.benchmark_df = df_bench_final
                        except (ValueError, TypeError):
                            # Formato vecchio o corrotto, scarica di nuovo
                            raise ValueError("Cache format incompatible")
                    else:
                        raise ValueError("No cache found")
                else:
                    raise ValueError("Cache not used")
                    
            except:
                # Download da yfinance
                try:
                    ticker_bench = yf.Ticker(self.benchmark_ticker)
                    df_bench_raw = ticker_bench.history(period=timeframe)
                    
                    if not df_bench_raw.empty:
                        # Salva nel cache
                        if use_cache:
                            self._save_cache(self.benchmark_ticker, timeframe, (df_bench_raw, None))
                            
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

    def plot_results(self):
        """Grafica l'andamento della strategia confrontato con il benchmark (Interattivo)."""
        if self.index_df is None:
            raise ValueError("Strategia non calcolata. Esegui run_strategy() prima di plottare.")
            
        fig = go.Figure()

        # --- PLOT STRATEGIA ---
        fig.add_trace(go.Scatter(
            x=self.index_df.index, 
            y=self.index_df['Valore Indice'],
            mode='lines',
            name='Indice Strategia',
            line=dict(color='#1f77b4', width=2)
        ))
        
        # --- PLOT BENCHMARK ---
        if self.benchmark_df is not None:
            common_idx = self.index_df.index.intersection(self.benchmark_df.index)
            if not common_idx.empty:
                btc_prices = self.benchmark_df['Prezzo di Chiusura'].loc[common_idx]
                btc_normalized = (btc_prices / btc_prices.iloc[0]) * self.initial_value
                
                fig.add_trace(go.Scatter(
                    x=btc_normalized.index, 
                    y=btc_normalized,
                    mode='lines',
                    name=f'{self.benchmark_ticker} (Benchmark)',
                    line=dict(color='#cc8306', width=2)
                ))
        
        # --- LINEA CAPITALE INIZIALE ---
        fig.add_hline(
            y=self.initial_value, 
            line_dash="dash", 
            line_color="red", 
            annotation_text=f"Capitale Iniziale ({self.initial_value}$)", 
            annotation_position="bottom right"
        )

        # --- LINEE DEI RIBILANCIAMENTI ---
        # Aggiungiamo una linea verticale per ogni data in cui è avvenuto un ribilanciamento
        if self.rebalance_dates:
            for date in self.rebalance_dates:
                fig.add_vline(
                    x=date, 
                    line_width=1, 
                    line_dash="dot", 
                    line_color="green",
                    opacity=0.6
                )
            # Aggiungo una riga invisibile solo per far comparire la legenda dei ribilanciamenti
            fig.add_trace(go.Scatter(
                x=[None], y=[None], mode='lines',
                line=dict(color='green', dash='dot'),
                name='Ribilanciamento'
            ))

        # --- LAYOUT INTERATTIVO ---
        fig.update_layout(
            title="Performance Strategia vs BTC-USD",
            xaxis_title="Data",
            yaxis_title="Valore del Portafoglio ($)",
            hovermode="x unified", # Mostra i dati di tutte le curve passando il mouse su un punto
            template="plotly_white",
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
        )
        
        fig.show()

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
            
        return pd.DataFrame(stats).round(4)

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

class RebalancedMarketCapStrategy(BaseCryptoStrategy):
    
    """
    Strategia figlia che seleziona dinamicamente le 10 crypto più capitalizzate.
    Effettua un ribilanciamento periodico (es. mensile): rivaluta l'intero universo
    di asset, estrae le nuove Top 10, ricalcola i pesi in base alla Mkt Cap 
    e rialloca il capitale accumulato fino a quel momento.
    """
    
    def run_strategy(self, rebalance_freq='Q', **kwargs):
        """
        rebalance_freq: Frequenza di ribilanciamento. 
        'M' (Month End) = fine mese, 'Q' (Quarter End) = fine trimestre, 'Y' = fine anno.
        """
        if not self.data_dict:
            raise ValueError("Nessun dato disponibile. Esegui import_data() per primo.")
            
        print(f"\nAvvio backtest: Top 10 Dinamica con ribilanciamento (frequenza: {rebalance_freq})...")
        
        df_prices = pd.DataFrame()
        df_mktcap = pd.DataFrame()
        
        # 1. Allineamento dati e calcolo della Market Cap
        for ticker in self.assets:
            df = self.data_dict[ticker].copy()
            df['MarketCap'] = df['Prezzo di Chiusura'] * df['Circulating Supply']
            
            df.index = pd.to_datetime(df.index)
            df_prices[ticker] = df['Prezzo di Chiusura']
            df_mktcap[ticker] = df['MarketCap']
            
        df_prices.ffill(inplace=True)
        df_mktcap.ffill(inplace=True)
        df_prices.dropna(how='all', inplace=True)
        
        dates = df_prices.index
        first_date = dates[0]
        
        # 2. Identificazione dei giorni di ribilanciamento
        # Usiamo resample per trovare l'ultimo giorno disponibile di ogni mese/trimestre
        rebalance_dates = df_prices.resample(rebalance_freq).last().index
        # Ci assicuriamo che le date calcolate siano effettivamente nell'indice
        rebalance_dates = [d for d in rebalance_dates if d in dates]
        
        portfolio_value = self.initial_value
        shares = {}
        current_top_10 = []
        index_values = []
        
        # 3. Loop giornaliero: simulazione day-by-day
        for current_date in dates:
            
            # --- A. AGGIORNAMENTO VALORE PORTAFOGLIO ---
            if not shares:
                # Giorno 1: il valore è il capitale iniziale
                pass 
            else:
                # Calcola il valore del ptf in base alle quote possedute e ai prezzi di oggi
                portfolio_value = sum(shares[ticker] * df_prices.loc[current_date, ticker] for ticker in current_top_10)
            
            index_values.append(portfolio_value)
            
            # --- B. CONTROLLO RIBILANCIAMENTO ---
            # Ribilanciamo se è il primo giorno assoluto o se è una data di ribilanciamento
            if current_date == first_date or current_date in rebalance_dates:
                
                # Prende la Mkt Cap di TUTTE le crypto in questa specifica data
                daily_mktcap = df_mktcap.loc[current_date].dropna()
                
                # Seleziona le NUOVE Top 10
                top_10 = daily_mktcap.nlargest(10)
                current_top_10 = top_10.index.tolist()
                
                total_mktcap = top_10.sum()
                if total_mktcap == 0:
                    continue # Evita divisioni per zero se i dati sono corrotti
                
                # Ricalcola i nuovi pesi
                weights = (top_10 / total_mktcap).to_dict()
                
                # Vende tutto e ricompra: ricalcola le quote esatte per le nuove Top 10
                shares = {}
                for ticker in current_top_10:
                    allocated_capital = portfolio_value * weights[ticker]
                    price = df_prices.loc[current_date, ticker]
                    # Assegna le nuove quote (se il prezzo è > 0 per evitare errori)
                    shares[ticker] = allocated_capital / price if price > 0 else 0
                    
        # 4. Salvataggio della serie storica
        self.index_df = pd.DataFrame({'Date': dates, 'Valore Indice': index_values})
        self.index_df.set_index('Date', inplace=True)
        
        print(f"Backtest completato. Composizione FINALE del portafoglio al {dates[-1].strftime('%Y-%m-%d')}:")
        for ticker in current_top_10:
            print(f"- {ticker}: {weights[ticker]:.2%} (Mkt Cap: {top_10[ticker]:,.0f})")

class VolMktCapStrategy(BaseCryptoStrategy):
    """
    Strategia figlia che seleziona i Top N asset per Market Cap tra quelli con dati sufficienti,
    e pondera il portafoglio in base al rapporto Volume/MarketCap.
    """
    
    def run_strategy(self, rebalance_freq_days: int = 90, top_n: int = 5):
        if not self.data_dict:
            raise ValueError("Nessun dato disponibile. Esegui import_data() per primo.")
            
        print(f"\nAvvio backtest con ribilanciamento ogni {rebalance_freq_days} giorni.")
        print(f"Selezione dinamica: Top {top_n} asset per Market Cap (esclusi asset con dati incompleti).")
        
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
        portfolio_value = self.initial_value
        
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

    def plot_weights(self):
        """Grafica l'evoluzione dei pesi del portafoglio nel tempo (Stacked Area Chart)."""
        if not hasattr(self, 'weights_df') or self.weights_df is None:
            raise ValueError("Pesi non calcolati. Esegui run_strategy() prima di plottare i pesi.")

        fig = go.Figure()

        # Filtriamo gli asset che sono stati in portafoglio almeno una volta (peso > 0)
        # Questo evita di avere 50 monete nella legenda se ne hai usate solo 8 nella Top 5 nel tempo
        active_assets = self.weights_df.columns[(self.weights_df > 0.001).any()]

        for ticker in active_assets:
            crypto_name = CRYPTO_NAMES.get(ticker, ticker)  # Usa il nome per esteso o il ticker se non trovato
            fig.add_trace(go.Scatter(
                x=self.weights_df.index,
                y=self.weights_df[ticker],
                mode='lines',
                name=crypto_name,
                stackgroup='one', # Imposta il grafico ad area impilata
                line=dict(width=0.5)
            ))

        # Aggiungiamo le linee verticali per le date di ribilanciamento
        if hasattr(self, 'rebalance_dates') and self.rebalance_dates:
            for date in self.rebalance_dates:
                fig.add_vline(
                    x=date, 
                    line_width=1, 
                    line_dash="dot", 
                    line_color="black",
                    opacity=0.5
                )

        fig.update_layout(
            title="Evoluzione dell'Allocazione del Portafoglio nel Tempo",
            xaxis_title="Data",
            yaxis_title="Percentuale di Allocazione",
            yaxis=dict(tickformat=".0%"), # Formatta l'asse Y come percentuale (es. 100%)
            hovermode="x unified",
            template="plotly_white",
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=1.01) # Legenda esterna a destra
        )

        fig.show()

        