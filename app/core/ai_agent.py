import os
import json
import urllib.request
import re

class VaultRAGAgent:
    def __init__(self, vault_path, api_key=""):
        """
        初始化基于硅基流动 (SiliconFlow) 的 RAG 引擎
        现在 api_key 由外部动态传入，不再硬编码！
        """
        self.vault_path = vault_path
        self.api_key = api_key
        # 使用硅基流动的 OpenAI 兼容接口
        self.api_url = "https://api.siliconflow.cn/v1/chat/completions"
        # 使用完全免费的开源顶流模型 Qwen 2.5 7B
        self.model_name = "Qwen/Qwen2.5-7B-Instruct"

    def search_context(self, query, top_k=3):
        """核心检索逻辑：从本地 Vault 中寻找与 query 相关的笔记片段"""
        query_words = set(re.findall(r'\w+', query.lower()))
        scores = []

        for root, _, files in os.walk(self.vault_path):
            for f in files:
                if f.endswith('.md'):
                    path = os.path.join(root, f)
                    try:
                        content = open(path, 'r', encoding='utf-8', errors='ignore').read()
                        content_lower = content.lower()
                        # 基于词频的轻量级权重计算
                        score = sum(content_lower.count(w) for w in query_words)
                        if score > 0:
                            scores.append((score, f, content[:800]))  # 截取前 800 字作为上下文
                    except Exception:
                        pass

        # 按相关性得分降序排列
        scores.sort(key=lambda x: x[0], reverse=True)
        return scores[:top_k]

    def ask(self, query):
        """整合检索结果，通过标准的 HTTP 请求向云端大模型发起问答"""
        # 【关键修改】：如果用户没填 Key，直接给友好的提示引导去设置
        if not self.api_key or not self.api_key.startswith("sk-"):
            return "⚠️ <b>未配置 API Key 或格式错误！</b><br><br>请点击左下角的 <b>⚙️设置</b> 按钮，填入您的硅基流动 API 密钥。"

        contexts = self.search_context(query)

        # 构建 Prompt，引入检索增强生成 (RAG) 的上下文
        if contexts:
            context_str = "\n".join([f"【{title}】: {text}..." for _, title, text in contexts])
            system_prompt = "你是一个智能笔记助手。请务必基于以下我知识库中的本地笔记内容来回答问题。如果笔记中没有相关信息，请直接说明，不要自行编造。"
            user_prompt = f"本地笔记参考：\n{context_str}\n\n我的问题：{query}"
        else:
            system_prompt = "你是一个智能笔记助手。当前知识库中未找到相关内容，请基于你的通用知识为我解答。"
            user_prompt = query

        # 构造 OpenAI 兼容格式的 JSON Payload
        data = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False
        }

        # 发起原生的 HTTP POST 请求
        req = urllib.request.Request(self.api_url, data=json.dumps(data).encode('utf-8'))
        req.add_header('Content-Type', 'application/json')
        req.add_header('Authorization', f'Bearer {self.api_key}')

        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.loads(response.read().decode('utf-8'))
                # 解析返回的回答文本
                return result["choices"][0]["message"]["content"]
        except Exception as e:
            return f"⚠️ <b>API 请求失败</b><br>请检查网络环境或确认 API Key 是否有效。<br>底层异常信息: {e}"