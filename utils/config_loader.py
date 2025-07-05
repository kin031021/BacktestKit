### === Module: utils/config_loader.py ===
"""
設定檔讀取工具
負責載入和驗證 YAML 設定檔，提供設定參數的存取介面
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from loguru import logger


class ConfigLoader:
    """設定檔載入器類別"""
    
    def __init__(self, config_path: str = 'configs/default.yml'):
        """
        初始化設定檔載入器
        
        Args:
            config_path (str): 設定檔路徑
        """
        self.config_path = Path(config_path)
        self.config = {}
        self._load_config()
        self._validate_config()
        
        logger.info(f"設定檔載入完成: {self.config_path}")
    
    def _load_config(self) -> None:
        """載入YAML設定檔"""
        try:
            if not self.config_path.exists():
                raise FileNotFoundError(f"設定檔不存在: {self.config_path}")
            
            with open(self.config_path, 'r', encoding='utf-8') as file:
                self.config = yaml.safe_load(file)
            
            logger.debug(f"成功載入設定檔: {self.config_path}")
            
        except yaml.YAMLError as e:
            logger.error(f"YAML格式錯誤: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"載入設定檔失敗: {str(e)}")
            raise
    
    def _validate_config(self) -> None:
        """驗證設定檔內容"""
        required_keys = [
            'start_date', 'end_date', 'symbol_files', 'strategy', 
            'cash', 'commission', 'slippage', 'sizer'
        ]
        
        # 檢查必要的頂層鍵值
        for key in required_keys:
            if key not in self.config:
                raise ValueError(f"設定檔缺少必要參數: {key}")
        
        # 驗證日期格式
        self._validate_dates()
        
        # 驗證數值範圍
        self._validate_numeric_values()
        
        # 驗證檔案路徑
        self._validate_file_paths()
        
        # 驗證策略設定
        self._validate_strategy_config()
        
        logger.debug("設定檔驗證通過")
    
    def _validate_dates(self) -> None:
        """驗證日期格式和範圍"""
        date_format = '%Y-%m-%d'
        
        try:
            start_date = datetime.strptime(self.config['start_date'], date_format)
            end_date = datetime.strptime(self.config['end_date'], date_format)
            
            if start_date >= end_date:
                raise ValueError("開始日期必須早於結束日期")
            
            # 檢查日期範圍合理性
            if start_date.year < 2000:
                logger.warning("開始日期過早，可能沒有資料")
            
            if end_date > datetime.now():
                logger.warning("結束日期超過當前日期")
                
        except ValueError as e:
            raise ValueError(f"日期格式錯誤: {str(e)}")
    
    def _validate_numeric_values(self) -> None:
        """驗證數值參數"""
        # 驗證現金
        cash = self.config.get('cash', 0)
        if cash <= 0:
            raise ValueError("初始資金必須大於0")
        
        # 驗證手續費率
        commission = self.config.get('commission', 0)
        if commission < 0 or commission > 0.1:
            raise ValueError("手續費率必須在0-10%之間")
        
        # 驗證滑價
        slippage = self.config.get('slippage', 0)
        if slippage < 0 or slippage > 0.1:
            raise ValueError("滑價必須在0-10%之間")
        
        # 驗證部位大小設定
        sizer = self.config.get('sizer', {})
        if 'percents' in sizer:
            percents = sizer['percents']
            if percents <= 0 or percents > 100:
                raise ValueError("部位百分比必須在0-100%之間")
    
    def _validate_file_paths(self) -> None:
        """驗證檔案路徑"""
        symbol_files = self.config.get('symbol_files', [])
        
        if not symbol_files:
            raise ValueError("必須指定至少一個股票清單檔案")
        
        missing_files = []
        for filepath in symbol_files:
            if not os.path.exists(filepath):
                missing_files.append(filepath)
        
        if missing_files:
            logger.warning(f"以下股票清單檔案不存在: {missing_files}")
    
    def _validate_strategy_config(self) -> None:
        """驗證策略設定"""
        strategy = self.config.get('strategy', {})
        
        if 'name' not in strategy:
            raise ValueError("必須指定策略名稱")
        
        if 'params' not in strategy:
            raise ValueError("必須指定策略參數")
        
        params = strategy['params']
        
        # 驗證 Breakout20 策略參數
        if strategy['name'] == 'Breakout20':
            required_params = ['sma_window', 'high_window']
            for param in required_params:
                if param not in params:
                    raise ValueError(f"Breakout20策略缺少參數: {param}")
                
                if params[param] <= 0:
                    raise ValueError(f"策略參數 {param} 必須大於0")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        取得設定值
        
        Args:
            key (str): 設定鍵值，支援點號分隔的巢狀鍵值
            default (Any): 預設值
            
        Returns:
            Any: 設定值
        """
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_start_date(self) -> str:
        """取得開始日期"""
        return self.config['start_date']
    
    def get_end_date(self) -> str:
        """取得結束日期"""
        return self.config['end_date']
    
    def get_symbol_files(self) -> List[str]:
        """取得股票清單檔案路徑"""
        return self.config['symbol_files']
    
    def get_strategy_name(self) -> str:
        """取得策略名稱"""
        return self.config['strategy']['name']
    
    def get_strategy_params(self) -> Dict[str, Any]:
        """取得策略參數"""
        return self.config['strategy']['params']
    
    def get_initial_cash(self) -> float:
        """取得初始資金"""
        return float(self.config['cash'])
    
    def get_commission(self) -> float:
        """取得手續費率"""
        return float(self.config['commission'])
    
    def get_slippage(self) -> float:
        """取得滑價"""
        return float(self.config['slippage'])
    
    def get_sizer_config(self) -> Dict[str, Any]:
        """取得部位大小設定"""
        return self.config['sizer']
    
    def get_data_config(self) -> Dict[str, Any]:
        """取得資料設定"""
        return self.config.get('data', {
            'cache_enabled': True,
            'cache_dir': 'data/cache',
            'download_timeout': 30,
            'retry_attempts': 3
        })
    
    def get_logging_config(self) -> Dict[str, Any]:
        """取得日誌設定"""
        return self.config.get('logging', {
            'level': 'INFO',
            'file_path': 'results/logs/backtest.log',
            'rotation': '10 MB',
            'retention': '30 days'
        })
    
    def get_output_config(self) -> Dict[str, Any]:
        """取得輸出設定"""
        return self.config.get('output', {
            'csv_path': 'results/csv/backtest_results.csv',
            'show_summary': True,
            'show_trades': False
        })
    
    def update(self, key: str, value: Any) -> None:
        """
        更新設定值
        
        Args:
            key (str): 設定鍵值，支援點號分隔的巢狀鍵值
            value (Any): 新的設定值
        """
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        logger.debug(f"更新設定: {key} = {value}")
    
    def save(self, output_path: Optional[str] = None) -> None:
        """
        儲存設定檔
        
        Args:
            output_path (Optional[str]): 輸出路徑，預設為原路徑
        """
        save_path = Path(output_path) if output_path else self.config_path
        
        try:
            with open(save_path, 'w', encoding='utf-8') as file:
                yaml.dump(
                    self.config, 
                    file, 
                    default_flow_style=False, 
                    allow_unicode=True,
                    indent=2
                )
            
            logger.info(f"設定檔已儲存: {save_path}")
            
        except Exception as e:
            logger.error(f"儲存設定檔失敗: {str(e)}")
            raise
    
    def print_config(self) -> None:
        """列印設定檔內容"""
        print("\n" + "="*50)
        print("           設定檔內容")
        print("="*50)
        
        def print_dict(d: Dict[str, Any], indent: int = 0):
            """遞迴列印字典內容"""
            for key, value in d.items():
                if isinstance(value, dict):
                    print("  " * indent + f"{key}:")
                    print_dict(value, indent + 1)
                else:
                    print("  " * indent + f"{key}: {value}")
        
        print_dict(self.config)
        print("="*50)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        取得設定檔字典
        
        Returns:
            Dict[str, Any]: 設定檔內容
        """
        return self.config.copy()


def load_config(config_path: str = 'configs/default.yml') -> ConfigLoader:
    """
    載入設定檔的便利函數
    
    Args:
        config_path (str): 設定檔路徑
        
    Returns:
        ConfigLoader: 設定檔載入器實例
    """
    return ConfigLoader(config_path)


def main():
    """測試函數"""
    try:
        # 載入預設設定檔
        config = ConfigLoader()
        
        # 列印設定檔內容
        config.print_config()
        
        # 測試取得各種設定值
        print(f"\n開始日期: {config.get_start_date()}")
        print(f"結束日期: {config.get_end_date()}")
        print(f"策略名稱: {config.get_strategy_name()}")
        print(f"初始資金: {config.get_initial_cash():,.0f}")
        print(f"手續費率: {config.get_commission():.4f}")
        
        print("\n設定檔載入測試完成")
        
    except Exception as e:
        print(f"設定檔載入測試失敗: {str(e)}")


if __name__ == '__main__':
    main()