import requests
import openai
import os
import yfinance as yf
from bs4 import BeautifulSoup
from datetime import datetime

# === 获取 BTC 价格 ===
def get_btc_price():
    try:
        api = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true"
        r = requests.get(api, timeout=10)
        r.raise_for_status()
        data = r.json()
        price = data['bitcoin']['usd']
        change = data['bitcoin']['usd_24h_change']
        if price < 60000:
            raise ValueError(f"BTC价格异常: {price}")
        return f"${price:,.0f}（{change:+.2f}% {'↑' if change > 0 else '↓'}）"
    except Exception as e:
        print(f"❌ BTC价格抓取失败: {e}")
        return "获取失败"

# === 使用全局 Session 对象以复用 Cookie 和连接 ===
session = requests.Session()

# === 获取 AHR 数据 ===
def get_ahr999():
    """
    请求接口并返回最新的 AHR 值，即最后一组数据中下标为 1 的数值
    接口返回数据示例：
    {
      "data": [
          [1742543998.0, 0.8226, 83931.04, 104902.81, 81624.25],
          [1742650162.0, 0.8238, 84094.3, 105006.32, 81743.14]
      ],
      "code": 200,
      "msg": "success"
    }
    """
    url = "https://dncapi.flink1.com/api/v2/index/arh999?code=bitcoin&webp=1"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/115.0.0.0 Safari/537.36"
        ),
        "Referer": "https://www.feixiaohao.com/",
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()  # 检查响应状态码
        data = resp.json()       # 解析 JSON 数据
        
        # 检查返回数据结构是否符合预期
        if data.get("code") == 200 and "data" in data:
            data_list = data["data"]
            if isinstance(data_list, list) and len(data_list) > 0:
                # 获取最后一组数据
                last_data = data_list[-1]
                if isinstance(last_data, list) and len(last_data) >= 2:
                    return last_data[1]
                else:
                    raise ValueError("最后一组数据格式不正确")
            else:
                raise ValueError("data 字段为空或格式不正确")
        else:
            raise ValueError(f"接口返回异常，返回数据：{data}")
    except Exception as e:
        print("❌ AHR 数据获取失败:", e)
        return "获取失败"

# === 获取 DXY 数据 ===


def get_dxy():
    """
    使用 yfinance 从 Yahoo Finance 获取 DXY（美元指数期货）数据，
    数据为延迟行情，适合观察趋势，不适合高频交易。
    """
    dxy = yf.download("DX-Y.NYB", period="1d", interval="1m")
    if not dxy.empty:
        latest_close = dxy["Close"].iloc[-1]
        return latest_close
    else:
        return "获取失败"

if __name__ == "__main__":
    dxy_value = get_dxy()
    print("最新 DXY 值:", dxy_value)


# === 获取 RRP余额 ===
def get_rrp_balance():
    try:
        # 示例数据，替换为真实抓取逻辑
        return "4800亿（-200亿 ↓）"
    except Exception as e:
        print(f"❌ RRP余额获取失败: {e}")
        return "获取失败"

# === 获取美债10年期收益率 ===
def get_us10y_yield():
    try:
        return "3.82%（-3bp ↓）"
    except Exception as e:
        print(f"❌ 美债10年期收益率获取失败: {e}")
        return "获取失败"

# === 获取 BTC现货ETF资金流 ===
def get_etf_flow():
    try:
        return "+1.5亿美元流入"
    except Exception as e:
        print(f"❌ BTC现货ETF资金流获取失败: {e}")
        return "获取失败"

def main():
    # === 主流程 ===
    btc_price_str = get_btc_price()
    dxy_value = get_dxy()
    ahr999_value = get_ahr999()
    rrp = get_rrp_balance()
    us10y = get_us10y_yield()
    etf_flow = get_etf_flow()

    # === 验证数据 ===
    if "获取失败" in [btc_price_str, ahr999_value]:
        print("❌ 数据异常，终止生成快报")
        exit()

    # === 拼接表格 ===
    table = f"""
| 指标                   | 当前数据（变化）         | 解读/结论                           |
|------------------------|--------------------------|------------------------------------|
| BTC现价                | {btc_price_str}          | 日内震荡上行，支撑位$83K           |
| DXY                    | {dxy_value}              | 美元走弱，流动性宽松，看多BTC      |
| AHR999                 | {ahr999_value}           | 判断是否达加仓区，建议持有         |
| RRP余额                | {rrp}                    | 美元流动性释放，资金宽松           |
| 美债10Y收益率          | {us10y}                  | 流动性小幅放松                     |
| BTC现货ETF资金流       | {etf_flow}               | 机构买入积极，支撑BTC价格          |
    """
    print(table)

    # === GPT生成总结 ===
    sum_prompt = f"""
请写一段BTC每日快报总结，不修改任何数据：
- 当前AHR999为{ahr999_value}，策略：AHR999<0.75加仓，>1.2减仓。
- BTC价格为{btc_price_str}。
总结全球流动性状况与操作建议，强调持有不追涨，等待低位加仓。
    """
    openai.api_key = os.getenv("OPENAI_API_KEY")
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "你是一位加密市场分析师，语言专业简洁。"},
                {"role": "user", "content": sum_prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        summary = response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        summary = "总结生成失败"
        print("GPT总结失败:", e)

    # === 最终快报 ===
    final_report = f"{table}\n\n总结：\n{summary}"
    print("生成的快报:\n", final_report)

    # === PushPlus 推送 ===
    pushplus_token = "fa7e3ae0480c4aec900a79ca110835d3"
    push_url = "https://www.pushplus.plus/send"
    payload = {
        "token": pushplus_token,
        "title": "BTC每日快报",
        "content": final_report,
        "template": "markdown"
    }

    try:
        resp = requests.post(push_url, json=payload)
        print("PushPlus回复:", resp.json())
    except Exception as e:
        print("PushPlus推送失败:", e)

if __name__ == "__main__":
    main()
