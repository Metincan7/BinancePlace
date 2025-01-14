import ccxt
import pandas as pd
from datetime import datetime

def check_volume(symbol):
    try:
        # Binance bağlantısı
        exchange = ccxt.binance({
            'enableRateLimit': True
        })
        
        print(f"\n{symbol} için hacim analizi yapılıyor...")
        
        # Son 100 mumun verilerini al
        ohlcv = exchange.fetch_ohlcv(
            symbol, 
            '5m',  # 5 dakikalık
            limit=100
        )
        
        # DataFrame'e çevir
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms').dt.tz_localize('UTC').dt.tz_convert('Europe/Istanbul')
        
        # Son 5 mumun hacim bilgilerini göster
        print(f"\n{symbol} Hacim Analizi")
        print("="*50)
        
        for i in range(-5, 0):
            row = df.iloc[i]
            print(f"""
⏰ Zaman: {row['timestamp'].strftime('%H:%M')}
💰 Fiyat: {row['close']:.3f}
📊 Hacim: {row['volume']:,.0f}
💵 USDT Hacim: ${(row['volume'] * row['close']):,.0f}
{'-'*30}""")
            
        # Ortalama hacim
        avg_volume = df['volume'].mean()
        print(f"\n📈 Son 100 mum ortalama hacim: {avg_volume:,.0f}")
        print(f"💰 Son 100 mum ortalama USDT hacim: ${(avg_volume * df['close'].mean()):,.0f}")
        
    except Exception as e:
        print(f"❌ Hata: {str(e)}")

if __name__ == "__main__":
    while True:
        symbol = input("\n📌 Kontrol edilecek sembol (örn: FIRO/USDT) [Çıkış için q]: ")
        if symbol.lower() == 'q':
            break
        check_volume(symbol) 