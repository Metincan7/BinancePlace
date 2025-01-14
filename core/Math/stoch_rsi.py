import pandas as pd
import numpy as np

def calculate_stoch_rsi(df, lengthRSI=14, lengthStoch=14, smoothK=3, smoothD=3):
    """
    TradingView'in Stokastik RSI formülü (5m için optimize edilmiş)
    
    Parametreler:
    - lengthRSI = 14 (RSI periyodu)
    - lengthStoch = 14 (Stokastik periyodu)
    - smoothK = 3 (K için smoothing)
    - smoothD = 3 (D için smoothing)
    """
    try:
        # 1. RSI hesapla - TradingView formülü
        close_diff = df['close'].diff()
        gain = close_diff.where(close_diff > 0, 0)
        loss = -close_diff.where(close_diff < 0, 0)
        
        # EMA kullanarak RSI hesapla (TradingView yöntemi)
        avg_gain = gain.ewm(com=lengthRSI-1, adjust=True).mean()
        avg_loss = loss.ewm(com=lengthRSI-1, adjust=True).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        # 2. Stokastik RSI hesapla
        min_rsi = rsi.rolling(window=lengthStoch).min()
        max_rsi = rsi.rolling(window=lengthStoch).max()
        stoch_rsi = (rsi - min_rsi) / (max_rsi - min_rsi)
        
        # 3. %K ve %D hesapla - SMA kullan
        k = stoch_rsi.rolling(window=smoothK, center=False).mean() * 100
        d = k.rolling(window=smoothD, center=False).mean()
        
        df['stoch_rsi_k'] = k
        df['stoch_rsi_d'] = d
        
        return df
        
    except Exception as e:
        print(f"Stokastik RSI hesaplama hatası: {str(e)}")
        return df

def analyze_stoch_rsi_signals(df):
    """
    Stokastik RSI sinyallerini analiz et
    
    Dönüş değerleri:
    - zone: Aşırı alım/satım bölgesi
    - signal: Alım/satım sinyali
    - trend: Trend yönü
    """
    try:
        last_k = df['stoch_rsi_k'].iloc[-1]
        last_d = df['stoch_rsi_d'].iloc[-1]
        prev_k = df['stoch_rsi_k'].iloc[-2]
        prev_d = df['stoch_rsi_d'].iloc[-2]
        
        # Bölge tespiti
        if last_k > 80:
            zone = "aşırı alım"
        elif last_k < 20:
            zone = "aşırı satım"
        else:
            zone = "nötr"
            
        # Sinyal tespiti
        if prev_k < prev_d and last_k > last_d:
            signal = "AL"  # Altın çapraz
        elif prev_k > prev_d and last_k < last_d:
            signal = "SAT"  # Ölüm çaprazı
        else:
            signal = "BEKLE"
            
        # Trend tespiti
        if last_k > prev_k and last_d > prev_d:
            trend = "yükseliş"
        elif last_k < prev_k and last_d < prev_d:
            trend = "düşüş"
        else:
            trend = "yatay"
            
        return {
            "k_value": last_k,
            "d_value": last_d,
            "zone": zone,
            "signal": signal,
            "trend": trend
        }
        
    except Exception as e:
        print(f"Stokastik RSI analiz hatası: {str(e)}")
        return None

def get_stoch_rsi_strength(stoch_data, signal_type):
    """
    Stokastik RSI'ya göre sinyal gücünü hesapla
    
    Parametreler:
    - stoch_data: analyze_stoch_rsi_signals'dan gelen veri
    - signal_type: "LONG" veya "SHORT"
    
    Dönüş:
    - 0-3 arası puan (3 en güçlü)
    """
    if not stoch_data:
        return 0
        
    points = 0
    k_value = stoch_data['k_value']
    d_value = stoch_data['d_value']
    zone = stoch_data['zone']
    trend = stoch_data['trend']
    
    if signal_type == "LONG":
        # Aşırı satım bölgesinden çıkış
        if zone == "aşırı satım" and k_value > d_value:
            points += 2
        # Yükseliş trendi
        if trend == "yükseliş":
            points += 1
            
    else:  # SHORT
        # Aşırı alım bölgesinden çıkış
        if zone == "aşırı alım" and k_value < d_value:
            points += 2
        # Düşüş trendi
        if trend == "düşüş":
            points += 1
            
    return points 

def stoch_rsi_points(signal_type, stoch_data):
    """
    StochRSI puanlaması (2 puan üzerinden)
    K ve D değerlerine göre puanlama yapar
    """
    points = 0
    k_value = stoch_data['k_value']
    d_value = stoch_data['d_value']
    
    if signal_type == "LONG":
        # Aşırı satım bölgesinden çıkış (1.5p)
        if k_value < 20:
            points += 1.5
        elif k_value < 30:
            points += 1.0
            
        # Orta bölge ve trend (1p)
        if 30 <= k_value <= 70:
            if k_value > d_value:  # K çizgisi D'yi yukarı kesiyor
                points += 1.0
            
    else:  # SHORT/SELL
        # Aşırı alım bölgesinden çıkış (1.5p)
        if k_value > 80:
            points += 1.5
        elif k_value > 70:
            points += 1.0
            
        # Orta bölge ve trend (1p)
        if 30 <= k_value <= 70:
            if k_value < d_value:  # K çizgisi D'yi aşağı kesiyor
                points += 1.0
            
    print(f"""
📊 StochRSI Analizi:
• K Değeri: {k_value:.2f}
• D Değeri: {d_value:.2f}
• Trend: {'Yukarı' if k_value > d_value else 'Aşağı'}
• Puan: {points}/2
""")
            
    return min(points, 2)  # Maximum 2 puan 