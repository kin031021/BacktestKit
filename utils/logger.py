### === Module: utils/logger.py ===
"""
日誌設定工具
使用 loguru 提供結構化的日誌記錄功能
"""

import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional
from loguru import logger


class LoggerConfig:
    """日誌設定管理器"""
    
    def __init__(self):
        """初始化日誌設定管理器"""
        self.is_configured = False
        self.handlers = []
    
    def setup_logger(
        self,
        level: str = "INFO",
        file_path: Optional[str] = None,
        rotation: str = "10 MB",
        retention: str = "30 days",
        format_string: Optional[str] = None,
        enable_console: bool = True,
        enable_file: bool = True
    ) -> None:
        """
        設定日誌系統
        
        Args:
            level (str): 日誌等級 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            file_path (Optional[str]): 日誌檔案路徑
            rotation (str): 日誌輪轉大小或時間
            retention (str): 日誌保留期間
            format_string (Optional[str]): 自訂格式字串
            enable_console (bool): 是否啟用控制台輸出
            enable_file (bool): 是否啟用檔案輸出
        """
        # 如果已經設定過，先移除所有現有的處理器
        if self.is_configured:
            self.remove_all_handlers()
        
        # 預設格式
        if format_string is None:
            format_string = (
                "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                "<level>{message}</level>"
            )
        
        # 設定控制台輸出
        if enable_console:
            console_handler = logger.add(
                sys.stdout,
                level=level,
                format=format_string,
                colorize=True,
                backtrace=True,
                diagnose=True
            )
            self.handlers.append(console_handler)
        
        # 設定檔案輸出
        if enable_file and file_path:
            # 確保日誌目錄存在
            log_path = Path(file_path)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logger.add(
                file_path,
                level=level,
                format=format_string,
                rotation=rotation,
                retention=retention,
                compression="zip",
                backtrace=True,
                diagnose=True,
                encoding="utf-8"
            )
            self.handlers.append(file_handler)
        
        self.is_configured = True
        logger.info(f"日誌系統設定完成 - 等級: {level}")
    
    def setup_from_config(self, config: Dict[str, Any]) -> None:
        """
        從設定字典設定日誌
        
        Args:
            config (Dict[str, Any]): 日誌設定字典
        """
        self.setup_logger(
            level=config.get('level', 'INFO'),
            file_path=config.get('file_path'),
            rotation=config.get('rotation', '10 MB'),
            retention=config.get('retention', '30 days'),
            format_string=config.get('format'),
            enable_console=config.get('enable_console', True),
            enable_file=config.get('enable_file', True)
        )
    
    def remove_all_handlers(self) -> None:
        """移除所有日誌處理器"""
        for handler_id in self.handlers:
            try:
                logger.remove(handler_id)
            except ValueError:
                # 處理器可能已經被移除
                pass
        
        self.handlers.clear()
        self.is_configured = False
    
    def add_file_handler(
        self,
        file_path: str,
        level: str = "INFO",
        rotation: str = "10 MB",
        retention: str = "30 days",
        format_string: Optional[str] = None
    ) -> int:
        """
        添加額外的檔案處理器
        
        Args:
            file_path (str): 日誌檔案路徑
            level (str): 日誌等級
            rotation (str): 日誌輪轉設定
            retention (str): 日誌保留期間
            format_string (Optional[str]): 格式字串
            
        Returns:
            int: 處理器ID
        """
        # 確保目錄存在
        log_path = Path(file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format_string is None:
            format_string = (
                "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | "
                "{name}:{function}:{line} | {message}"
            )
        
        handler_id = logger.add(
            file_path,
            level=level,
            format=format_string,
            rotation=rotation,
            retention=retention,
            compression="zip",
            encoding="utf-8"
        )
        
        self.handlers.append(handler_id)
        return handler_id
    
    def set_level(self, level: str) -> None:
        """
        設定日誌等級
        
        Args:
            level (str): 日誌等級
        """
        # 移除現有處理器
        self.remove_all_handlers()
        
        # 重新設定為新等級
        self.setup_logger(level=level)
    
    def get_logger(self):
        """取得日誌記錄器"""
        return logger


# 全域日誌設定管理器實例
_logger_config = LoggerConfig()


def setup_logger(
    level: str = "INFO",
    file_path: Optional[str] = "results/logs/backtest.log",
    rotation: str = "10 MB",
    retention: str = "30 days",
    **kwargs
) -> None:
    """
    快速設定日誌系統
    
    Args:
        level (str): 日誌等級
        file_path (Optional[str]): 日誌檔案路徑
        rotation (str): 日誌輪轉大小
        retention (str): 日誌保留期間
        **kwargs: 其他設定參數
    """
    _logger_config.setup_logger(
        level=level,
        file_path=file_path,
        rotation=rotation,
        retention=retention,
        **kwargs
    )


def setup_logger_from_config(config: Dict[str, Any]) -> None:
    """
    從設定字典設定日誌
    
    Args:
        config (Dict[str, Any]): 日誌設定字典
    """
    _logger_config.setup_from_config(config)


def get_logger():
    """取得日誌記錄器"""
    return _logger_config.get_logger()


def add_file_handler(file_path: str, **kwargs) -> int:
    """
    添加檔案處理器
    
    Args:
        file_path (str): 檔案路徑
        **kwargs: 其他參數
        
    Returns:
        int: 處理器ID
    """
    return _logger_config.add_file_handler(file_path, **kwargs)


def set_log_level(level: str) -> None:
    """
    設定日誌等級
    
    Args:
        level (str): 日誌等級
    """
    _logger_config.set_level(level)


def remove_all_handlers() -> None:
    """移除所有日誌處理器"""
    _logger_config.remove_all_handlers()


class BacktestLogger:
    """回測專用日誌記錄器"""
    
    def __init__(self, name: str = "backtest"):
        """
        初始化回測日誌記錄器
        
        Args:
            name (str): 日誌記錄器名稱
        """
        self.name = name
        self.logger = logger.bind(module=name)
    
    def info(self, message: str, **kwargs) -> None:
        """記錄資訊等級日誌"""
        self.logger.info(message, **kwargs)
    
    def debug(self, message: str, **kwargs) -> None:
        """記錄除錯等級日誌"""
        self.logger.debug(message, **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """記錄警告等級日誌"""
        self.logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        """記錄錯誤等級日誌"""
        self.logger.error(message, **kwargs)
    
    def critical(self, message: str, **kwargs) -> None:
        """記錄嚴重錯誤等級日誌"""
        self.logger.critical(message, **kwargs)
    
    def trade(self, symbol: str, action: str, price: float, size: int, **kwargs) -> None:
        """
        記錄交易日誌
        
        Args:
            symbol (str): 股票代碼
            action (str): 交易動作 (BUY/SELL)
            price (float): 價格
            size (int): 數量
            **kwargs: 其他參數
        """
        self.logger.info(
            f"交易執行 - {symbol} {action} {size}股 @ {price:.2f}",
            symbol=symbol,
            action=action,
            price=price,
            size=size,
            **kwargs
        )
    
    def performance(self, metrics: Dict[str, Any]) -> None:
        """
        記錄績效日誌
        
        Args:
            metrics (Dict[str, Any]): 績效指標
        """
        self.logger.info(
            f"績效指標 - 總報酬: {metrics.get('total_return_pct', 0):.2f}%, "
            f"夏普比率: {metrics.get('sharpe_ratio', 0):.3f}, "
            f"最大回撤: {metrics.get('max_drawdown_pct', 0):.2f}%",
            **metrics
        )
    
    def strategy_signal(self, symbol: str, signal_type: str, details: str, **kwargs) -> None:
        """
        記錄策略信號日誌
        
        Args:
            symbol (str): 股票代碼
            signal_type (str): 信號類型
            details (str): 詳細資訊
            **kwargs: 其他參數
        """
        self.logger.info(
            f"策略信號 - {symbol} {signal_type}: {details}",
            symbol=symbol,
            signal_type=signal_type,
            details=details,
            **kwargs
        )


def create_backtest_logger(name: str = "backtest") -> BacktestLogger:
    """
    創建回測日誌記錄器
    
    Args:
        name (str): 日誌記錄器名稱
        
    Returns:
        BacktestLogger: 回測日誌記錄器實例
    """
    return BacktestLogger(name)


def main():
    """測試函數"""
    # 測試基本日誌設定
    setup_logger(
        level="DEBUG",
        file_path="test_logs/test.log"
    )
    
    # 測試日誌記錄
    test_logger = get_logger()
    test_logger.info("這是一個測試資訊")
    test_logger.debug("這是一個測試除錯訊息")
    test_logger.warning("這是一個測試警告")
    test_logger.error("這是一個測試錯誤")
    
    # 測試回測專用日誌記錄器
    backtest_logger = create_backtest_logger()
    backtest_logger.info("回測開始")
    backtest_logger.trade("2330", "BUY", 500.0, 1000)
    backtest_logger.performance({
        'total_return_pct': 15.5,
        'sharpe_ratio': 1.25,
        'max_drawdown_pct': 8.2
    })
    backtest_logger.strategy_signal("2330", "ENTRY", "突破20日高點")
    
    print("日誌系統測試完成")
    
    # 清理
    remove_all_handlers()


if __name__ == '__main__':
    main()