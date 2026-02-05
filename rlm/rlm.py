from abc import ABC, abstractmethod
from typing import List, Dict


class RLM(ABC):
    @abstractmethod
    def completion(self, context: List[str] | str | List[Dict[str, str]], query: str = None) -> str:
        """核心执行代码"""
        pass

    @abstractmethod
    def cost_summary(self) -> dict[str, float]:
        """成本计算"""
        pass

    @abstractmethod
    def reset(self):
        """重置数据"""
        pass
