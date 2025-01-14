import ccxt
import pandas as pd
from datetime import datetime, timezone, timedelta
import json
import os
from Math.volume_analyzer import VolumeAnalyzer
from Math.stoch_rsi import calculate_stoch_rsi, analyze_stoch_rsi_signals
from Math.rsi_indicator import calculate_rsi, analyze_rsi_signals
from Math.bollinger_bands import calculate_bollinger_bands, analyze_bb_signals
from Math.ema_ribbon import calculate_ema_signals
import time

def load_config():
    """Config dosyasından API anahtarlarını oku"""
    try:
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Config dosyası okuma hatası: {str(e)}")
        return None

def test_indicators():
    # Config'i yükle
    config = load_config()
    if not config:
        print("❌ Config yüklenemedi!")
        return

    try:
        # Binance client'ı başlat
        exchange = ccxt.binance({
            'apiKey': config['api_key'],
            'secret': config['api_secret'],
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot',
                'adjustForTimeDifference': True
            }
        })
        
        # BTC/USDT için veri al
        symbol = 'BTC/USDT'
        ohlcv = exchange.fetch_ohlcv(symbol, '5m', limit=300)
        
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms').dt.tz_localize('UTC').dt.tz_convert('Europe/Istanbul')
        df.set_index('timestamp', inplace=True)
        
        # Son mum bilgileri
        current_candle = df.iloc[-1]
        last_closed_candle = df.iloc[-2]
        
        print(f"\n{'='*50}")
        print(f"🕒 Son Güncelleme: {df.index[-1].strftime('%H:%M:%S')}")
        print(f"📊 {symbol} Anlık Durum:")
        print(f"{'='*50}")
        
        # Aktif mum bilgileri
        print("\n📈 AKTİF MUM:")
        print(f"Açılış: {current_candle['open']:.2f}")
        print(f"Yüksek: {current_candle['high']:.2f}")
        print(f"Düşük: {current_candle['low']:.2f}")
        print(f"Güncel: {current_candle['close']:.2f}")
        print(f"Hacim: {current_candle['volume']:.2f}")
        
        # İndikatörleri hesapla
        df_indicators = df.copy()
        df_indicators = calculate_rsi(df_indicators, period=14)
        df_indicators = calculate_stoch_rsi(
            df_indicators, 
            lengthRSI=14,
            lengthStoch=14,
            smoothK=3,
            smoothD=3
        )
        df_indicators = calculate_bollinger_bands(df_indicators, length=20, mult=2.0)
        df_indicators = calculate_ema_signals(df_indicators)
        
        # Volume analizi
        volume_analyzer = VolumeAnalyzer(df_indicators)
        volume_score = volume_analyzer.get_volume_score()
        
        # RSI analizi
        rsi_analysis = analyze_rsi_signals(df_indicators)
        
        # Stoch RSI analizi
        stoch_analysis = analyze_stoch_rsi_signals(df_indicators)
        
        # Bollinger Bands analizi
        bb_analysis = analyze_bb_signals(df_indicators)
        
        # EMA Ribbon analizi
        last_row = df_indicators.iloc[-1]
        ema_trend = "yükseliş" if last_row['ema_trend'] == 1 else "düşüş" if last_row['ema_trend'] == -1 else "nötr"
        ema_signal = "AL" if last_row['signal'] == 1 else "SAT" if last_row['signal'] == -1 else "YOK"
        
        print(f"\n📊 İNDİKATÖRLER (Son Kapanmış Mum):")
        print(f"RSI: {rsi_analysis['current_rsi']:.1f}")
        print(f"RSI Bölge: {rsi_analysis['zone']}")
        print(f"RSI Trend: {rsi_analysis['trend']}")
        
        print(f"\nStoch RSI:")
        print(f"K Değeri: {stoch_analysis['k_value']:.1f}")
        print(f"D Değeri: {stoch_analysis['d_value']:.1f}")
        print(f"Bölge: {stoch_analysis['zone']}")
        print(f"Trend: {stoch_analysis['trend']}")
        
        print(f"\nHacim Analizi:")
        print(f"Skor: {volume_score['score']:.2f}")
        print(f"Değişim: %{volume_score['change_percent']:.1f}")
        print(f"Güncel Hacim: {volume_score['current_volume']:.0f}")
        print(f"Ortalama Hacim: {volume_score['avg_volume']:.0f}")
        
        print(f"\nBollinger Bands:")
        print(f"Üst Bant: {bb_analysis['upper']:.1f}")
        print(f"Orta Bant: {bb_analysis['basis']:.1f}")
        print(f"Alt Bant: {bb_analysis['lower']:.1f}")
        print(f"Pozisyon: {bb_analysis['position']}")
        print(f"Trend: {bb_analysis['trend']}")
        print(f"Bant Genişliği: {bb_analysis['width']:.1f}")
        print(f"Sıkışma: {'Var' if bb_analysis['squeeze'] else 'Yok'}")
        
        print(f"\nEMA Ribbon:")
        print(f"Trend: {ema_trend}")
        print(f"Sinyal: {ema_signal}")
        print(f"EMA Değerleri:")
        for period in [5, 8, 13, 20, 50, 100, 200]:
            print(f"EMA{period}: {last_row[f'ema_{period}']:.1f}")
        
        print(f"\n{'='*50}")
        
    except Exception as e:
        print(f"❌ Hata: {str(e)}")

if __name__ == "__main__":
    while True:
        test_indicators()
        # 5 saniye bekle
        time.sleep(5) 