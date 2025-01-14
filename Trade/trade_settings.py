# Trade ayarları
TRADE_SETTINGS = {
    # Sinyal ayarları
    'MIN_SIGNAL_SCORE': 10,      # Minimum sinyal skoru
    
    # İşlem büyüklüğü ayarları
    'POSITION_SIZE': 1,          # USDT cinsinden işlem büyüklüğü
    'LEVERAGE': 10,              # Kaldıraç oranı
    
    # Risk yönetimi (Gerçek değerler kaldıraçsız)
    'STOP_LOSS_PERCENT': 1.0,    # Stop Loss yüzdesi (%1 * 10x = %10)
    'TAKE_PROFIT_PERCENT': 1.5,  # Take Profit yüzdesi (%1.5 * 10x = %15)
    
    # İşlem limitleri
    'MAX_OPEN_POSITIONS': 2,     # Maksimum 2 açık pozisyon
    'MIN_VOLUME': 1000000,       # Minimum 24s hacim (USDT)
    
    # Market türü
    'MARKET_TYPE': 'future',    # Futures piyasası
    
    # Zaman ayarları
    'POSITION_CHECK_INTERVAL': 5,    # Pozisyon kontrol aralığı (saniye)
    'ORDER_TIMEOUT': 120,            # Emir timeout süresi (2 dakika)
    
    # Limit order ayarları
    'PRICE_DEVIATION': 0.1,      # Limit fiyat sapması (%)
}

# Market türleri
MARKET_TYPES = {
    'SPOT': 'spot',
    'FUTURES': 'future'
}

# İşlem yönleri
TRADE_SIDES = {
    'BUY': 'BUY',
    'SELL': 'SELL'
}

# Emir türleri (sadece futures için)
ORDER_TYPES = {
    'MARKET': 'MARKET',
    'LIMIT': 'LIMIT',
    'STOP_LOSS': 'STOP_MARKET',
    'TAKE_PROFIT': 'TAKE_PROFIT_MARKET'
} 