import yfinance as yf
from datetime import date, timedelta
import pandas as pd
import streamlit as st
import altair as alt

ticker_symbols = ['FSPTX', 'FBMPX', 'FSENX', 'FDFAX', 'VFINX', 'VEUAX']

@st.cache_data
def download_data(ticker_symbols, start_date):
    data = {}
    for ticker_symbol in ticker_symbols:
        df = yf.download(ticker_symbol, start=start_date, end=date.today())
        df['Date'] = pd.to_datetime(df.index)
        data[ticker_symbol] = df
    return data

def calculate_percentage_change(df, period):
    return ((df['Close'] - df['Close'].shift(period)) / df['Close'].shift(period)) * 100

def investing_method(selected_tickers, use_smoothed, selected_date, investing_method):
    dfs = []
    data = download_data(selected_tickers, "2020-01-01")
    
    selected_date = pd.to_datetime(selected_date)

    for ticker_symbol in selected_tickers:
        df = data[ticker_symbol].copy()
        
        if investing_method == 'industry rotation':
            period = 8 * 21  # Approximately 8 months
        else:  # dual momentum
            period = [21, 3*21, 6*21]  # Approximately 1, 3, and 6 months

        if investing_method == 'industry rotation':
            df['Percentage Change'] = calculate_percentage_change(df, period)
        else:
            df['Percentage Change'] = sum(calculate_percentage_change(df, p) for p in period)

        df['Smoothed Percentage Change'] = df['Percentage Change'].rolling(window=10).mean()
        
        st.header(f"Statistics for {ticker_symbol}")
        try:
            st.write(f"Percentage change for selected date {ticker_symbol}: {df['Percentage Change'].loc[selected_date]}")
        except KeyError:
            st.write(f"No data available for the selected date for {ticker_symbol}")
            continue

        dfs.append(df[['Date', 'Percentage Change', 'Smoothed Percentage Change']].rename(
            columns={'Percentage Change': f'Percentage Change_{ticker_symbol}',
                     'Smoothed Percentage Change': f'Smoothed Percentage Change_{ticker_symbol}'}))

    if not dfs:
        st.warning("No data to display.")
        return

    joined_df = pd.concat(dfs, axis=1).loc[:, ~pd.concat(dfs, axis=1).columns.duplicated()]

    chart_data = joined_df.melt(id_vars=['Date'], var_name='Ticker', value_name='Percentage Change')
    
    if use_smoothed:
        chart_data = chart_data[chart_data['Ticker'].str.contains('Smoothed Percentage Change')]
    else:
        chart_data = chart_data[chart_data['Ticker'].str.contains('Percentage Change') & ~chart_data['Ticker'].str.contains('Smoothed')]

    chart = alt.Chart(chart_data).mark_line().encode(
        x='Date:T',
        y='Percentage Change:Q',
        color='Ticker:N'
    ).properties(
        width=800,
        height=400
    )

    st.altair_chart(chart)

st.title('Asset Management - Family Office')
selected_date = st.date_input('Select Date', value=date.today())

selected_tickers = st.multiselect('Select Ticker Symbols', ticker_symbols, default=ticker_symbols)
select_investing_method = st.selectbox('Select Investing Method', ['industry rotation', 'dual momentum'])
use_smoothed = st.checkbox('Use Smoothed Percentage Change')

if st.button('Compare'):
    investing_method(selected_tickers, use_smoothed, selected_date, select_investing_method)

