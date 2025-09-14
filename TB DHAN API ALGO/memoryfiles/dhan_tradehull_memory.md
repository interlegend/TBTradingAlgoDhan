# Dhan Tradehull API and Instrument Master File Details

## Overview
This document contains important details about the Dhan Tradehull API and the instrument master file structure based on analysis of the `all_instrument 2025-09-10.csv` file.

## Instrument Master File Structure
The instrument master file (`all_instrument 2025-09-10.csv`) contains detailed information about all tradable instruments. Key columns include:

1. **SEM_EXM_EXCH_ID** - Exchange ID (NSE, BSE)
2. **SEM_SEGMENT** - Market segment
3. **SEM_SMST_SECURITY_ID** - Security ID
4. **SEM_INSTRUMENT_NAME** - Instrument type (OPTIDX, FUTCUR, etc.)
5. **SEM_EXPIRY_CODE** - Expiry code
6. **SEM_TRADING_SYMBOL** - Trading symbol used for API calls
7. **SEM_LOT_UNITS** - Lot size
8. **SEM_CUSTOM_SYMBOL** - Custom symbol/underlying
9. **SEM_EXPIRY_DATE** - Expiry date
10. **SEM_STRIKE_PRICE** - Strike price (for options)
11. **SEM_OPTION_TYPE** - Option type (CE for Call, PE for Put)
12. **SEM_TICK_SIZE** - Tick size
13. **SEM_EXPIRY_FLAG** - Expiry flag
14. **SEM_EXCH_INSTRUMENT_TYPE** - Exchange instrument type
15. **SEM_SERIES** - Series
16. **SM_SYMBOL_NAME** - Symbol name

## Exchange IDs
- **NSE** - National Stock Exchange
- **BSE** - Bombay Stock Exchange

## Instrument Types
- **OPTIDX** - Index Options
- **FUTCUR** - Currency Futures
- **OPTCUR** - Currency Options
- **EQUITY** - Equity shares
- **ETF** - Exchange Traded Funds

## Option Types
- **CE** - Call European
- **PE** - Put European
- **XX** - Not applicable (for futures)

## NIFTY Index Options Details
NIFTY index options are available with the following characteristics:
- **Exchange**: NSE
- **Instrument Type**: OPTIDX
- **Underlying**: NIFTY (and variations like NIFTYNXT50)
- **Lot Size**: 75 (standard for NIFTY options)
- **Tick Size**: 5.0
- **Option Types**: CE (Call) and PE (Put)

Example NIFTY option symbols:
- NIFTY-Sep2025-19200-CE
- NIFTY-Sep2025-19200-PE

## BANKNIFTY Index Options Details
BANKNIFTY index options are available with the following characteristics:
- **Exchange**: NSE
- **Instrument Type**: OPTIDX
- **Underlying**: BANKNIFTY
- **Lot Size**: 35 (standard for BANKNIFTY options)
- **Tick Size**: 5.0
- **Option Types**: CE (Call) and PE (Put)

Example BANKNIFTY option symbols:
- BANKNIFTY-Sep2025-40600-CE
- BANKNIFTY-Sep2025-40600-PE

## Important Notes for Tradehull API
1. **Symbol Format**: Use the exact `SEM_TRADING_SYMBOL` from the instrument master file when making API calls
2. **Exchange Parameter**: Specify the correct exchange (NSE or BSE) when making API calls
3. **Lot Sizes**: Different indices have different lot sizes (NIFTY: 75, BANKNIFTY: 35)
4. **Instrument Resolution**: Use the `order_manager.py` functions to resolve ATM/ITM/OTM options based on spot price and date

## Common API Parameters
When using the Tradehull API wrapper:
- **tradingsymbol**: Exact trading symbol from SEM_TRADING_SYMBOL
- **exchange**: Exchange ID (NSE, BSE)
- **instrument_type**: OPTIDX for index options
- **option_type**: CE or PE for options
- **strike_price**: Numerical strike price
- **expiry_date**: Expiry date in required format

## File Location
The instrument master file is located at:
`TB DHAN API ALGO/Dependencies/all_instrument 2025-09-10.csv`

This file is essential for resolving trading symbols and understanding instrument characteristics when using the Dhan Tradehull API.