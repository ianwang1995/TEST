import requests
import openai
import os
from bs4 import BeautifulSoup
from datetime import datetime

# === 获取 BTC 价格 ===
def get_btc_price():
    coingecko_api = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true"
    try:
        response = requests.get(coingecko_api, timeout=10)
        response.raise_for_status()  # 检查请求是否成功
        data = response.json()
        price = data['bitcoin']['usd']
        change = data['bitcoin']['usd_24h_change']
        btc_price_str = f"${price:,.2f}（{change:+.2f}% {'↑' if change > 0 else '↓'}）"
    except requests.RequestException as e:
        btc_price_str = "获取失败"
        print(f"获取 BTC 价格时出现网络错误: {e}")
    except KeyError:
        btc_price_str = "获取失败"
        print("解析 BTC 价格数据时出现错误")
    return btc_price_str


# === 获取 AHR999 （非小号） ===
def get_ahr999():
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get("https://www.feixiaohao.com/data/ahr999/", headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        ahr_value = soup.find('div', class_='coininfo-data-num').text.strip()
        AHR999 = ahr_value
    except Exception as e:
        AHR999 = "获取失败"
        print("AHR999获取失败:", e)
    return AHR999

# === 获取 DXY （Investing） ===
def get_dxy():
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get("https://www.investing.com/indices/us-dollar-index", headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        dxy_value = soup.find('span', {'data-test': 'instrument-price-last'}).text.strip()
        dxy_change = soup.find('span', {'data-test': 'instrument-price-change-percent'}).text.strip()
        arrow = '↑' if '-' not in dxy_change else '↓'
        DXY = f"{dxy_value}（{dxy_change}{arrow}）"
    except Exception as e:
        DXY = "获取失败"
        print("DXY获取失败:", e)
    return DXY

# === 获取 RRP余额、美债10Y收益率、ETF资金流 ===
def get_rrp_balance():
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get("https://www.newyorkfed.org/markets/desk-operations/reverse-repo", headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        rrp_value = soup.find('td', text='Total').find_next_sibling('td').text.strip()
        RRP = f"{rrp_value}亿美元"
    except Exception as e:
        RRP = "获取失败"
        print("RRP余额获取失败:", e)
    return RRP

def get_us10y_yield():
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get("https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/textview", headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        date_str = datetime.now().strftime("%b %d, %Y")
        us10y_value = soup.find('td', text=date_str).find_next_sibling('td').text.strip()
        US10Y = f"{us10y_value}%"
    except Exception as e:
        US10Y = "获取失败"
        print("美债10年期收益率获取失败:", e)
    return US10Y

def get_etf_flow():
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get("https://www.coinglass.com/zh/bitcoin-etf", headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        etf_data = soup.find('div', class_='etf-data').text.strip()
        ETFflow = f"{etf_data}亿美元"
    except Exception as e:
        ETFflow = "获取失败"
        print("BTC现货ETF资金流获取失败:", e)
    return ETFflow

# === 构建GPT Prompt ===
def build_prompt():
    btc_price_str = get_btc_price()
    DXY = get_dxy()
    AHR999 = get_ahr999()
    RRP = get_rrp_balance()
    US10Y = get_us10y_yield()
    ETFflow = get_etf_flow()

    prompt = f"""
请用简洁、专业的语言生成今天的BTC每日快报，**所有数值禁止修改或四舍五入**：，格式如下：

| 指标                   | 当前数据（变化）         | 解读/结论                           |
|------------------------|--------------------------|------------------------------------|
| BTC现价                | {btc_price_str}          | 日内震荡上行，支撑位$83K           |
| DXY                    | {DXY}                    | 美元走弱，流动性宽松，看多BTC      |
| AHR999                 | {AHR999}                 | 判断是否达加仓区，建议持有         |
| RRP余额                | {RRP}                    | 美元流动性释放，资金宽松           |
| 美债10Y收益率          | {US10Y}                  | 流动性小幅放松                     |
| BTC现货ETF资金流       | {ETFflow}                | 机构买入积极，支撑BTC价格          |

总结：
全球流动性释放，BTC获支撑。根据我的BTC翻盘策略，当前AHR999为{AHR999}，未触加仓，继续持有，等待低位机会稳健加仓，实现翻倍。
"""
    return prompt

# === GPT生成快报 ===
def generate_report():
    openai.api_key = os.getenv("OPENAI_API_KEY")
    try:
        prompt = build_prompt()
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "你是一位加密市场分析师，语言专业简洁。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        report = response["choices"][0]["message"]["content"].strip()
        print("生成的快报:\n", report)
    except Exception as e:
        print("GPT生成失败:", e)
        report = prompt
    return report

# === PushPlus 推送 ===
def push_to_pushplus(report):
    pushplus_token = "fa7e3ae0480c4aec900a79ca110835d3"
    url = "https://www.pushplus.plus/send"
    data = {
        "token": pushplus_token,
        "title": "BTC每日快报",
        "content": report,
        "template": "html"
    }
    try:
        resp = requests.post(url, json=data)
        print("PushPlus回复:", resp.json())
    except Exception as e:
        print("PushPlus推送失败:", e)

# === 主执行 ===
if __name__ == "__main__":
    report = generate_report()
    push_to_pushplus(report)
