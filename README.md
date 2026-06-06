# 🧳 智能旅行助手 Agent

《Hello Agents》第一章 1.3 节实践项目 —— 基于 Thought → Action → Observation 循环的智能体。

## 功能

- 查询指定城市的实时天气
- 根据天气推荐旅游景点
- 支持 **CLI 命令行** 和 **Web 网页** 两种交互方式

## 在线体验

👉 [travel-agent-production-e21d.up.railway.app](https://travel-agent-production-e21d.up.railway.app)

无需部署，浏览器打开即可使用。

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置密钥

复制 `.env.example` 为 `.env`，填入你的 API 密钥：

```bash
cp .env.example .env
```

需要申请的服务：
- [DeepSeek API](https://platform.deepseek.com/) — LLM 模型
- [Tavily API](https://tavily.com/) — 景点搜索

### 3. 运行

#### CLI 模式（终端交互）

```bash
python FirstAgentTest.py
```

运行后输入任务，回车执行；输入 `q` 退出。

#### Web 模式（浏览器）

```bash
python FirstAgentTest.py --web
```

打开浏览器访问 `http://127.0.0.1:5000`

## 部署到云端

本应用已适配 [Railway](https://railway.app/) 云平台，支持一键部署。

1. 将代码推送到 GitHub
2. 在 Railway 新建项目 → 关联 GitHub 仓库
3. 设置 **Start Command** 为 `python FirstAgentTest.py --web`
4. 在 **Variables** 中添加环境变量（参考 `.env.example`）

## 项目结构

```
chapter1/
├── FirstAgentTest.py       # 主程序（CLI + Web）
├── FirstAgentTest.ipynb    # Jupyter Notebook 版本
├── templates/
│   └── index.html          # Web 页面
├── requirements.txt        # Python 依赖
├── .env                    # 本地密钥（不提交）
├── .env.example            # 环境变量模板
└── README.md               # 本文件
```

## 技术原理

智能体通过 **Thought → Action → Observation** 循环工作：

1. **Thought（思考）**：LLM 分析当前任务和历史，决定下一步
2. **Action（行动）**：调用工具（天气查询 / 景点搜索）
3. **Observation（观察）**：将工具返回结果反馈给 LLM

循环直到 LLM 输出 `Finish[最终答案]` 结束任务。
