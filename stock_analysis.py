import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from tabulate import tabulate
import sqlite3

def download_stock_data(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Download stock data from Yahoo Finance
    
    Args:
        symbol: Stock symbol (e.g., 'AAPL')
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format
    
    Returns:
        DataFrame with stock data
    """
    try:
        stock = yf.Ticker(symbol)
        df = stock.history(start=start_date, end=end_date)
        return df
    except Exception as e:
        print(f"Error downloading data: {e}")
        return None

def calculate_profit(symbol: str, purchase_date: str) -> dict:
    """
    Calculate daily profits for 7 days after purchase date
    
    Args:
        symbol: Stock symbol (e.g., 'AAPL')
        purchase_date: Purchase date in 'YYYY-MM-DD' format
    
    Returns:
        Dictionary containing daily profits
    """
    # Convert purchase_date to datetime
    purchase_date = datetime.strptime(purchase_date, '%Y-%m-%d')
    
    # Calculate end date (purchase date + 8 days to include the 7th day)
    end_date = purchase_date + timedelta(days=8)
    
    # Download data
    df = download_stock_data(symbol, 
                           purchase_date.strftime('%Y-%m-%d'),
                           end_date.strftime('%Y-%m-%d'))
    
    if df is None or df.empty:
        return {"error": "No data available"}
    
    # Get purchase price (Close price on purchase date)
    purchase_price = df.iloc[0]['Close']
    
    # Calculate daily profits
    profits = {}
    for i in range(1, min(8, len(df))):
        current_price = df.iloc[i]['Close']
        profit_percentage = ((current_price - purchase_price) / purchase_price) * 100
        day_date = (purchase_date + timedelta(days=i)).strftime('%Y-%m-%d')
        profits[day_date] = {
            'profit_percentage': round(profit_percentage, 2),
            'price': round(current_price, 2)
        }
    
    return profits

def create_database():
    """
    Create SQLite database and required tables if they don't exist
    """
    conn = sqlite3.connect('stock_analysis.db')
    cursor = conn.cursor()
    
    # Create table for stock analysis results
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS stock_analysis (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT NOT NULL,
        purchase_date DATE NOT NULL,
        purchase_price REAL NOT NULL,
        analysis_date DATE NOT NULL,
        closing_price REAL NOT NULL,
        profit_percentage REAL NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()

def save_results_to_db(symbol: str, purchase_date: str, purchase_price: float, results: dict):
    """
    Save analysis results to SQLite database
    """
    conn = sqlite3.connect('stock_analysis.db')
    cursor = conn.cursor()
    
    try:
        # Insert each day's result
        for date, data in results.items():
            cursor.execute('''
            INSERT INTO stock_analysis 
            (symbol, purchase_date, purchase_price, analysis_date, closing_price, profit_percentage)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                symbol,
                purchase_date,
                purchase_price,
                date,
                data['price'],
                data['profit_percentage']
            ))
        
        conn.commit()
        print("\nResults saved to database successfully!")
        
    except sqlite3.Error as e:
        print(f"Error saving to database: {e}")
        conn.rollback()
    
    finally:
        conn.close()

def main():
    """
    Main function to handle user input and display results in a table format
    """
    # Create database and tables if they don't exist
    create_database()
    
    # Example usage
    symbol = input("Enter stock symbol (e.g., AAPL): ")
    purchase_date = input("Enter purchase date (YYYY-MM-DD): ")
    
    results = calculate_profit(symbol, purchase_date)
    
    if "error" in results:
        print(results["error"])
    else:
        # Get the first day's data to show purchase price
        first_date = min(results.keys())
        purchase_price = results[first_date]['price'] / (1 + results[first_date]['profit_percentage']/100)
        
        # Prepare table data
        table_data = []
        headers = ["Date", "Price ($)", "Profit (%)"]
        
        for date, data in results.items():
            table_data.append([
                date,
                f"{data['price']:.2f}",
                f"{data['profit_percentage']:+.2f}"
            ])
        
        # Print results in table format
        print(f"\nProfit analysis for {symbol} from {purchase_date}")
        print(f"Purchase price: ${purchase_price:.2f}")
        print(tabulate(table_data, headers=headers, tablefmt="grid"))
        
        # Save results to database
        save_results_to_db(symbol, purchase_date, purchase_price, results)

if __name__ == "__main__":
    main() 