"""
Hacim analizi için özel modül
"""
import pandas as pd
import numpy as np
from datetime import datetime

class VolumeAnalyzer:
    def __init__(self, df):
        self.df = df
        
    def get_volume_score(self):
        """Hacim skoru hesapla"""
        try:
            # Son kapanmış mumun hacmi
            current_volume = self.df['volume'].iloc[-1]
            
            # Hacim ortalamaları
            volume_ma10 = self.df['volume'].rolling(window=10).mean().iloc[-1]
            volume_ma50 = self.df['volume'].rolling(window=50).mean().iloc[-1]
            
            # Hacim değişim yüzdeleri
            short_term_change = ((current_volume - volume_ma10) / volume_ma10) * 100
            long_term_change = ((current_volume - volume_ma50) / volume_ma50) * 100
            
            score = 0
            
            # Kısa vadeli hacim artışı (değerleri düşürdük)
            if short_term_change > 40:  # %50 -> %30
                score += 0.5
            elif short_term_change > 15:  # %20 -> %10
                score += 0.3
            
            # Uzun vadeli hacim artışı (değerleri düşürdük)
            if long_term_change > 40:  # %50 -> %30
                score += 0.5
            elif long_term_change > 15:  # %20 -> %10
                score += 0.3
            
            print(f"""
--------------------------------------------------
📊 HACİM ANALİZİ:
• Mevcut Hacim: {int(current_volume):,}
• 10 Mum Ort.: {int(volume_ma10):,}
• 50 Mum Ort.: {int(volume_ma50):,}
• Kısa Vadeli Değişim: %{short_term_change:.1f}
• Uzun Vadeli Değişim: %{long_term_change:.1f}
• Hacim Skoru: {score:.2f}
--------------------------------------------------
""")
            return score
            
        except Exception as e:
            print(f"❌ Hacim hesaplama hatası: {str(e)}")
            return 0.0
    
    def get_previous_volumes(self, idx, lookback=3):
        """Önceki mumların hacim bilgisi"""
        idx_loc = self.df.index.get_loc(idx)
        prev_volumes = []
        
        for i in range(max(0, idx_loc-lookback), idx_loc):
            prev_time = self.df.index[i]
            prev_volumes.append(self.df.loc[prev_time, 'volume'])
        
        return prev_volumes 