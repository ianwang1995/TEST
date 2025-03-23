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

import requests
import json
import time

def get_etf_flow():
    try:
        # 配置 ParseHub 项目和 API Key（生产环境建议用环境变量）
        project_token = "tB6uAjQYUA5C"
        api_key = "tkcBJ4rg19HT"

        # 1. 触发新的运行
        trigger_url = f"https://www.parsehub.com/api/v2/projects/{project_token}/run"
        params = {"api_key": api_key}
        trigger_response = requests.post(trigger_url, data=params, timeout=10)
        trigger_response.raise_for_status()
        trigger_data = trigger_response.json()
        run_token = trigger_data.get("run_token")
        if not run_token:
            raise Exception("触发运行后未返回 run_token。")

        print("触发运行成功，run_token:", run_token)

        # 2. 轮询等待该 run 的数据准备好
        run_status_url = f"https://www.parsehub.com/api/v2/runs/{run_token}"
        max_retries = 20         # 根据情况调整重试次数
        retry_delay = 10         # 每次等待 10 秒
        data_ready = False
        for i in range(max_retries):
            status_response = requests.get(run_status_url, params={"api_key": api_key}, timeout=10)
            status_response.raise_for_status()
            status_data = status_response.json()
            print(f"第 {i+1} 次轮询，状态：", status_data.get("status"), " data_ready:", status_data.get("data_ready"))
            if status_data.get("data_ready"):
                data_ready = True
                break
            time.sleep(retry_delay)
        if not data_ready:
            raise Exception("运行未在预定时间内完成数据采集。")

        # 3. 获取最新的数据：使用 last_ready_run 接口（返回 JSON 格式）
        data_url = f"https://www.parsehub.com/api/v2/projects/{project_token}/last_ready_run/data"
        data_response = requests.get(data_url, params={"api_key": api_key, "format": "json"}, timeout=10)
        data_response.raise_for_status()
        data_json = data_response.json()

        # 调试时打印完整返回数据，确认数据结构后再提取你需要的字段
        # print(json.dumps(data_json, ensure_ascii=False, indent=2))
        
        # 4. 根据实际返回的数据结构提取 ETF net flow 数据
        # 这里假设返回的数据中有 "flows" 节点，其下有 "net_flow" 字段
        net_flow = data_json.get("flows", {}).get("net_flow")
        if net_flow is None:
            return "获取失败：未找到 net flow 数据"
        else:
            return f"{net_flow}亿美元"
    except Exception as e:
        print("ETF净流数据获取失败:", e)
        return "获取失败"

if __name__ == '__main__':
    flow = get_etf_flow()
    print("ETF净流数据:", flow)


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
