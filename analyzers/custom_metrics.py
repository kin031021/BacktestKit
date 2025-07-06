### === Module: analyzers/custom_metrics.py ===
"""
自訂績效分析器
提供詳細的回測績效指標計算和分析功能
"""

import math
import backtrader as bt
import pandas as pd
from collections import OrderedDict
from datetime import datetime
from typing import Dict, Any, List, Tuple
from loguru import logger


class CustomMetricsAnalyzer(bt.Analyzer):
    """
    自訂績效指標分析器
    
    計算包括：
    - CAGR (年化複合報酬率)
    - Total Return (總報酬率)
    - Sharpe Ratio (夏普比率)
    - Maximum Drawdown (最大回撤)
    - Win Rate (勝率)
    - Profit Factor (獲利因子)
    - Average Trade (平均交易)
    - Total Number of Trades (總交易次數)
    """
    
    def __init__(self):
        """初始化分析器"""
        # 績效追蹤變數
        self.start_value = None
        self.end_value = None
        self.start_date = None
        self.end_date = None
        
        # 淨值追蹤
        self.portfolio_values = []
        self.dates = []
        
        # 交易記錄
        self.trades = []
        self.winning_trades = []
        self.losing_trades = []
        
        # 回撤計算
        self.peak_value = 0
        self.max_drawdown = 0
        self.max_drawdown_duration = 0
        self.current_drawdown_duration = 0
        self.in_drawdown = False
        
        # 日報酬率
        self.daily_returns = []
        
        logger.debug("自訂績效分析器初始化完成")
    
    def start(self):
        """回測開始時執行"""
        # self.start_value 不在此處初始化
        # self.start_date 不在此處初始化
        self.peak_value = self.strategy.broker.getvalue() # 峰值可以先設為初始資金
        
        logger.info(f"分析器啟動 - 初始資金: {self.strategy.broker.getvalue():,.2f}")

    def next(self):
        """每個交易日執行"""
        # 首次執行 next 時，記錄開始資訊
        if self.start_date is None:
            self.start_date = self.strategy.datetime.date(0)
            self.start_value = self.strategy.broker.getvalue()
            self.peak_value = self.start_value
            logger.info(f"回測資料開始 - 日期: {self.start_date}, 資金: {self.start_value:,.2f}")

        current_value = self.strategy.broker.getvalue()
        current_date = self.strategy.datetime.date(0)
        
        # 記錄淨值和日期
        self.portfolio_values.append(current_value)
        self.dates.append(current_date)
        
        # 計算日報酬率
        if len(self.portfolio_values) > 1:
            daily_return = (current_value - self.portfolio_values[-2]) / self.portfolio_values[-2]
            self.daily_returns.append(daily_return)
        
        # 更新最大回撤
        self._update_drawdown(current_value)
    
    def notify_trade(self, trade):
        """交易完成通知"""
        if trade.isclosed:
            # 記錄交易資訊
            entry_date = bt.num2date(trade.dtopen)
            exit_date = bt.num2date(trade.dtclose)
            
            trade_info = {
                'entry_date': entry_date,
                'exit_date': exit_date,
                'symbol': trade.data._name,
                'size': trade.size,
                'entry_price': trade.price,
                'exit_price': trade.pnlcomm / trade.size + trade.price if trade.size != 0 else 0,
                'pnl': trade.pnl,
                'pnl_comm': trade.pnlcomm,
                'commission': trade.commission,
                'duration': (exit_date - entry_date).days,
                'return_pct': trade.pnl / (abs(trade.size) * trade.price) * 100 if trade.price != 0 and trade.size != 0 else 0
            }
            
            self.trades.append(trade_info)
            
            # 分類盈虧交易
            if trade.pnlcomm > 0:
                self.winning_trades.append(trade_info)
            elif trade.pnlcomm < 0:
                self.losing_trades.append(trade_info)
            
            logger.debug(f"交易記錄: {trade.data._name} PnL: {trade.pnlcomm:.2f}")
    
    def stop(self):
        """回測結束時執行"""
        self.end_value = self.strategy.broker.getvalue()
        self.end_date = self.strategy.datetime.date(0)
        
        logger.info(f"回測結束 - 最終資金: {self.end_value:,.2f}")
    
    def _update_drawdown(self, current_value: float):
        """
        更新回撤計算
        
        Args:
            current_value (float): 當前資產淨值
        """
        if current_value > self.peak_value:
            # 創新高
            self.peak_value = current_value
            if self.in_drawdown:
                self.in_drawdown = False
                self.current_drawdown_duration = 0
        else:
            # 在回撤中
            if not self.in_drawdown:
                self.in_drawdown = True
            
            self.current_drawdown_duration += 1
            self.max_drawdown_duration = max(
                self.max_drawdown_duration, 
                self.current_drawdown_duration
            )
            
            # 計算當前回撤
            current_drawdown = (self.peak_value - current_value) / self.peak_value
            self.max_drawdown = max(self.max_drawdown, current_drawdown)
    
    def _calculate_cagr(self) -> float:
        """
        計算年化複合報酬率 (CAGR)
        
        Returns:
            float: CAGR百分比
        """
        if not self.start_value or not self.end_value or not self.start_date or not self.end_date:
            return 0.0
        
        total_days = (self.end_date - self.start_date).days
        if total_days <= 0:
            return 0.0
        
        years = total_days / 365.25
        if years <= 0:
            return 0.0
        
        cagr = (self.end_value / self.start_value) ** (1/years) - 1
        return cagr * 100
    
    def _calculate_total_return(self) -> float:
        """
        計算總報酬率
        
        Returns:
            float: 總報酬率百分比
        """
        if not self.start_value or not self.end_value:
            return 0.0
        
        return (self.end_value - self.start_value) / self.start_value * 100
    
    def _calculate_sharpe_ratio(self, risk_free_rate: float = 0.01) -> float:
        """
        計算夏普比率
        
        Args:
            risk_free_rate (float): 無風險利率 (年化)
            
        Returns:
            float: 夏普比率
        """
        if not self.daily_returns or len(self.daily_returns) < 2:
            return 0.0
        
        # 計算年化報酬率
        mean_daily_return = sum(self.daily_returns) / len(self.daily_returns)
        annual_return = (1 + mean_daily_return) ** 252 - 1
        
        # 計算年化標準差
        variance = sum([(r - mean_daily_return) ** 2 for r in self.daily_returns]) / (len(self.daily_returns) - 1)
        daily_std = math.sqrt(variance)
        annual_std = daily_std * math.sqrt(252)
        
        if annual_std == 0:
            return 0.0
        
        sharpe = (annual_return - risk_free_rate) / annual_std
        return sharpe
    
    def _calculate_win_rate(self) -> float:
        """
        計算勝率
        
        Returns:
            float: 勝率百分比
        """
        total_trades = len(self.trades)
        if total_trades == 0:
            return 0.0
        
        winning_trades = len(self.winning_trades)
        return winning_trades / total_trades * 100
    
    def _calculate_profit_factor(self) -> float:
        """
        計算獲利因子
        
        Returns:
            float: 獲利因子
        """
        total_profit = sum(trade['pnl_comm'] for trade in self.winning_trades)
        total_loss = abs(sum(trade['pnl_comm'] for trade in self.losing_trades))
        
        if total_loss == 0:
            return float('inf') if total_profit > 0 else 0.0
        
        return total_profit / total_loss
    
    def _calculate_average_trade(self) -> Tuple[float, float]:
        """
        計算平均交易
        
        Returns:
            Tuple[float, float]: (平均獲利交易, 平均虧損交易)
        """
        avg_win = sum(trade['pnl_comm'] for trade in self.winning_trades) / len(self.winning_trades) if self.winning_trades else 0.0
        avg_loss = sum(trade['pnl_comm'] for trade in self.losing_trades) / len(self.losing_trades) if self.losing_trades else 0.0
        
        return avg_win, avg_loss
    
    def _calculate_volatility(self) -> float:
        """
        計算年化波動率
        
        Returns:
            float: 年化波動率百分比
        """
        if not self.daily_returns or len(self.daily_returns) < 2:
            return 0.0
        
        mean_return = sum(self.daily_returns) / len(self.daily_returns)
        variance = sum([(r - mean_return) ** 2 for r in self.daily_returns]) / (len(self.daily_returns) - 1)
        daily_volatility = math.sqrt(variance)
        annual_volatility = daily_volatility * math.sqrt(252)
        
        return annual_volatility * 100
    
    def get_analysis(self) -> Dict[str, Any]:
        """
        取得分析結果
        
        Returns:
            Dict[str, Any]: 完整的績效分析結果
        """
        # 基本績效指標
        cagr = self._calculate_cagr()
        total_return = self._calculate_total_return()
        sharpe_ratio = self._calculate_sharpe_ratio()
        win_rate = self._calculate_win_rate()
        profit_factor = self._calculate_profit_factor()
        avg_win, avg_loss = self._calculate_average_trade()
        volatility = self._calculate_volatility()
        
        # 交易統計
        total_trades = len(self.trades)
        winning_trades = len(self.winning_trades)
        losing_trades = len(self.losing_trades)
        
        # 最大獲利/虧損交易
        best_trade = max(self.trades, key=lambda x: x['pnl_comm'])['pnl_comm'] if self.trades else 0
        worst_trade = min(self.trades, key=lambda x: x['pnl_comm'])['pnl_comm'] if self.trades else 0
        
        # 平均持倉天數
        avg_duration = sum(trade['duration'] for trade in self.trades) / len(self.trades) if self.trades else 0
        
        results = OrderedDict([
            # 基本資訊
            ('start_date', self.start_date.strftime('%Y-%m-%d') if self.start_date else ''),
            ('end_date', self.end_date.strftime('%Y-%m-%d') if self.end_date else ''),
            ('start_value', self.start_value or 0),
            ('end_value', self.end_value or 0),
            
            # 報酬指標
            ('total_return_pct', round(total_return, 2)),
            ('cagr_pct', round(cagr, 2)),
            ('sharpe_ratio', round(sharpe_ratio, 3)),
            ('volatility_pct', round(volatility, 2)),
            
            # 風險指標
            ('max_drawdown_pct', round(self.max_drawdown * 100, 2)),
            ('max_drawdown_duration', self.max_drawdown_duration),
            
            # 交易統計
            ('total_trades', total_trades),
            ('winning_trades', winning_trades),
            ('losing_trades', losing_trades),
            ('win_rate_pct', round(win_rate, 2)),
            ('profit_factor', round(profit_factor, 2) if profit_factor != float('inf') else 'Inf'),
            
            # 交易明細
            ('avg_winning_trade', round(avg_win, 2)),
            ('avg_losing_trade', round(avg_loss, 2)),
            ('best_trade', round(best_trade, 2)),
            ('worst_trade', round(worst_trade, 2)),
            ('avg_duration_days', round(avg_duration, 1)),
            
            # 其他統計
            ('total_commission', round(sum(trade['commission'] for trade in self.trades), 2)),
            ('trading_days', len(self.portfolio_values)),
        ])
        
        return results
    
    def get_trades_dataframe(self) -> pd.DataFrame:
        """
        取得交易明細DataFrame
        
        Returns:
            pd.DataFrame: 交易明細表
        """
        if not self.trades:
            return pd.DataFrame()
        
        df = pd.DataFrame(self.trades)
        
        # 格式化日期
        df['entry_date'] = pd.to_datetime(df['entry_date'])
        df['exit_date'] = pd.to_datetime(df['exit_date'])
        
        # 排序
        df = df.sort_values('entry_date').reset_index(drop=True)
        
        # 四捨五入數值
        numeric_columns = ['entry_price', 'exit_price', 'pnl', 'pnl_comm', 'commission', 'return_pct']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = df[col].round(2)
        
        return df
    
    def print_summary(self):
        """列印績效摘要"""
        results = self.get_analysis()
        
        print("\n" + "="*60)
        print("             回測績效摘要報告")
        print("="*60)
        
        print(f"回測期間: {results['start_date']} ~ {results['end_date']}")
        print(f"初始資金: {results['start_value']:,.0f}")
        print(f"最終資金: {results['end_value']:,.0f}")
        print("-"*60)
        
        print("報酬指標:")
        print(f"  總報酬率: {results['total_return_pct']:.2f}%")
        print(f"  年化報酬率 (CAGR): {results['cagr_pct']:.2f}%")
        print(f"  夏普比率: {results['sharpe_ratio']:.3f}")
        print(f"  年化波動率: {results['volatility_pct']:.2f}%")
        print("-"*60)
        
        print("風險指標:")
        print(f"  最大回撤: {results['max_drawdown_pct']:.2f}%")
        print(f"  最大回撤期間: {results['max_drawdown_duration']} 天")
        print("-"*60)
        
        print("交易統計:")
        print(f"  總交易次數: {results['total_trades']}")
        print(f"  獲利交易: {results['winning_trades']}")
        print(f"  虧損交易: {results['losing_trades']}")
        print(f"  勝率: {results['win_rate_pct']:.2f}%")
        print(f"  獲利因子: {results['profit_factor']}")
        print("-"*60)
        
        print("交易明細:")
        print(f"  平均獲利交易: {results['avg_winning_trade']:,.2f}")
        print(f"  平均虧損交易: {results['avg_losing_trade']:,.2f}")
        print(f"  最佳交易: {results['best_trade']:,.2f}")
        print(f"  最差交易: {results['worst_trade']:,.2f}")
        print(f"  平均持倉天數: {results['avg_duration_days']:.1f}")
        print(f"  總手續費: {results['total_commission']:,.2f}")
        
        print("="*60)


def main():
    """測試函數"""
    # 這裡可以添加分析器的測試程式碼
    print("自訂績效分析器載入成功")


if __name__ == '__main__':
    main()