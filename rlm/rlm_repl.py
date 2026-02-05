from typing import Optional, List, Dict

from rlm.logger.repl_logger import REPLEnvLogger
from rlm.logger.root_logger import ColorfulLogger
from rlm.rlm import RLM
from rlm.execute_env.rlm_env import REPLEnv
from rlm.utils import utils
from rlm.utils.llm import LlmClient
from rlm.utils.prompts import DEFAULT_QUERY, build_system_prompt, next_action_prompt


class RLMRepl(RLM):
    """
        SetupLLM 客户端可以通过递归调用自身来处理长上下文。
    """

    def __init__(self,
                 api_key: Optional[str] = None,
                 model: str = None,
                 recursive_model: str = None,
                 max_iterations: int = 20,
                 depth: int = 0,
                 enable_logging: bool = False,
                 base_url: str = None,
                 ):
        """
            :param api_key: API密钥，用于认证LLM服务，默认为None
            :param model: 主要使用的语言模型名称，默认为None
            :param recursive_model: 用于递归调用的模型名称，默认为None
            :param max_iterations: 最大迭代次数，防止无限循环，默认为20次
            :param depth: 递归调用深度，默认为0（当前版本未使用）
            :param enable_logging: 是否启用日志记录功能，默认为False
            :param base_url: LLM服务的基础URL地址，默认为None
        """
        self.api_key = api_key
        self.model = model
        self.recursive_model = recursive_model
        self.llm = LlmClient(api_key, model, base_url)

        # 跟踪递归调用深度以防止无限循环
        self.repl_env = None
        self.depth = depth
        self.max_iterations = max_iterations

        # 初始化日志模块
        self.logger = ColorfulLogger(enabled=enable_logging)
        self.repl_env_logger = REPLEnvLogger(enabled=enable_logging)

        self.messages = []  # Initialize messages list
        self.query = None

    def setup_context(self, context: List[str] | str | List[Dict[str, str]], query: Optional[str] = None):
        """
        为 RLMClient 设置上下文。

        参数：
        context：要分析的大型上下文，可以是消息列表、字符串或字典形式
        query：用户的问题
        """
        if query is None:
            query = DEFAULT_QUERY

        self.query = query
        self.logger.log_query_start(query)

        # 构造请求提示词
        self.messages = build_system_prompt()
        self.logger.log_initial_messages(self.messages)

        # 使用上下文数据，初始化 REPL 环境
        context_data, context_str = utils.convert_context_for_repl(context)

        self.repl_env = REPLEnv(
            context_json=context_data,
            context_str=context_str,
            recursive_model=self.recursive_model,
        )

        return self.messages

    def cost_summary(self) -> dict[str, float]:
        pass

    def reset(self):
        """
            重置 (REPL) 环境和消息历史。
        """
        self.repl_env = REPLEnv()
        self.messages = []
        self.query = None

    def completion(self, context: list[str] | str | dict[str, str], query: str = None) -> str:
        # 构建历史会话记录
        self.messages = self.setup_context(context, query)

        # 最大迭代次数
        for iteration in range(self.max_iterations):
            print(f"迭代第{iteration}次")
            # 查询根语言模型以与 REPL 环境交互
            response = self.llm.completion(self.messages + [next_action_prompt(query, iteration)])

            # 检查代码块，查询是否需要执行
            code_blocks = utils.find_code_blocks(response)
            self.logger.log_model_response(response, has_tool_calls=code_blocks is not None)

            # 存在代码块在沙箱环境执行代码
            # 核心代码模块，需要理解，首先根据前文的提示词+用户输入（或大模型结构构建的数据再次输入），输出结果，检查结果，走不同分支
            if code_blocks is not None:
                self.messages = utils.process_code_execution(
                    response, self.messages, self.repl_env,
                    self.repl_env_logger, self.logger
                )
            else:
                # 当没有代码块时添加助手消息
                assistant_message = {"role": "assistant", "content": "你回复:\n" + response}
                self.messages.append(assistant_message)

            # 检查输出结果是否有最终答案，如果存在就返回最终答案
            final_answer = utils.check_for_final_answer(
                response, self.repl_env, self.logger,
            )

            # 在实际操作中，你可能需要一些保护措施。
            if final_answer:
                self.logger.log_final_response(final_answer)
                return final_answer

        # 容错机制，当递归深度已超过上线时，根据当前最好的已有的推理条件输出一个最好的数据。
        print("在任何迭代中都未找到最终答案")
        # 达到最大迭代次数
        self.messages.append(next_action_prompt(query, self.max_iterations, final_answer=True))
        final_answer = self.llm.completion(self.messages)
        self.logger.log_final_response(final_answer)

        return final_answer
