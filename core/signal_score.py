import pandas as pd
from datetime import datetime, timezone, timedelta
from core.Math.volume_analyzer import VolumeAnalyzer
from core.Math.stoch_rsi import calculate_stoch_rsi, stoch_rsi_points
from core.Math.rsi_indicator import calculate_rsi, rsi_points
from core.Math.bollinger_bands import calculate_bollinger_bands,  bb_points
from core.Math.ema_ribbon import calculate_ema_signals

class SignalScore:
    def __init__(self, exchange):
        self.exchange = exchange
        
    def enhanced_ema_ribbon_score(self, ema_values, price):
        """
        Geliştirilmiş EMA Ribbon skor hesaplaması
        
        Args:
            ema_values (list): [EMA5, EMA8, EMA13, EMA20, EMA50, EMA100, EMA200]
            price (float): Mevcut fiyat
            
        Returns:
            int: 0-9 arası skor
        """
        score = 0
        try:
            # 1. Temel dizilim kontrolü (3 puan)
            correct_alignment = True
            for i in range(len(ema_values)-1):
                if ema_values[i] <= ema_values[i+1]:
                    correct_alignment = False
                    break
            if correct_alignment:
                score += 3
                print("✅ EMA Dizilimi doğru: +3 puan")
            
            # 2. Fiyat pozisyonu kontrolü (2 puan)
            if price > ema_values[0]:  # Fiyat en kısa EMA'nın üstünde
                score += 2
                print("✅ Fiyat EMA5'in üzerinde: +2 puan")
            
            # 3. Açılma/Momentum kontrolü (2 puan)
            spread = (ema_values[0] - ema_values[-1]) / ema_values[-1] * 100
            if spread > 1.0:  # %1'den fazla açılma
                score += 2
                print(f"✅ EMA Ribbon açılımı yeterli (%{spread:.2f}): +2 puan")
            
            # 4. Trend gücü kontrolü (2 puan)
            trend_strength = True
            for i in range(len(ema_values)-1):
                if abs(ema_values[i] - ema_values[i+1]) <= 0.001:
                    trend_strength = False
                    break
            if trend_strength:
                score += 2
                print("✅ Trend gücü yeterli: +2 puan")
            
            print(f"📊 Toplam EMA Ribbon Skoru: {score}/9")
            return score
            
        except Exception as e:
            print(f"❌ EMA Ribbon skor hesaplama hatası: {str(e)}")
            return 0

    def calculate_score(self, signal_data):
        """Sinyal skorunu hesapla (toplam 18 puan)"""
        try:
            score = 0
            print("\n📊 SKOR HESAPLAMA:")
            print("="*40)

            # OHLCV verilerini al
            ohlcv = self.exchange.fetch_ohlcv(signal_data['symbol'], '5m', limit=100)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            # İndikatörleri hesapla
            df = calculate_rsi(df)
            df = calculate_stoch_rsi(df)
            df = calculate_bollinger_bands(df)
            
            # EMA'ları hesapla
            for period in [5, 8, 13, 21, 34, 55, 89]:
                df[f'ema_{period}'] = df['close'].ewm(span=period, adjust=False).mean()
            
            # RSI Analizi (0-3 puan)
            rsi_value = df['rsi'].iloc[-1]
            rsi_score = 0
            
            if signal_data['type'] == 'buy':
                if 30 <= rsi_value <= 70:
                    rsi_score = 3
                elif rsi_value < 30:
                    rsi_score = 2
            else:  # sell
                if rsi_value >= 70:
                    rsi_score = 3
                elif rsi_value > 30:
                    rsi_score = 2
                    
            score += rsi_score
            print(f"• RSI Skoru: {rsi_score}/3 (RSI: {rsi_value:.1f})")
            
            # Stochastic RSI Analizi (0-3 puan)
            stoch_score = 0
            stoch_k = df['stoch_rsi_k'].iloc[-1]
            stoch_d = df['stoch_rsi_d'].iloc[-1]
            
            if signal_data['type'] == 'buy':
                if stoch_k < 20 and stoch_d < 20:
                    stoch_score = 3
                elif stoch_k < 30 and stoch_d < 30:
                    stoch_score = 2
            else:  # sell
                if stoch_k > 80 and stoch_d > 80:
                    stoch_score = 3
                elif stoch_k > 70 and stoch_d > 70:
                    stoch_score = 2
                    
            score += stoch_score
            print(f"• Stoch RSI Skoru: {stoch_score}/3 (K: {stoch_k:.1f}, D: {stoch_d:.1f})")
            
            # Bollinger Bands Analizi (0-3 puan)
            bb_score = 0
            price = signal_data['price']
            upper_band = df['bb_upper'].iloc[-1]
            lower_band = df['bb_lower'].iloc[-1]
            
            if signal_data['type'] == 'buy':
                if price <= lower_band:
                    bb_score = 3
                elif price <= lower_band * 1.01:
                    bb_score = 2
            else:  # sell
                if price >= upper_band:
                    bb_score = 3
                elif price >= upper_band * 0.99:
                    bb_score = 2
                    
            score += bb_score
            print(f"• BB Skoru: {bb_score}/3")
            
            # EMA Ribbon Analizi (0-9 puan)
            try:
                ema_values = [
                    df['ema_5'].iloc[-1],
                    df['ema_8'].iloc[-1],
                    df['ema_13'].iloc[-1],
                    df['ema_21'].iloc[-1],
                    df['ema_34'].iloc[-1],
                    df['ema_55'].iloc[-1],
                    df['ema_89'].iloc[-1]
                ]
                
                ema_score = 0
                if signal_data['type'] == 'buy':
                    if all(ema_values[i] > ema_values[i+1] for i in range(len(ema_values)-1)):
                        ema_score = 9
                    elif all(ema_values[i] > ema_values[i+1] for i in range(3)):
                        ema_score = 6
                else:  # sell
                    if all(ema_values[i] < ema_values[i+1] for i in range(len(ema_values)-1)):
                        ema_score = 9
                    elif all(ema_values[i] < ema_values[i+1] for i in range(3)):
                        ema_score = 6
                        
                score += ema_score
                print(f"• EMA Ribbon Skoru: {ema_score}/9")
                
            except Exception as e:
                print(f"❌ EMA hesaplama hatası: {str(e)}")
                ema_score = 0
            
            print("="*40)
            print(f"📈 TOPLAM SKOR: {score}/18")
            return score
            
        except Exception as e:
            print(f"❌ Skor hesaplama hatası: {str(e)}")
            return 0

    def calculate_ema_score(self, ema_values, signal_type):
        """EMA Ribbon skoru hesapla"""
        try:
            score = 0
            # EMA'ları küçükten büyüğe sırala
            sorted_emas = sorted(ema_values)
            
            if signal_type == "buy":
                # Alış sinyali için EMA'lar yukarı bakmalı
                if ema_values == sorted_emas[::-1]:
                    score += 5  # Mükemmel sıralama
                else:
                    # Kısmi puanlama
                    for i in range(len(ema_values)-1):
                        if ema_values[i] > ema_values[i+1]:
                            score += 1
                            
            else:  # sell
                # Satış sinyali için EMA'lar aşağı bakmalı
                if ema_values == sorted_emas:
                    score += 5  # Mükemmel sıralama
                else:
                    # Kısmi puanlama
                    for i in range(len(ema_values)-1):
                        if ema_values[i] < ema_values[i+1]:
                            score += 1
            
            # Trend gücü
            if score >= 3:
                score += 2
                print("✅ Trend gücü yeterli: +2 puan")
            
            return score
            
        except Exception as e:
            print(f"❌ EMA skor hesaplama hatası: {str(e)}")
            return 0

    def calculate_bb_points(self, bb_data, signal_type):
        """Bollinger Bands puanı hesapla"""
        try:
            return bb_points(signal_type, bb_data)
        except Exception as e:
            print(f"❌ BB puan hesaplama hatası: {str(e)}")
            return 0

    def calculate_rsi_points(self, signal_type, rsi_value):
        """RSI puanı hesapla"""
        try:
            return rsi_points(signal_type, rsi_value)
        except Exception as e:
            print(f"❌ RSI puan hesaplama hatası: {str(e)}")
            return 0

    def calculate_stoch_points(self, signal_type, stoch_data):
        """StochRSI puanı hesapla"""
        try:
            return stoch_rsi_points(signal_type, stoch_data)
        except Exception as e:
            print(f"❌ StochRSI puan hesaplama hatası: {str(e)}")
            return 0