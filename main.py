### === Module: main.py ===
"""
Backtrader 量化交易回測系統主程式
整合所有模組，執行完整的回測流程
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, List
import argparse

import backtrader as bt
import pandas as pd

# 加入本地模組路徑
sys.path.append(str(Path(__file__).parent))

from utils.config_loader import ConfigLoader
from utils.logger import setup_logger_from_config, create_backtest_logger
from data.utils.data_manager import DataManager
from data.stock_lists.generator import StockListGenerator
from strategies.breakout20 import get_strategy_class
from analyzers.custom_metrics import CustomMetricsAnalyzer


class BacktestRunner:
    """回測執行器"""
    
    def __init__(self, config_path: str = 'configs/default.yml'):
        """
        初始化回測執行器
        
        Args:
            config_path (str): 設定檔路徑
        """
        # 載入設定
        self.config = ConfigLoader(config_path)
        
        # 設定日誌
        self._setup_logging()
        
        # 初始化日誌記錄器
        self.logger = create_backtest_logger("main")
        
        # 初始化資料管理器
        data_config = self.config.get_data_config()
        self.data_manager = DataManager(
            cache_dir=data_config['cache_dir'],
            cache_enabled=data_config['cache_enabled']
        )
        
        # 初始化 Cerebro 引擎
        self.cerebro = None
        
        self.logger.info("回測執行器初始化完成")
    
    def _setup_logging(self) -> None:
        """設定日誌系統"""
        logging_config = self.config.get_logging_config()
        setup_logger_from_config(logging_config)
    
    def _ensure_stock_lists_exist(self) -> None:
        """確保股票清單檔案存在"""
        symbol_files = self.config.get_symbol_files()
        missing_files = [f for f in symbol_files if not os.path.exists(f)]
        
        if missing_files:
            self.logger.warning(f"股票清單檔案不存在，將自動生成: {missing_files}")
            
            # 生成股票清單
            generator = StockListGenerator()
            generator.generate_all_lists()
            
            self.logger.info("股票清單檔案生成完成")
    
    def _load_stock_symbols(self) -> List[str]:
        """
        載入股票代碼清單
        
        Returns:
            List[str]: 股票代碼清單
        """
        self._ensure_stock_lists_exist()
        
        symbol_files = self.config.get_symbol_files()
        symbols = self.data_manager.load_symbols_from_files(symbol_files)
        
        self.logger.info(f"載入 {len(symbols)} 個股票代碼")
        return symbols
    
    def _download_data(self, symbols: List[str]) -> Dict[str, pd.DataFrame]:
        """
        下載股票資料
        
        Args:
            symbols (List[str]): 股票代碼清單
            
        Returns:
            Dict[str, pd.DataFrame]: 股票資料字典
        """
        self.logger.info("開始下載股票資料...")
        
        data_config = self.config.get_data_config()
        
        stock_data = self.data_manager.download_multiple_stocks(
            symbols=symbols,
            start_date=self.config.get_start_date(),
            end_date=self.config.get_end_date(),
            show_progress=True,
            timeout=data_config.get('download_timeout', 30),
            retry_attempts=data_config.get('retry_attempts', 3)
        )
        
        self.logger.info(f"成功下載 {len(stock_data)} 檔股票資料")
        return stock_data
    
    def _setup_cerebro(self) -> None:
        """設定 Cerebro 引擎"""
        self.cerebro = bt.Cerebro()
        
        # 設定初始資金
        initial_cash = self.config.get_initial_cash()
        self.cerebro.broker.setcash(initial_cash)
        
        # 設定手續費
        commission = self.config.get_commission()
        self.cerebro.broker.setcommission(commission=commission)
        
        # 設定部位大小
        sizer_config = self.config.get_sizer_config()
        if sizer_config['type'] == 'PercentSizer':
            self.cerebro.addsizer(
                bt.sizers.PercentSizer,
                percents=sizer_config['percents']
            )
        
        # 添加策略
        strategy_name = self.config.get_strategy_name()
        strategy_params = self.config.get_strategy_params()
        
        if strategy_name == 'Breakout20':
            strategy_class = get_strategy_class(optimized=False)
            self.cerebro.addstrategy(
                strategy_class,
                **strategy_params
            )
        else:
            raise ValueError(f"不支援的策略: {strategy_name}")
        
        # 添加分析器
        self.cerebro.addanalyzer(CustomMetricsAnalyzer, _name='metrics')
        
        self.logger.info(f"Cerebro 引擎設定完成 - 初始資金: {initial_cash:,.0f}")
    
    def _add_data_feeds(self, stock_data: Dict[str, pd.DataFrame]) -> None:
        """
        添加資料來源到 Cerebro
        
        Args:
            stock_data (Dict[str, pd.DataFrame]): 股票資料字典
        """
        self.logger.info("添加資料來源...")
        
        data_count = 0
        for symbol, data in stock_data.items():
            try:
                # 準備資料格式
                data_feed = bt.feeds.PandasData(
                    dataname=data,
                    name=symbol,
                    fromdate=pd.to_datetime(self.config.get_start_date()),
                    todate=pd.to_datetime(self.config.get_end_date())
                )
                
                self.cerebro.adddata(data_feed)
                data_count += 1
                
            except Exception as e:
                self.logger.warning(f"添加 {symbol} 資料失敗: {str(e)}")
        
        self.logger.info(f"成功添加 {data_count} 檔股票資料到 Cerebro")
    
    def _run_backtest(self) -> List[bt.Strategy]:
        """
        執行回測
        
        Returns:
            List[bt.Strategy]: 策略結果清單
        """
        self.logger.info("開始執行回測...")
        
        # 記錄開始資訊
        start_value = self.cerebro.broker.getvalue()
        self.logger.info(f"回測開始 - 初始資產: {start_value:,.2f}")
        
        # 執行回測
        results = self.cerebro.run()
        
        # 記錄結束資訊
        end_value = self.cerebro.broker.getvalue()
        self.logger.info(f"回測完成 - 最終資產: {end_value:,.2f}")
        
        return results
    
    def _analyze_results(self, results: List[bt.Strategy]) -> Dict[str, Any]:
        """
        分析回測結果
        
        Args:
            results (List[bt.Strategy]): 策略結果清單
            
        Returns:
            Dict[str, Any]: 分析結果
        """
        self.logger.info("開始分析回測結果...")
        
        # 取得第一個策略的分析器結果
        strategy = results[0]
        analyzer = strategy.analyzers.metrics
        
        # 取得分析結果
        analysis_results = analyzer.get_analysis()
        
        # 列印績效摘要
        output_config = self.config.get_output_config()
        if output_config.get('show_summary', True):
            analyzer.print_summary()
        
        return analysis_results
    
    def _save_results(self, results: List[bt.Strategy], analysis: Dict[str, Any]) -> None:
        """
        儲存回測結果
        
        Args:
            results (List[bt.Strategy]): 策略結果清單
            analysis (Dict[str, Any]): 分析結果
        """
        output_config = self.config.get_output_config()
        csv_path = output_config.get('csv_path', 'results/csv/backtest_results.csv')
        
        try:
            # 確保輸出目錄存在
            Path(csv_path).parent.mkdir(parents=True, exist_ok=True)
            
            # 取得交易明細
            strategy = results[0]
            analyzer = strategy.analyzers.metrics
            trades_df = analyzer.get_trades_dataframe()
            
            if not trades_df.empty:
                # 儲存交易明細
                trades_df.to_csv(csv_path, index=False, encoding='utf-8-sig')
                self.logger.info(f"交易明細已儲存至: {csv_path}")
                
                # 顯示交易明細預覽
                if output_config.get('show_trades', False):
                    print(f"\n交易明細預覽 (前10筆):")
                    print(trades_df.head(10).to_string(index=False))
            else:
                self.logger.warning("無交易記錄可儲存")
            
            # 儲存績效摘要
            summary_path = csv_path.replace('.csv', '_summary.csv')
            summary_df = pd.DataFrame([analysis])
            summary_df.to_csv(summary_path, index=False, encoding='utf-8-sig')
            self.logger.info(f"績效摘要已儲存至: {summary_path}")
            
        except Exception as e:
            self.logger.error(f"儲存結果失敗: {str(e)}")
    
    def run(self) -> Dict[str, Any]:
        """
        執行完整的回測流程
        
        Returns:
            Dict[str, Any]: 回測結果
        """
        try:
            # 1. 載入股票代碼
            symbols = self._load_stock_symbols()
            
            # 2. 下載資料
            stock_data = self._download_data(symbols)
            
            if not stock_data:
                raise ValueError("無有效的股票資料可用於回測")
            
            # 3. 設定 Cerebro 引擎
            self._setup_cerebro()
            
            # 4. 添加資料來源
            self._add_data_feeds(stock_data)
            
            # 5. 執行回測
            results = self._run_backtest()
            
            # 6. 分析結果
            analysis = self._analyze_results(results)
            
            # 7. 儲存結果
            self._save_results(results, analysis)
            
            self.logger.info("回測流程完成")
            return analysis
            
        except Exception as e:
            self.logger.error(f"回測執行失敗: {str(e)}")
            raise


def run_download_test():
    """
    執行獨立的資料下載測試
    """
    import logging
    print("--- 開始測試資料下載功能 ---")
    
    try:
        runner = BacktestRunner(config_path='configs/default.yml')
        logging.basicConfig(level=logging.INFO)
        runner.logger = logging.getLogger("test_download")
        print("BacktestRunner 初始化成功。")
    except Exception as e:
        print(f"BacktestRunner 初始化失敗: {e}")
        return

    test_symbols = ['2330', '2317', '2888']
    print(f"將測試下載以下股票: {test_symbols}")

    try:
        print("正在呼叫 _download_data...")
        stock_data = runner._download_data(symbols=test_symbols)
        print("方法執行完畢。")
    except Exception as e:
        print(f"執行 _download_data 時發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return

    print("\n--- 測試結果驗證 ---")
    if isinstance(stock_data, dict):
        print(f"成功下載 {len(stock_data)}/{len(test_symbols)} 檔股票資料。")
        for symbol, data in stock_data.items():
            if data is not None and not data.empty:
                print(f"  - {symbol}: 下載成功，共 {len(data)} 筆記錄。")
            else:
                print(f"  - {symbol}: 下載失敗或無資料。")
    else:
        print("測試失敗：回傳的不是一個字典。")

    print("\n--- 測試結束 ---")


def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='Backtrader 量化交易回測系統')
    parser.add_argument(
        '--config',
        type=str,
        default='configs/default.yml',
        help='設定檔路徑'
    )
    parser.add_argument(
        '--generate-lists',
        action='store_true',
        help='只生成股票清單檔案'
    )
    parser.add_argument(
        '--test-download',
        action='store_true',
        help='只執行資料下載功能的獨立測試'
    )
    
    args = parser.parse_args()
    
    try:
        if args.generate_lists:
            # 只生成股票清單
            print("正在生成股票清單檔案...")
            generator = StockListGenerator()
            generator.generate_all_lists()
            print("股票清單檔案生成完成")
            return
        
        if args.test_download:
            run_download_test()
            return
        
        # 執行完整回測
        print("="*60)
        print("     Backtrader 量化交易回測系統")
        print("="*60)
        
        runner = BacktestRunner(args.config)
        results = runner.run()
        
        print("\n回測執行成功完成！")
        
    except KeyboardInterrupt:
        print("\n回測被用戶中斷")
    except Exception as e:
        print(f"\n回測執行失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
