### === Module: data/utils/data_manager.py ===
"""
資料下載與快取管理器
負責從 yfinance 下載台股資料，並提供快取機制以提升效能
"""

import os
import csv
import warnings
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf
from joblib import Memory
from loguru import logger


# 抑制 yfinance 警告
warnings.filterwarnings('ignore', category=FutureWarning)

# --- Joblib 快取設定 ---
# 將 Memory 初始化移至模組層級，避免在類別實例中造成 PicklingError
CACHE_DIR = Path('data/cache')
CACHE_DIR.mkdir(parents=True, exist_ok=True)
memory = Memory(str(CACHE_DIR), verbose=0)


@memory.cache
def _download_stock_data_impl(
    symbol: str,
    start_date: str,
    end_date: str,
    timeout: int = 30,
    retry_attempts: int = 3
) -> Optional[pd.DataFrame]:
    """
    實際下載股票資料的實作函數（已移至模組層級以支援快取）

    Args:
        symbol (str): 股票代碼
        start_date (str): 開始日期
        end_date (str): 結束日期
        timeout (int): 下載超時時間(秒)
        retry_attempts (int): 重試次數

    Returns:
        Optional[pd.DataFrame]: 股票資料DataFrame，失敗則返回None
    """
    # 為台股代碼加上 .TW 後綴
    tw_symbol = f"{symbol}.TW" if not symbol.endswith('.TW') else symbol
    
    for attempt in range(retry_attempts):
        try:
            logger.debug(f"下載 {tw_symbol} 資料 (嘗試 {attempt + 1}/{retry_attempts})")
            
            # 使用 yfinance 下載資料
            ticker = yf.Ticker(tw_symbol)
            data = ticker.history(
                start=start_date,
                end=end_date,
                timeout=timeout
            )
            
            if data.empty:
                logger.warning(f"股票 {tw_symbol} 無資料")
                return None
            
            # 重新命名欄位為英文
            data.columns = [col.lower() for col in data.columns]
            
            # 確保必要欄位存在
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            missing_columns = [col for col in required_columns if col not in data.columns]
            
            if missing_columns:
                logger.error(f"股票 {tw_symbol} 缺少必要欄位: {missing_columns}")
                return None
            
            # 移除缺失值過多的資料
            if data.isnull().sum().sum() > len(data) * 0.1:  # 缺失值超過10%
                logger.warning(f"股票 {tw_symbol} 缺失值過多，跳過")
                return None
            
            # 前向填補缺失值
            data = data.fillna(method='ffill')
            
            logger.debug(f"成功下載 {tw_symbol} 資料，共 {len(data)} 筆記錄")
            return data
            
        except Exception as e:
            logger.warning(f"下載 {tw_symbol} 失敗 (嘗試 {attempt + 1}/{retry_attempts}): {str(e)}")
            
            if attempt < retry_attempts - 1:
                # 等待後重試
                import time
                time.sleep(1)
            else:
                logger.error(f"下載 {tw_symbol} 最終失敗")
                return None
    
    return None


class DataManager:
    """資料下載與快取管理器"""
    
    def __init__(self, cache_dir: str = 'data/cache', cache_enabled: bool = True):
        """
        初始化資料管理器
        
        Args:
            cache_dir (str): 快取目錄路徑
            cache_enabled (bool): 是否啟用快取
        """
        self.cache_dir = Path(cache_dir)
        self.cache_enabled = cache_enabled
        self.memory = memory  # 使用模組層級的 memory 物件
        
        logger.info(f"資料管理器初始化完成，快取啟用: {self.cache_enabled}")

    def download_stock_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        **kwargs
    ) -> Optional[pd.DataFrame]:
        """
        下載股票資料（帶快取）
        
        Args:
            symbol (str): 股票代碼
            start_date (str): 開始日期
            end_date (str): 結束日期
            **kwargs: 其他參數
            
        Returns:
            Optional[pd.DataFrame]: 股票資料DataFrame
        """
        if self.cache_enabled:
            return _download_stock_data_impl(symbol, start_date, end_date, **kwargs)
        else:
            # 如果禁用快取，直接呼叫函式，但不通過 memory.cache
            return _download_stock_data_impl.__wrapped__(symbol, start_date, end_date, **kwargs)

    def load_symbol_list(self, filepath: str) -> List[str]:
        """
        從CSV檔案載入股票代碼清單
        
        Args:
            filepath (str): CSV檔案路徑
            
        Returns:
            List[str]: 股票代碼清單
        """
        symbol_list = []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                symbol_list = [row['symbol'] for row in reader if row['symbol']]
            
            logger.info(f"從 {filepath} 載入 {len(symbol_list)} 個股票代碼")
            
        except FileNotFoundError:
            logger.error(f"找不到檔案: {filepath}")
        except Exception as e:
            logger.error(f"載入股票清單失敗: {str(e)}")
        
        return symbol_list
    
    def download_multiple_stocks(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str,
        show_progress: bool = True,
        **kwargs
    ) -> Dict[str, pd.DataFrame]:
        """
        批量下載多檔股票資料
        
        Args:
            symbols (List[str]): 股票代碼清單
            start_date (str): 開始日期
            end_date (str): 結束日期
            show_progress (bool): 是否顯示進度
            **kwargs: 其他參數
            
        Returns:
            Dict[str, pd.DataFrame]: 股票代碼對應資料的字典
        """
        stock_data = {}
        
        if show_progress:
            from tqdm import tqdm
            symbols_iter = tqdm(symbols, desc="下載股票資料")
        else:
            symbols_iter = symbols
        
        for symbol in symbols_iter:
            data = self.download_stock_data(symbol, start_date, end_date, **kwargs)
            if data is not None and not data.empty:
                stock_data[symbol] = data
            else:
                logger.warning(f"跳過股票 {symbol}：無有效資料")
        
        logger.info(f"成功下載 {len(stock_data)}/{len(symbols)} 檔股票資料")
        return stock_data
    
    def load_symbols_from_files(self, symbol_files: List[str]) -> List[str]:
        """
        從多個CSV檔案載入股票代碼
        
        Args:
            symbol_files (List[str]): CSV檔案路徑清單
            
        Returns:
            List[str]: 合併的股票代碼清單
        """
        all_symbols = []
        
        for filepath in symbol_files:
            if os.path.exists(filepath):
                symbols = self.load_symbol_list(filepath)
                all_symbols.extend(symbols)
            else:
                logger.warning(f"股票清單檔案不存在: {filepath}")
        
        # 去除重複的股票代碼
        unique_symbols = list(set(all_symbols))
        
        logger.info(f"從 {len(symbol_files)} 個檔案載入 {len(unique_symbols)} 個唯一股票代碼")
        return unique_symbols
    
    def clear_cache(self) -> None:
        """清除所有快取資料"""
        if self.cache_enabled and hasattr(self.memory, 'clear'):
            self.memory.clear()
            logger.info("快取已清除")
        else:
            logger.info("快取未啟用或無法清除")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """
        取得快取資訊
        
        Returns:
            Dict[str, Any]: 快取資訊
        """
        cache_info = {
            'enabled': self.cache_enabled,
            'cache_dir': str(self.cache_dir),
            'cache_size': 0,
            'file_count': 0
        }
        
        if self.cache_dir.exists():
            cache_files = list(self.cache_dir.rglob('*'))
            cache_info['file_count'] = len([f for f in cache_files if f.is_file()])
            
            # 計算快取大小
            total_size = sum(f.stat().st_size for f in cache_files if f.is_file())
            cache_info['cache_size'] = total_size
        
        return cache_info
    
    def validate_date_range(self, start_date: str, end_date: str) -> bool:
        """
        驗證日期範圍是否有效
        
        Args:
            start_date (str): 開始日期
            end_date (str): 結束日期
            
        Returns:
            bool: 日期範圍是否有效
        """
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            
            if start >= end:
                logger.error("開始日期必須早於結束日期")
                return False
            
            # 檢查是否超過合理範圍
            if start < datetime(2000, 1, 1):
                logger.warning("開始日期過早，可能沒有資料")
            
            if end > datetime.now() + timedelta(days=1):
                logger.warning("結束日期超過當前日期")
            
            return True
            
        except ValueError as e:
            logger.error(f"日期格式錯誤: {str(e)}")
            return False


def main():
    """測試函數"""
    # 初始化資料管理器
    data_manager = DataManager()
    
    # 測試下載單一股票
    print("測試下載台積電資料...")
    data = data_manager.download_stock_data('2330', '2023-01-01', '2023-12-31')
    if data is not None:
        print(f"成功下載資料，共 {len(data)} 筆記錄")
        print(data.head())
    else:
        print("下載失敗")
    
    # 顯示快取資訊
    cache_info = data_manager.get_cache_info()
    print(f"\n快取資訊: {cache_info}")


if __name__ == '__main__':
    main()
