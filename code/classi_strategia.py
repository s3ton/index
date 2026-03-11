from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
import yfinance as yf
import os
import json 
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import time
import requests  # <-- Nuovo import per API Fear & Greed
import re        # <-- Nuovo import per pulire le etichette dell'Heatmap

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
        self.rebalance_dates = [] 
        self.weights_df = None
        self.mktcap_df = None 

    # ------------------------------------------------------------------
    # Metodo per salvare le metriche aggiuntive
    # ------------------------------------------------------------------
    # ------------------------------------------------------------------
    # Metodo per salvare le metriche aggiuntive
    # ------------------------------------------------------------------
    def _save_metrics_json(self, save_dir: str):
        """Calcola e salva le metriche di riepilogo in un file metrics.json."""
        if self.index_df is None or self.index_df.empty:
            return

        # 1. Ultimo valore
        last_val = self.index_df['Valore Indice'].iloc[-1]
        
        # 2. Variazione ultime 24h
        var_24h = 0.0
        if len(self.index_df) >= 2:
            var_24h = (last_val / self.index_df['Valore Indice'].iloc[-2]) - 1

        # 3. Variazione ultimi 7g
        var_7d = 0.0
        if len(self.index_df) >= 8:
            var_7d = (last_val / self.index_df['Valore Indice'].iloc[-8]) - 1
        elif len(self.index_df) > 0:
            var_7d = (last_val / self.index_df['Valore Indice'].iloc[0]) - 1

        # 4. Variazione da inizio anno (YTD)
        last_date = self.index_df.index[-1]
        current_year = last_date.year
        prev_year_data = self.index_df[self.index_df.index.year < current_year]
        
        if not prev_year_data.empty:
            base_ytd_val = prev_year_data['Valore Indice'].iloc[-1]
        else:
            base_ytd_val = self.index_df[self.index_df.index.year == current_year]['Valore Indice'].iloc[0]
            
        var_ytd = (last_val / base_ytd_val) - 1 if base_ytd_val > 0 else 0.0

        # 5. Ultima allocazione dei pesi
        last_weights = {}
        if hasattr(self, 'weights_df') and self.weights_df is not None and not self.weights_df.empty:
            last_row = self.weights_df.iloc[-1]
            last_weights = {str(ticker): float(weight) for ticker, weight in last_row.items() if weight > 0.0001}

        # 6. Ultima Market Cap 
        last_mktcap = {}
        if hasattr(self, 'mktcap_df') and self.mktcap_df is not None and not self.mktcap_df.empty:
            if last_date in self.mktcap_df.index:
                row_mktcap = self.mktcap_df.loc[last_date]
                for ticker in last_weights.keys():
                    val = row_mktcap.get(ticker, 0.0)
                    last_mktcap[str(ticker)] = float(val) if not pd.isna(val) else 0.0

        # 7. --- NUOVO: CALCOLO RENDIMENTI ANNUALI ---
        def calc_annual_returns(series):
            annual_rets = {}
            years = series.index.year.unique()
            for y in years:
                data_y = series[series.index.year == y]
                if data_y.empty:
                    continue
                
                last_val_y = data_y.iloc[-1]
                data_prev = series[series.index.year < y]
                
                # Usiamo l'ultimo giorno dell'anno precedente come base di partenza.
                # Se non esiste, usiamo il primo giorno dell'anno corrente.
                if not data_prev.empty:
                    first_val_y = data_prev.iloc[-1]
                else:
                    first_val_y = data_y.iloc[0]
                
                if first_val_y > 0:
                    ret = (last_val_y / first_val_y) - 1
                    annual_rets[str(y)] = round(float(ret * 100), 1)
                else:
                    annual_rets[str(y)] = 0.0
            return annual_rets

        rendimenti_annuali = calc_annual_returns(self.index_df['Valore Indice'])
        
        benchmark_annuali = {}
        if hasattr(self, 'benchmark_df') and self.benchmark_df is not None and not self.benchmark_df.empty:
            # Assicuriamoci che l'indice sia datetime
            if not pd.api.types.is_datetime64_any_dtype(self.benchmark_df.index):
                self.benchmark_df.index = pd.to_datetime(self.benchmark_df.index)
            benchmark_annuali = calc_annual_returns(self.benchmark_df['Prezzo di Chiusura'])

        # Costruisco il dizionario finale
        metrics = {
            "ultimo_valore_indice": float(last_val),
            "variazione_24h_pct": float(var_24h),
            "variazione_7g_pct": float(var_7d),
            "variazione_ytd_pct": float(var_ytd),
            "ultima_allocazione_pesi": last_weights,
            "capitalizzazione_mercato": last_mktcap,
            "rendimenti_annuali": rendimenti_annuali,
            "benchmark_annuali": benchmark_annuali
        }

        os.makedirs(save_dir, exist_ok=True)
        with open(os.path.join(save_dir, "metrics.json"), "w") as f:
            json.dump(metrics, f, indent=4)

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
                xaxis_title="Data",
                yaxis=dict(
                    title="Valore del Portafoglio ($)",
                    tickformat=",.0f",    
                    hoverformat=",.0f"    
                ),
                hovermode="x unified",
                template="plotly_white",
                legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
                font=dict(family="Times New Roman, serif", size=12),
                margin=dict(t=40)
            )
            return fig

    def _generate_stats_fig(self, stats_df: pd.DataFrame, title: str = None) -> go.Figure:
        fig_stats = go.Figure(go.Table(
            header=dict(values=["Metriche"] + list(stats_df.columns),
                        fill_color='paleturquoise', align='left'),
            cells=dict(values=[stats_df.index] + [stats_df[col] for col in stats_df.columns],
                       fill_color='lavender', align='left')
        ))
        stats_title = (f"Statistiche della Strategia - {title}") if title else "Statistiche della Strategia"
        fig_stats.update_layout(title_text=stats_title, margin=dict(t=40, b=10)) 
        return fig_stats

    def _generate_weights_fig(self, title: str = None) -> go.Figure:
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
            font=dict(family="Times New Roman, serif", size=12),
            margin=dict(t=40)
        )
        return fig

    def save_charts_json(self, output_dir: str, title: str = None):
        if self.index_df is None:
            raise ValueError("Strategia non calcolata. Esegui run_strategy() prima di salvare i grafici.")

        os.makedirs(output_dir, exist_ok=True)
        stats_df = self.print_stats()

        perf_fig = self._generate_performance_fig(title)
        perf_fig.write_json(os.path.join(output_dir, "performance.json"))

        stats_fig = self._generate_stats_fig(stats_df, title)
        stats_fig.write_json(os.path.join(output_dir, "stats.json"))
        
        self._save_metrics_json(output_dir)

        try:
            weights_title = (f"{title} - Pesi") if title else None
            weights_fig = self._generate_weights_fig(weights_title)
            weights_fig.write_json(os.path.join(output_dir, "weights.json"))
        except ValueError:
            pass

    def import_data(self, assets: list, timeframe: str = "1y", save_historical: bool = True, historical_dir: str = "../data/historical"):
        print(f"Inizio download dati per il periodo '{timeframe}'...")
        self.assets = []
        
        # --- NOVITÀ: Creazione della cartella per lo storico ---
        if save_historical:
            os.makedirs(historical_dir, exist_ok=True)
            print(f"Cartella per lo storico dati preparata in: {historical_dir}")
        
        for ticker_symbol in assets:
            try:
                ticker = yf.Ticker(ticker_symbol)
                df_raw = ticker.history(period=timeframe)
                
                if df_raw.empty:
                    print(f"Nessun dato per {ticker_symbol}. Salto.")
                    continue
                    
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

                # --- NOVITÀ: Salvataggio JSON per lo Strategy Builder ---
                if save_historical:
                    # Pulisco il nome (es. "BTC-USD" diventa "btc")
                    clean_name = str(ticker_symbol).replace("-USD", "").lower()
                    # Rimuovo eventuali numeri (es. "UNI7083" diventa "uni")
                    import re
                    clean_name = re.sub(r'\d+', '', clean_name)
                    
                    file_path = os.path.join(historical_dir, f"{clean_name}.json")
                    
                    # Formatto i dati per il frontend: un array di date e un array di prezzi
                    hist_data = {
                        "ticker": ticker_symbol,
                        "dates": df_final.index.strftime('%Y-%m-%d').tolist(),
                        "prices": df_final['Prezzo di Chiusura'].tolist()
                    }
                    
                    with open(file_path, "w") as f:
                        json.dump(hist_data, f)
                    
            except Exception as e:
                print(f"Errore durante il recupero di {ticker_symbol}: {e}")

        # --- LOGICA DEL BENCHMARK ---
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
        pass

    def calculate_stats(self):
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
    
    def print_stats(self):
        stats_df = self.calculate_stats()
        stats_to_show = stats_df.copy().astype(object)
        for metric in stats_to_show.index:
            for col in stats_to_show.columns:
                val = stats_to_show.at[metric, col]
                if isinstance(val, (int, float)):
                    if metric.lower().startswith('sharpe'):
                        stats_to_show.at[metric, col] = f"{val:.2f}"
                    else:
                        stats_to_show.at[metric, col] = f"{val:.2f}%"

        try:
            from tabulate import tabulate
            print(tabulate(stats_to_show, headers="keys", tablefmt="github"))
        except ImportError:
            print(stats_to_show.to_string())

        return stats_df

    def _compute_metrics(self, returns: pd.Series) -> dict:
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
# Figlie Strategie
# ==========================================

class RebalancedMarketCapStrategy(BaseCryptoStrategy):
    
    def run_strategy(self, rebalance_freq_days: int = 180, btc_ticker: str = 'BTC-USD', **kwargs):
        if not self.data_dict:
            raise ValueError("Nessun dato disponibile. Esegui import_data() per primo.")
            
        print(f"\nAvvio backtest: Top Dinamica con ribilanciamento (ogni {rebalance_freq_days} giorni)...")
        
        df_prices = pd.DataFrame()
        df_mktcap = pd.DataFrame()
        
        for ticker in self.assets:
            df = self.data_dict[ticker].copy()
            df['Market Cap'] = df['Prezzo di Chiusura'] * df['Circulating Supply']
            
            df.index = pd.to_datetime(df.index)
            df_prices[ticker] = df['Prezzo di Chiusura']
            df_mktcap[ticker] = df['Market Cap']
            
        df_prices.ffill(inplace=True)
        df_mktcap.ffill(inplace=True)
        df_prices.dropna(how='all', inplace=True)
        
        if df_prices.empty:
            raise ValueError("Dopo l'allineamento i prezzi sono vuoti. Controlla i dati sorgente.")
        
        dates = df_prices.index
        first_date = dates[0]
        
        if not isinstance(rebalance_freq_days, int) or rebalance_freq_days <= 0:
            raise ValueError(f"Parametro rebalance_freq_days non valido: {rebalance_freq_days}")

        rebalance_dates = []
        start = first_date
        end = dates[-1]
        current_target = start

        while current_target <= end:
            idx = dates.searchsorted(current_target)
            if idx < len(dates):
                candidate = dates[idx]
                if not rebalance_dates or candidate != rebalance_dates[-1]:
                    rebalance_dates.append(candidate)
            current_target = current_target + pd.Timedelta(days=rebalance_freq_days)

        self.rebalance_dates = rebalance_dates
        
        if btc_ticker in df_prices.columns:
            btc_initial_price = df_prices.loc[first_date, btc_ticker]
        else:
            print(f"Recupero il prezzo storico di {btc_ticker} per impostare il capitale iniziale...")
            try:
                yf_ticker = btc_ticker if "-" in btc_ticker else f"{btc_ticker}-USD"
                ticker_obj = yf.Ticker(yf_ticker)
                
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

        shares = {}
        current_top = []
        index_values = []
        last_top = []
        last_weights = {}
        last_top_mktcap = None
        daily_weights_history = {}
        
        for current_date in dates:
            if shares:
                pv = 0.0
                for ticker in current_top:
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
                if daily_mktcap.empty:
                    continue
                
                top = daily_mktcap.nlargest(5)
                current_top = top.index.tolist()
                
                total_mktcap = top.sum()
                if total_mktcap == 0:
                    continue 
                
                weights = (top / total_mktcap).to_dict()
                
                last_top = current_top.copy()
                last_weights = weights.copy()
                last_top_mktcap = top.copy()
                
                shares = {}
                for ticker in current_top:
                    price = df_prices.loc[current_date, ticker]
                    if pd.isna(price) or price <= 0:
                        shares[ticker] = 0.0
                        continue
                    allocated_capital = portfolio_value * weights[ticker]
                    shares[ticker] = allocated_capital / price
                    
        self.index_df = pd.DataFrame({'Date': dates, 'Valore Indice': index_values})
        self.index_df.set_index('Date', inplace=True)
        self.weights_df = pd.DataFrame.from_dict(daily_weights_history, orient='index')
        self.mktcap_df = df_mktcap 
        
        print(f"Backtest completato. Composizione FINALE del portafoglio al {dates[-1].strftime('%Y-%m-%d')}:")

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
            self._save_metrics_json(save_json_dir) 

        perf_fig.show()
        stats_fig.show()

        try:
            weights_title = (f"{title} - Pesi") if title else None
            self.plot_weights(weights_title, save_json_dir=save_json_dir, return_fig=True)
        except Exception:
            pass

        if return_fig:
            return perf_fig, stats_fig, None

class VolMktCapStrategy(BaseCryptoStrategy):
    def run_strategy(self, rebalance_freq_days: int = 180, top_n: int = 5, btc_ticker: str = 'BTC-USD', **kwargs):
        # NOTA: Se questa strategia ti serve in futuro, la logica sarà simile a quella sotto,
        # ma con l'aggiunta di un filtro basato sulla volatilità prima di applicare i pesi.
        print("VolMktCapStrategy non ancora implementata. Usa MarketCapThresholdStrategy per gli indici settoriali.")
        pass 

class MarketCapThresholdStrategy(BaseCryptoStrategy):
    """
    Strategia usata per gli indici Tech, DeFi e Payments:
    Filtra gli asset che superano una soglia minima di Market Cap (es. 1 Miliardo)
    e li pesa proporzionalmente alla loro capitalizzazione.
    """
    def run_strategy(self, rebalance_freq_days: int = 180, min_mktcap: float = 1_000_000_000, btc_ticker: str = 'BTC-USD', **kwargs):
        if not self.data_dict:
            raise ValueError("Nessun dato disponibile. Esegui import_data() per primo.")
            
        print(f"\nAvvio backtest: Threshold Strategy (Mkt Cap > {min_mktcap/1e9}B$) con ribilanciamento (ogni {rebalance_freq_days} giorni)...")
        
        # --- 1. PREPARAZIONE DATI ---
        df_prices = pd.DataFrame()
        df_mktcap = pd.DataFrame()
        
        for ticker in self.assets:
            df = self.data_dict[ticker].copy()
            df['Market Cap'] = df['Prezzo di Chiusura'] * df['Circulating Supply']
            
            df.index = pd.to_datetime(df.index)
            df_prices[ticker] = df['Prezzo di Chiusura']
            df_mktcap[ticker] = df['Market Cap']
            
        df_prices.ffill(inplace=True)
        df_mktcap.ffill(inplace=True)
        df_prices.dropna(how='all', inplace=True)

        if df_prices.empty:
            raise ValueError("Nessun dato di prezzo valido dopo la pulizia.")
        
        dates = df_prices.index
        first_date = dates[0]
        
        # --- 2. CALCOLO DATE DI RIBILANCIAMENTO ---
        rebalance_dates = []
        current_target = first_date
        end = dates[-1]

        while current_target <= end:
            idx = dates.searchsorted(current_target)
            if idx < len(dates):
                candidate = dates[idx]
                if not rebalance_dates or candidate != rebalance_dates[-1]:
                    rebalance_dates.append(candidate)
            current_target = current_target + pd.Timedelta(days=rebalance_freq_days)

        self.rebalance_dates = rebalance_dates
        
        # --- 3. ALLINEAMENTO AL BENCHMARK (BTC) ---
        if btc_ticker in df_prices.columns:
            btc_initial_price = df_prices.loc[first_date, btc_ticker]
        else:
            try:
                yf_ticker = btc_ticker if "-" in btc_ticker else f"{btc_ticker}-USD"
                ticker_obj = yf.Ticker(yf_ticker)
                end_date = first_date + pd.Timedelta(days=3)
                btc_data = ticker_obj.history(start=first_date, end=end_date)
                btc_initial_price = float(btc_data['Close'].iloc[0]) if not btc_data.empty else 10000.0
            except Exception as e:
                print(f"Impossibile recuperare il prezzo di {btc_ticker} al {first_date}: {e}. Uso 10k come fallback.")
                btc_initial_price = 10000.0
                
        portfolio_value = float(btc_initial_price)
        self.portfolio_value = portfolio_value

        # --- 4. SIMULAZIONE DEL PORTAFOGLIO GIORNO PER GIORNO ---
        shares = {}
        current_assets = []
        index_values = []
        daily_weights_history = {}
        
        for current_date in dates:
            if shares:
                pv = 0.0
                for ticker in current_assets:
                    price = df_prices.loc[current_date, ticker]
                    if not pd.isna(price):
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
                
                eligible_assets = daily_mktcap[daily_mktcap >= min_mktcap]
                
                if not eligible_assets.empty:
                    current_assets = eligible_assets.index.tolist()
                    total_eligible_mktcap = eligible_assets.sum()
                    
                    weights = (eligible_assets / total_eligible_mktcap).to_dict()
                    
                    shares = {}
                    for ticker in current_assets:
                        price = df_prices.loc[current_date, ticker]
                        if pd.isna(price) or price <= 0:
                            shares[ticker] = 0.0
                            continue
                        allocated_capital = portfolio_value * weights[ticker]
                        shares[ticker] = allocated_capital / price
                        
        # --- 5. SALVATAGGIO PER L'ESPORTAZIONE ---
        self.index_df = pd.DataFrame({'Date': dates, 'Valore Indice': index_values})
        self.index_df.set_index('Date', inplace=True)
        self.weights_df = pd.DataFrame.from_dict(daily_weights_history, orient='index')
        self.mktcap_df = df_mktcap

class EqualWeightThresholdStrategy(BaseCryptoStrategy):
    """
    Simile alla precedente, ma assegna un peso uguale (Equal Weight)
    a tutti gli asset che superano la soglia.
    """
    def run_strategy(self, rebalance_freq_days: int = 180, min_mktcap: float = 1_000_000_000, btc_ticker: str = 'BTC-USD', **kwargs):
        # [Logica identica a MarketCapThresholdStrategy, ma cambia il calcolo dei pesi]
        # Invece di: weights = (eligible_assets / total_eligible_mktcap).to_dict()
        # Si usa:
        # equal_weight = 1.0 / len(eligible_assets)
        # weights = {ticker: equal_weight for ticker in eligible_assets.index}
        print("EqualWeightThresholdStrategy in fase di implementazione...")
        pass

# ==========================================
# NUOVA CLASSE PER LA MARKET ANALYTICS
# ==========================================

class GlobalMarketAnalytics(BaseCryptoStrategy):
    """
    Questa classe si occupa unicamente di generare grafici macro sul mercato
    utilizzando i dati globali degli asset scaricati.
    """
    
    def run_strategy(self, **kwargs):
        pass

    def _slice_timeframe(self, df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
        """Helper interno per tagliare il dataframe in base al timeframe desiderato."""
        if df.empty or timeframe == 'max':
            return df
        
        last_date = df.index[-1]
        tf = timeframe.lower().strip()
        
        try:
            if tf.endswith('mo'):
                months = int(tf.replace('mo', ''))
                cutoff = last_date - pd.DateOffset(months=months)
            elif tf.endswith('y'):
                years = int(tf.replace('y', ''))
                cutoff = last_date - pd.DateOffset(years=years)
            elif tf.endswith('d'):
                days = int(tf.replace('d', ''))
                cutoff = last_date - pd.DateOffset(days=days)
            elif tf == 'ytd':
                cutoff = pd.Timestamp(year=last_date.year, month=1, day=1, tz=last_date.tz)
            else:
                return df 
            
            return df[df.index >= cutoff]
        except Exception as e:
            print(f"Errore nel taglio del timeframe '{timeframe}': {e}")
            return df
        
    def generate_analytics_charts(self, 
                                  conio_coin: list,
                                  save_dir: str = "charts/market_analytics", 
                                  tf_dom: str = '1y',     
                                  tf_vol: str = '3mo',    
                                  show_figs: bool = False):
        """
        Genera e salva in JSON i grafici richiesti.
        Permette di definire timeframe indipendenti per ogni grafico.
        La Heatmap è calcolata di default sugli ultimi 12 mesi completati.
        """
        if not self.data_dict:
            raise ValueError("Nessun dato disponibile. Esegui import_data() prima.")
            
        print(f"\nGenerazione grafici Market Analytics in '{save_dir}'...")
        os.makedirs(save_dir, exist_ok=True)
        
        # Preparazione Dati Totali 
        df_prices_full = pd.DataFrame()
        df_vol_full = pd.DataFrame()
        df_mktcap_full = pd.DataFrame()
        
        for ticker in self.assets:
            df = self.data_dict[ticker]
            df_prices_full[ticker] = df['Prezzo di Chiusura']
            df_vol_full[ticker] = df['Volume 24h']
            df_mktcap_full[ticker] = df['Prezzo di Chiusura'] * df['Circulating Supply']
            
        df_prices_full.ffill(inplace=True)
        df_vol_full.ffill(inplace=True)
        df_mktcap_full.ffill(inplace=True)
        
        # ---------------------------------------------------------
        # GRAFICO 1: Bitcoin Dominance (%) 
        # ---------------------------------------------------------
        df_mktcap_dom = self._slice_timeframe(df_mktcap_full, tf_dom)
        
        total_mktcap = df_mktcap_dom.sum(axis=1)
        if 'BTC-USD' in df_mktcap_dom.columns:
            btc_dom = (df_mktcap_dom['BTC-USD'] / total_mktcap) * 100
            
            fig_dom = go.Figure()
            fig_dom.add_trace(go.Scatter(x=btc_dom.index, y=btc_dom, mode='lines', fill='tozeroy', name='BTC Dominance', line=dict(color='#F7931A', width=2)))
            fig_dom.update_layout(
                margin=dict(l=40, r=40, t=40, b=40), plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                hovermode="x unified", yaxis=dict(title="Dominance (%)", tickformat=".2f")
            )
            fig_dom.write_json(os.path.join(save_dir, "btc_dominance.json"))
            if show_figs: fig_dom.show()
            print(f" - btc_dominance.json ({tf_dom}) salvato.")
            
        # ---------------------------------------------------------
        # GRAFICO 2: Volume Globale di Mercato (24h) 
        # ---------------------------------------------------------
        df_vol_chart = self._slice_timeframe(df_vol_full, tf_vol)
        total_vol = df_vol_chart.sum(axis=1)
        
        fig_vol = go.Figure(go.Bar(x=total_vol.index, y=total_vol, marker_color='#1f77b4', name='Global Volume'))
        fig_vol.update_layout(
            margin=dict(l=40, r=40, t=40, b=40), plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            hovermode="x unified", yaxis=dict(title="Volume 24h ($)", tickformat="$,.0f")
        )
        fig_vol.write_json(os.path.join(save_dir, "market_volume.json"))
        if show_figs: fig_vol.show()
        print(f" - market_volume.json ({tf_vol}) salvato.")

        # ---------------------------------------------------------
        # GRAFICO 3: Fear & Greed Index 
        # ---------------------------------------------------------
        fng_val, fng_text = 50, "Neutral"
        try:
            r = requests.get("https://api.alternative.me/fng/", timeout=5)
            if r.status_code == 200:
                data = r.json()
                fng_val = int(data['data'][0]['value'])
                fng_text = data['data'][0]['value_classification']
        except Exception as e:
            print(f"Errore recupero API Fear & Greed: {e}")
            
        fig_fng = go.Figure(go.Indicator(
            mode="gauge+number", value=fng_val, title={'text': f"<span style='font-size:0.8em;color:gray'>{fng_text}</span>"},
            gauge={
                'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
                'bar': {'color': "rgba(0,0,0,0)"}, 'bgcolor': "white", 'borderwidth': 2, 'bordercolor': "gray",
                'steps': [{'range': [0, 24], 'color': "#ef4444"}, {'range': [25, 45], 'color': "#f97316"},
                          {'range': [46, 54], 'color': "#eab308"}, {'range': [55, 74], 'color': "#84cc16"},
                          {'range': [75, 100], 'color': "#22c55e"}],
                'threshold': {'line': {'color': "black", 'width': 5}, 'thickness': 0.8, 'value': fng_val}
            }
        ))
        fig_fng.update_layout(margin=dict(l=20, r=20, t=50, b=20), plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        fig_fng.write_json(os.path.join(save_dir, "fear_and_greed.json"))
        if show_figs: fig_fng.show()
        print(" - fear_and_greed.json salvato.")

        # ---------------------------------------------------------
        # GRAFICO 4: Correlazione con BTC vs Ultimi 12 Mesi
        # ---------------------------------------------------------
        valid_coins = [c for c in conio_coin if c in df_prices_full.columns]
        
        if valid_coins and 'BTC-USD' in valid_coins:
            corr_results = {}
            
            last_data_date = df_prices_full.index[-1]
            current_month_start = pd.Timestamp(year=last_data_date.year, month=last_data_date.month, day=1, tz=last_data_date.tz)
            
            for i in range(12, 0, -1):
                m_start = current_month_start - pd.DateOffset(months=i)
                m_end = current_month_start - pd.DateOffset(months=i-1) - pd.Timedelta(days=1)
                
                label = m_start.strftime("%b %y")
                df_m = df_prices_full.loc[m_start:m_end][valid_coins]
                
                if len(df_m) > 5:
                    # RIMOSSO IL .dropna() DA QUI! In questo modo non distrugge le righe se un asset non esiste.
                    ret_m = df_m.pct_change()
                    
                    # corrwith gestisce automaticamente e a coppie le date vuote.
                    corr_results[label] = ret_m.corrwith(ret_m['BTC-USD'])
                else:
                    corr_results[label] = pd.Series(index=valid_coins, dtype=float)
                    
            df_heatmap = pd.DataFrame(corr_results)
            
            if 'BTC-USD' in df_heatmap.index:
                df_heatmap.drop(index='BTC-USD', inplace=True)
                
            # Riordiniamo le righe in base alla lista originale per mantenere l'ordine desiderato
            y_assets = [c for c in valid_coins if c != 'BTC-USD']
            df_heatmap = df_heatmap.reindex(y_assets)
            
            import re
            clean_y_names = [re.sub(r'\d+', '', str(c).replace('-USD', '')) for c in df_heatmap.index]
            
            custom_colorscale = [
                [0.0, "#04114f"],
                [0.5, "#0050ff"],
                [0.75, "#8800ff"],
                [1.0, "#ffffff"]
            ]
            
            fig_corr = px.imshow(
                df_heatmap.values, 
                x=df_heatmap.columns, 
                y=clean_y_names, 
                color_continuous_scale=custom_colorscale, 
                zmin=-1, zmax=1,                   
                aspect="auto"
            )
            
            fig_corr.update_traces(
                hovertemplate='Asset: %{y}<br>Mese: %{x}<br>Correlazione con BTC: %{z:.2f}<extra></extra>'
            )
            
            fig_corr.update_layout(
                margin=dict(l=40, r=40, t=40, b=40), 
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)"
            )
            fig_corr.write_json(os.path.join(save_dir, "correlation_heatmap.json"))
            if show_figs: fig_corr.show()
            print(" - correlation_heatmap.json salvato.\n")
        else:
            print(" - Errore Heatmap: BTC-USD mancante dall'universo o lista conio_coin vuota.")