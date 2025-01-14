import pandas as pd
import numpy as np

def calculate_bollinger_bands(df, length=20, mult=2.0):
    """
    Bollinger Bands hesaplama (TradingView ile aynı)
    """
    try:
        # Kaynak fiyat (close)
        src = df['close']
        
        # Orta bant (Basis) - SMA20
        basis = src.rolling(window=length, min_periods=length).mean()
        
        # Standart sapma (TradingView ile aynı)
        dev = mult * src.rolling(window=length, min_periods=length).std(ddof=1)
        
        # Üst ve alt bantlar
        upper = basis + dev
        lower = basis - dev
        
        # DataFrame'e ekle (4 ondalık hassasiyet)
        df['bb_upper'] = upper.round(4)
        df['bb_basis'] = basis.round(4)
        df['bb_lower'] = lower.round(4)
        
        # Fiyatın bant pozisyonunu belirle
        df['bb_position'] = 'middle'
        df.loc[df['close'] >= df['bb_upper'], 'bb_position'] = 'upper'
        df.loc[df['close'] <= df['bb_lower'], 'bb_position'] = 'lower'
        
        # Trend yönünü belirle
        df['bb_trend'] = 'neutral'
        df.loc[(df['close'] > df['bb_basis']) & (df['close'].shift(1) <= df['bb_basis']), 'bb_trend'] = 'up'
        df.loc[(df['close'] < df['bb_basis']) & (df['close'].shift(1) >= df['bb_basis']), 'bb_trend'] = 'down'
        
        return df
        
    except Exception as e:
        print(f"Bollinger Bands hesaplama hatası: {str(e)}")
        return df

def analyze_bb_signals(df):
    """
    Bollinger Bands sinyal analizi
    """
    try:
        last_row = df.iloc[-1]
        prev_row = df.iloc[-2]
        
        # Bant genişliği
        width = last_row['bb_upper'] - last_row['bb_lower']
        prev_width = prev_row['bb_upper'] - prev_row['bb_lower']
        
        # Sıkışma durumu (son 3 mum bant daralıyor mu?)
        squeeze = width < prev_width
        
        # Fiyatın bantlara göre pozisyonu
        if last_row['close'] > last_row['bb_basis']:
            position = "upper_half"  # Orta bandın üstünde
        else:
            position = "lower_half"  # Orta bandın altında
            
        # Trend yönü
        if last_row['close'] > prev_row['close'] and last_row['bb_basis'] > prev_row['bb_basis']:
            trend = "up"
        elif last_row['close'] < prev_row['close'] and last_row['bb_basis'] < prev_row['bb_basis']:
            trend = "down"
        else:
            trend = "neutral"
        
        return {
            'position': position,
            'trend': trend,
            'upper': last_row['bb_upper'],
            'basis': last_row['bb_basis'],
            'lower': last_row['bb_lower'],
            'width': width,
            'squeeze': squeeze
        }
        
    except Exception as e:
        print(f"BB sinyal analizi hatası: {str(e)}")
        return None

def bb_points(signal_type, bb_data):
    """
    Bollinger Bands puanlaması (2 puan üzerinden)
    Fiyat pozisyonu ve trend durumuna göre puanlama
    """
    points = 0
    
    if signal_type == "LONG":
        # Fiyat alt banda yakın veya kırmış (1.5p)
        if bb_data['position'] == "lower":
            points += 1.5  # Güçlü sinyal
        elif bb_data['position'] == "lower_half":
            points += 1.0  # Orta sinyal
        elif bb_data['position'] == "middle":
            points += 0.5  # Zayıf sinyal
            
        # Trend yukarı veya sıkışma (0.5p)
        if bb_data['trend'] == "up":
            points += 0.5
        elif bb_data['squeeze']:
            points += 0.25
            
    else:  # SHORT/SELL
        # Fiyat üst banda yakın veya kırmış (1.5p)
        if bb_data['position'] == "upper":
            points += 1.5  # Güçlü sinyal
        elif bb_data['position'] == "upper_half":
            points += 1.0  # Orta sinyal
        elif bb_data['position'] == "middle":
            points += 0.5  # Zayıf sinyal
            
        # Trend aşağı veya sıkışma (0.5p)
        if bb_data['trend'] == "down":
            points += 0.5
        elif bb_data['squeeze']:
            points += 0.25
            
    print(f"""
📊 Bollinger Bands Analizi:
• Pozisyon: {bb_data['position']}
• Trend: {bb_data['trend']}
• Sıkışma: {'Var' if bb_data['squeeze'] else 'Yok'}
• Puan: {points}/2
""")
            
    return min(points, 2)  # Maximum 2 puan 