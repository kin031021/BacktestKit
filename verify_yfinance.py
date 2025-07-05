import yfinance as yf
import warnings
import requests

# 抑制 yfinance 可能產生的警告
warnings.filterwarnings('ignore', category=FutureWarning)

def verify_download(symbol='2330.TW', start='2025-01-01', end='2025-01-31'):
    """
    一個極簡的 yfinance 下載測試函式
    """
    print(f"--- 開始獨立驗證 yfinance ---")
    print(f"目標股票: {symbol}")
    print(f"時間範圍: {start} 到 {end}")

    try:
        # 核心測試程式碼
        print("\n1. 建立 requests.Session 並停用 SSL 驗證...")
        session = requests.Session()
        session.verify = False
        print("   Session 建立成功。")

        print("\n2. 建立 Ticker 物件...")
        ticker = yf.Ticker(symbol, session=session)
        print(f"   Ticker 物件建立成功: {ticker}")

        print("\n3. 呼叫 history() 方法下載資料...")
        data = ticker.history(start=start, end=end, timeout=30)
        print("   history() 方法執行完畢。")

        # 驗證結果
        print("\n--- 驗證結果 ---")
        if data.empty:
            print("結果: 下載失敗，回傳的 DataFrame 為空。")
            print("可能原因：股票代碼錯誤、該時段無資料、或網路連線問題。")
        else:
            print(f"結果: 下載成功！共 {len(data)} 筆記錄。")
            print("資料預覽：")
            print(data.head())

    except Exception as e:
        print(f"\n--- 發生未預期的錯誤 ---")
        print(f"錯誤類型: {type(e).__name__}")
        print(f"錯誤訊息: {e}")
        print("\n請檢查您的網路連線、防火牆設定，以及 SSL 憑證問題。")
        import traceback
        traceback.print_exc()

    print("\n--- 驗證結束 ---")


if __name__ == '__main__':
    # 您可以在這裡修改要測試的股票代碼和日期
    verify_download(symbol='2888.TW')
