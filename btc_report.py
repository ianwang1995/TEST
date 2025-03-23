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
    ticker = yf.Ticker("DX-Y.NYB")
    data = ticker.history(period="1d", interval="1m")
    if not data.empty:
        latest_close = data["Close"].iloc[-1]
        return latest_close
    else:
        return "获取失败"

print("最新 DXY 值:", get_dxy())

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
