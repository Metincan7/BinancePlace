class PositionCalculator:
    def __init__(self, leverage=10):
        self.leverage = leverage

    def calculate_tp_sl(self, entry_price, side, sl_percent=1.0, tp_percent=1.5):
        """
        TP ve SL seviyelerini hesapla
        
        Args:
            entry_price (float): Giriş fiyatı
            side (str): İşlem yönü ('LONG' veya 'SHORT')
            sl_percent (float): Stop Loss yüzdesi (kaldıraçsız)
            tp_percent (float): Take Profit yüzdesi (kaldıraçsız)
            
        Returns:
            dict: TP ve SL seviyeleri ve yüzdeleri
        """
        # Kaldıraçlı yüzdeleri hesapla
        leveraged_sl = sl_percent * self.leverage
        leveraged_tp = tp_percent * self.leverage
        
        if side == 'LONG':
            sl_price = entry_price * (1 - (sl_percent / 100))
            tp_price = entry_price * (1 + (tp_percent / 100))
        else:  # SHORT
            sl_price = entry_price * (1 + (sl_percent / 100))
            tp_price = entry_price * (1 - (tp_percent / 100))
            
        return {
            'entry_price': entry_price,
            'sl_price': sl_price,
            'tp_price': tp_price,
            'sl_percent': sl_percent,
            'tp_percent': tp_percent,
            'leveraged_sl': leveraged_sl,
            'leveraged_tp': leveraged_tp
        }

    def calculate_position_size(self, usdt_amount, entry_price):
        """
        Pozisyon büyüklüğünü hesapla
        
        Args:
            usdt_amount (float): USDT cinsinden işlem büyüklüğü
            entry_price (float): Giriş fiyatı
            
        Returns:
            float: Coin cinsinden pozisyon büyüklüğü
        """
        position_size = (usdt_amount * self.leverage) / entry_price
        return position_size

    def calculate_risk(self, position_size, entry_price, sl_price):
        """
        Risk miktarını hesapla
        
        Args:
            position_size (float): Coin cinsinden pozisyon büyüklüğü
            entry_price (float): Giriş fiyatı
            sl_price (float): Stop Loss fiyatı
            
        Returns:
            float: USDT cinsinden risk miktarı
        """
        risk = abs(entry_price - sl_price) * position_size
        return risk

    def print_position_info(self, calc_result, position_size, side):
        """
        Pozisyon bilgilerini yazdır
        """
        print(f"\n📊 POZİSYON BİLGİLERİ:")
        print(f"{'='*40}")
        print(f"Yön: {'🟢 LONG' if side == 'LONG' else '🔴 SHORT'}")
        print(f"Giriş Fiyatı: {calc_result['entry_price']:.4f}")
        print(f"Stop Loss: {calc_result['sl_price']:.4f} (-%{calc_result['leveraged_sl']:.1f})")
        print(f"Take Profit: {calc_result['tp_price']:.4f} (+%{calc_result['leveraged_tp']:.1f})")
        print(f"Pozisyon Büyüklüğü: {position_size:.8f}")
        print(f"Kaldıraç: {self.leverage}x")
        
        # Risk hesapla
        risk = self.calculate_risk(position_size, calc_result['entry_price'], calc_result['sl_price'])
        print(f"Risk (USDT): {risk:.2f}")
        print(f"{'='*40}")


# Örnek kullanım:
if __name__ == "__main__":
    # Test
    calc = PositionCalculator(leverage=10)
    
    # Örnek değerler
    entry_price = 50000  # BTC örneği
    side = 'LONG'
    usdt_amount = 1  # 1 USDT
    
    # TP/SL hesapla
    result = calc.calculate_tp_sl(
        entry_price=entry_price,
        side=side,
        sl_percent=1.0,   # %1 -> kaldıraçla %10
        tp_percent=1.5    # %1.5 -> kaldıraçla %15
    )
    
    # Pozisyon büyüklüğünü hesapla
    pos_size = calc.calculate_position_size(usdt_amount, entry_price)
    
    # Bilgileri yazdır
    calc.print_position_info(result, pos_size, side) 