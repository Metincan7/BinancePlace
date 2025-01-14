import pandas as pd
import numpy as np

class RangeFilter:
    def __init__(self, period=100, multiplier=3.0):
        self.period = period
        self.multiplier = multiplier

    def smooth_range(self, data, source='close'):
        """Pine Script'teki smoothrng fonksiyonunun birebir çevirisi"""
        x = data[source]
        wper = self.period * 2 - 1
        
        # math.abs(x - x[1]) kısmının çevirisi
        abs_diff = (x - x.shift(1)).abs()
        
        # ta.ema çevirisi
        avrng = abs_diff.ewm(span=self.period, adjust=False).mean()
        smoothrng = avrng.ewm(span=wper, adjust=False).mean() * self.multiplier
        return smoothrng

    def range_filter(self, data, source='close'):
        """Pine Script'teki rngfilt fonksiyonunun birebir çevirisi"""
        x = data[source]
        r = self.smooth_range(data, source)
        filt = pd.Series(index=data.index, dtype='float64')
        
        for i in range(len(data)):
            if i == 0:
                filt.iloc[i] = x.iloc[i]
                continue
            
            prev_filt = filt.iloc[i-1]
            curr_x = x.iloc[i]
            curr_r = r.iloc[i]
            
            if curr_x > prev_filt:
                if curr_x - curr_r < prev_filt:
                    filt.iloc[i] = prev_filt
                else:
                    filt.iloc[i] = curr_x - curr_r
            else:
                if curr_x + curr_r > prev_filt:
                    filt.iloc[i] = prev_filt
                else:
                    filt.iloc[i] = curr_x + curr_r
        
        return filt

    def generate_signals(self, data):
        src = data['close']
        filt = self.range_filter(data)
        smrng = self.smooth_range(data)
        
        # Filter Direction - Pine Script'ten birebir çeviri
        upward = pd.Series(0.0, index=data.index)
        downward = pd.Series(0.0, index=data.index)
        
        for i in range(1, len(data)):
            if filt.iloc[i] > filt.iloc[i-1]:
                upward.iloc[i] = upward.iloc[i-1] + 1
                downward.iloc[i] = 0
            elif filt.iloc[i] < filt.iloc[i-1]:
                downward.iloc[i] = downward.iloc[i-1] + 1
                upward.iloc[i] = 0
            else:
                upward.iloc[i] = upward.iloc[i-1]
                downward.iloc[i] = downward.iloc[i-1]
        
        # Break Outs - Pine Script'ten birebir çeviri
        long_cond = ((src > filt) & (src > src.shift(1)) & (upward > 0)) | \
                    ((src > filt) & (src < src.shift(1)) & (upward > 0))
        
        short_cond = ((src < filt) & (src < src.shift(1)) & (downward > 0)) | \
                     ((src < filt) & (src > src.shift(1)) & (downward > 0))
        
        # CondIni hesaplama
        cond_ini = pd.Series(0, index=data.index)
        for i in range(1, len(data)):
            if long_cond.iloc[i]:
                cond_ini.iloc[i] = 1
            elif short_cond.iloc[i]:
                cond_ini.iloc[i] = -1
            else:
                cond_ini.iloc[i] = cond_ini.iloc[i-1]
        
        # Final sinyal koşulları
        long_condition = long_cond & (cond_ini.shift(1) == -1)
        short_condition = short_cond & (cond_ini.shift(1) == 1)
        
        return {
            'filter': round(filt, 2),
            'upper_band': round(filt + smrng, 2),
            'lower_band': round(filt - smrng, 2),
            'buy_signals': long_condition,
            'sell_signals': short_condition,
            'trend': cond_ini,
            'upward': upward,
            'downward': downward
        }
