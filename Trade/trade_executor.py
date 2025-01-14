# trade_executor.py

import ccxt
import json
import os
from datetime import datetime
from .position_calculator import PositionCalculator
from .trade_settings import TRADE_SETTINGS, ORDER_TYPES, TRADE_SIDES

class TradeExecutor:
    def __init__(self):
        self.config = self.load_config()
        self.exchange = self.initialize_exchange()
        self.calculator = PositionCalculator(leverage=TRADE_SETTINGS['LEVERAGE'])
        self.open_positions = {}

    def load_config(self):
        """Config dosyasından API anahtarlarını yükle"""
        try:
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Config yüklenemedi: {str(e)}")
            return None

    def initialize_exchange(self):
        """Binance Futures bağlantısını başlat"""
        exchange = ccxt.binance({
            'apiKey': self.config['api_key'],
            'secret': self.config['api_secret'],
            'enableRateLimit': True,
            'options': {
                'defaultType': 'future',
                'adjustForTimeDifference': True
            }
        })
        
        if self.config.get('testnet', False):
            exchange.set_sandbox_mode(True)
            print("🔧 TESTNET modu aktif!")
        
        return exchange

    def execute_trade(self, signal_data):
        """Sinyal geldiğinde işlemi aç"""
        try:
            symbol = signal_data['symbol']
            side = 'LONG' if signal_data['type'] == 'buy' else 'SHORT'
            entry_price = float(signal_data['price'])

            # Kaldıraç ayarla
            self.exchange.fapiPrivate_post_leverage({
                'symbol': symbol.replace('/', ''),
                'leverage': TRADE_SETTINGS['LEVERAGE']
            })

            # TP/SL hesapla
            calc_result = self.calculator.calculate_tp_sl(
                entry_price=entry_price,
                side=side,
                sl_percent=TRADE_SETTINGS['STOP_LOSS_PERCENT'],
                tp_percent=TRADE_SETTINGS['TAKE_PROFIT_PERCENT']
            )

            # Pozisyon büyüklüğünü hesapla
            position_size = self.calculator.calculate_position_size(
                TRADE_SETTINGS['POSITION_SIZE'],
                entry_price
            )

            # Limit fiyatı hesapla
            price_deviation = TRADE_SETTINGS['PRICE_DEVIATION'] / 100
            if side == 'LONG':
                limit_price = entry_price * (1 + price_deviation)
            else:
                limit_price = entry_price * (1 - price_deviation)

            # İşlemi aç
            order = self.exchange.create_order(
                symbol=symbol,
                type=ORDER_TYPES['LIMIT'],
                side=TRADE_SIDES[side],
                amount=position_size,
                price=limit_price,
                params={
                    'timeInForce': 'GTC',
                    'stopLoss': {
                        'type': ORDER_TYPES['STOP_LOSS'],
                        'stopPrice': calc_result['sl_price']
                    },
                    'takeProfit': {
                        'type': ORDER_TYPES['TAKE_PROFIT'],
                        'stopPrice': calc_result['tp_price']
                    }
                }
            )

            # Pozisyon bilgilerini yazdır
            self.calculator.print_position_info(calc_result, position_size, side)
            
            print(f"\n✅ İşlem açıldı! Order ID: {order['id']}")
            return True

        except Exception as e:
            print(f"❌ İşlem açılırken hata: {str(e)}")
            return False

    def check_order_status(self, symbol, order_id):
        """Emir durumunu kontrol et"""
        try:
            order = self.exchange.fetch_order(order_id, symbol)
            return order['status']
        except Exception as e:
            print(f"❌ Emir kontrol hatası: {str(e)}")
            return None