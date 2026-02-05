from typing import List, Dict

from rlm.rlm import RLM
from rlm.utils.llm import LlmClient


class RLMSub(RLM):
    """简单子模型调用"""

    def __init__(self, model: str = None):
        self.model = model
        self.client = LlmClient()

    def completion(self, context: List[str] | str | List[Dict[str, str]], query: str = None) -> str:
        """
            用于子语言模型调用的简单语言模型查询。
        """
        try:
            # 处理字符串和字典/列表输入
            response = self.client.completion(
                messages=context,
                timeout=300
            )
            return response
        except Exception as e:
            error_msg = f"Error making LLM query: {str(e)}"
            return error_msg

    def cost_summary(self) -> dict[str, float]:
        pass

    def reset(self):
        pass
