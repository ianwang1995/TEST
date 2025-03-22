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

import requests
from bs4 import BeautifulSoup

import requests
from bs4 import BeautifulSoup

# 使用全局 Session 对象以复用 Cookie 和连接
session = requests.Session()

# === 获取 AHR 数据 ===
import requests

def get_ahr999():
    url = "https://dncapi.flink1.com/api/v2/index/arh999?code=bitcoin&webp=1"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        # 如果需要，可以加上 Referer 或其他头部
        # "Referer": "https://www.feixiaohao.com/data/ahrdata.html",
        # 还可以根据实际需要添加 Cookie 等
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()  # 若状态码不是200，这会抛出异常
        data = resp.json()       # 解析JSON响应
        
        # data 的结构大致可能是：
        # {
        #   "code": 0,
        #   "msg": "success",
        #   "data": {
        #       "value": 0.8272,
        #       ...
        #   }
        # }
        
        # 具体字段名以实际返回内容为准
        if data.get("code") == 0 and "data" in data:
            ahr_value = data["data"].get("value")
            return ahr_value
        else:
            # 如果返回结构跟预期不一致，就抛出异常或返回“获取失败”
            raise ValueError(f"接口返回异常, data={data}")
    except Exception as e:
        print("❌ AHR999抓取失败:", e)
        return "获取失败"


if __name__ == "__main__":
    value = get_ahr999()
    print("AHR999 值:", value)

# === 获取 DXY 数据 ===
def get_dxy():
    try:
        url = "https://www.marketwatch.com/investing/index/dxy"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.marketwatch.com/'
        }
        response = session.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            raise ValueError(f"请求失败，状态码: {response.status_code}")
        
        soup = BeautifulSoup(response.text, 'lxml')
        element = soup.select_one("bg-quote.value")
        if not element:
            raise ValueError("未能定位到 bg-quote.value")
        return element.text.strip()
    except Exception as e:
        print("❌ DXY获取失败:", e)
        return "获取失败"

if __name__ == "__main__":
    ahr_data = get_ahr_data()
    dxy_value = get_dxy()
    print("AHR数据:", ahr_data)
    print("DXY:", dxy_value)



# 示例：调用函数并打印结果
if __name__ == "__main__":
    ahr999_value = get_ahr999()
    dxy_value = get_dxy()
    print("AHR999:", ahr999_value)
    print("DXY:", dxy_value)



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
