“””
Cloud-Optimized Indian Penny Stocks Analyzer
Perfect for Railway deployment - Sends to iPhone via Telegram
“””

import requests
import pandas as pd
from datetime import datetime
import time
import os
from typing import List, Dict
import yfinance as yf
import schedule

class CloudPennyStockAnalyzer:
def **init**(self):
“”“Initialize with environment variables”””
self.telegram_bot_token = os.getenv(‘TELEGRAM_BOT_TOKEN’, ‘’)
self.telegram_chat_id = os.getenv(‘TELEGRAM_CHAT_ID’, ‘’)
self.penny_stock_threshold = int(os.getenv(‘PENNY_THRESHOLD’, ‘50’))

```
def get_nse_penny_stocks(self) -> List[Dict]:
    """Fetch penny stocks from NSE"""
    nse_symbols = [
        "YESBANK.NS", "SUZLON.NS", "RPOWER.NS", "ZEEL.NS",
        "GTPL.NS", "SPICEJET.NS", "VODAIDEA.NS", "NBCC.NS",
        "SAIL.NS", "PNB.NS", "NMDC.NS", "BHEL.NS", "IRFC.NS",
        "RECLTD.NS", "ASHOKLEY.NS", "TATASTEEL.NS",
        "JSWSTEEL.NS", "HINDALCO.NS", "SBIN.NS", "BANKBARODA.NS",
        "CANBK.NS", "IOB.NS", "CENTRALBK.NS", "INDHOTEL.NS"
    ]
    
    penny_stocks = []
    print(f"Fetching data for {len(nse_symbols)} stocks...")
    
    for symbol in nse_symbols:
        try:
            stock = yf.Ticker(symbol)
            info = stock.info
            hist = stock.history(period="1mo")
            
            if len(hist) == 0:
                continue
            
            current_price = info.get('currentPrice', hist['Close'].iloc[-1])
            
            if current_price <= self.penny_stock_threshold:
                stock_data = {
                    'symbol': symbol.replace('.NS', ''),
                    'name': info.get('longName', symbol.replace('.NS', '')),
                    'current_price': round(current_price, 2),
                    'volume': info.get('volume', 0),
                    'market_cap': info.get('marketCap', 0),
                    'day_high': round(info.get('dayHigh', current_price), 2),
                    'day_low': round(info.get('dayLow', current_price), 2),
                    'pe_ratio': round(info.get('trailingPE', 0), 2) if info.get('trailingPE') else 'N/A',
                    'week_52_high': round(info.get('fiftyTwoWeekHigh', 0), 2),
                    'week_52_low': round(info.get('fiftyTwoWeekLow', 0), 2),
                }
                penny_stocks.append(stock_data)
                print(f"✓ {symbol}: ₹{current_price}")
                
            time.sleep(0.3)
                    
        except Exception as e:
            print(f"✗ Error fetching {symbol}: {str(e)[:50]}")
            continue
    
    print(f"\nFound {len(penny_stocks)} penny stocks")
    return penny_stocks

def analyze_stock(self, symbol: str) -> Dict:
    """Perform technical analysis"""
    try:
        stock = yf.Ticker(symbol + ".NS")
        hist = stock.history(period="3mo")
        
        if len(hist) < 20:
            return None
        
        close_prices = hist['Close']
        volumes = hist['Volume']
        
        sma_20 = close_prices.rolling(window=20).mean().iloc[-1]
        sma_50 = close_prices.rolling(window=50).mean().iloc[-1] if len(hist) >= 50 else None
        
        delta = close_prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs)).iloc[-1]
        
        avg_volume = volumes.mean()
        current_volume = volumes.iloc[-1]
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
        
        price_change_1d = ((close_prices.iloc[-1] - close_prices.iloc[-2]) / close_prices.iloc[-2] * 100)
        price_change_1w = ((close_prices.iloc[-1] - close_prices.iloc[-5]) / close_prices.iloc[-5] * 100) if len(hist) >= 5 else 0
        price_change_1m = ((close_prices.iloc[-1] - close_prices.iloc[0]) / close_prices.iloc[0] * 100)
        
        volatility = close_prices.pct_change().std() * 100
        
        analysis = {
            'sma_20': round(sma_20, 2),
            'sma_50': round(sma_50, 2) if sma_50 else 'N/A',
            'rsi': round(rsi, 2),
            'volume_ratio': round(volume_ratio, 2),
            'price_change_1d': round(price_change_1d, 2),
            'price_change_1w': round(price_change_1w, 2),
            'price_change_1m': round(price_change_1m, 2),
            'volatility': round(volatility, 2),
            'signal': self.generate_signal(rsi, sma_20, close_prices.iloc[-1], volume_ratio, price_change_1w)
        }
        
        return analysis
        
    except Exception as e:
        print(f"Error analyzing {symbol}: {e}")
        return None

def generate_signal(self, rsi: float, sma_20: float, current_price: float, 
                   volume_ratio: float, price_change_1w: float) -> str:
    """Generate trading signal with score"""
    score = 0
    signals = []
    
    if rsi < 30:
        score += 3
        signals.append("Oversold")
    elif rsi < 40:
        score += 2
        signals.append("Weak")
    elif rsi > 70:
        score -= 3
        signals.append("Overbought")
    elif rsi > 60:
        score -= 1
        signals.append("Strong")
    
    if current_price > sma_20:
        score += 2
        signals.append("Above SMA20")
    else:
        score -= 1
        signals.append("Below SMA20")
    
    if volume_ratio > 1.5:
        score += 2
        signals.append("High Volume")
    elif volume_ratio < 0.5:
        score -= 1
        signals.append("Low Volume")
    
    if price_change_1w > 5:
        score += 2
        signals.append("Uptrend")
    elif price_change_1w < -5:
        score -= 2
        signals.append("Downtrend")
    
    if score >= 5:
        return f"🟢 STRONG BUY ({score}/10) - " + ", ".join(signals)
    elif score >= 3:
        return f"🟢 BUY ({score}/10) - " + ", ".join(signals)
    elif score <= -3:
        return f"🔴 SELL ({score+10}/10) - " + ", ".join(signals)
    elif score <= -1:
        return f"🟡 CAUTION ({score+10}/10) - " + ", ".join(signals)
    else:
        return f"⚪ HOLD ({score+5}/10) - " + ", ".join(signals)

def format_number(self, num) -> str:
    """Format numbers in Indian style"""
    if num >= 10000000:
        return f"{num/10000000:.2f}Cr"
    elif num >= 100000:
        return f"{num/100000:.2f}L"
    elif num >= 1000:
        return f"{num/1000:.2f}K"
    else:
        return str(num)

def format_report(self, stocks_data: List[Dict], analyses: Dict) -> List[str]:
    """Format report into multiple messages"""
    messages = []
    
    header = "📊 *INDIAN PENNY STOCKS ANALYSIS*\n"
    header += f"📅 {datetime.now().strftime('%d %b %Y, %I:%M %p')}\n"
    header += f"💰 Threshold: ₹{self.penny_stock_threshold}\n"
    header += f"📈 Stocks Analyzed: {len(stocks_data)}\n"
    header += "="*40
    messages.append(header)
    
    scored_stocks = []
    for stock in stocks_data:
        analysis = analyses.get(stock['symbol'], {})
        if analysis and 'signal' in analysis:
            signal = analysis['signal']
            if '(' in signal and '/10)' in signal:
                score_str = signal.split('(')[1].split('/10)')[0]
                try:
                    score = int(score_str)
                except:
                    score = 5
            else:
                score = 5
            scored_stocks.append((stock, analysis, score))
    
    scored_stocks.sort(key=lambda x: x[2], reverse=True)
    
    if scored_stocks:
        top_msg = "\n🏆 *TOP PICKS TODAY*\n"
        for i, (stock, analysis, score) in enumerate(scored_stocks[:3], 1):
            top_msg += f"{i}. *{stock['symbol']}* - ₹{stock['current_price']}\n"
            top_msg += f"   {analysis['signal']}\n"
        messages.append(top_msg)
    
    for stock, analysis, score in scored_stocks[:10]:
        msg = f"\n🏢 *{stock['name']}*\n"
        msg += f"Symbol: {stock['symbol']}\n\n"
        
        msg += f"💵 *Price Info*\n"
        msg += f"Current: ₹{stock['current_price']}\n"
        msg += f"Day Range: ₹{stock['day_low']} - ₹{stock['day_high']}\n"
        msg += f"52W Range: ₹{stock['week_52_low']} - ₹{stock['week_52_high']}\n\n"
        
        msg += f"📊 *Market Data*\n"
        msg += f"Volume: {self.format_number(stock['volume'])}\n"
        msg += f"Market Cap: ₹{self.format_number(stock['market_cap'])}\n"
        msg += f"P/E Ratio: {stock['pe_ratio']}\n\n"
        
        msg += f"📈 *Technical Analysis*\n"
        msg += f"SMA 20: ₹{analysis['sma_20']}\n"
        msg += f"SMA 50: ₹{analysis['sma_50']}\n"
        msg += f"RSI: {analysis['rsi']}\n"
        msg += f"Volume Ratio: {analysis['volume_ratio']}x\n\n"
        
        msg += f"📉 *Performance*\n"
        msg += f"1 Day: {analysis['price_change_1d']:+.2f}%\n"
        msg += f"1 Week: {analysis['price_change_1w']:+.2f}%\n"
        msg += f"1 Month: {analysis['price_change_1m']:+.2f}%\n"
        msg += f"Volatility: {analysis['volatility']:.2f}%\n\n"
        
        msg += f"*{analysis['signal']}*\n"
        msg += "="*40
        
        messages.append(msg)
    
    footer = "\n⚠️ *Disclaimer*\n"
    footer += "For educational purposes only.\n"
    footer += "Not financial advice.\n"
    footer += "Do your own research before investing.\n\n"
    footer += "💡 _Powered by Cloud Penny Stock Analyzer_"
    messages.append(footer)
    
    return messages

def send_telegram_message(self, message: str) -> bool:
    """Send message via Telegram"""
    try:
        url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
        payload = {
            'chat_id': self.telegram_chat_id,
            'text': message,
            'parse_mode': 'Markdown'
        }
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Telegram error: {e}")
        return False

def run_analysis(self):
    """Main analysis function"""
    start_time = time.time()
    print(f"\n{'='*50}")
    print(f"Starting analysis at {datetime.now()}")
    print(f"{'='*50}\n")
    
    stocks = self.get_nse_penny_stocks()
    if not stocks:
        self.send_telegram_message("❌ No penny stocks found today")
        return
    
    print(f"\n{'='*50}")
    print("Analyzing stocks...")
    print(f"{'='*50}\n")
    
    analyses = {}
    for stock in stocks:
        print(f"Analyzing {stock['symbol']}...")
        analysis = self.analyze_stock(stock['symbol'])
        if analysis:
            analyses[stock['symbol']] = analysis
        time.sleep(0.3)
    
    print(f"\n{'='*50}")
    print("Generating reports...")
    print(f"{'='*50}\n")
    
    messages = self.format_report(stocks, analyses)
    
    print("Sending to Telegram...")
    for i, msg in enumerate(messages, 1):
        success = self.send_telegram_message(msg)
        if success:
            print(f"✓ Message {i}/{len(messages)} sent")
        else:
            print(f"✗ Message {i}/{len(messages)} failed")
        time.sleep(1)
    
    elapsed = time.time() - start_time
    print(f"\n{'='*50}")
    print(f"✅ Analysis completed in {elapsed:.2f} seconds")
    print(f"{'='*50}\n")
```

def job():
“”“Job to run on schedule”””
analyzer = CloudPennyStockAnalyzer()
if not analyzer.telegram_bot_token or not analyzer.telegram_chat_id:
print(“ERROR: Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID”)
return
analyzer.run_analysis()

if **name** == “**main**”:
# Schedule for 9:30 AM IST (4:00 AM UTC)
schedule.every().day.at(“04:00”).do(job)

```
print("=" * 50)
print("📊 PENNY STOCKS ANALYZER STARTED")
print("=" * 50)
print(f"⏰ Scheduled for 9:30 AM IST daily")
print(f"🚀 First run in progress...\n")

# Run immediately on start
job()

# Then wait for scheduled time
print("\n⏳ Waiting for next scheduled run...")
while True:
    schedule.run_pending()
    time.sleep(60)
```