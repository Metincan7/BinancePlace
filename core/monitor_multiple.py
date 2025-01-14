from http import client
import sys
import os

# Core klasörünü path'e ekle
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

import ccxt
import pandas as pd
from core.Math.range_filter import RangeFilter
from core.Math.rsi_indicator import calculate_rsi
from core.Math.stoch_rsi import calculate_stoch_rsi
from core.Math.bollinger_bands import calculate_bollinger_bands
import time
from datetime import datetime, timezone, timedelta
import json
from signal_validator import SignalValidator
from signal_score import SignalScore
from Trade.position_calculator import PositionCalculator
from Trade.trade_settings import TRADE_SETTINGS, ORDER_TYPES, TRADE_SIDES
from Trade.futures_position import open_futures_position

active_trading_pairs = set()  # Global değişken olarak ekle

def load_config():
    """Config dosyasından API anahtarlarını oku"""
    try:
        # Doğrudan proje kök dizininden config.json'u oku
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
        print(f"Config dosyası aranıyor: {config_path}")  # Debug için
        
        if not os.path.exists(config_path):
            print(f"Config dosyası bulunamadı: {config_path}")
            return None
            
        with open(config_path, 'r') as f:
            config = json.load(f)
            print("Config dosyası başarıyla yüklendi!")  # Debug için
            return config
    except Exception as e:
        print(f"Config dosyası okuma hatası: {str(e)}")
        print(f"Çalışma dizini: {os.getcwd()}")  # Debug için
        return None

def get_usdt_pairs(exchange):
    """USDT çiftlerini al"""
    try:
        send_log_to_backend("\nUSDT çiftleri alınıyor...")
        markets = exchange.load_markets()
        send_log_to_backend(f"Toplam market sayısı: {len(markets)}")
        
        # Sadece USDT çiftlerini filtrele ve volume > 1M olanları al
        usdt_pairs = []
        send_log_to_backend("Volume > 1M USD olan çiftler filtreleniyor...")
        
        for symbol in markets:
            if symbol.endswith('/USDT'):
                try:
                    ticker = exchange.fetch_ticker(symbol)
                    if ticker['quoteVolume'] and ticker['quoteVolume'] > 1000000:  # 1M USD volume
                        usdt_pairs.append(symbol)
                except Exception as e:
                    print(f"Ticker hatası ({symbol}): {str(e)}")
                    continue
        
        # Bulunan coinleri JSON'a kaydet
        coin_data = {
            "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "coins": usdt_pairs
        }
        
        with open('coinlist.json', 'w') as f:
            json.dump(coin_data, f, indent=4)
            print(f"\n✅ {len(usdt_pairs)} coin coinlist.json'a kaydedildi")
        
        return usdt_pairs
        
    except Exception as e:
        send_log_to_backend(f"❌ USDT çiftleri alınırken hata: {str(e)}")
        return []

def check_coin(exchange, symbol, rf):
    """Tek bir coin için kontrol"""
    try:
        print(f"\n🔍 {symbol} analiz ediliyor...")
        
        ohlcv = exchange.fetch_ohlcv(symbol, '5m', limit=1000)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms').dt.tz_localize('UTC').dt.tz_convert('Europe/Istanbul')
        df.set_index('timestamp', inplace=True)
        
        # Aktif mumu çıkar
        df = df.iloc[:-1]
        
        # İndikatörleri hesapla
        df = calculate_rsi(df, period=14)
        df = calculate_stoch_rsi(df)
        df = calculate_bollinger_bands(df)
        
        # EMA'ları hesapla
        for period in [5, 8, 13, 21, 34, 55, 89, 200]:
            df[f'ema_{period}'] = df['close'].ewm(span=period, adjust=False).mean()
        
        signals = rf.generate_signals(df)
        
        # Son kapanmış mumda sinyal var mı?
        last_buy = signals['buy_signals'].iloc[-1]
        last_sell = signals['sell_signals'].iloc[-1]
        
        if last_buy or last_sell:
            print("\n📊 Sinyal bulundu...")
            signal_data = {
                "symbol": symbol,
                "time": datetime.now().strftime('%H:%M:%S'),
                "price": float(df['close'].iloc[-1]),
                "filter": float(signals['filter'].iloc[-1]),
                "highTarget": float(signals['upper_band'].iloc[-1]),
                "lowTarget": float(signals['lower_band'].iloc[-1]),
                "type": "buy" if last_buy else "sell",
                "rsi": float(df['rsi'].iloc[-1]),
                "stoch_rsi_k": float(df['stoch_rsi_k'].iloc[-1]),
                "stoch_rsi_d": float(df['stoch_rsi_d'].iloc[-1])
            }
            
            # Önce validasyon yap
            validator = SignalValidator(exchange)
            validation_result = validator.validate_signal(df, signal_data)
            
            if validation_result:
                # Validasyon başarılıysa skor hesapla
                scorer = SignalScore(exchange)
                score = scorer.calculate_score(signal_data)
                
                if score >= 9:
                    print("\n🚀 YÜKSEK SKOR! İşlem açılıyor...")
                    try:
                        result = open_futures_position(exchange, symbol, signal_data)
                        if result:
                            print("✅ İşlem başarıyla açıldı!")
                        else:
                            print("❌ İşlem açılamadı!")
                        return result
                    except Exception as e:
                        print(f"❌ İşlem açma hatası: {str(e)}")
                        print(f"Hata tipi: {type(e).__name__}")
                        return False
                else:
                    print(f"\n❌ DÜŞÜK KALİTE SİNYAL - Skor: {score}/18")
            else:
                print("\n❌ Validasyon başarısız!")
            
        return False
            
    except Exception as e:
        print(f"❌ Analiz hatası ({symbol}): {str(e)}")
        return False

def load_coin_list():
    """JSON'dan coin listesini oku"""
    try:
        # core klasörü altındaki coinlist.json'u oku
        config_dir = os.path.dirname(os.path.abspath(__file__))
        coinlist_path = os.path.join(config_dir, 'coinlist.json')
        
        print(f"Coin listesi aranıyor: {coinlist_path}")  # Debug için
        
        if not os.path.exists(coinlist_path):
            print(f"❌ Coin listesi bulunamadı: {coinlist_path}")
            return None
            
        with open(coinlist_path, 'r') as f:
            data = json.load(f)
            print(f"✅ {len(data['coins'])} coin yüklendi")
            print(f"📅 Son güncelleme: {data['last_updated']}")
            return data['coins']
    except Exception as e:
        print(f"❌ Coin listesi okunamadı: {str(e)}")
        return None

def monitor_all_coins():
    # Config'i yükle
    config = load_config()
    if not config:
        print("❌ Config yüklenemedi! Program sonlandırılıyor...")
        return

    try:
        # Exchange'i futures modunda başlat
        exchange = ccxt.binance({
            'apiKey': config['api_key'],
            'secret': config['api_secret'],
            'enableRateLimit': True,
            'options': {
                'defaultType': 'future',
                'adjustForTimeDifference': True
            },
            'timeout': 30000
        })
        
        exchange.load_time_difference()
        print("✅ Binance Futures bağlantısı başarılı")
        
        # Önce marketleri yükle
        print("📊 Marketler yükleniyor...")
        markets = exchange.load_markets()
        print(f"✅ {len(markets)} market yüklendi")
        
        # Margin type'ı ISOLATED yap
        try:
            futures_symbols = [symbol for symbol in markets if symbol.endswith('/USDT') and markets[symbol]['future']]
            print(f"🔄 {len(futures_symbols)} futures çifti için margin type ayarlanıyor...")
            
            for symbol in futures_symbols:
                try:
                    exchange.fapiPrivate_post_margintype({
                        'symbol': symbol.replace('/', ''),
                        'marginType': 'ISOLATED'
                    })
                except Exception as e:
                    if "No need to change margin type" not in str(e):
                        print(f"⚠️ {symbol} için margin type hatası: {str(e)}")
            print("✅ Margin type ayarları tamamlandı")
        except Exception as e:
            print(f"⚠️ Margin type ayarlanamadı: {str(e)}")
        
        rf = RangeFilter(period=100, multiplier=3.0)
        
        # JSON'dan coin listesini oku
        pairs = load_coin_list()
        if not pairs:
            print("❌ Coin listesi yüklenemedi!")
            return
            
        print(f"\n📊 Toplam {len(pairs)} coin izleniyor...")
        
        while True:
            try:
                # Açık pozisyonları kontrol et
                positions = exchange.fetch_positions()
                active_positions = [p for p in positions if float(p['contracts']) > 0]
                
                
                active_trading_pairs.clear()
                for pos in active_positions:
                    symbol = pos['symbol'].split(':')[0]
                    if 'USDT' in symbol:
                        symbol = symbol.replace('USDT', '/USDT')
                        active_trading_pairs.add(symbol)
                
                print(f"\n📊 Aktif Pozisyonlar: {len(active_positions)}/{TRADE_SETTINGS['MAX_OPEN_POSITIONS']}")
                print("🔒 İşlem Açık Olan Coinler:", active_trading_pairs)
                
                # Maksimum açık pozisyon kontrolü
                if len(active_positions) >= TRADE_SETTINGS['MAX_OPEN_POSITIONS']:
                    print("\n⚠️ Maksimum açık pozisyon sayısına ulaşıldı!")
                    continue
                
                # Son kez pozisyon kontrolü
                positions_final = exchange.fetch_positions()
                final_count = len([p for p in positions_final if float(p['contracts']) > 0])
                if final_count >= TRADE_SETTINGS['MAX_OPEN_POSITIONS']:
                    print("\n⚠️ Yeni pozisyon tespit edildi, tarama durduruluyor!")
                    continue
                
                # Yeni sinyalleri tara
                signal_count = 0
                print(f"\n⏰ {datetime.now().strftime('%H:%M:%S')} - Tarama başladı...")
                
                for symbol in pairs:
                    # Eğer coin'de aktif işlem varsa atla
                    if symbol in active_trading_pairs:
                        continue
                        
                    if check_coin(exchange, symbol, rf):
                        signal_count += 1
                        # İşlem açıldıysa coin'i aktif listeye ekle
                        active_trading_pairs.add(symbol)
                        break
                
                if signal_count == 0:
                    print("ℹ️ Sinyal yok.")
                    
            except Exception as e:
                print(f"\n❌ Döngü hatası: {str(e)}")
                print(f"Hata tipi: {type(e).__name__}")
                
    except Exception as e:
        print(f"❌ Ana fonksiyon hatası: {str(e)}")

def send_log_to_backend(message):
    """Backend'e log gönder"""
    # Backend'e log göndermeyi devre dışı bırak
    print(message)  # Sadece konsola yazdır
    # try:
    #     log_data = {
    #         "message": message,
    #         "timestamp": datetime.now().strftime('%H:%M:%S')
    #     }
    #     response = requests.post('http://localhost:5012/api/log', json=log_data)
    #     if response.status_code != 200:
    #         print(f"Backend hata döndü: {response.text}")
    # except Exception as e:
    #     print(f"Log gönderme hatası: {str(e)}")

def get_klines(symbol, interval='15m', limit=100):  # 5m yerine 15m, 1000 yerine 100
    try:
        klines = client.get_klines(
            symbol=symbol,
            interval=interval,
            limit=limit
        )
        return pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 
                                           'close_time', 'quote_asset_volume', 'number_of_trades',
                                           'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
    except Exception as e:
        send_log_to_backend(f"❌ Hata ({symbol}): {str(e)}")
        return None

# def send_signal_to_backend(signal_data):
#     """Backend'e sinyal gönder"""
#     try:
#         print(f"Sinyal gönderiliyor: {signal_data}")
#         response = requests.post('http://localhost:5012/api/signal', json=signal_data)
#         if response.status_code == 200:
#             send_log_to_backend("✅ Sinyal backend'e gönderildi")
#         else:
#             send_log_to_backend(f"❌ Sinyal gönderme hatası: {response.status_code}")
#     except Exception as e:
#         send_log_to_backend(f"❌ Sinyal gönderme hatası: {str(e)}")

class MarketMonitor:
    def __init__(self):
        self.active_trading_pairs = set()  # Aktif işlem olan coinleri tutacak set
        self.config = load_config()
        self.exchange = None
        self.rf = RangeFilter(period=100, multiplier=3.0)
        self.pairs = None
        
    def initialize_exchange(self):
        self.exchange = ccxt.binance({
            'apiKey': self.config['api_key'],
            'secret': self.config['api_secret'],
            'enableRateLimit': True,
            'options': {
                'defaultType': 'future',
                'adjustForTimeDifference': True
            },
            'timeout': 30000
        })

if __name__ == "__main__":
    print("Program başlatılıyor...")
    monitor_all_coins()