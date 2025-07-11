### === Module: data/stock_lists/generator.py ===
"""
股票列表生成器
用於生成台股0050成分股和中型100成分股的CSV檔案
"""

import csv
import os
from pathlib import Path
from typing import List, Tuple


class StockListGenerator:
    """股票列表生成器類別"""
    
    def __init__(self):
        """初始化生成器"""
        self.current_dir = Path(__file__).parent
    
    def get_0050_components(self) -> List[Tuple[str, str]]:
        """
        取得台灣50(0050)成分股清單
        
        Returns:
            List[Tuple[str, str]]: 股票代碼和名稱的元組列表
        """
        # 台灣50主要成分股 (簡化版本，實際應從證交所API取得)
        stocks = [
            ('2330', '台積電'),
            ('2454', '聯發科'),
            ('2317', '鴻海'),
            ('1301', '台塑'),
            ('1303', '南亞'),
            ('2308', '台達電'),
            ('2382', '廣達'),
            ('6505', '台塑化'),
            ('2886', '兆豐金'),
            ('2891', '中信金'),
            ('2884', '玉山金'),
            ('2892', '第一金'),
            ('2880', '華南金'),
            ('2881', '富邦金'),
            ('2883', '開發金'),
            ('3711', '日月光投控'),
            ('2303', '聯電'),
            ('2412', '中華電'),
            ('3008', '大立光'),
            ('2207', '和泰車'),
            ('1216', '統一'),
            ('2002', '中鋼'),
            ('1101', '台泥'),
            ('2327', '國巨'),
            ('2357', '華碩'),
            ('2395', '研華'),
            ('3045', '台灣大'),
            ('4938', '和碩'),
            ('2379', '瑞昱'),
            ('2324', '仁寶'),
            ('2409', '友達'),
            ('3231', '緯創'),
            ('2408', '南亞科'),
            ('6415', '矽力-KY'),
            ('2385', '群光'),
            ('2603', '長榮'),
            ('3034', '聯詠'),
            ('2356', '英業達'),
            ('2609', '陽明'),
            ('1102', '亞泥'),
            ('3017', '奇鋐'),
            ('2801', '彰銀'),
            ('5880', 'F-合庫金'),
            ('1326', '台化'),
            ('2890', '永豐金'),
            ('2887', '台新金'),
            ('2609', '陽明'),
            ('2912', '統一超'),
            ('1605', '華新'),
            ('2888', '新光金'),
        ]
        return stocks[:50]  # 確保只取50檔
    
    def get_mid100_components(self) -> List[Tuple[str, str]]:
        """
        取得中型100成分股清單
        
        Returns:
            List[Tuple[str, str]]: 股票代碼和名稱的元組列表
        """
        # 中型100主要成分股 (簡化版本)
        stocks = [
            ('2615', '萬海'),
            ('2618', '長榮航'),
            ('3443', '創意'),
            ('3661', '世芯-KY'),
            ('6669', '緯穎'),
            ('3653', '健策'),
            ('6770', '力積電'),
            ('2344', '華邦電'),
            ('8046', '南電'),
            ('2049', '上銀'),
            ('5269', '祥碩'),
            ('3037', '欣興'),
            ('2377', '微星'),
            ('2376', '技嘉'),
            ('2313', '華通'),
            ('2347', '聯強'),
            ('2474', '可成'),
            ('6239', '力成'),
            ('3006', '晶豪科'),
            ('2368', '金像電'),
            ('2345', '智邦'),
            ('6285', '啟碁'),
            ('3702', '大聯大'),
            ('2325', '矽品'),
            ('2610', '華航'),
            ('2352', '佳世達'),
            ('8081', '致新'),
            ('3533', '嘉澤'),
            ('2059', '川湖'),
            ('6271', '同欣電'),
            ('2548', '華固'),
            ('2542', '興富發'),
            ('2915', '潤泰全'),
            ('3005', '神基'),
            ('2449', '京元電子'),
            ('2329', '華碩'),
            ('2455', '全新'),
            ('3481', '群創'),
            ('2439', '美律'),
            ('2545', '皇翔'),
            ('3189', '景碩'),
            ('2421', '建準'),
            ('2458', '義隆'),
            ('3529', '力旺'),
            ('2441', '超豐'),
            ('2637', '慧洋-KY'),
            ('2636', '台驊投控'),
            ('3665', '貿聯-KY'),
            ('2634', '漢翔'),
            ('3035', '智原'),
            ('6668', '中茂'),
            ('2617', '台航'),
            ('4919', '新唐'),
            ('2633', '台灣高鐵'),
            ('6244', '茂迪'),
            ('5234', '達興材料'),
            ('3714', '富采'),
            ('3630', '新鉅科'),
            ('5871', '中租-KY'),
            ('9904', '寶成'),
            ('2105', '正新'),
            ('2201', '裕隆'),
            ('2915', '潤泰全'),
            ('1402', '遠東新'),
            ('1717', '長興'),
            ('2204', '中華'),
            ('2227', '裕日車'),
            ('2371', '大同'),
            ('2393', '億光'),
            ('2301', '光寶科'),
            ('2537', '聯上發'),
            ('1504', '東元'),
            ('2104', '國際中橡'),
            ('1802', '台玻'),
            ('1907', '永豐餘'),
            ('2201', '裕隆'),
            ('2228', '劍麟'),
            ('2535', '達欣工'),
            ('3406', '玉晶光'),
            ('3008', '大立光'),
            ('3044', '健鼎'),
            ('3094', '聯傑'),
            ('3532', '台勝科'),
            ('4904', '遠傳'),
            ('4958', '臻鼎-KY'),
            ('5388', '中磊'),
            ('6176', '瑞儀'),
            ('6531', '愛普'),
            ('8454', '富邦媒'),
            ('9921', '巨大'),
            ('2731', '雄獅'),
            ('2038', '海光'),
            ('5274', '信驊'),
            ('3706', '神達'),
            ('3049', '和鑫'),
            ('3596', '智易'),
            ('3707', '漢磊'),
            ('4968', '立積'),
            ('6456', 'GIS-KY'),
            ('6643', 'M31'),
            ('8110', '華東'),
            ('8299', '群聯'),
        ]
        return stocks[:100]  # 確保只取100檔
    
    def generate_csv(self, filename: str, stocks: List[Tuple[str, str]]) -> None:
        """
        生成股票清單CSV檔案
        
        Args:
            filename (str): 檔案名稱
            stocks (List[Tuple[str, str]]): 股票代碼和名稱的元組列表
        """
        filepath = self.current_dir / filename
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['symbol', 'name'])  # 標題行
            
            for symbol, name in stocks:
                writer.writerow([symbol, name])
        
        print(f"已生成 {filename}，包含 {len(stocks)} 檔股票")
    
    def generate_all_lists(self) -> None:
        """生成所有股票清單檔案"""
        print("開始生成股票清單檔案...")
        
        # 生成0050成分股清單
        stocks_0050 = self.get_0050_components()
        self.generate_csv('0050_list.csv', stocks_0050)
        
        # 生成中型100成分股清單
        stocks_mid100 = self.get_mid100_components()
        self.generate_csv('mid100_list.csv', stocks_mid100)
        
        print("所有股票清單檔案生成完成！")


def main():
    """主函數"""
    generator = StockListGenerator()
    generator.generate_all_lists()


if __name__ == '__main__':
    main()