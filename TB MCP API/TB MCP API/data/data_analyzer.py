import pandas as pd
from ta.trend import MACD
from ta.volatility import BollingerBands
from ta.trend import ADXIndicator
import json
import os

# --- Load candle data ---
if not os.path.exists("fetched_candles.json"):
    print("❌ fetched_candles.json not found. Please run the data fetcher first.")
    exit(1)

with open("fetched_candles.json", "r") as f:
    candles = json.load(f)

df = pd.DataFrame(candles)

# --- Add MACD indicator ---
macd = MACD(close=df['close'])
df['macd'] = macd.macd()
df['macd_signal'] = macd.macd_signal()

# --- Detect MACD crossovers ---
df['macd_cross_up'] = (df['macd'] > df['macd_signal']) & (df['macd'].shift(1) <= df['macd_signal'].shift(1))
df['macd_cross_down'] = (df['macd'] < df['macd_signal']) & (df['macd'].shift(1) >= df['macd_signal'].shift(1))

df['breakout_signal'] = 'HOLD'
df.loc[df['macd_cross_up'], 'breakout_signal'] = 'BUY'
df.loc[df['macd_cross_down'], 'breakout_signal'] = 'SELL'

# --- Add Bollinger Bands ---
bb = BollingerBands(close=df['close'])
df['bb_high'] = bb.bollinger_hband()
df['bb_low'] = bb.bollinger_lband()

# --- Add ADX indicator ---
adx = ADXIndicator(high=df['high'], low=df['low'], close=df['close'])
df['adx'] = adx.adx()
df['adx_pos'] = adx.adx_pos()
df['adx_neg'] = adx.adx_neg()

# --- Print a basic summary ---
print("DataFrame Summary:")
print(df.describe())
print("\nFirst 5 rows:")
print(df.head())
print("\nLast 5 rows:")
print(df.tail())

# --- Print last 10 rows ---
print(df[['date', 'close', 'macd', 'macd_signal', 'macd_cross_up', 'macd_cross_down', 'breakout_signal']].tail(10))
