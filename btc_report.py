import openai
import requests
import os

openai.api_key = os.getenv("OPENAI_API_KEY")
openai.organization = os.getenv("OPENAI_ORG_ID")
openai.project = os.getenv("OPENAI_PROJECT_ID")
server_key = os.getenv("SERVER_CHAN_KEY")

messages = [
    {"role": "system", "content": "你是一位加密市场分析师，语言专业简洁。"},
    {"role": "user", "content": "生成一份今天的BTC快报，包含DXY，AHR999，ETF资金流趋势，总结流动性状况和操作建议，语气专业简洁，用中文回答。"}
]

try:
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=messages,
        temperature=0.7,
        max_tokens=800
    )
    report = response["choices"][0]["message"]["content"].strip()
    print("生成的快报:\\n", report)

    url = f"https://sctapi.ftqq.com/{server_key}.send"
    data = {
        "title": "BTC快报",
        "desp": report
    }
    resp = requests.post(url, data=data)
    print("Server酱回复:", resp.json())

except Exception as e:
    print("出错:", e)
