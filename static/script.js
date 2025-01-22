let chart = null;
let volumeSeries = null;

async function loadDbEntries() {
    try {
        const response = await fetch('/api/entries');
        const entries = await response.json();
        const select = document.getElementById('db-entries');
        select.innerHTML = entries.map(entry => 
            `<option value="${entry.symbol}|${entry.date}">${entry.symbol} - ${entry.date}</option>`
        ).join('');
    } catch (error) {
        console.error('Error loading database entries:', error);
    }
}

function createChart(container) {
    if (chart) {
        container.innerHTML = '';
    }

    chart = LightweightCharts.createChart(container, {
        height: 600,
        layout: {
            background: { color: '#131722' },
            textColor: '#d1d4dc',
        },
        grid: {
            vertLines: { color: '#1e222d' },
            horzLines: { color: '#1e222d' },
        },
    });

    return chart;
}

async function fetchStockInfo(symbol) {
    try {
        const response = await fetch(`/api/stock-info/${symbol}`);
        const data = await response.json();
        updateStockInfo(data);
    } catch (error) {
        console.error('Error fetching stock info:', error);
        clearStockInfo();
    }
}

function updateStockInfo(info) {
    document.getElementById('company-name').textContent = info.name;
    document.getElementById('sector').textContent = info.sector;
    document.getElementById('industry').textContent = info.industry;
    document.getElementById('market-cap').textContent = formatMarketCap(info.market_cap);
    document.getElementById('pe-ratio').textContent = formatNumber(info.pe_ratio);
    document.getElementById('dividend-yield').textContent = formatPercentage(info.dividend_yield);
    document.getElementById('52w-high').textContent = formatPrice(info.fifty_two_week_high);
    document.getElementById('52w-low').textContent = formatPrice(info.fifty_two_week_low);
    document.getElementById('avg-volume').textContent = formatVolume(info.avg_volume);
}

function clearStockInfo() {
    const elements = ['company-name', 'sector', 'industry', 'market-cap', 
                     'pe-ratio', 'dividend-yield', '52w-high', '52w-low', 'avg-volume'];
    elements.forEach(id => document.getElementById(id).textContent = '-');
}

function formatMarketCap(value) {
    if (!value) return 'N/A';
    const billion = 1000000000;
    const million = 1000000;
    if (value >= billion) {
        return `$${(value / billion).toFixed(2)}B`;
    }
    return `$${(value / million).toFixed(2)}M`;
}

function formatNumber(value) {
    return value === 'N/A' ? 'N/A' : Number(value).toFixed(2);
}

function formatPercentage(value) {
    return value ? `${(value * 100).toFixed(2)}%` : 'N/A';
}

function formatPrice(value) {
    return value ? `$${value.toFixed(2)}` : 'N/A';
}

function formatVolume(value) {
    return value ? value.toLocaleString() : 'N/A';
}

async function showChart() {
    const symbol = document.getElementById('symbol').value;
    const purchaseDate = document.getElementById('purchase-date').value;
    
    if (!symbol || !purchaseDate) {
        alert('Please enter both symbol and date');
        return;
    }

    try {
        // Fetch both chart data and stock info
        const [chartResponse, infoResponse] = await Promise.all([
            fetch('/api/chart-data', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    symbol: symbol,
                    purchase_date: purchaseDate,
                }),
            }),
            fetch(`/api/stock-info/${symbol}`)
        ]);

        const chartData = await chartResponse.json();
        const infoData = await infoResponse.json();
        
        renderChart(chartData, symbol);
        updateStockInfo(infoData);
    } catch (error) {
        console.error('Error loading data:', error);
        alert('Error loading data');
        clearStockInfo();
    }
}

function showDbChart() {
    const select = document.getElementById('db-entries');
    const [symbol, date] = select.value.split('|');
    
    document.getElementById('symbol').value = symbol;
    document.getElementById('purchase-date').value = date;
    showChart();
}

function renderChart(data, symbol) {
    const container = document.getElementById('chart-container');
    const chart = createChart(container);

    // Candlestick series
    const candlestickSeries = chart.addCandlestickSeries({
        upColor: '#26a69a',
        downColor: '#ef5350',
        borderVisible: false,
        wickUpColor: '#26a69a',
        wickDownColor: '#ef5350',
    });
    candlestickSeries.setData(data.candlestick);

    // Volume series
    const volumeSeries = chart.addHistogramSeries({
        color: '#26a69a',
        priceFormat: {
            type: 'volume',
        },
        priceScaleId: 'volume',
        scaleMargins: {
            top: 0.8,
            bottom: 0,
        },
    });
    volumeSeries.setData(data.volume);

    // Add marker for purchase point
    candlestickSeries.setMarkers([
        {
            time: data.purchase_timestamp,
            position: 'belowBar',
            color: '#ffeb3b',
            shape: 'arrowUp',
            text: 'BUY',
        }
    ]);

    // Fit the chart to the data
    chart.timeScale().fitContent();
}

// Load database entries when page loads
document.addEventListener('DOMContentLoaded', loadDbEntries); 