import numpy as np
import pandas as pd

class ConsolidationAnalyzer:
    def __init__(self):
        self.window_size = 20  # Bu iyi
        self.price_threshold = 0.02  # %2'ye çıkaralım (şu an %1.5)
        self.bb_width_threshold = 0.015  # %1.5'e çıkaralım
        self.signal_density_threshold = 3  # Bu iyi
        
    def analyze(self, df):
        """
        Konsolidasyon analizi yap
        Returns:
            dict: {
                'is_consolidation': bool,
                'reason': str,
                'metrics': dict
            }
        """
        try:
            # Buy ve sell sinyallerinin varlığını kontrol et
            if 'buy_signals' not in df.columns or 'sell_signals' not in df.columns:
                return {
                    'is_consolidation': False,
                    'reason': "Sinyal kolonları eksik",
                    'metrics': {}
                }
            # BB sütun isimlerini güncelle
            bb_columns = ['bb_upper', 'bb_lower', 'bb_basis']  # bb_middle -> bb_basis
            if not all(col in df.columns for col in bb_columns):
                print("❌ BB sütunları eksik!")
                print("• Mevcut sütunlar:", df.columns.tolist())
                return {
                    'is_consolidation': True,
                    'reason': "BB hesaplaması eksik",
                    'metrics': {}
                }
            
            result = {
                'is_consolidation': False,
                'reason': '',
                'metrics': {}
            }
            
            # 1. Fiyat Aralığı Kontrolü
            recent_high = df['high'].tail(self.window_size).max()
            recent_low = df['low'].tail(self.window_size).min()
            price_range = (recent_high - recent_low) / recent_low
            result['metrics']['price_range'] = price_range
            
            if price_range < self.price_threshold:
                result['is_consolidation'] = True
                result['reason'] = f"Fiyat dar bantta sıkışmış (%{price_range*100:.1f})"
                return result
            
            # 2. Bollinger Bands Genişlik Kontrolü
            bb_width = (df['bb_upper'].iloc[-1] - df['bb_lower'].iloc[-1]) / df['bb_basis'].iloc[-1]  # bb_middle -> bb_basis
            result['metrics']['bb_width'] = bb_width
            
            if bb_width < self.bb_width_threshold:
                result['is_consolidation'] = True
                result['reason'] = f"BB bantları çok dar (%{bb_width*100:.1f})"
                return result
            
            # 3. EMA Ribbon Sıkışma Kontrolü
            ema_values = [
                df['ema_5'].iloc[-1],
                df['ema_8'].iloc[-1],
                df['ema_13'].iloc[-1],
                df['ema_21'].iloc[-1],
                df['ema_34'].iloc[-1]
            ]
            
            ema_range = (max(ema_values) - min(ema_values)) / min(ema_values)
            result['metrics']['ema_range'] = ema_range
            
            if ema_range < 0.01:  # %1'den az ayrışma
                result['is_consolidation'] = True
                result['reason'] = f"EMA'lar sıkışmış (%{ema_range*100:.1f})"
                return result
            
            # 4. Volatilite Kontrolü (ATR kullanarak)
            if 'atr' in df.columns:
                atr_ratio = df['atr'].iloc[-1] / df['close'].iloc[-1]
                result['metrics']['atr_ratio'] = atr_ratio
                
                if atr_ratio < 0.001:  # %0.1'den az volatilite
                    result['is_consolidation'] = True
                    result['reason'] = f"Düşük volatilite (%{atr_ratio*100:.3f})"
                    return result
            
            # Trend yönü kontrolü ekleyelim
            price_direction = df['close'].tail(self.window_size).diff().mean()
            if abs(price_direction) > 0.0002:  # Net trend varsa
                return {
                    'is_consolidation': False,
                    'reason': "Net trend mevcut",
                    'metrics': {'price_direction': price_direction}
                }
                
            result['reason'] = "Trend bölgesi"
            return result
            
        except Exception as e:
            print(f"❌ Konsolidasyon analizi hatası: {str(e)}")
            return {'is_consolidation': True, 'reason': f"Hata: {str(e)}", 'metrics': {}} 