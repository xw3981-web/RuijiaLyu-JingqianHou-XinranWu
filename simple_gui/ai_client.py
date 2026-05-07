# -*- coding: utf-8 -*-

import sys
from openai import OpenAI

# ✅ 防止 Mac 终端乱码 / ascii 报错
sys.stdout.reconfigure(encoding='utf-8')

# ===============================
# 🔑 API 配置
# ===============================
client = OpenAI(
    api_key="sk-JQ2XUVVyIFl4cCuEr37RwXzkCNipJmdwxw7kTGHhtP1PtfJi",   # ← 建议别写死提交版本
    base_url="https://api.34ku.com/v1"
)

# ===============================
# 🤖 全局状态（核心）
# ===============================
chat_history = []   # 上下文记忆
personality = "You are a friendly and helpful chatbot."

# ===============================
# 🎭 设置人格
# ===============================
def set_personality(p: str):
    global personality
    personality = f"You are a {p} chatbot."
    print(f"[DEBUG] Personality set to: {personality}")

# ===============================
# 🧹 清空记忆
# ===============================
def reset_chat():
    global chat_history
    chat_history = []
    print("[DEBUG] Chat history cleared")

# ===============================
# 🧠 核心聊天函数（稳定版）
# ===============================
def ask_llm(prompt: str) -> str:
    global chat_history, personality

    try:
        # 👉 拼接人格 + 历史（关键！避免 API 不支持 system role）
        full_prompt = personality + "\n\n"

        # 只保留最近 6 条对话（防止太长）
        for m in chat_history[-6:]:
            full_prompt += f"{m['role']}: {m['content']}\n"

        full_prompt += f"user: {prompt}"

        # 👉 调用 API（只用 user 角色，最兼容）
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",   # 可换 gpt-4o-mini / deepseek-chat
            messages=[
                {"role": "user", "content": full_prompt}
            ],
            temperature=0.7,
        )

        reply = response.choices[0].message.content

        # 👉 保存上下文（实现记忆）
        chat_history.append({"role": "user", "content": prompt})
        chat_history.append({"role": "assistant", "content": reply})

        # 👉 防止编码炸掉
        return reply.encode("utf-8", "ignore").decode("utf-8")

    except Exception as e:
        print("LLM ERROR:", str(e))
        return f"(Demo Bot 🤖) You said: {prompt}"

# ===============================
# 🧪 本地测试
# ===============================
if __name__ == "__main__":
    print("Testing chatbot...\n")

    print("Bot:", ask_llm("Who are you?"))

    print("\n--- Test Memory ---")
    ask_llm("My name is Alex")
    print("Bot:", ask_llm("What is my name?"))

    print("\n--- Test Personality ---")
    set_personality("funny")
    print("Bot:", ask_llm("Tell me a joke"))