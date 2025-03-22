import openai
import requests
import os

# 读取密钥与环境变量
openai.api_key = os.getenv("OPENAI_API_KEY")
openai.organization = os.getenv("OPENAI_ORG_ID")
openai.project = os.getenv("OPENAI_PROJECT_ID")
server_key = os.getenv("SERVER_CHAN_KEY")

# 定义 Prompt
messages = [
    {
        "role": "system",
        "content": "你是一位加密市场分析师，语言专业简洁。"
    },
    {
        "role": "user",
        "content": """请用简洁、专业的语言生成今天的BTC快报，格式如下：

表格内容包含以下6项，格式严格按要求排版：

| 指标                   | 当前数据（变化）         | 解读/结论                           |
|------------------------|--------------------------|------------------------------------|
| BTC现价                | （请写明价格及涨跌幅）     | 简要走势 + 支撑位判断               |
| DXY                    | （请写明数值及涨跌幅）     | 美元强弱 → 解读流动性对BTC影响       |
| AHR999                 | （请写明数值）            | 判断是否达加仓或减仓区，并建议       |
| RRP余额                | （请写明数值及变化）       | 美元流动性释放与否 → 解读资金面       |
| 美债10Y收益率          | （请写明数值及变化）       | 判断流动性方向 → 对BTC影响            |
| BTC现货ETF资金流       | （近七日流入/流出金额）     | 机构态度与买入积极性分析              |

表格后写总结（不超过2段），内容必须结合以下BTC翻盘计划策略：

“我的策略为：AHR999<0.75加仓，>1.2减仓。当前指数若未达加仓区，只持有不追涨。我只在流动性宽松、指标低位加仓，目标牛市稳健翻倍。”

整体风格简洁高密度，适合金融交易员阅读，重点突出操作建议与流动性判断。"""
    }
]

try:
    # GPT生成快报
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=messages,
        temperature=0.7,
        max_tokens=1000
    )
    report = response["choices"][0]["message"]["content"].strip()
    print("生成的快报:\n", report)

    # Server酱推送
    url = f"https://sctapi.ftqq.com/{server_key}.send"
    data = {
        "title": "BTC快报",
        "desp": report
    }
    resp = requests.post(url, data=data)
    print("Server酱回复:", resp.json())

except Exception as e:
    print("出错:", e)
