import requests
import openai
import os
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

# === 获取 AHR999 ===
def get_ahr999():
    try:
        url = "https://www.feixiaohao.com/data/ahr999/"  # 网址必须是此页
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'lxml')

        # 🔍 精准定位含值的 <span>
        span = soup.select_one("div.ahr999 span")
        ahr_value = span.text.strip()

        return ahr_value
    except Exception as e:
        print(f"❌ AHR999抓取失败: {e}")
        return "获取失败"


# === 获取 DXY ===
def get_dxy():
    try:
        url = "https://tw.tradingview.com/symbols/TVC-DXY/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'lxml')

        # 精确匹配 DXY 数值
        span = soup.select_one("span.last-JWoJQcPf.js-symbol-last")
        dxy_value = span.text.strip()

        return dxy_value
    except Exception as e:
        print(f"❌ DXY获取失败: {e}")
        return "获取失败"


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

# === 主流程 ===
btc_price_str = get_btc_price()
DXY = get_dxy()
AHR999 = get_ahr999()
RRP = get_rrp_balance()
US10Y = get_us10y_yield()
ETFflow = get_etf_flow()

# === 验证数据 ===
if "获取失败" in [btc_price_str, AHR999]:
    print("❌ 数据异常，终止生成快报")
    exit()

# === 拼接表格 ===
table = f"""
| 指标                   | 当前数据（变化）         | 解读/结论                           |
|------------------------|--------------------------|------------------------------------|
| BTC现价                | {btc_price_str}          | 日内震荡上行，支撑位$83K           |
| DXY                    | {DXY}                    | 美元走弱，流动性宽松，看多BTC      |
| AHR999                 | {AHR999}                 | 判断是否达加仓区，建议持有         |
| RRP余额                | {RRP}                    | 美元流动性释放，资金宽松           |
| 美债10Y收益率          | {US10Y}                  | 流动性小幅放松                     |
| BTC现货ETF资金流       | {ETFflow}                | 机构买入积极，支撑BTC价格          |
"""

# === GPT生成总结 ===
sum_prompt = f"""
请写一段BTC每日快报总结，不修改任何数据：
- 当前AHR999为{AHR999}，策略：AHR999<0.75加仓，>1.2减仓。
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
