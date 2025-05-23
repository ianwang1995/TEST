import os
import requests
import http.client
import json
from datetime import datetime
import yfinance as yf
import openai  # 别忘了导入openai

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
    ma110, ma350Mu2 = get_pi_indicator()
    zscore = get_mvrv_zscore()

    # --- 数据校验 ---
    if None in [btc_price, btc_change, dxy, ahr999, ma110, ma350Mu2, zscore]:
        print("❌ 数据不全，终止生成")
        return None

    # === 表格与字符串格式化 ===
    btc_str = f"${btc_price:,.0f}（{btc_change:+.2f}% {'↑' if btc_change > 0 else '↓'}）"
    mvrv_str = f"{zscore:.2f}"
    pi_str = f"110DMA: ${ma110:,.2f}, 350DMAx2: ${ma350Mu2:,.2f}"

    # === 解读 ===
    dxy_comment = "美元走弱，利好BTC" if dxy < 104 else "美元走强，警惕BTC回调"
    ahr_comment = "策略：>1.2减仓，<0.75加仓"
    mvrv_comment = "高估⚠️" if zscore > 4 else ("极度低估✅" if zscore < 0 else "市场正常，观望为主")
    pi_comment = "⚠️ Pi指标预警：接近顶部" if ma110 >= ma350Mu2 * 0.95 else "✅ Pi指标健康，未到顶部区域"

    # === 输出表格 ===
    table = f"""
| 指标            | 当前数据                           | 解读/建议                          |
|-----------------|------------------------------------|------------------------------------|
| BTC现价         | {btc_str}                          |                                    |
| DXY             | {dxy:.2f}                          | {dxy_comment}                      |
| AHR999          | {ahr999:.2f}                       | {ahr_comment}                      |
| MVRV Z-Score    | {mvrv_str}                         | {mvrv_comment}                     |
| Pi循环指标      | {pi_str}                           | {pi_comment}                       |
"""

    # === GPT总结 ===
    summary_prompt = f"""
BTC现价为{btc_str}，AHR999为{ahr999:.2f}。策略是AHR999<0.75加仓，>1.2减仓。根据我记忆库里的BTC翻盘计划和策略，不修改任何数据，根据全球流动性和指标生成1-2话的今日总结，并给一个明确的结论：耐心等待或者加仓或者卖出（不要说废话，比如注意风险之类的，我要精炼的信息）。
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
        print("GPT调用失败:", e)

    final_report = f"📊 BTC每日快报\n{table}\n📢 总结：\n{summary}"
    print(final_report)
    return final_report

def push_report(report):
    if not report:
        print("❌ 没有可推送的报告")
        return

    push_tokens = [
        "fa7e3ae0480c4aec900a79ca110835d3",
        "9214b072485b429b8b041d65b9e8886b"
    ]
    push_url = "https://www.pushplus.plus/send"

    for token in push_tokens:
        payload = {
            "token": token,
            "title": "BTC每日快报",
            "content": report,
            "template": "markdown"
        }
        try:
            r = requests.post(push_url, json=payload, timeout=10)
            r.raise_for_status()
            print(f"✅ 推送成功 ({token}):", r.json())
        except Exception as e:
            print(f"❌ 推送失败 ({token}):", e)

if __name__ == "__main__":
    # 生成报告并推送
    report = format_and_analyze()
    push_report(report)
