import requests
import http.client
import json
from datetime import datetime
import yfinance as yf

# === 获取 BTC 价格 ===
def get_btc_price():
    try:
        api = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true"
        r = requests.get(api, timeout=10)
        r.raise_for_status()
        data = r.json()
        price = data['bitcoin']['usd']
        change = data['bitcoin']['usd_24h_change']
        return price, change
    except Exception as e:
        print(f"❌ BTC价格抓取失败: {e}")
        return None, None

# === 获取 DXY ===
def get_dxy():
    try:
        ticker = yf.Ticker("DX-Y.NYB")
        data = ticker.history(period="1d", interval="1m")
        if not data.empty:
            return data["Close"].iloc[-1]
        else:
            return None
    except Exception as e:
        print("❌ DXY 获取失败:", e)
        return None

# === 获取 AHR999 ===
def get_ahr999():
    url = "https://dncapi.flink1.com/api/v2/index/arh999?code=bitcoin&webp=1"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.feixiaohao.com/"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") == 200 and "data" in data:
            last_data = data["data"][-1]
            return last_data[1]
        else:
            raise ValueError(f"接口返回异常: {data}")
    except Exception as e:
        print("❌ AHR999 获取失败:", e)
        return None

# === 获取 ETF 流入 ===
def get_etf_flow():
    try:
        conn = http.client.HTTPSConnection("open-api.coinank.com")
        headers = {'apikey': 'cae396cf323241b686a4c0b76844c848'}
        conn.request("GET", "/api/etf/usBtcInflow", '', headers)
        res = conn.getresponse()
        data = res.read()
        json_data = json.loads(data.decode("utf-8"))
        today_flow = json_data.get("data", {}).get("totalNetInflow", 0)
        return today_flow
    except Exception as e:
        print("❌ ETF流获取失败:", e)
        return None

# === 获取 Pi 指标 ===
def get_pi_indicator():
    try:
        conn = http.client.HTTPSConnection("open-api.coinank.com")
        headers = {'apikey': 'cae396cf323241b686a4c0b76844c848'}
        conn.request("GET", "/api/indicator/getBtcPi", '', headers)
        res = conn.getresponse()
        data = json.loads(res.read().decode("utf-8"))
        ma110 = data["data"]["ma110"][-1]
        ma350Mu2 = data["data"]["ma350Mu2"][-1]
        return ma110, ma350Mu2
    except Exception as e:
        print("❌ Pi指标获取失败:", e)
        return None, None

# === 获取 MVRV Z-Score ===
def get_mvrv_zscore():
    try:
        conn = http.client.HTTPSConnection("open-api.coinank.com")
        headers = {'apikey': 'cae396cf323241b686a4c0b76844c848'}
        conn.request("GET", "/api/indicator/index/charts?type=/charts/mvrv-zscore/", '', headers)
        res = conn.getresponse()
        data = json.loads(res.read().decode("utf-8"))
        zscore = data["data"]["value4"][-1]
        return zscore
    except Exception as e:
        print("❌ MVRV Z-Score 获取失败:", e)
        return None

# === 格式化数据与解读 ===
def format_and_analyze():
    btc_price, btc_change = get_btc_price()
    dxy = get_dxy()
    ahr999 = get_ahr999()
    etf_flow = get_etf_flow()
    ma110, ma350Mu2 = get_pi_indicator()
    zscore = get_mvrv_zscore()

    # --- 数据校验 ---
    if None in [btc_price, btc_change, dxy, ahr999, etf_flow, ma110, ma350Mu2, zscore]:
        print("❌ 数据不全，终止生成")
        return

    # === 表格 ===
    btc_str = f"${btc_price:,.0f}（{btc_change:+.2f}% {'↑' if btc_change > 0 else '↓'}）"
    etf_str = f"{etf_flow:,.0f} USD"
    mvrv_str = f"MVRV Z-Score: {zscore:.2f}"
    pi_str = f"110DMA: ${ma110:,.2f}, 350DMAx2: ${ma350Mu2:,.2f}"

    # === 解读 ===
    dxy_comment = "美元走弱，利好BTC" if dxy < 104 else "美元走强，警惕BTC回调"
    ahr_comment = f"策略：{'>1.2减仓，<0.75加仓'}"
    mvrv_comment = "极度高估⚠️" if zscore > 7 else ("极度低估✅" if zscore < 0 else "市场正常，观望为主")
    pi_comment = "⚠️ Pi指标预警：接近顶部" if ma110 >= ma350Mu2 * 0.95 else "✅ Pi指标健康，未到顶部区域"

    # === 输出表格 ===
    print(f"""📢 BTC每日快报
| 指标            | 当前数据                       | 解读/建议                          |
|-----------------|--------------------------------|-----------------------------------|
| BTC现价         | {btc_str}                     |                                   |
| DXY             | {dxy:.2f}                      | {dxy_comment}                     |
| AHR999          | {ahr999:.2f}                   | {ahr_comment}                     |
| MVRV Z-Score    | {mvrv_str}                     | {mvrv_comment}                    |
| Pi循环指标      | {pi_str}                       | {pi_comment}                      |
| ETF流入         | {etf_str}                      | 机构资金流，短期波动支撑BTC       |
""")

    # === GPT总结 ===
    summary_prompt = f"""
BTC现价为{btc_str}，AHR999为{ahr999:.2f}。策略是AHR999<0.75加仓，>1.2减仓。根据我记忆库里的BTC翻盘计划和策略，不修改任何数据，根据全球流动性和指标生成今日总结。
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
    format_and_analyze()

