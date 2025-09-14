# ---- order_manager.py (fixed) ----
import os
import pandas as pd
from datetime import datetime
import pytz

IST = pytz.timezone("Asia/Kolkata")

def _normalize_instruments(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize instrument CSV column names to canonical ones."""
    cols = {c.lower(): c for c in df.columns}

    def pick(*names):
        for n in names:
            if n.lower() in cols:
                return cols[n.lower()]
        return None

    ren = {}
    if pick("sem_trading_symbol"):
        ren[pick("sem_trading_symbol")] = "SEM_TRADING_SYMBOL"
    if pick("sem_custom_symbol"):
        ren[pick("sem_custom_symbol")] = "UNDERLYING"
    if pick("sem_expiry_date"):
        ren[pick("sem_expiry_date")] = "EXPIRY"
    if pick("sem_strike_price"):
        ren[pick("sem_strike_price")] = "STRIKE_PRICE"
    if pick("sem_option_type"):
        ren[pick("sem_option_type")] = "OPTION_TYPE"
    if pick("sem_exm_exch_id"):
        ren[pick("sem_exm_exch_id")] = "EXCHANGE"

    df = df.rename(columns=ren)

    # Parse types
    if "EXPIRY" in df.columns:
        df["EXPIRY"] = pd.to_datetime(df["EXPIRY"], errors="coerce").dt.date
    if "STRIKE_PRICE" in df.columns:
        df["STRIKE_PRICE"] = pd.to_numeric(df["STRIKE_PRICE"], errors="coerce").astype("Int64")
    if "UNDERLYING" in df.columns:
        df["UNDERLYING"] = df["UNDERLYING"].astype(str).str.upper().str.strip()
    if "OPTION_TYPE" in df.columns:
        df["OPTION_TYPE"] = df["OPTION_TYPE"].astype(str).str.upper().str.strip()
    if "EXCHANGE" in df.columns:
        df["EXCHANGE"] = df["EXCHANGE"].astype(str).str.upper().str.strip()

    return df


def _nearest_50(x: float) -> int:
    return int(round(x / 50.0) * 50)


def get_atm_option_symbols_from_master(spot: float, when_dt, instrument_df: pd.DataFrame):
    """
    Return dict: {'CE_symbol', 'PE_symbol', 'exchange', 'expiry'}
    Based on nearest 50 strike and earliest valid expiry for NIFTY 50.
    """
    if not isinstance(when_dt, datetime):
        when_dt = pd.to_datetime(when_dt).to_pydatetime()
    when_date = when_dt.astimezone(IST).date()

    df = _normalize_instruments(instrument_df.copy())

    # Filter only NIFTY options (accept several common aliases)
    aliases = {"NIFTY", "NIFTY 50", "NIFTY50"}
    q = df[
        df.get("UNDERLYING").isin(aliases)
        & df["STRIKE_PRICE"].notna()
        & df["OPTION_TYPE"].isin(["CE", "PE", "CALL", "PUT"])
    ]
    if q.empty:
        raise ValueError("Instrument master missing NIFTY 50 option rows.")

    strike = _nearest_50(float(spot))
    q = q[q["STRIKE_PRICE"] == strike]

    if q.empty:
        # fallback: +/- 50
        for off in (50, -50, 100, -100):
            qq = df[
                (df.get("UNDERLYING") == "NIFTY 50")
                & (df["STRIKE_PRICE"] == strike + off)
                & df["OPTION_TYPE"].isin(["CE", "PE"])
            ]
            if not qq.empty:
                q = qq
                strike = strike + off
                break

    if q.empty:
        raise ValueError("No rows for NIFTY 50 strike near ATM in instrument master.")

    # Earliest expiry >= today
    q = q[q["EXPIRY"] >= when_date].sort_values("EXPIRY")
    if q.empty:
        q = df[(df.get("UNDERLYING") == "NIFTY 50") & (df["STRIKE_PRICE"] == strike)].sort_values("EXPIRY")
        if q.empty:
            raise ValueError("Could not find any future expiry for NIFTY 50 in instrument master.")

    expiry = q["EXPIRY"].iloc[0]
    exch = q["EXCHANGE"].iloc[0]

    ce_row = q[q["OPTION_TYPE"] == "CE"].head(1)
    pe_row = q[q["OPTION_TYPE"] == "PE"].head(1)

    if ce_row.empty or pe_row.empty:
        raise ValueError("Missing CE/PE symbols for ATM strike.")

    ce_symbol = ce_row["SEM_TRADING_SYMBOL"].iloc[0]
    pe_symbol = pe_row["SEM_TRADING_SYMBOL"].iloc[0]

    return {
        "CE_symbol": str(ce_symbol),
        "PE_symbol": str(pe_symbol),
        "exchange": str(exch),
        "expiry": expiry,
    }


# --- Backwards-compatible wrapper used by paper_trader.py ---
import glob

def _latest_instrument_csv(pattern: str = "all_instrument*.csv") -> str:
    files = sorted(glob.glob(pattern), key=os.path.getmtime)
    return files[-1] if files else None


def get_atm_option_symbols(spot: float, when_dt=None, instrument_csv: str = None):
    """
    Wrapper for convenience in paper_trader.
    - Auto-selects latest instrument CSV if not provided
    - Normalizes instrument master and delegates to get_atm_option_symbols_from_master
    - Prints a short diagnostic line on the resolved ATM symbols
    """
    if when_dt is None:
        when_dt = datetime.now(IST)
    if instrument_csv is None:
        instrument_csv = _latest_instrument_csv(r"C:\Users\sakth\Desktop\VSCODE\TB DHAN API ALGO\all_instrument*.csv")
        if instrument_csv is None:
            raise FileNotFoundError("No instrument CSV found (all_instrument*.csv)")

    inst_df = pd.read_csv(instrument_csv, low_memory=False, dtype=str)
    inst_df = _normalize_instruments(inst_df)

    # Normalize underlying values for matching
    if "UNDERLYING" in inst_df.columns:
        inst_df["UNDERLYING"] = inst_df["UNDERLYING"].astype(str).str.upper().str.strip()

    res = get_atm_option_symbols_from_master(spot, when_dt, inst_df)
    print(f"[ATM-RESOLVER] spot={float(spot):.2f} expiry={res.get('expiry')} CE={res.get('CE_symbol')} PE={res.get('PE_symbol')}")
    return res
