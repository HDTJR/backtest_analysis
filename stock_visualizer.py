import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sqlite3

def get_stock_data(symbol: str, start_date: str, days: int = 30) -> tuple:
    """
    Get stock data for visualization
    
    Args:
        symbol: Stock symbol (e.g., 'AAPL')
        start_date: Purchase date in 'YYYY-MM-DD' format
        days: Number of days to show (default 30 days)
    
    Returns:
        Tuple of (DataFrame with stock data, purchase_price)
    """
    # Convert start_date to datetime
    start_date = datetime.strptime(start_date, '%Y-%m-%d')
    
    # Get data from 15 days before purchase to 15 days after
    before_days = days // 2
    after_days = days - before_days
    
    start = start_date - timedelta(days=before_days)
    end = start_date + timedelta(days=after_days)
    
    # Download data
    stock = yf.Ticker(symbol)
    df = stock.history(start=start.strftime('%Y-%m-%d'),
                      end=end.strftime('%Y-%m-%d'))
    
    # Get purchase price
    purchase_price = df.loc[start_date.strftime('%Y-%m-%d')]['Close']
    
    return df, purchase_price

def create_candlestick_chart(symbol: str, purchase_date: str):
    """
    Create an interactive candlestick chart with volume bars and purchase point marked
    
    Args:
        symbol: Stock symbol (e.g., 'AAPL')
        purchase_date: Purchase date in 'YYYY-MM-DD' format
    """
    # Get data
    df, purchase_price = get_stock_data(symbol, purchase_date)
    
    # Create figure with secondary y-axis
    fig = go.Figure()
    
    # Add candlestick chart
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name='Candlesticks',
            yaxis='y'
        )
    )
    
    # Add volume bars
    colors = ['red' if row['Open'] > row['Close'] else 'green' for _, row in df.iterrows()]
    fig.add_trace(
        go.Bar(
            x=df.index,
            y=df['Volume'],
            name='Volume',
            marker_color=colors,
            yaxis='y2'
        )
    )
    
    # Add purchase point marker
    fig.add_trace(
        go.Scatter(
            x=[purchase_date],
            y=[purchase_price],
            mode='markers',
            marker=dict(
                symbol='triangle-up',
                size=15,
                color='yellow',
            ),
            name='Purchase Point',
            yaxis='y'
        )
    )
    
    # Update layout with secondary y-axis
    fig.update_layout(
        title=f'{symbol} Stock Price with Volume',
        yaxis=dict(
            title='Price ($)',
            side='left',
            domain=[0.3, 1.0]  # Upper 70% of the plot
        ),
        yaxis2=dict(
            title='Volume',
            side='right',
            domain=[0, 0.2],   # Lower 20% of the plot
            showgrid=False
        ),
        xaxis_title='Date',
        template='plotly_dark',
        showlegend=True,
        xaxis_rangeslider_visible=False  # Disable rangeslider to save space
    )
    
    # Show the plot
    fig.show()

def visualize_from_db():
    """
    Visualize stock data from database entries
    """
    conn = sqlite3.connect('stock_analysis.db')
    cursor = conn.cursor()
    
    # Get unique symbol-purchase_date combinations
    cursor.execute('''
    SELECT DISTINCT symbol, purchase_date
    FROM stock_analysis
    ORDER BY created_at DESC
    ''')
    
    entries = cursor.fetchall()
    conn.close()
    
    if not entries:
        print("No entries found in database.")
        return
    
    # Show available entries
    print("\nAvailable entries:")
    for i, (symbol, date) in enumerate(entries, 1):
        print(f"{i}. {symbol} - {date}")
    
    try:
        choice = int(input("\nSelect entry number to visualize (0 to exit): "))
        if choice == 0:
            return
        if 1 <= choice <= len(entries):
            symbol, date = entries[choice - 1]
            create_candlestick_chart(symbol, date)
        else:
            print("Invalid selection.")
    except ValueError:
        print("Please enter a valid number.")

def main():
    """
    Main function to handle visualization options
    """
    print("\nStock Visualization Options:")
    print("1. Visualize new stock data")
    print("2. Visualize from database")
    print("0. Exit")
    
    choice = input("\nEnter your choice: ")
    
    if choice == "1":
        symbol = input("Enter stock symbol (e.g., AAPL): ")
        purchase_date = input("Enter purchase date (YYYY-MM-DD): ")
        create_candlestick_chart(symbol, purchase_date)
    elif choice == "2":
        visualize_from_db()
    elif choice == "0":
        return
    else:
        print("Invalid choice.")

if __name__ == "__main__":
    main() 