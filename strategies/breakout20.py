### === Module: strategies/breakout20.py ===
"""
Breakout20 策略實作
基於20日移動平均線和20日最高價突破的量化交易策略
"""

import backtrader as bt
from loguru import logger
from typing import Dict, Any


class Breakout20Strategy(bt.Strategy):
    """
    Breakout20 策略類別
    
    策略邏輯：
    1. 追蹤啟動：收盤價跌破20日SMA時設定 tracking=True
    2. 進場條件：tracking=True 且收盤價突破過去20日最高價
    3. 停損條件：日內最低價跌破進場時最低價，以收盤價出場
    4. 重啟條件：平倉後重設 tracking=False
    """
    
    params = (
        ('sma_window', 20),      # SMA移動平均線週期
        ('high_window', 20),     # 最高價突破週期
        ('printlog', False),     # 是否列印交易日誌
    )
    
    def __init__(self):
        """初始化策略"""
        # 追蹤每檔股票的狀態
        self.tracking = {}           # 是否進入追蹤狀態
        self.entry_low = {}          # 進場當日最低價
        self.order_pending = {}      # 是否有掛單
        
        # 為每檔股票計算技術指標
        self.sma = {}               # 20日移動平均線
        self.highest = {}           # 20日最高價
        
        # 初始化每檔股票的指標和狀態
        for i, data in enumerate(self.datas):
            # 技術指標
            self.sma[data] = bt.indicators.SimpleMovingAverage(
                data.close, period=self.params.sma_window
            )
            self.highest[data] = bt.indicators.Highest(
                data.high, period=self.params.high_window
            )
            
            # 初始狀態
            self.tracking[data] = False
            self.entry_low[data] = None
            self.order_pending[data] = None
            
            logger.debug(f"策略初始化完成 - 股票: {data._name}")
    
    def log(self, txt: str, dt=None, data_name: str = ""):
        """
        記錄日誌
        
        Args:
            txt (str): 日誌內容
            dt: 日期時間
            data_name (str): 股票名稱
        """
        dt = dt or self.datas[0].datetime.date(0)
        if self.params.printlog:
            print(f'{dt.isoformat()} [{data_name}] {txt}')
        
        # 使用 loguru 記錄
        logger.info(f'{dt.isoformat()} [{data_name}] {txt}')
    
    def notify_order(self, order):
        """
        訂單狀態通知
        
        Args:
            order: 訂單物件
        """
        data = order.data
        data_name = data._name
        
        if order.status in [order.Submitted, order.Accepted]:
            # 訂單已提交/已接受
            self.order_pending[data] = order
            return
        
        if order.status in [order.Completed]:
            if order.isbuy():
                # 買單完成
                self.log(
                    f'買入執行 - 價格: {order.executed.price:.2f}, '
                    f'數量: {order.executed.size}, '
                    f'手續費: {order.executed.comm:.2f}',
                    data_name=data_name
                )
                # 記錄進場當日最低價
                self.entry_low[data] = data.low[0]
                
            elif order.issell():
                # 賣單完成
                self.log(
                    f'賣出執行 - 價格: {order.executed.price:.2f}, '
                    f'數量: {order.executed.size}, '
                    f'手續費: {order.executed.comm:.2f}',
                    data_name=data_name
                )
                # 平倉後重設追蹤狀態
                self.tracking[data] = False
                self.entry_low[data] = None
                
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            # 訂單被取消/保證金不足/被拒絕
            self.log(f'訂單取消/拒絕 - 狀態: {order.getstatusname()}', data_name=data_name)
        
        # 清除掛單記錄
        self.order_pending[data] = None
    
    def notify_trade(self, trade):
        """
        交易完成通知
        
        Args:
            trade: 交易物件
        """
        data = trade.data
        data_name = data._name
        
        if not trade.isclosed:
            return
        
        # 計算交易績效
        gross_pnl = trade.pnl
        net_pnl = trade.pnlcomm
        
        self.log(
            f'交易關閉 - 毛利: {gross_pnl:.2f}, 淨利: {net_pnl:.2f}',
            data_name=data_name
        )
    
    def next(self):
        """策略主邏輯"""
        for data in self.datas:
            self.process_data(data)
    
    def process_data(self, data):
        """
        處理單一股票的策略邏輯
        
        Args:
            data: 股票資料物件
        """
        data_name = data._name
        
        # --- DEBUG LOGGING START ---
        try:
            log_msg = (
                f"Processing Data - Stock: {data_name}, "
                f"Date: {self.datetime.date(0)}, "
                f"Data Len: {len(data)}, "
                f"SMA: {self.sma[data][0] if len(self.sma[data]) > 0 else 'N/A'}, "
                f"Highest: {self.highest[data][0] if len(self.highest[data]) > 0 else 'N/A'}"
            )
            logger.debug(log_msg)
        except IndexError:
            logger.warning(
                f"IndexError during logging - Stock: {data_name}, "
                f"Date: {self.datetime.date(0)}, "
                f"Data Len: {len(data)}"
            )
        # --- DEBUG LOGGING END ---
        
        # 檢查是否有足夠的歷史資料
        if len(data) < max(self.params.sma_window, self.params.high_window):
            return
        
        # 檢查是否有掛單
        if self.order_pending[data]:
            return
        
        # 取得當前價格和指標值
        current_close = data.close[0]
        current_low = data.low[0]
        sma_value = self.sma[data][0]
        highest_value = self.highest[data][0]
        
        # 取得倉位資訊
        position = self.getposition(data)
        
        if not position:
            # 無倉位時的邏輯
            self.handle_no_position(data, current_close, sma_value, highest_value, data_name)
        else:
            # 有倉位時的邏輯
            self.handle_with_position(data, current_low, data_name)
    
    def handle_no_position(self, data, current_close: float, sma_value: float, 
                          highest_value: float, data_name: str):
        """
        處理無倉位時的邏輯
        
        Args:
            data: 股票資料物件
            current_close (float): 當前收盤價
            sma_value (float): SMA值
            highest_value (float): 最高價值
            data_name (str): 股票名稱
        """
        # 1. 檢查是否啟動追蹤：收盤價跌破20日SMA
        if not self.tracking[data] and current_close < sma_value:
            self.tracking[data] = True
            self.log(
                f'啟動追蹤 - 收盤價 {current_close:.2f} < SMA {sma_value:.2f}',
                data_name=data_name
            )
        
        # 2. 檢查進場條件：追蹤中且收盤價突破20日最高價
        if (self.tracking[data] and 
            current_close > highest_value):
            
            # Backtrader 會自動使用 sizer 計算部位大小，我們只需下單即可
            # 執行買入
            order = self.buy(data=data)
            self.order_pending[data] = order
            
            self.log(
                f'買入信號 - 收盤價 {current_close:.2f} > 20日高點 {highest_value:.2f}',
                data_name=data_name
            )
    
    def handle_with_position(self, data, current_low: float, data_name: str):
        """
        處理有倉位時的邏輯
        
        Args:
            data: 股票資料物件
            current_low (float): 當前最低價
            data_name (str): 股票名稱
        """
        position = self.getposition(data)
        
        # 停損條件：日內最低價跌破進場時最低價
        if (self.entry_low[data] is not None and 
            current_low < self.entry_low[data]):
            
            # 執行賣出（以收盤價出場）
            order = self.sell(data=data, size=position.size)
            self.order_pending[data] = order
            
            self.log(
                f'停損信號 - 當前低點 {current_low:.2f} < 進場低點 {self.entry_low[data]:.2f}',
                data_name=data_name
            )
    
    
    def stop(self):
        """策略結束時的處理"""
        self.log(f'策略結束 - 最終資產: {self.broker.getvalue():.2f}')
        
        # 統計追蹤狀態
        tracking_count = sum(1 for tracking in self.tracking.values() if tracking)
        logger.info(f'策略結束時仍在追蹤的股票數量: {tracking_count}/{len(self.tracking)}')


class Breakout20StrategyOptimized(Breakout20Strategy):
    """
    優化版本的 Breakout20 策略
    添加額外的風險控制和優化邏輯
    """
    
    params = (
        ('sma_window', 20),
        ('high_window', 20),
        ('printlog', False),
        ('max_positions', 10),        # 最大持倉數量
        ('min_volume', 1000),         # 最小成交量要求
        ('volatility_filter', True),   # 是否使用波動率過濾
        ('atr_period', 14),           # ATR週期
        ('atr_multiplier', 2.0),      # ATR倍數
    )
    
    def __init__(self):
        """初始化優化策略"""
        super().__init__()
        
        # 添加額外指標
        self.atr = {}  # Average True Range
        
        for data in self.datas:
            if self.params.volatility_filter:
                self.atr[data] = bt.indicators.AverageTrueRange(
                    data, period=self.params.atr_period
                )
    
    def handle_no_position(self, data, current_close: float, sma_value: float,
                          highest_value: float, data_name: str):
        """
        處理無倉位時的邏輯 (優化版本)
        """
        # 檢查最大持倉限制
        current_positions = sum(1 for d in self.datas if self.getposition(d).size > 0)
        if current_positions >= self.params.max_positions:
            return

        # 檢查成交量
        if data.volume[0] < self.params.min_volume:
            return

        # 根據 ATR 調整風險 (此處不直接調整部位，而是作為進場過濾器)
        if self.params.volatility_filter and data in self.atr:
            if len(data) >= self.params.atr_period:
                atr_value = self.atr[data][0]
                price = data.close[0]
                # 如果波動過大，則跳過
                if (atr_value / price) > 0.05: # ATR 超過股價5%，視為波動過大
                    return

        # 呼叫基礎版本的邏輯
        super().handle_no_position(data, current_close, sma_value, highest_value, data_name)


def get_strategy_class(optimized: bool = False):
    """
    取得策略類別
    
    Args:
        optimized (bool): 是否使用優化版本
        
    Returns:
        class: 策略類別
    """
    return Breakout20StrategyOptimized if optimized else Breakout20Strategy


def main():
    """測試函數"""
    import backtrader as bt
    
    # 建立 Cerebro 引擎
    cerebro = bt.Cerebro()
    
    # 添加策略
    cerebro.addstrategy(Breakout20Strategy, printlog=True)
    
    # 設定初始資金
    cerebro.broker.setcash(1000000)
    
    print(f'初始資產: {cerebro.broker.getvalue():.2f}')
    
    # 這裡需要添加資料才能執行
    # cerebro.adddata(data)
    # cerebro.run()
    
    print("策略類別載入成功")


if __name__ == '__main__':
    main()