import ccxt
import pandas as pd
from datetime import datetime, timedelta
import backtrader as bt
import streamlit as st
import matplotlib.pyplot as plt

@st.cache_data()
def get_data(symbol='BTC/USDT', timeframe='1d', since='2025-01-01T00:00:00Z', limit=1000):
    exchange = ccxt.binance()
    since = exchange.parse8601(since)
    ohlcv = exchange.fetch_ohlcv(symbol=symbol, timeframe=timeframe, since=since, limit=limit)

    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    return df

class SmaCross(bt.Strategy):
    params = dict(short=10, long=30)

    def __init__(self):
        sma1 = bt.ind.SMA(period=self.p.short)
        sma2 = bt.ind.SMA(period=self.p.long)
        self.crossover = bt.ind.CrossOver(sma1, sma2)

    def next(self):
        if not self.position:
            if self.crossover > 0:
                self.buy()
        elif self.crossover < 0:
            self.sell()

st.header('BTC/USDT Chart with SMA Crossover Strategy')
short = st.sidebar.slider("Media Corta (short)", 5, 50, 10)
long = st.sidebar.slider("Media Larga (long)", 10, 200, 55)
timeframe = st.sidebar.selectbox("Timeframe", ["1h", "4h", "1d", "1w"])
capital_inicial = st.sidebar.number_input("Capital inicial (USDT)", 100, 100000, 10000)
percents = st.sidebar.slider("Tamaño de la posición (%)", 1, 100, 10)

df = get_data(timeframe=timeframe)

if st.button("Run Backtest"):
    cerebro = bt.Cerebro()
    cerebro.addstrategy(SmaCross, short=short, long=long)
    data = bt.feeds.PandasData(dataname=df)
    cerebro.adddata(data)
    
    cerebro.broker.setcash(capital_inicial)
    cerebro.broker.setcommission(commission=0.001)
    cerebro.addsizer(bt.sizers.PercentSizer, percents=percents)
    st.write(f"💰 Capital inicial: {capital_inicial} USDT")
    cerebro.run()
    capital_final = cerebro.broker.getvalue()
    st.write(f"💰 Capital final: {capital_final:.2f} USDT")
    
    # Graficar resultados
    fig = cerebro.plot(style='candlestick')[0][0]
    st.pyplot(fig)
    