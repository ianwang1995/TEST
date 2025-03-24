import requests
import openai
import os
import http.client
import json
from datetime import datetime
import yfinance as yf

# === BTC 价格 ===
def get_btc_price():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        price = data['bitcoin']['usd']
        change = data['bitcoin']['usd_24h_change']
        if price < 60000:
            raise ValueError(f"BTC价格异常: {price}")
        return price, change
    except Exception as e:
        print(f"❌ BTC价格抓取失败: {e}")
        return None, None

# === AHR999 ===
def get_ahr999():
    url = "https://dncapi.flink1.com/api/v2/index/arh999?code=bitcoin&webp=1"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.feixiaohao.com/",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        data = resp.json()
        last_data = data["data"][-1]
        return last_data[1]
    except Exception as e:
        print("❌ AHR999获取失败:", e)
        return None

# === DXY ===
def get_dxy():
    try:
        ticker = yf.Ticker("DX-Y.NYB")
        data = ticker.history(period="1d", interval="1m")
        return data["Close"].iloc[-1] if not data.empty else None
    except Exception as e:
        print("❌ DXY获取失败:", e)
        return None

# === Pi Cycle ===
def get_pi_cycle():
    api_key = 'cae396cf323241b686a4c0b76844c848'  # 替换你的 CoinAnk API key
    conn = http.client.HTTPSConnection("open-api.coinank.com")
    headers = {'apikey': api_key}
    conn.request("GET", "/api/indicator/getBtcPi", '', headers)
    res = conn.getresponse()
    data = res.read().decode("utf-8")
    json_data = json.loads(data)

    if json_data.get("success") and "data" in json_data:
        try:
            d = json_data["data"]
            btc_price = d["priceList"][-1]
            ma110 = d["ma110"][-1]
            ma350x2 = d["ma350Mu2"][-1]
            now_date = datetime.utcfromtimestamp(d["timeList"][-1]/1000).strftime("%Y-%m-%d")
            desc = f"📅 {now_date}\nBTC：${btc_price:,.2f}，110DMA：${ma110:,.2f}，350DMAx2：${ma350x2:,.2f}"

            if ma110 > ma350x2:
                status = "⚠️ Pi指标预警：接近顶部，警惕回调"
            elif abs(ma110 - ma350x2) / ma350x2 < 0.05:
                status = "⏳ Pi指标接近顶部区域，保持警惕"
            else:
                status = "✅ Pi指标健康，未到顶部区域"
            return f"{desc}\n{status}"
        except Exception as e:
            print("❌ Pi数据解析失败:", e)
            return "获取失败"
    else:
        return "获取失败"

# === MVRV Z-Score ===
def get_mvrv_zscore():
    api_key = 'cae396cf323241b686a4c0b76844c848'  # 替换你的 CoinAnk API key
    conn = http.client.HTTPSConnection("open-api.coinank.com")
    headers = {'apikey': api_key}
    conn.request("GET", "/api/indicator/index/charts?type=/charts/mvrv-zscore/", '', headers)
    res = conn.getresponse()
    data = res.read().decode("utf-8")
    json_data = json.loads(data)

    if json_data.get("success") and "data" in json_data:
        try:
            zscore = json_data["data"]["value4"][-1]
            if zscore > 7:
                status = f"📍 MVRV Z-Score：{zscore:.2f}，⚠️ 高估，建议减仓"
            elif zscore < 0:
                status = f"📍 MVRV Z-Score：{zscore:.2f}，✅ 低估，定投良机"
            else:
                status = f"📍 MVRV Z-Score：{zscore:.2f}，⏳ 市场正常，观望为主"
            return status
        except Exception as e:
            print("❌ MVRV解析失败:", e)
            return "获取失败"
    else:
        return "获取失败"

# === 快报主函数 ===
def main():
    btc_price, change = get_btc_price()
    ahr999 = get_ahr999()
    dxy = get_dxy()
    pi_cycle = get_pi_cycle()
    mvrv = get_mvrv_zscore()

    if None in [btc_price, ahr999]:
        print("❌ 核心数据获取失败，终止生成")
        return

    # === 数据整理 ===
    btc_str = f"${btc_price:,.0f}（{change:+.2f}% {'↑' if change > 0 else '↓'}）"
    table = f"""
| 指标             | 当前数据           | 解读/建议                     |
|------------------|--------------------|-------------------------------|
| BTC现价          | {btc_str}          | 支撑位$83K，短期波动         |
| DXY              | {dxy:.2f}          | 美元走弱，利好BTC           |
| AHR999           | {ahr999:.2f}       | 策略：>1.2减仓，<0.75加仓    |
| MVRV Z-Score     | {mvrv}             |                               |
| Pi循环指标       | {pi_cycle}         |                               |
"""

    # === GPT总结 ===
    summary_prompt = f"""
BTC现价为{btc_str}，AHR999为{ahr999:.2f}。策略是AHR999<0.75加仓，>1.2减仓。根据全球流动性和指标生成今日总结，提醒稳健操作、持币为主。
"""
    try:
        openai.api_key = os.getenv("OPENAI_API_KEY")
        resp = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": summary_prompt}],
            temperature=0.7,
            max_tokens=500
        )
        summary = resp["choices"][0]["message"]["content"].strip()
    except Exception as e:
        summary = "总结生成失败"
        print("GPT失败:", e)

    final_report = f"📊 BTC每日快报\n{table}\n📢 总结：\n{summary}"
    print(final_report)

    # === 推送 PushPlus ===
    push_token = "fa7e3ae0480c4aec900a79ca110835d3"
    push_url = "https://www.pushplus.plus/send"
    payload = {
        "token": push_token,
        "title": "BTC每日快报",
        "content": final_report,
        "template": "markdown"
    }
    try:
        r = requests.post(push_url, json=payload)
        print("✅ 推送成功:", r.json())
    except Exception as e:
        print("❌ 推送失败:", e)

if __name__ == "__main__":
    main()
