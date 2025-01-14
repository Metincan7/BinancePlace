from Trade.position_calculator import PositionCalculator
from Trade.trade_settings import TRADE_SETTINGS, ORDER_TYPES, TRADE_SIDES

def open_futures_position(exchange, symbol, signal_data):
    """Futures pozisyonu aç"""
    try:
        print("\n" + "="*60)
        print("🔄 FUTURES POZİSYON AÇILIYOR")
        print("="*60)
        
        print(f"📊 Gelen Sinyal Detayları:")
        print(f"• Symbol: {symbol}")
        print(f"• Fiyat: {signal_data['price']}")
        print(f"• Yön: {signal_data['type']}")
        
        # Symbol formatını düzelt
        symbol_without_slash = symbol.replace('/', '')
        print(f"\n1️⃣ Symbol düzeltildi: {symbol} -> {symbol_without_slash}")
        
        try:
            # Futures moduna geç
            exchange.options['defaultType'] = 'future'
            print(f"2️⃣ Market tipi future olarak ayarlandı")
            
            # Margin type'ı ISOLATED yap
            try:
                exchange.set_margin_mode('ISOLATED', symbol_without_slash)
                print(f"3️⃣ Margin type ISOLATED olarak ayarlandı")
            except Exception as e:
                if "No need to change margin type" not in str(e):
                    print(f"⚠️ Margin type hatası: {str(e)}")
            
            # Kaldıracı ayarla
            try:
                exchange.set_leverage(TRADE_SETTINGS['LEVERAGE'], symbol_without_slash)
                print(f"4️⃣ Kaldıraç {TRADE_SETTINGS['LEVERAGE']}x olarak ayarlandı")
            except Exception as e:
                print(f"⚠️ Kaldıraç ayarlama hatası: {str(e)}")
            
            # İşlem yönünü belirle
            side = TRADE_SIDES['BUY'] if signal_data['type'] == 'buy' else TRADE_SIDES['SELL']
            print(f"5️⃣ İşlem yönü: {side}")
            
            # Position Calculator ile hesaplamalar
            calculator = PositionCalculator(leverage=TRADE_SETTINGS['LEVERAGE'])
            position_size = calculator.calculate_position_size(
                TRADE_SETTINGS['POSITION_SIZE'],
                signal_data['price']
            )
            print(f"6️⃣ Pozisyon büyüklüğü hesaplandı: {position_size}")
            
            # TP/SL hesapla
            calc_result = calculator.calculate_tp_sl(
                entry_price=signal_data['price'],
                side='LONG' if side == 'BUY' else 'SHORT',
                sl_percent=TRADE_SETTINGS['STOP_LOSS_PERCENT'],
                tp_percent=TRADE_SETTINGS['TAKE_PROFIT_PERCENT']
            )
            print("\n7️⃣ TP/SL Seviyeleri:")
            print(f"• Giriş: {calc_result['entry_price']:.4f}")
            print(f"• Stop Loss: {calc_result['sl_price']:.4f}")
            print(f"• Take Profit: {calc_result['tp_price']:.4f}")
            
            print("\n8️⃣ Market emri gönderiliyor...")
            # Ana order'ı aç
            order = exchange.create_market_order(
                symbol=symbol_without_slash,
                side=side.lower(),
                amount=position_size,
                params={'type': 'future'}
            )
            print(f"✅ Market emri açıldı! Order ID: {order['id']}")
            
            print("\n9️⃣ Stop Loss emri gönderiliyor...")
            # Stop Loss emri
            sl_order = exchange.create_order(
                symbol=symbol_without_slash,
                type='STOP_MARKET',
                side='sell' if side == 'BUY' else 'buy',
                amount=position_size,
                params={
                    'stopPrice': calc_result['sl_price'],
                    'reduceOnly': True,
                    'workingType': 'MARK_PRICE'
                }
            )
            print(f"✅ Stop Loss emri yerleştirildi! Order ID: {sl_order['id']}")
            
            print("\n🔟 Take Profit emri gönderiliyor...")
            # Take Profit emri
            tp_order = exchange.create_order(
                symbol=symbol_without_slash,
                type='TAKE_PROFIT_MARKET',
                side='sell' if side == 'BUY' else 'buy',
                amount=position_size,
                params={
                    'stopPrice': calc_result['tp_price'],
                    'reduceOnly': True,
                    'workingType': 'MARK_PRICE'
                }
            )
            print(f"✅ Take Profit emri yerleştirildi! Order ID: {tp_order['id']}")
            
            print(f"""
{'='*60}
✅ POZİSYON BAŞARIYLA AÇILDI!
• Symbol: {symbol}
• Yön: {side}
• Giriş: {calc_result['entry_price']:.4f}
• Stop Loss: {calc_result['sl_price']:.4f}
• Take Profit: {calc_result['tp_price']:.4f}
• Miktar: {position_size}
• Kaldıraç: {TRADE_SETTINGS['LEVERAGE']}x
• Order ID: {order['id']}
{'='*60}
""")
            return True
            
        except Exception as e:
            print(f"\n❌ İŞLEM HATASI!")
            print(f"• Hata Tipi: {type(e).__name__}")
            print(f"• Hata Mesajı: {str(e)}")
            print(f"• Son İşlem: {e.__traceback__.tb_frame.f_code.co_name}")
            return False
            
    except Exception as e:
        print(f"\n❌ GENEL HATA!")
        print(f"• Hata Tipi: {type(e).__name__}")
        print(f"• Hata Mesajı: {str(e)}")
        return False 