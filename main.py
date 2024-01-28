import os
import datetime
import pandas as pd
import dotenv
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame


dotenv.load_dotenv()
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
ALPACA_BASE_URL = os.getenv("ALPACA_BASE_URL")
TIME_INTERVAL = os.getenv("TIME_INTERVAL")

def get_watchlist():
    """ Converts watchlist.csv to pandas dataframe """
    watchlist_name = "./watchlist.csv"
    print(f"Reading {watchlist_name}...")
    tickers_watchlist = pd.read_csv(watchlist_name)
    return tickers_watchlist


def get_historical_data_start_date(days=30):
    """ Gets start date n days back from today """
    start_date = datetime.date.today() - datetime.timedelta(days=days)
    return start_date


def get_historical_data_timeframe(time_interval="1Day"):
    """ Return Alpaca TimeFrame object based on time_interval """
    if time_interval == "1Day":
        return TimeFrame.Day
    else:
        print("Invalid time interval in .env")


def get_historical_data(watchlist):
    """ Fetches historical data for given tickers and returns dictionary of Dataframes"""
    tickers_historical_data = {}
    data_client = StockHistoricalDataClient(api_key=ALPACA_API_KEY, secret_key=ALPACA_SECRET_KEY)
    start_date = get_historical_data_start_date()
    timeframe = get_historical_data_timeframe()
    for current_ticker, _sell_qty in watchlist.values:
        print(f"Fetching historical data for {current_ticker} ")
        try:
            request_params = StockBarsRequest(
                symbol_or_symbols=current_ticker,
                timeframe=timeframe,
                start=start_date,
                extended_hours=True,
            )
            tickers_historical_data[current_ticker] = data_client.get_stock_bars(request_params).df
        except Exception as e:
            print(f"Failed to get historical data for {current_ticker}: {e}")
            continue

    return tickers_historical_data


def calculate_average_true_range(ticker_df):
    """Calculates the Average True Range (ATR) and appends it to the DataFrame"""
    atr_range = 14
    high_low = ticker_df['high'] - ticker_df['low']
    high_close = (ticker_df['high'] - ticker_df['close'].shift()).abs()
    low_close = (ticker_df['low'] - ticker_df['close'].shift()).abs()

    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)

    average_true_range = true_range.ewm(alpha=1/atr_range, adjust=False).mean()

    ticker_df['average_true_range'] = average_true_range

    return ticker_df

tickers = get_watchlist()
tickers_historical_data = get_historical_data(tickers)

for ticker, data in tickers_historical_data.items():
    tickers_historical_data[ticker] = calculate_average_true_range(data)


