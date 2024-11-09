import os
import requests
import pandas as pd
import matplotlib.pyplot as plt
import base64
from io import BytesIO
from flask import Flask, render_template, request
from datetime import datetime

# Set Matplotlib to use a non-GUI backend
import matplotlib
matplotlib.use('Agg')

app = Flask(__name__)

# Alpha Vantage API Key
API_KEY = "FVQDMTI5GIVCHLQT"

# Function to fetch stock data from Alpha Vantage API
def get_stock_data(symbol, interval='1min', start_date=None, end_date=None, function='TIME_SERIES_INTRADAY'):
    try:
        url = f'https://www.alphavantage.co/query'
        params = {
            'function': function,
            'symbol': symbol,
            'interval': interval,
            'apikey': API_KEY
        }

        if function == 'TIME_SERIES_DAILY':
            params['outputsize'] = 'full'  # Fetch more data if using daily time series
        
        response = requests.get(url, params=params)

        if response.status_code == 200:
            data = response.json()
            if function == 'TIME_SERIES_INTRADAY' and 'Time Series (1min)' in data:
                df = pd.DataFrame.from_dict(data['Time Series (1min)'], orient='index')
                df.columns = ['open', 'high', 'low', 'close', 'volume']
                df = df.astype(float)

            elif function == 'TIME_SERIES_DAILY' and 'Time Series (Daily)' in data:
                df = pd.DataFrame.from_dict(data['Time Series (Daily)'], orient='index')
                df.columns = ['open', 'high', 'low', 'close', 'volume']
                df = df.astype(float)
            
            # Filter data by date range if provided
            if start_date and end_date:
                df.index = pd.to_datetime(df.index)
                df = df[(df.index >= start_date) & (df.index <= end_date)]

            return df
        else:
            print("Error fetching data:", response.status_code)
    except Exception as e:
        print("Exception in get_stock_data:", e)
    return None

# Function to create a chart from the stock data
def create_chart(df, chart_type='line'):
    try:
        # Create a plot based on the user's chart preference
        fig, ax = plt.subplots(figsize=(10, 5))

        if chart_type == 'line':
            ax.plot(df.index, df['close'], label='Close Price', color='blue')
        elif chart_type == 'bar':
            ax.bar(df.index, df['close'], label='Close Price', color='blue')

        ax.set_xlabel('Time')
        ax.set_ylabel('Stock Price (USD)')
        ax.set_title('Stock Price Over Time')
        ax.legend()

        # Save the plot to a BytesIO object instead of displaying it
        img_stream = BytesIO()
        plt.savefig(img_stream, format='png')
        img_stream.seek(0)
        plt.close(fig)
        
        # Convert to base64 encoding
        img_base64 = base64.b64encode(img_stream.getvalue()).decode('utf8')
        return img_base64
    except Exception as e:
        print("Exception in create_chart:", e)
        return None

# Route for home page (render the form)
@app.route('/', methods=['GET', 'POST'])
def home():
    stock_symbols = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'META']
    chart_img = None
    error_message = None

    if request.method == 'POST':
        symbol = request.form.get('symbol')
        chart_type = request.form.get('chart_type')
        time_series_function = request.form.get('function')
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')

        # Validate dates
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d') if start_date_str else None
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else None

            if end_date and start_date and end_date < start_date:
                error_message = "End date cannot be before the start date."
            else:
                df = get_stock_data(symbol, function=time_series_function, start_date=start_date, end_date=end_date)

                if df is not None:
                    chart_img = create_chart(df, chart_type)
                    if chart_img is None:
                        error_message = 'Error: Could not generate chart image.'
                else:
                    error_message = 'Error: Could not fetch data for the selected symbol or date range.'
        except ValueError:
            error_message = "Invalid date format. Please use YYYY-MM-DD."

    return render_template('Body.html', stock_symbols=stock_symbols, chart_img=chart_img, error_message=error_message)

if __name__ == '__main__':
    app.run(debug=True)
