import os
import json
import time
import datetime
import requests
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor, as_completed

_FALLBACK_EURUSD_RATE = 1.08
_CG_API_KEY = "CG-S9X7s5DvT8wi2C2Rx6eNYq7a"


# ------------------------------------------------------------------
# Helpers per la conversione del timeframe
# ------------------------------------------------------------------

def _get_since_timestamp(timeframe: str) -> int:
    """Converte una stringa timeframe (es. '5y', '3mo') in un Unix timestamp."""
    now = datetime.datetime.utcnow()
    tf = timeframe.lower().strip()
    try:
        if tf.endswith('y'):
            delta = datetime.timedelta(days=int(tf[:-1]) * 365)
        elif tf.endswith('mo'):
            delta = datetime.timedelta(days=int(tf[:-2]) * 30)
        elif tf.endswith('d'):
            delta = datetime.timedelta(days=int(tf[:-1]))
        else:
            delta = datetime.timedelta(days=5 * 365)
    except Exception:
        delta = datetime.timedelta(days=5 * 365)
    return int((now - delta).timestamp())


# ------------------------------------------------------------------
# Fetch prezzi da Conio
# ------------------------------------------------------------------

def _fetch_conio_ohlc(conio_ticker: str, start_ts: int, end_ts: int) -> list:
    """Scarica prezzi giornalieri in EUR dall'API Conio, pagina per anno."""
    all_parsed = {}
    current_start = start_ts
    step = 365 * 24 * 3600

    while current_start < end_ts:
        curr_end = min(current_start + step, end_ts)
        url = (f"https://pricing.conio.com/api/v2.0/price/{conio_ticker}/historical"
               f"?interval=86400&start={current_start}&end={curr_end}")
        try:
            r = requests.get(url, timeout=15)
            if r.status_code != 200:
                current_start += step
                continue
            recs = r.json().get('values', [])
            if not recs:
                current_start += step
                continue
            for item in recs:
                ts = int(item.get('timestamp_sec', 0))
                date_str = datetime.datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d')
                all_parsed[date_str] = {"Date": date_str, "Price": float(item.get('fiat', 0))}
            last_ts = recs[-1].get('timestamp_sec', 0)
            current_start = last_ts + 86400 if last_ts > current_start else current_start + step
            time.sleep(0.3)
        except Exception:
            current_start += step

    return sorted(all_parsed.values(), key=lambda x: x['Date'])


# ------------------------------------------------------------------
# Fetch volumi da Kraken
# ------------------------------------------------------------------

def _fetch_kraken_volume(pair: str, since: int) -> list:
    """Scarica volumi giornalieri da Kraken OHLC (campo volume = entry[6])."""
    all_parsed = {}
    current_since = since
    last_timestamp = 0

    while True:
        url = f"https://api.kraken.com/0/public/OHLC?pair={pair}&interval=1440&since={current_since}"
        try:
            r = requests.get(url, timeout=15)
            if r.status_code != 200:
                break
            data = r.json()
            if data.get('error'):
                break
            result_keys = [k for k in data['result'] if k != 'last']
            if not result_keys:
                break
            records = data['result'][result_keys[0]]
            kraken_last = data['result'].get('last', 0)
            if not records or kraken_last == last_timestamp:
                break
            for entry in records:
                date_str = datetime.datetime.utcfromtimestamp(int(entry[0])).strftime('%Y-%m-%d')
                all_parsed[date_str] = {"Date": date_str, "Volume": float(entry[6])}
            last_timestamp = current_since
            current_since = kraken_last
            time.sleep(0.5)
        except Exception:
            break

    return sorted(all_parsed.values(), key=lambda x: x['Date'])


# ------------------------------------------------------------------
# Fetch supply storica da CoinGecko
# ------------------------------------------------------------------

def _fetch_cg_market_history(coingecko_id: str) -> dict:
    """
    Recupera la history completa (price + market cap) da CoinGecko.
    Calcola la circulating supply come mcap / price.
    Ritorna {date_str: {"supply": int, "mcap": float}}.
    """
    if not coingecko_id:
        return {}

    url = f"https://api.coingecko.com/api/v3/coins/{coingecko_id}/market_chart?vs_currency=eur&days=max"
    headers = {"accept": "application/json", "x-cg-demo-api-key": _CG_API_KEY}
    history = {}

    for attempt in range(3):
        try:
            r = requests.get(url, headers=headers, timeout=30)
            if r.status_code == 200:
                data = r.json()
                for (pts, p_val), (_, m_val) in zip(data.get('prices', []), data.get('market_caps', [])):
                    if p_val and p_val > 0 and m_val and m_val > 0:
                        date_str = datetime.datetime.utcfromtimestamp(pts / 1000).strftime('%Y-%m-%d')
                        history[date_str] = {"supply": round(m_val / p_val), "mcap": m_val}
                time.sleep(1.5)
                return history
            if r.status_code == 429:
                print(f"  [CoinGecko] Rate limit per {coingecko_id}. Attesa 30s...")
                time.sleep(30)
            else:
                print(f"  [CoinGecko] Errore {r.status_code} per {coingecko_id}")
                return history
        except Exception as e:
            print(f"  [CoinGecko] Errore connessione per {coingecko_id}: {e}")
            time.sleep(2)

    return history


# ------------------------------------------------------------------
# Fetch supply storica da Yahoo Finance
# ------------------------------------------------------------------

def _fetch_yf_supply(yf_ticker: str, start_str: str, end_str: str) -> dict:
    """Scarica circulating supply storica da Yahoo Finance."""
    history = {}
    if not yf_ticker:
        return history
    try:
        shares = yf.Ticker(yf_ticker).get_shares_full(start=start_str, end=end_str)
        if shares is not None and len(shares) > 0:
            for ts_idx, val in shares.items():
                if val and val > 0:
                    date_str = ts_idx.strftime('%Y-%m-%d') if hasattr(ts_idx, 'strftime') else str(ts_idx)[:10]
                    history[date_str] = {"supply": int(val), "mcap": None}
    except Exception:
        pass
    return history


# ------------------------------------------------------------------
# Fetch cambio EUR/USD
# ------------------------------------------------------------------

def fetch_eurusd_history() -> dict:
    """Recupera la cronologia del cambio EUR/USD (10 anni) da Yahoo Finance."""
    print("  [Setup] Recupero storico cambio EURUSD=X...")
    try:
        df = yf.Ticker("EURUSD=X").history(period="10y")
        return {d.strftime('%Y-%m-%d'): v for d, v in zip(df.index, df['Close'])}
    except Exception as e:
        print(f"  [Errore] Impossibile recuperare EURUSD: {e}")
        return {}


# ------------------------------------------------------------------
# Funzione principale
# ------------------------------------------------------------------

def download_all_market_data(assets: list, timeframe: str = "5y",
                              data_dir: str = "data", benchmark_ticker: str = 'BTC'):
    """
    Scarica e salva i dati storici per ogni asset.

    Flusso per ciascun asset:
      A) CSV CoinGecko locale (data/cg_data/{symbol}-usd-max.csv) → conversione USD→EUR
      B) Fallback API: Conio (prezzi) + Kraken (volumi) + CoinGecko/YF (supply)

    Output:
      - data/{symbol}/prices.json  → Price, Circulating Supply, Market Cap
      - data/{symbol}/volume.json  → Volume (Calculated from data/cg_volume_data/{symbol}.json and current Price)
    """
    print(f"Inizio download dati per il periodo '{timeframe}'...")
    os.makedirs(data_dir, exist_ok=True)

    try:
        with open("master_assets.json", "r") as f:
            master_registry = json.load(f)
    except FileNotFoundError:
        print("Errore: file 'master_assets.json' non trovato.")
        return

    unique_assets = list(set(assets + [benchmark_ticker]))
    start_ts = _get_since_timestamp(timeframe)
    start_str = datetime.datetime.utcfromtimestamp(start_ts).strftime('%Y-%m-%d')
    end_str = datetime.datetime.utcnow().strftime('%Y-%m-%d')
    eurusd_map = fetch_eurusd_history()
    cg_csv_dir = os.path.join(data_dir, "cg_data")

    # --- Fetch supply storica Alternative.me (fallback corrente) ---
    altme_supply = {}
    try:
        r = requests.get("https://api.alternative.me/v2/ticker/?limit=0", timeout=10)
        if r.status_code == 200:
            for coin_data in r.json().get('data', {}).values():
                symbol = coin_data.get('symbol', '').upper()
                altme_supply[symbol] = coin_data.get('circulating_supply')
        print(f"Alternative.me: recuperati {len(altme_supply)} simboli.")
    except Exception as e:
        print(f"Avviso: impossibile recuperare supply da Alternative.me: {e}")

    # --- Pre-fetch supply storica (CoinGecko + YF) in parallelo ---
    print(f"\nPre-fetch supply storica per {len(unique_assets)} asset (CoinGecko + YF)...")

    def fetch_merged_history(symbol: str) -> tuple:
        """Unisce CoinGecko (fonte primaria) e Yahoo Finance (fallback)."""
        info = master_registry.get(symbol, {})
        cg_data = _fetch_cg_market_history(info.get("coingecko_id", ""))
        yf_data = _fetch_yf_supply(info.get("yf_ticker", ""), start_str, end_str)
        merged = {d: cg_data[d] for d in set(cg_data) | set(yf_data) if d in cg_data or d in yf_data}
        # CoinGecko ha priorità
        for d in yf_data:
            if d not in merged:
                merged[d] = yf_data[d]
        return symbol, merged, len(cg_data), len(yf_data)

    all_supply_histories = {}
    with ThreadPoolExecutor(max_workers=1) as executor:
        futures = {executor.submit(fetch_merged_history, sym): sym
                   for sym in unique_assets if sym in master_registry}
        for future in as_completed(futures):
            sym, merged, cg_days, yf_days = future.result()
            all_supply_histories[sym] = merged
            print(f"  {sym}: CG={cg_days}gg, YF={yf_days}gg -> merge={len(merged)}gg")

    # --- Elaborazione per asset ---
    for base_symbol in unique_assets:
        try:
            asset_info = master_registry.get(base_symbol)
            if not asset_info:
                continue

            print(f"\nElaborazione {base_symbol}...")
            asset_folder = os.path.join(data_dir, base_symbol)
            os.makedirs(asset_folder, exist_ok=True)
            prices_file = os.path.join(asset_folder, "prices.json")
            volume_file = os.path.join(asset_folder, "volume.json")
            final_prices = []
            final_volumes = []

            # A. Caricamento PREZZI da CSV CoinGecko (USD → EUR)
            csv_path = os.path.join(cg_csv_dir, f"{base_symbol.lower()}-usd-max.csv")
            if not os.path.exists(csv_path):
                csv_path = os.path.join(cg_csv_dir, f"{base_symbol}-usd-max.csv")

            if os.path.exists(csv_path):
                print(f"  [CSV] {os.path.basename(csv_path)} trovato. Conversione USD → EUR per i prezzi...")
                try:
                    import pandas as pd
                    df_csv = pd.read_csv(csv_path)
                    for _, row in df_csv.iterrows():
                        date_str = str(row['snapped_at']).split(' ')[0]
                        rate = eurusd_map.get(date_str, _FALLBACK_EURUSD_RATE)
                        p_usd = row['price']
                        m_usd = row['market_cap']
                        if pd.notna(p_usd) and pd.notna(m_usd) and p_usd > 0:
                            final_prices.append({
                                "Date": date_str,
                                "Price": round(p_usd / rate, 6),
                                "Circulating Supply": round(m_usd / p_usd),
                                "Market Cap": m_usd / rate,
                            })
                except Exception as e:
                    print(f"  [Errore CSV Prezzi] {e}")
                    final_prices = []

            # B. Fallback API Prezzi (Conio + CoinGecko/YF)
            if not final_prices:
                print(f"  [API] Scaricamento prezzi da Conio...")
                conio_ticker = asset_info["conio_ticker"]
                new_prices = _fetch_conio_ohlc(conio_ticker, start_ts, int(time.time()))
                supply_history = all_supply_histories.get(base_symbol, {})
                fallback_supply = altme_supply.get(asset_info.get("alt_me_symbol", ""), 0) or 0
                sorted_supply_dates = sorted(supply_history)

                for p in new_prices:
                    date = p['Date']
                    if sorted_supply_dates:
                        if date in supply_history:
                            rec = supply_history[date]
                        else:
                            past = [d for d in sorted_supply_dates if d <= date]
                            rec = supply_history[past[-1]] if past else supply_history[sorted_supply_dates[0]]
                        p['Circulating Supply'] = rec['supply']
                        p['Market Cap'] = rec['mcap'] if rec.get('mcap') else p['Price'] * rec['supply']
                    else:
                        p['Circulating Supply'] = fallback_supply
                        p['Market Cap'] = p['Price'] * fallback_supply

                final_prices = new_prices

            # C. Caricamento VOLUMI da cg_volume_data (Sommatoria + Conversione EUR)
            cg_vol_file = os.path.join(data_dir, "cg_volume_data", f"{base_symbol}.json")
            if not os.path.exists(cg_vol_file) and base_symbol == "POL":
                cg_vol_file = os.path.join(data_dir, "cg_volume_data", "MATIC.json")

            if os.path.exists(cg_vol_file):
                print(f"  [Volume] Caricamento da {os.path.basename(cg_vol_file)}...")
                try:
                    with open(cg_vol_file, "r") as f:
                        raw_vols = json.load(f)
                    
                    # Raggruppiamo per data (somma canali/exchange)
                    daily_vols_units = {}
                    for entry in raw_vols:
                        dt = entry.get("Data")
                        v_units = entry.get("Volume", 0)
                        if dt:
                            daily_vols_units[dt] = daily_vols_units.get(dt, 0) + v_units
                    
                    # Convertiamo in EUR usando i prezzi caricati
                    price_map = {p['Date']: p['Price'] for p in final_prices}
                    for dt in sorted(daily_vols_units.keys()):
                        price = price_map.get(dt)
                        if price is not None:
                            final_volumes.append({
                                "Date": dt,
                                "Volume": daily_vols_units[dt] * price
                            })
                except Exception as e:
                    print(f"  [Errore Volume] {e}")
            else:
                print(f"  [Avviso] File volumi non trovato: {cg_vol_file}")

            # Filtro speciale ATOM
            if base_symbol == "ATOM":
                final_prices = [p for p in final_prices if p['Date'] >= "2023-06-16"]

            # Salvataggio
            if final_prices:
                with open(prices_file, 'w') as f:
                    json.dump(final_prices, f, indent=4)
                print(f"  Prices: {len(final_prices)} record salvati.")
            if final_volumes:
                with open(volume_file, 'w') as f:
                    json.dump(final_volumes, f, indent=4)
                print(f"  Volume: {len(final_volumes)} record salvati.")

        except Exception as e:
            print(f"Errore durante l'elaborazione di {base_symbol}: {e}")

    print("\n--- AGGIORNAMENTO COMPLETATO CON SUCCESSO ---")
