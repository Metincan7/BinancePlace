"""
EMA Ribbon indikatörü - TradingView uyumlu
"""
import pandas as pd
import numpy as np

def calculate_ema(series, period):
    """
    TradingView uyumlu EMA hesaplama
    """
    multiplier = 2 / (period + 1)
    ema = series.ewm(span=period, adjust=False).mean()
    return ema

def calculate_ema_signals(df, periods=[5, 8, 13, 20, 50, 100, 200]):
    """
    TradingView uyumlu EMA Ribbon hesaplama
    """
    try:
        # DataFrame'in derin kopyasını oluştur
        df = df.copy(deep=True)
        
        # EMA'ları hesapla
        for period in periods:
            df[f'ema_{period}'] = df['close'].ewm(span=period, adjust=False).mean()
        
        # Signal sütununu başlangıçta oluştur
        df['signal'] = 0
        df['ema_trend'] = 0
        
        # Önceki 3 mum trend değişimi olmadığından emin ol
        for i in range(3, len(df)):
            # EMA trend kontrolü
            short_term = [df[f'ema_{p}'].iloc[i] for p in periods[:4]]
            long_term = [df[f'ema_{p}'].iloc[i] for p in periods[4:]]
            
            # Yükseliş trendi
            if all(short > long for short in short_term for long in long_term):
                df.loc[df.index[i], 'ema_trend'] = 1
            # Düşüş trendi
            elif all(short < long for short in short_term for long in long_term):
                df.loc[df.index[i], 'ema_trend'] = -1
            
            # Önceki trendleri kontrol et
            prev_trends = df['ema_trend'].iloc[i-3:i].values
            current_trend = df['ema_trend'].iloc[i]
            
            # Yükseliş sinyali
            if current_trend == 1 and all(t <= 0 for t in prev_trends):
                df.loc[df.index[i], 'signal'] = 1
            # Düşüş sinyali
            elif current_trend == -1 and all(t >= 0 for t in prev_trends):
                df.loc[df.index[i], 'signal'] = -1
        
        return df
        
    except Exception as e:
        print(f"EMA sinyalleri hesaplanırken hata: {str(e)}")
        return None

def get_ribbon_colors(df):
    """
    EMA çizgilerinin renklerini belirle
    Returns:
        dict: Her EMA için renk (green/red)
    """
    colors = {}
    periods = [5, 8, 13, 21, 34, 55, 89, 144, 233]
    
    for period in periods:
        ema_name = f'ema_{period}'
        # Yükseliş trendinde yeşil, düşüş trendinde kırmızı
        colors[ema_name] = np.where(df['ema_trend'] == 1, 'green', 
                                  np.where(df['ema_trend'] == -1, 'red', 'orange'))
    
    return colors 