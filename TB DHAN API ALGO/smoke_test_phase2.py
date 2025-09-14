import pandas as pd
from data_fetcher import get_nifty_ohlc, get_option_ohlc, set_tsl
from order_manager import get_atm_option_symbols

def run_smoke_test():
    """
    Executes the Phase 2 smoke test:
    1. Initializes the Tradehull client.
    2. Fetches NIFTY OHLC.
    3. Resolves ATM CE/PE symbols.
    4. Fetches OHLC for the ATM call option.
    """
    try:
        print("[START] Running Phase 2 Smoke Test...")
        
        # 0. Initialize client
        set_tsl()

        # 1. Fetch NIFTY OHLC data successfully.
        nifty_df = get_nifty_ohlc(interval=5)
        if nifty_df is None or nifty_df.empty:
            raise RuntimeError("Failed to fetch NIFTY OHLC.")
        print("\n[SUCCESS] Fetched NIFTY OHLC data:")
        print(nifty_df.tail(2))

        # 2. Correctly resolve the ATM CE & PE symbols.
        spot_price = nifty_df['close'].iloc[-1]
        atm_info = get_atm_option_symbols(base_symbol='NIFTY', spot=spot_price)
        print(f"\n[SUCCESS] Resolved ATM symbols for spot={spot_price:.2f}:")
        print(atm_info)

        # 3. Fetch OHLC data for one of those option symbols.
        ce_symbol = atm_info['CE_symbol']
        ce_ohlc_df = get_option_ohlc(tradingsymbol=ce_symbol, interval=5)
        if ce_ohlc_df is None or ce_ohlc_df.empty:
            raise RuntimeError(f"Failed to fetch OHLC for ATM CE symbol: {ce_symbol}")
        print(f"\n[SUCCESS] Fetched OHLC for ATM CE ({ce_symbol}):")
        print(ce_ohlc_df.tail(2))
        
        print("\n[PASSED] Smoke Test Completed Successfully.")

    except Exception as e:
        print(f"\n[FAILED] Smoke Test encountered an error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_smoke_test()
