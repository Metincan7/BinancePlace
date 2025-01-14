from core.Math.bollinger_bands import calculate_bollinger_bands
from core.Math.stoch_rsi import calculate_stoch_rsi
from core.Math.rsi_indicator import calculate_rsi
from core.Math.consolidation_analyzer import ConsolidationAnalyzer

class SignalValidator:
    def __init__(self, exchange):
        self.exchange = exchange
        self.consolidation_analyzer = ConsolidationAnalyzer()
        
    def validate_signal(self, df, signal_data):
        try:
            print("\n--------------------------------------------------")
            
            # İndikatörleri hesapla
            df = calculate_bollinger_bands(df)
            df = calculate_stoch_rsi(df)
            df = calculate_rsi(df)
            
            # Konsolidasyon Analizi
            cons_result = self.consolidation_analyzer.analyze(df)
            
            if cons_result['is_consolidation']:
                print(f"⚠️ KONSOLİDASYON BÖLGESİ!")
                print(f"• Sebep: {cons_result['reason']}")
                if cons_result['metrics']:
                    print("\n📊 Metrikler:")
                    print(f"• Son 40 mumdaki sinyal sayısı: {cons_result['metrics']['long_signals']}")
                    print(f"• Son 20 mumdaki sinyal sayısı: {cons_result['metrics']['short_signals']}")
                print("--------------------------------------------------")
                return False
            
            print("✅ TREND BÖLGESİ - Sinyal Geçerli")
            
            # Hacim Analizi...
            current_volume = df['volume'].iloc[-1] * signal_data['price']
            volume_ma_10 = (df['volume'] * df['close']).rolling(10).mean().iloc[-1]
            volume_ma_50 = (df['volume'] * df['close']).rolling(50).mean().iloc[-1]
            
            # Hacim değişim yüzdeleri
            short_term_change = ((current_volume - volume_ma_10) / volume_ma_10) * 100
            long_term_change = ((current_volume - volume_ma_50) / volume_ma_50) * 100
            
            print(f"• Mevcut Hacim: {current_volume:,.0f}")
            print(f"• 10 Mum Ort.: {volume_ma_10:,.0f}")
            print(f"• 50 Mum Ort.: {volume_ma_50:,.0f}")
            print(f"• Kısa Vadeli Değişim: %{short_term_change:.1f}")
            print(f"• Uzun Vadeli Değişim: %{long_term_change:.1f}")
            
            # Hacim kriterleri
            volume_score = 0
            if current_volume > 500_000:  # 500k USD minimum hacim
                volume_score += 1
            if current_volume > volume_ma_10:  # 10 mumluk ortalamadan yüksek
                volume_score += 1
            if current_volume > volume_ma_50:  # 50 mumluk ortalamadan yüksek
                volume_score += 1
                
            print(f"• Hacim Skoru: {volume_score:.2f}")
            print("--------------------------------------------------\n")
            
            return volume_score >= 1  # En az 1 kriteri karşılamalı

        except Exception as e:
            print(f"❌ Validasyon hatası: {str(e)}")
            return False 