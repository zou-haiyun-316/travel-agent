# ============================================================
# FirstAgentTest.py — 智能旅行助手 Agent
# 对应《Hello Agents》第一章 1.3 节
# ============================================================
# 这是一个完整的智能体示例，展示 Thought → Action → Observation
# 循环的工作原理。智能体能够查询天气、推荐景点，并最终给出答案。
#
# 运行前：
#   1. 添加需要的python库：pip install requests openai tavily-python
#   2. 替换下方 API 配置区的密钥
# ============================================================


# ============================================================
# 板块一：系统提示词（System Prompt）—— 智能体的"说明书"
# ============================================================
# 作用：告诉 LLM 它的角色、可用工具、以及输出格式要求。
# 所属阶段：思考阶段（Thought）的指导规则 + 工具选择（Tool Selection）
# ============================================================

AGENT_SYSTEM_PROMPT = """
你是一个智能旅行助手。你的任务是分析用户的请求，并使用可用工具一步步地解决问题。

# 可用工具:
- `get_weather(city: str)`: 查询指定城市的实时天气。
- `get_attraction(city: str, weather: str)`: 根据城市和天气搜索推荐的旅游景点。

# 输出格式要求:
你的每次回复必须严格遵循以下格式，包含一对Thought和Action：

Thought: [你的思考过程和下一步计划]
Action: [你要执行的具体行动]

Action的格式必须是以下之一：
1. 调用工具：function_name(arg_name="arg_value")
2. 结束任务：Finish[最终答案]

# 重要提示:
- 每次只输出一对Thought-Action
- Action必须在同一行，不要换行
- 当收集到足够信息可以回答用户问题时，必须使用 Action: Finish[最终答案] 格式结束

请开始吧！
"""


# ============================================================
# 板块二：工具定义（Tools）—— 智能体的"手"
# ============================================================
# 工具是智能体的执行器（Actuator），用于对环境施加影响。
# 每个工具函数接收 LLM 传入的参数，执行具体操作，并将结果
# 以自然语言形式返回，作为下一轮循环的 Observation（观察）。
# ============================================================


# ----- 工具 1：天气查询 -----
# 传感器（Sensor）：导入 Python 的 HTTP 库，通过 HTTP 请求从 wttr.in 获取实时天气数据
import requests

# 定义一个工具函数：输入城市名，返回天气描述字符串。**执行器（Actuator）**的一部分。
def get_weather(city: str) -> str:
    """
    通过调用 wttr.in API 查询指定城市的实时天气。
    """
    # 构造 wttr.in（免费天气 API）的请求 URL。format=j1 表示返回 JSON 格式。
    url = f"https://wttr.in/{city}?format=j1"

    try:
        # 感知（Perception）：向外部 API 发送请求获取数据
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        # 感知处理：从返回的 JSON 中提取天气描述和温度
        current_condition = data['current_condition'][0]
        weather_desc = current_condition['weatherDesc'][0]['value']
        temp_c = current_condition['temp_C']

        # 观察的格式化：将原始数据封装成自然语言，作为 Observation 返回
        return f"{city}当前天气：{weather_desc}，气温{temp_c}摄氏度"

    # 错误处理：网络异常或数据格式不对时，返回友好错误信息（而不是让程序崩溃）。
    except requests.exceptions.RequestException as e:
        return f"错误：查询天气时遇到网络问题 - {e}"
    except (KeyError, IndexError) as e:
        return f"错误：解析天气数据失败，可能是城市名称无效 - {e}"


# ----- 工具 2：景点推荐 -----
# 传感器（Sensor）：通过 Tavily Search API 获取实时搜索结果
import os
from tavily import TavilyClient

# 定义第二个工具函数：输入城市和天气，返回景点推荐。这是**行动（Action）**的另一种表现。
def get_attraction(city: str, weather: str) -> str:
    """
    根据城市和天气，使用 Tavily Search API 搜索并返回景点推荐。
    """
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        return "错误：未配置TAVILY_API_KEY。"

    tavily = TavilyClient(api_key=api_key)

    # 将结构化参数构造成自然语言搜索查询
    query = f"'{city}' 在'{weather}'天气下最值得去的旅游景点推荐及理由"

    try:
        # 感知（Perception）：调用搜索引擎，获取实时信息
        response = tavily.search(query=query, search_depth="basic", include_answer=True)

        # 有综合回答则直接返回，否则手动格式化搜索结果
        if response.get("answer"):
            return response["answer"]

        # 没有综合回答时，手动格式化搜索结果列表。这也是**观察（Observation）**的格式化过程。
        formatted_results = []
        for result in response.get("results", []):
            formatted_results.append(f"- {result['title']}: {result['content']}")

        if not formatted_results:
            return "抱歉，没有找到相关的旅游景点推荐。"

        return "根据搜索，为您找到以下信息：\n" + "\n".join(formatted_results)

    except Exception as e:
        return f"错误：执行Tavily搜索时出现问题 - {e}"


# ----- 工具注册表 -----
# 将工具名映射到实际函数，主循环通过此字典路由调用
available_tools = {
    "get_weather": get_weather,
    "get_attraction": get_attraction,
}


# ============================================================
# 板块三：LLM 客户端（LLM Client）—— 智能体的"大脑"
# ============================================================
# 封装对大语言模型的调用。兼容任何 OpenAI 格式的 API
#（如 DeepSeek、通义千问、Ollama 等）。
# 所属阶段：思考阶段（Thought）——LLM 根据规则 + 上下文生成
#           下一步的 Thought 和 Action。
# ============================================================

from openai import OpenAI

class OpenAICompatibleClient:
    """
    一个用于调用任何兼容 OpenAI 接口的 LLM 服务的客户端。
    """

    def __init__(self, model: str, api_key: str, base_url: str):
        self.model = model
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def generate(self, prompt: str, system_prompt: str) -> str:
        """
        调用 LLM API 生成回应。
        参数 prompt 包含当前任务和全部历史（Thought-Action-Observation），
        参数 system_prompt 包含角色设定和格式规则。
        返回 LLM 输出的 Thought + Action 字符串。
        """
        print("正在调用大语言模型...")
        try:
            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': prompt}
            ]
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=False
            )
            answer = response.choices[0].message.content
            print("大语言模型响应成功。")
            return answer

        except Exception as e:
            print(f"调用LLM API时发生错误: {e}")
            return "错误：调用语言模型服务时出错。"


# ============================================================
# 板块四：API 配置区
# ============================================================
# 请将下方的占位符替换为你自己的密钥和模型信息。
# 注意：Tavily API Key 通过环境变量传递给 get_attraction 函数。
# ============================================================

# 从 .env 文件中读取本地密钥（该文件已加入 .gitignore，不会上传到 GitHub）
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.environ.get("DEEPSEEK_API_KEY", "请设置 DEEPSEEK_API_KEY 环境变量")
BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
MODEL_ID = os.environ.get("DEEPSEEK_MODEL_ID", "deepseek-v4-flash")
if "TAVILY_API_KEY" not in os.environ:
    os.environ['TAVILY_API_KEY'] = "请设置 TAVILY_API_KEY 环境变量"

# 实例化 LLM 客户端——创建智能体的"大脑"
llm = OpenAICompatibleClient(
    model=MODEL_ID,
    api_key=API_KEY,
    base_url=BASE_URL
)


# ============================================================
# 板块五：Agent 主循环（Agent Loop）
# ============================================================
# 这是智能体的"神经系统"，驱动整个感知-思考-行动-观察的闭环。
# 每次循环：
#   ① 将历史记录发给 LLM → LLM 返回 Thought + Action（思考阶段）
#   ② 解析 Action，执行对应工具或结束任务（行动阶段）
#   ③ 将工具返回结果包装为 Observation，追加到历史（观察阶段）
#   ④ 进入下一轮循环，直到 Action = Finish[...]
# ============================================================

import re

# ----- 5.1 默认提示词 -----
# 直接按回车（不输入任何内容）时使用的默认任务，方便快速测试
DEFAULT_PROMPT = "你好，请帮我查询一下今天北京的天气，然后根据天气推荐一个合适的旅游景点。"

import sys

def run_agent(user_prompt):
    """
    运行一次 Agent 任务，返回结构化步骤列表和最终答案。
    供 CLI 和 Web 两种模式调用。
    """
    prompt_history = [f"用户请求: {user_prompt}"]
    steps = []
    final_answer = None

    # ----- 单次任务主循环（最多 5 轮，防止无限循环）-----
    for i in range(5):
        print(f"--- 循环 {i + 1} ---\n")

        # ========== 阶段 1：思考（Thought）==========
        # 将完整历史发给 LLM，让它基于当前进展决定下一步做什么
        full_prompt = "\n".join(prompt_history)
        llm_output = llm.generate(full_prompt, system_prompt=AGENT_SYSTEM_PROMPT)

        # 安全截断：如果 LLM 一次输出多对 Thought-Action，只保留第一对
        match = re.search(
            r'(Thought:.*?Action:.*?)(?=\n\s*(?:Thought:|Action:|Observation:)|\Z)',
            llm_output,
            re.DOTALL
        )
        if match:
            truncated = match.group(1).strip()
            if truncated != llm_output.strip():
                llm_output = truncated
                print("已截断多余的 Thought-Action 对")

        print(f"模型输出:\n{llm_output}\n")
        prompt_history.append(llm_output)

        # 从输出中分别提取 Thought 内容（供 Web 版显示思考过程使用）
        thought_match = re.search(r'Thought:(.*?)(?=Action:)', llm_output, re.DOTALL)
        thought_text = thought_match.group(1).strip() if thought_match else ""

        # ========== 阶段 2：解析并执行行动（Action）==========
        # 2a. 从 LLM 输出中提取 Action 字段
        action_match = re.search(r"Action: (.*)", llm_output, re.DOTALL)
        if not action_match:
            observation = "错误: 未能解析到 Action 字段。请确保你的回复严格遵循 'Thought: ... Action: ...' 的格式。"
            observation_str = f"Observation: {observation}"
            print(f"{observation_str}\n" + "=" * 40)
            prompt_history.append(observation_str)
            steps.append({
                "thought": thought_text,
                "action": "（解析失败）",
                "observation": observation
            })
            continue

        action_str = action_match.group(1).strip()

        # 2b. 检查是否应该结束任务
        if action_str.startswith("Finish"):
            final_answer = re.match(r"Finish\[(.*)\]", action_str).group(1)
            print(f"任务完成，最终答案: {final_answer}")
            steps.append({
                "thought": thought_text,
                "action": action_str,
                "observation": "（任务完成）"
            })
            break

        # 2c. 解析工具名和参数，执行工具调用
        tool_name = re.search(r"(\w+)\(", action_str).group(1)
        args_str = re.search(r"\((.*)\)", action_str).group(1)
        kwargs = dict(re.findall(r'(\w+)="([^"]*)"', args_str))

        if tool_name in available_tools:
            # 行动阶段：智能体通过工具对环境施加影响
            observation = available_tools[tool_name](**kwargs)
        else:
            observation = f"错误：未定义的工具 '{tool_name}'"

        # ========== 阶段 3：记录观察结果（Observation）==========
        # 将工具返回结果包装为 Observation，追加到历史。
        # 下一轮循环中 LLM 会看到这个 Observation，据此做下一步决策。
        observation_str = f"Observation: {observation}"
        print(f"{observation_str}\n" + "=" * 40)
        prompt_history.append(observation_str)

        steps.append({
            "thought": thought_text,
            "action": action_str,
            "observation": observation
        })

    return steps, final_answer

# ============================================================
# 板块六：选择 Web/CLI 服务模式
# ============================================================

# ----- Web 模式：命令行加 --web 参数启动 -----
# 用法：python FirstAgentTest.py --web
# 然后浏览器打开 http://127.0.0.1:5000
if len(sys.argv) > 1 and sys.argv[1] == '--web':
    from flask import Flask, render_template, request, jsonify

    app = Flask(__name__)

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/chat', methods=['POST'])
    def chat():
        data = request.json
        user_message = data.get('message', '').strip()
        if not user_message:
            return jsonify({"error": "消息不能为空"}), 400
        try:
            steps, final_answer = run_agent(user_message)
            return jsonify({"steps": steps, "final_answer": final_answer})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    print("🧳 智能旅行助手 Web 版已启动")
    # 云部署：监听 0.0.0.0，端口从环境变量读取
    port = int(os.environ.get("PORT", 5000))
    print(f"监听端口: {port}")
    app.run(host='0.0.0.0', port=port)
    sys.exit(0)


# ----- CLI 模式: 交互式多轮对话-----
# 运行后程序会等待你输入任务，处理完一个可以继续输入下一个。
# 每次 input() = 一次新任务，prompt_history（TAO 历史）会重置，
# 避免旧任务的上下文干扰新任务。
# 输入 q 退出程序。
while True:
    # 获取用户输入
    user_input = input("\n>>> 请输入任务（直接回车用默认，输入 q 退出）: ").strip()
    if user_input.lower() == 'q':
        print("再见！")
        break

    # 有输入就用输入的，没输入就用默认
    user_prompt = user_input if user_input else DEFAULT_PROMPT
    print(f"\n用户输入: {user_prompt}\n" + "=" * 40)

    # ----- 运行 Agent（调用公共函数）-----
    steps, final_answer = run_agent(user_prompt)
