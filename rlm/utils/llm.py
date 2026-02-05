import os
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


class LlmClient:
    def __init__(self,
                 api_key: Optional[str] = None,
                 model: Optional[str] = None,
                 base_url: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("MAIN_MODEL")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL")
        if not (self.api_key and self.model and self.base_url):
            raise ValueError("缺少LLM必要参数")

        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def completion(self,
                   messages: list[dict[str, str]],
                   max_tokens: Optional[int] = None,
                   **kwargs) -> str:
        try:
            if isinstance(messages, str):
                messages = [{"role": "user", "content": messages}]
            elif isinstance(messages, dict):
                messages = [messages]
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_completion_tokens=max_tokens,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"运行llm模型报错如下：{str(e)}")
