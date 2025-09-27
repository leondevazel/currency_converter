import requests
import json
import os
from datetime import datetime
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import urllib.parse

# Currency data
CURRENCIES = {
    'USD': {'name': 'US Dollar', 'symbol': '$'},
    'EUR': {'name': 'Euro', 'symbol': '€'},
    'GBP': {'name': 'British Pound', 'symbol': '£'},
    'JPY': {'name': 'Japanese Yen', 'symbol': '¥'},
    'KRW': {'name': 'Korean Won', 'symbol': '₩'},
    'CNY': {'name': 'Chinese Yuan', 'symbol': '¥'},
    'AUD': {'name': 'Australian Dollar', 'symbol': 'A$'},
    'CAD': {'name': 'Canadian Dollar', 'symbol': 'C$'},
    'CHF': {'name': 'Swiss Franc', 'symbol': 'Fr'},
    'INR': {'name': 'Indian Rupee', 'symbol': '₹'}
}

API_BASE_URL = "https://api.exchangerate-api.com/v4/latest/"
HISTORY_FILE = "conversion_history.json"


class CurrencyConverter:
    """Main currency converter class"""
    
    def __init__(self):
        self.exchange_rates = {}
        self.last_update = None
        
    def fetch_exchange_rates(self, base_currency):
        """Fetch exchange rates from API"""
        try:
            print(f"Fetching rates for {base_currency}...")
            response = requests.get(f"{API_BASE_URL}{base_currency}", timeout=10)
            response.raise_for_status()
            data = response.json()
            
            self.exchange_rates = data['rates']
            self.last_update = data.get('time_last_updated', datetime.now().isoformat())
            
            return True, "Success"
        except requests.exceptions.RequestException as e:
            return False, f"Error fetching rates: {str(e)}"
    
    def convert(self, amount, from_currency, to_currency):
        """Convert amount from one currency to another"""
        success, message = self.fetch_exchange_rates(from_currency)
        
        if not success:
            return None, message
        
        if to_currency not in self.exchange_rates:
            return None, f"Currency {to_currency} not found"
        
        rate = self.exchange_rates[to_currency]
        converted = amount * rate
        
        return {
            'amount': amount,
            'from': from_currency,
            'to': to_currency,
            'rate': rate,
            'result': round(converted, 2),
            'timestamp': datetime.now().isoformat()
        }, "Success"
    
    def get_popular_rates(self, base_currency):
        """Get popular currency rates"""
        popular = ['EUR', 'GBP', 'JPY', 'KRW', 'CNY', 'AUD']
        rates = {}
        
        for currency in popular:
            if currency != base_currency and currency in self.exchange_rates:
                rates[currency] = self.exchange_rates[currency]
        
        return rates


class HistoryManager:
    """Manage conversion history"""
    
    @staticmethod
    def load_history():
        """Load history from JSON file"""
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    @staticmethod
    def save_conversion(conversion):
        """Save conversion to history"""
        history = HistoryManager.load_history()
        history.insert(0, conversion)
        history = history[:10]  # Keep only last 10
        
        with open(HISTORY_FILE, 'w') as f:
            json.dump(history, f, indent=2)
        
        return history
    
    @staticmethod
    def clear_history():
        """Clear all history"""
        if os.path.exists(HISTORY_FILE):
            os.remove(HISTORY_FILE)
        return []


class WebInterface(BaseHTTPRequestHandler):
    """Simple web server to display results"""
    
    converter = None
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            # Read HTML file
            with open('index.html', 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            self.wfile.write(html_content.encode('utf-8'))
        
        elif self.path.startswith('/api/convert'):
            self.handle_convert()
        
        elif self.path == '/api/history':
            self.send_json(HistoryManager.load_history())
        
        elif self.path == '/api/clear':
            HistoryManager.clear_history()
            self.send_json({'success': True})
        
        elif self.path == '/api/currencies':
            self.send_json(CURRENCIES)
    
    def handle_convert(self):
        """Handle conversion request"""
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        
        amount = float(params.get('amount', [1])[0])
        from_curr = params.get('from', ['USD'])[0]
        to_curr = params.get('to', ['KRW'])[0]
        
        result, message = self.converter.convert(amount, from_curr, to_curr)
        
        if result:
            HistoryManager.save_conversion(result)
            popular_rates = self.converter.get_popular_rates(from_curr)
            self.send_json({
                'success': True,
                'result': result,
                'popular_rates': popular_rates,
                'last_update': self.converter.last_update
            })
        else:
            self.send_json({'success': False, 'error': message})
    
    def send_json(self, data):
        """Send JSON response"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass


def create_html_file():
    """Create HTML file if it doesn't exist"""
    if not os.path.exists('index.html'):
        html_content = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Currency Converter</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { text-align: center; color: white; margin-bottom: 30px; }
        .header h1 { font-size: 2.5rem; margin-bottom: 10px; }
        .grid { display: grid; grid-template-columns: 2fr 1fr; gap: 20px; }
        @media (max-width: 768px) { .grid { grid-template-columns: 1fr; } }
        .card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        .input-group { margin-bottom: 15px; }
        .input-group label { display: block; font-weight: bold; margin-bottom: 5px; }
        .input-group input, .input-group select {
            width: 100%;
            padding: 10px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 16px;
        }
        .currency-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            cursor: pointer;
            font-weight: bold;
        }
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            width: 100%;
            margin-top: 15px;
        }
        .btn-primary:hover { opacity: 0.9; }
        .result {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 25px;
            border-radius: 12px;
            margin-top: 20px;
            text-align: center;
        }
        .result .amount { font-size: 2.5rem; font-weight: bold; color: #667eea; margin: 10px 0; }
        .quick-rates { margin-top: 20px; }
        .rate-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-top: 10px; }
        .rate-item {
            background: #f8f9fa;
            padding: 12px;
            border-radius: 8px;
            text-align: center;
        }
        .rate-item .currency { font-size: 0.85rem; color: #666; }
        .rate-item .value { font-size: 1.2rem; font-weight: bold; color: #333; }
        .history-item {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 10px;
        }
        .history-item .conversion { font-weight: bold; color: #333; }
        .history-item .result { font-size: 1.3rem; font-weight: bold; color: #667eea; margin: 5px 0; }
        .btn-clear {
            background: #e53e3e;
            color: white;
            padding: 8px 16px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            float: right;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Currency Converter</h1>
            <p>Real-time exchange rates powered by Python</p>
        </div>
        
        <div class="grid">
            <div>
                <div class="card">
                    <div class="input-group">
                        <label>Amount</label>
                        <input type="number" id="amount" value="1">
                    </div>
                    
                    <div class="currency-grid">
                        <div class="input-group">
                            <label>From</label>
                            <select id="from">
                                <option value="USD">USD - US Dollar</option>
                                <option value="EUR">EUR - Euro</option>
                                <option value="GBP">GBP - British Pound</option>
                                <option value="JPY">JPY - Japanese Yen</option>
                                <option value="KRW">KRW - Korean Won</option>
                                <option value="CNY">CNY - Chinese Yuan</option>
                                <option value="AUD">AUD - Australian Dollar</option>
                                <option value="CAD">CAD - Canadian Dollar</option>
                                <option value="CHF">CHF - Swiss Franc</option>
                                <option value="INR">INR - Indian Rupee</option>
                            </select>
                        </div>
                        <div class="input-group">
                            <label>To</label>
                            <select id="to">
                                <option value="USD">USD - US Dollar</option>
                                <option value="EUR">EUR - Euro</option>
                                <option value="GBP">GBP - British Pound</option>
                                <option value="JPY">JPY - Japanese Yen</option>
                                <option value="KRW" selected>KRW - Korean Won</option>
                                <option value="CNY">CNY - Chinese Yuan</option>
                                <option value="AUD">AUD - Australian Dollar</option>
                                <option value="CAD">CAD - Canadian Dollar</option>
                                <option value="CHF">CHF - Swiss Franc</option>
                                <option value="INR">INR - Indian Rupee</option>
                            </select>
                        </div>
                    </div>
                    
                    <button class="btn btn-primary" onclick="convert()">Convert & Save</button>
                    
                    <div id="result" style="display:none;" class="result">
                        <div id="result-text"></div>
                    </div>
                </div>
                
                <div class="card quick-rates" id="quick-rates" style="margin-top:20px;display:none;">
                    <h3>Quick Rates</h3>
                    <div class="rate-grid" id="rates-grid"></div>
                </div>
            </div>
            
            <div class="card">
                <h3>History <button class="btn-clear" onclick="clearHistory()">Clear</button></h3>
                <div style="clear:both;margin-top:15px;" id="history"></div>
            </div>
        </div>
    </div>
    
    <script>
        async function convert() {
            const amount = document.getElementById('amount').value;
            const from = document.getElementById('from').value;
            const to = document.getElementById('to').value;
            
            const response = await fetch(`/api/convert?amount=${amount}&from=${from}&to=${to}`);
            const data = await response.json();
            
            if (data.success) {
                const r = data.result;
                document.getElementById('result-text').innerHTML = `
                    <div>${r.amount} ${r.from} =</div>
                    <div class="amount">${r.result.toLocaleString()} ${r.to}</div>
                    <div>Rate: 1 ${r.from} = ${r.rate.toFixed(4)} ${r.to}</div>
                `;
                document.getElementById('result').style.display = 'block';
                
                let ratesHtml = '';
                for (const [curr, rate] of Object.entries(data.popular_rates)) {
                    ratesHtml += `
                        <div class="rate-item">
                            <div class="currency">${curr}</div>
                            <div class="value">${rate.toFixed(2)}</div>
                        </div>
                    `;
                }
                document.getElementById('rates-grid').innerHTML = ratesHtml;
                document.getElementById('quick-rates').style.display = 'block';
                
                loadHistory();
            }
        }
        
        async function loadHistory() {
            const response = await fetch('/api/history');
            const history = await response.json();
            
            if (history.length === 0) {
                document.getElementById('history').innerHTML = '<p>No history yet</p>';
                return;
            }
            
            let html = '';
            history.forEach(item => {
                html += `
                    <div class="history-item">
                        <div class="conversion">${item.amount} ${item.from} to ${item.to}</div>
                        <div class="result">${item.result.toLocaleString()} ${item.to}</div>
                        <div style="font-size:0.85rem;color:#666;">Rate: ${item.rate.toFixed(4)}</div>
                    </div>
                `;
            });
            document.getElementById('history').innerHTML = html;
        }
        
        async function clearHistory() {
            await fetch('/api/clear');
            loadHistory();
        }
        
        loadHistory();
    </script>
</body>
</html>"""
        
        with open('index.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print("Created index.html file")


def start_server(converter):
    """Start the web server"""
    create_html_file()
    
    WebInterface.converter = converter
    server = HTTPServer(('localhost', 8000), WebInterface)
    print("\n" + "="*50)
    print("Currency Converter Server Started!")
    print("="*50)
    print("Server running at: http://localhost:8000")
    print("Opening browser...")
    print("Press Ctrl+C to stop the server")
    print("="*50 + "\n")
    
    threading.Timer(1.5, lambda: webbrowser.open('http://localhost:8000')).start()
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\nServer stopped. Goodbye!")
        server.shutdown()


if __name__ == "__main__":
    converter = CurrencyConverter()
    start_server(converter)