"""
RSI (Relative Strength Index) indikatörü - TradingView uyumlu
"""
import pandas as pd
import numpy as np

def calculate_rsi(df, period=14):
    """
    TradingView ile birebir aynı RSI hesaplama
    """
    try:
        df = df.copy()
        
        # Fiyat değişimlerini hesapla
        delta = df['close'].diff()
        
        # Pozitif ve negatif değişimler
        gain = (delta.where(delta > 0, 0)).fillna(0)
        loss = (-delta.where(delta < 0, 0)).fillna(0)
        
        # İlk SMA değerleri
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        
        # Wilder's smoothing method - iloc kullanarak düzeltildi
        for i in range(period, len(df)):
            avg_gain.iloc[i] = (avg_gain.iloc[i-1] * (period-1) + gain.iloc[i]) / period
            avg_loss.iloc[i] = (avg_loss.iloc[i-1] * (period-1) + loss.iloc[i]) / period
        
        rs = avg_gain / avg_loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        return df
        
    except Exception as e:
        print(f"RSI hesaplanırken hata: {str(e)}")
        return None

def analyze_rsi_signals(df):
    """RSI sinyallerini analiz et - Son 1 saatlik trend"""
    try:
        # Son 1 saat (12 mum çünkü 5dk'lık)
        last_hour = df.tail(12)
        last_row = df.iloc[-1]
        
        analysis = {
            'current_rsi': last_row['rsi'],
            'zone': 'normal',
            'trend': 'yatay',
            'divergence': 'yok'
        }
        
        # Bölge kontrolü
        if last_row['rsi'] >= 70:
            analysis['zone'] = 'overbought'
        elif last_row['rsi'] <= 30:
            analysis['zone'] = 'oversold'
            
        # Son 1 saatlik trend kontrolü
        rsi_values = last_hour['rsi'].values
        rsi_min = rsi_values.min()
        rsi_max = rsi_values.max()
        current_rsi = rsi_values[-1]
        
        # Trend belirleme
        if current_rsi > rsi_values[-2]:  # Son mum yükseliyor
            if rsi_min < rsi_values[-2]:  # Dip yapıp yükseliyor
                analysis['trend'] = 'yükseliş'
        elif current_rsi < rsi_values[-2]:  # Son mum düşüyor
            if rsi_max > rsi_values[-2]:  # Tepe yapıp düşüyor
                analysis['trend'] = 'düşüş'
            
        return analysis
        
    except Exception as e:
        print(f"RSI analizi sırasında hata: {str(e)}")
        return None

def analyze_signal_performance(df, signal_time, signal_type, signal_price):
    """
    Sinyal sonrası performans analizi - Zarar kesme -%1, Kar alma +%1
    """
    try:
        df_after_signal = df[df.index > signal_time]
        next_hour = df_after_signal.head(12)  # 1 saat
        
        if next_hour.empty:
            return {
                'status': 'veri_yok',
                'exit_time': None,
                'exit_price': None,
                'result': 0
            }
        
        # Her mum için kontrol et
        for idx, row in next_hour.iterrows():
            # LONG pozisyon için
            if signal_type == 'LONG':
                # Önce low ile zarar kontrolü
                worst_profit = (row['low'] - signal_price) / signal_price * 100
                if worst_profit <= -1.0:  # -%1 zarar kesme
                    return {
                        'status': 'zarar_ile_kapandı',
                        'exit_time': idx,
                        'exit_price': row['low'],
                        'result': round(worst_profit, 2)
                    }
                
                # Sonra high ile kar kontrolü
                best_profit = (row['high'] - signal_price) / signal_price * 100
                if best_profit >= 1.0:  # +%1 kar alma
                    return {
                        'status': 'kar_ile_kapandı',
                        'exit_time': idx,
                        'exit_price': row['high'],
                        'result': round(best_profit, 2)
                    }
            
            # SHORT pozisyon için
            else:
                # Önce high ile zarar kontrolü
                worst_profit = (signal_price - row['high']) / signal_price * 100
                if worst_profit <= -1.0:  # -%1 zarar kesme
                    return {
                        'status': 'zarar_ile_kapandı',
                        'exit_time': idx,
                        'exit_price': row['high'],
                        'result': round(worst_profit, 2)
                    }
                
                # Sonra low ile kar kontrolü
                best_profit = (signal_price - row['low']) / signal_price * 100
                if best_profit >= 1.0:  # +%1 kar alma
                    return {
                        'status': 'kar_ile_kapandı',
                        'exit_time': idx,
                        'exit_price': row['low'],
                        'result': round(best_profit, 2)
                    }
        
        # 1 saat sonunda hala açık - son fiyatla hesapla
        final_row = next_hour.iloc[-1]
        if signal_type == 'LONG':
            final_result = (final_row['close'] - signal_price) / signal_price * 100
        else:
            final_result = (signal_price - final_row['close']) / signal_price * 100
            
        return {
            'status': 'açık_pozisyon',
            'exit_time': next_hour.index[-1],
            'exit_price': final_row['close'],
            'result': round(final_result, 2)
        }
        
    except Exception as e:
        print(f"Performans analizi sırasında hata: {str(e)}")
        return None

def rsi_points(signal_type, rsi_value):
    """
    RSI puanlaması (2 puan üzerinden)
    Trend ve aşırı bölgelere göre puanlama yapar
    """
    points = 0
    
    if signal_type == "LONG":
        # Aşırı satım bölgesi
        if rsi_value < 30:
            points += 1.5  # Güçlü sinyal
        elif rsi_value < 40:
            points += 1.0  # Orta sinyal
        elif rsi_value < 50:
            points += 0.5  # Zayıf sinyal
            
    else:  # SHORT/SELL
        # Aşırı alım bölgesi
        if rsi_value > 70:
            points += 1.5  # Güçlü sinyal
        elif rsi_value > 60:
            points += 1.0  # Orta sinyal
        elif rsi_value > 50:
            points += 0.5  # Zayıf sinyal
            
    print(f"""
📊 RSI Analizi:
• RSI Değeri: {rsi_value:.2f}
• Puan: {points}/2
""")
            
    return min(points, 2)  # Maximum 2 puan

if __name__ == "__main__":
    # Test
    from range_filter import get_test_data
    
    # Test için 2indicator.py'den gelen coini kullan
    df = get_test_data(None, limit=500)  # symbol parametresini None yapıyoruz
    
    if df is not None:
        # RSI hesapla
        df = calculate_rsi(df)
        
        # Son durumu analiz et
        analysis = analyze_rsi_signals(df)
        
        if analysis:
            print(f"\nRSI Analizi:")  # Spesifik coin adını kaldırdık
            print(f"RSI Değeri: {analysis['current_rsi']:.2f}")
            print(f"Bölge: {analysis['zone']}")
            print(f"Trend: {analysis['trend']}")
            print(f"Divergence: {analysis['divergence']}")  # signal yerine divergence 