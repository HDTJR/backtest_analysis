from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd
import sqlite3
from pydantic import BaseModel
from typing import List, Dict, Any

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class StockData(BaseModel):
    symbol: str
    purchase_date: str

def get_stock_data(symbol: str, start_date: str, days: int = 30) -> Dict[str, List]:
    """
    Get stock data for visualization
    """
    try:
        # Convert start_date to datetime
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        
        # Get data from 15 days before purchase to 15 days after
        before_days = days * 2
        after_days = days + 30
        
        start = start_date - timedelta(days=before_days)
        end = start_date + timedelta(days=after_days)
        
        # Download data
        stock = yf.Ticker(symbol)
        df = stock.history(start=start.strftime('%Y-%m-%d'),
                         end=end.strftime('%Y-%m-%d'))
        
        # Reset index to make date accessible
        df = df.reset_index()
        
        # Prepare data for chart
        candlestick_data = []
        volume_data = []
        
        for _, row in df.iterrows():
            timestamp = int(row['Date'].timestamp())
            
            candlestick_data.append({
                "time": timestamp,
                "open": float(row['Open']),
                "high": float(row['High']),
                "low": float(row['Low']),
                "close": float(row['Close'])
            })
            
            volume_data.append({
                "time": timestamp,
                "value": float(row['Volume']),
                "color": "rgba(38, 166, 154, 0.5)" if row['Close'] >= row['Open'] else "rgba(239, 83, 80, 0.5)"
            })
        
        return {
            "candlestick": candlestick_data,
            "volume": volume_data,
            "purchase_timestamp": int(start_date.timestamp())
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

def get_stock_info(symbol: str) -> Dict[str, Any]:
    """
    Get basic stock information
    """
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        
        return {
            "name": info.get("longName", "N/A"),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "market_cap": info.get("marketCap", 0),
            "pe_ratio": info.get("trailingPE", "N/A"),
            "dividend_yield": info.get("dividendYield", 0),
            "fifty_two_week_high": info.get("fiftyTwoWeekHigh", 0),
            "fifty_two_week_low": info.get("fiftyTwoWeekLow", 0),
            "avg_volume": info.get("averageVolume", 0)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

def get_db_entries() -> List[Dict[str, str]]:
    """Get entries from database"""
    try:
        conn = sqlite3.connect('stock_analysis.db')
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT DISTINCT symbol, purchase_date
        FROM stock_analysis
        ORDER BY created_at DESC
        ''')
        
        entries = [{"symbol": symbol, "date": date} for symbol, date in cursor.fetchall()]
        conn.close()
        return entries
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# API Routes
@app.get("/")
async def root():
    with open("static/index.html") as f:
        return HTMLResponse(content=f.read())

@app.get("/api/entries")
async def get_entries():
    return get_db_entries()

@app.post("/api/chart-data")
async def get_chart_data(stock_data: StockData):
    return get_stock_data(stock_data.symbol, stock_data.purchase_date)

@app.get("/api/stock-info/{symbol}")
async def get_info(symbol: str):
    return get_stock_info(symbol)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static") 