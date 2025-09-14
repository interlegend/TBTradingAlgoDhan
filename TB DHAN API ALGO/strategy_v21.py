import pandas as pd
import numpy as np
from datetime import time

# === Helper Functions ===
def EMA(series, period):
    return series.ewm(span=period, adjust=False).mean()

def ATR(df, period=14):
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    return true_range.rolling(period).mean()

def MACD(series, fast=12, slow=26, signal=9):
    ema_fast = EMA(series, fast)
    ema_slow = EMA(series, slow)
    macd = ema_fast - ema_slow
    macd_signal = EMA(macd, signal)
    macd_hist = macd - macd_signal
    return macd, macd_signal, macd_hist

# === Backtest Engine ===
def backtest(data):
    trades = []
    position = None

    for i in range(35, len(data)):  # warmup for indicators
        row = data.iloc[i]
        dt = row['datetime']
        t = dt.time()
        close = row['close']
        high = row['high']
        low = row['low']
        ema21 = row['ema21']
        atr = row['atr']
        macd = row['macd']
        signal = row['macd_signal']
        hist = row['macd_hist']

        # === Entry ===
        if not position and time(9, 30) <= t <= time(15, 15):
            rng = high - low
            ce_strength = (close - low) / rng if rng > 0 else 0
            pe_strength = (high - close) / rng if rng > 0 else 0
            bullish_cross = data['macd'].iloc[i-1] < data['macd_signal'].iloc[i-1] and macd > signal
            bearish_cross = data['macd'].iloc[i-1] > data['macd_signal'].iloc[i-1] and macd < signal
            hist_rising = hist > data['macd_hist'].iloc[i-1] > data['macd_hist'].iloc[i-2]
            hist_falling = hist < data['macd_hist'].iloc[i-1] < data['macd_hist'].iloc[i-2]

            if (bullish_cross or hist_rising) and (macd - signal) > 0.15 and ce_strength > 0.75 and close > ema21:
                position = dict(side="BUY_CE", entry_time=dt, entry_price=close,
                                sl=round(close - 1.5*atr, 2), tp1=close + 15, tp1_hit=False,
                                highest=close, sl_trail_count=0)
                print(f"[ENTRY] BUY_CE {dt} price={close}")

            elif (bearish_cross or hist_falling) and (macd - signal) < -0.15 and pe_strength > 0.75 and close < ema21:
                position = dict(side="SELL_PE", entry_time=dt, entry_price=close,
                                sl=round(close + 1.5*atr, 2), tp1=close - 15, tp1_hit=False,
                                lowest=low, sl_trail_count=0)
                print(f"[ENTRY] SELL_PE {dt} price={close}")

        # === Manage Trade ===
        if position:
            side = position['side']
            entry = position['entry_price']
            tp1 = position['tp1']

            # update highs/lows
            if side == "BUY_CE":
                position['highest'] = max(position['highest'], high)
            else:
                position['lowest'] = min(position['lowest'], low)

            # TP1 check (lock SL but do not exit same candle)
            if not position['tp1_hit']:
                if side == "BUY_CE" and high >= tp1:
                    position['tp1_hit'] = True
                    position['sl'] = round(tp1 - 2, 2)
                    position['tp1_candle'] = dt
                    print(f"[TP1] BUY_CE {dt} tp1={tp1} locked_sl={position['sl']}")

                elif side == "SELL_PE" and low <= tp1:
                    position['tp1_hit'] = True
                    position['sl'] = round(tp1 + 2, 2)
                    position['tp1_candle'] = dt
                    print(f"[TP1] SELL_PE {dt} tp1={tp1} locked_sl={position['sl']}")

                        # === Trail SL update (after TP1 candle only, use closes) ===
            if position.get('tp1_hit', False) and dt > position['tp1_candle']:
                if side == "BUY_CE":
                    position['highest'] = max(position['highest'], close)
                    new_sl = round(position['highest'] - 5, 2)
                    if new_sl > position['sl']:
                        position['sl'] = new_sl
                        position['sl_trail_count'] += 1
                        print(f"[TRAIL] BUY_CE {dt} new_sl={new_sl}")

                elif side == "SELL_PE":
                    position['lowest'] = min(position['lowest'], close)
                    new_sl = round(position['lowest'] + 5, 2)
                    if new_sl < position['sl']:
                        position['sl'] = new_sl
                        position['sl_trail_count'] += 1
                        print(f"[TRAIL] SELL_PE {dt} new_sl={new_sl}")

            # === Stop Loss / Trail Exit (skip same candle as TP1) ===
            if not (position.get('tp1_hit') and dt == position.get('tp1_candle')):
                if side == "BUY_CE" and close <= position['sl']:
                    reason = "SL Hit"
                    if position['tp1_hit']:
                        reason = "TP1 Only" if position['sl_trail_count'] == 0 else "Trail Profit"
                    print(f"[EXIT] BUY_CE {dt} {reason} @ {position['sl']}")
                    trades.append((position['entry_time'], side, entry, dt, position['sl'], reason, position['sl']))
                    position = None
                    continue

                elif side == "SELL_PE" and close >= position['sl']:
                    reason = "SL Hit"
                    if position['tp1_hit']:
                        reason = "TP1 Only" if position['sl_trail_count'] == 0 else "Trail Profit"
                    print(f"[EXIT] SELL_PE {dt} {reason} @ {position['sl']}")
                    trades.append((position['entry_time'], side, entry, dt, position['sl'], reason, position['sl']))
                    position = None
                    continue

            # === EMA Exit (skip same candle as TP1) ===
            if not (position.get('tp1_hit') and dt == position.get('tp1_candle')):
                if (side == "BUY_CE" and close < ema21) or (side == "SELL_PE" and close > ema21):
                    reason = "EMA Exit (post-TP1)" if position['tp1_hit'] else "EMA Exit"
                    print(f"[EXIT] {side} {dt} {reason} @ {close}")
                    trades.append((position['entry_time'], side, entry, dt, close, reason, position['sl']))
                    position = None
                    continue

            # EOD Exit
            if t >= time(15, 25):
                print(f"[EXIT] {side} {dt} EOD Exit @ {close}")
                trades.append((position['entry_time'], side, entry, dt, close, "EOD Exit", position['sl']))
                position = None
                continue

    # === Save Trade Log ===
    trade_rows, pnl = [], []
    for tr in trades:
        et, side, entry, xt, xp, reason, sl_val = tr
        pnl_pts = (xp - entry) if side == "BUY_CE" else (entry - xp)
        pnl_inr = pnl_pts * 75
        pnl.append(pnl_inr)
        trade_rows.append([
            et, side, entry, xt, xp, reason,
            sl_val,  # new column
            round(pnl_pts, 2), round(pnl_inr, 2)
        ])

    pd.DataFrame(trade_rows, columns=[
        "EntryTime", "Side", "EntryPrice", "ExitTime", "ExitPrice", "Reason",
        "Exit_SL_Value",  # new column
        "PnL_Points", "PnL_INR"
    ]).to_csv("V21_trade_log.csv", index=False)

    print("\n=== 📈 SUMMARY ===")
    print(f"Total Trades: {len(trades)}")
    print(f"Winrate: {(np.array(pnl) > 0).mean() * 100:.2f}%")
    print(f"PnL: ₹{sum(pnl):.2f}")



def run_backtest(data_path="nifty_5min_last_month.csv"):
    df = pd.read_csv(data_path)
    df['datetime'] = pd.to_datetime(df['datetime'])
    df['ema21'] = EMA(df['close'], 21)
    df['macd'], df['macd_signal'], df['macd_hist'] = MACD(df['close'])
    df['atr'] = ATR(df)
    return backtest(df)
