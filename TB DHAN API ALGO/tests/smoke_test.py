import os
import pytest
import pandas as pd

# These tests are network-bound and require valid credentials in config.py.
# They are skipped by default unless RUN_NETWORK_TESTS=1 is set.

RUN_NET = os.environ.get("RUN_NETWORK_TESTS") == "1"

pytestmark = pytest.mark.skipif(not RUN_NET, reason="Set RUN_NETWORK_TESTS=1 to run network smoke tests.")


def test_index_bars_alignment():
    from data_fetcherperp import set_tsl, get_nifty_ohlc
    set_tsl()
    df = get_nifty_ohlc(interval=5)
    assert df is not None and not df.empty
    # Expect at least 30 bars intra-session
    assert len(df) >= 30
    # First bar at 09:15 IST
    ts0 = pd.to_datetime(df["datetime"].iloc[0]) if "datetime" in df.columns else pd.to_datetime(df["timestamp"].iloc[0])
    assert ts0.tz_convert("Asia/Kolkata").strftime("%H:%M") == "09:15"


def test_atm_symbol_resolution():
    from data_fetcherperp import set_tsl, get_nifty_ohlc
    from order_manager import get_atm_option_symbols
    set_tsl()
    idx = get_nifty_ohlc(interval=5)
    spot = float(idx["close"].iloc[-1])
    res = get_atm_option_symbols(spot=spot)
    assert "CE_symbol" in res and "PE_symbol" in res
    assert isinstance(res["CE_symbol"], str) and isinstance(res["PE_symbol"], str)


def test_option_ohlc_schema():
    from data_fetcherperp import set_tsl, get_nifty_ohlc, get_option_ohlc
    from order_manager import get_atm_option_symbols
    set_tsl()
    idx = get_nifty_ohlc(interval=5)
    spot = float(idx["close"].iloc[-1])
    atm = get_atm_option_symbols(spot=spot)
    ce = get_option_ohlc(atm["CE_symbol"], interval=5, exchange="NFO")
    assert not ce.empty
    cols = ["datetime", "open", "high", "low", "close"]
    for c in cols:
        assert c in ce.columns

