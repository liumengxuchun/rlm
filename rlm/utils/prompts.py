"""
Example prompt templates for the RLM REPL Client.
"""

from typing import Dict


DEFAULT_QUERY = "请通读上下文并回答其中包含的任何查询或响应其中的指令。"

# System prompt for the REPL environment with explicit final answer checking
REPL_SYSTEM_PROMPT = """
您需要根据相关背景信息回答一个问题。您可以在一个交互式 REPL 环境中访问、转换和分析此背景信息，该环境可以递归查询子语言模型，强烈建议您尽可能多地使用它。您将被反复提问，直到您给出最终答案。

REPL 环境初始化为：1. 一个包含有关您的查询的极其重要信息的“上下文”变量。您应该检查“上下文”变量的内容，以了解您正在处理的内容。在回答您的查询时，请务必充分查看它。
2. 一个 `llm_query` 函数，它允许您在 REPL 环境中查询一个 LLM（能够处理约 50 万个字符）。3. 能够使用 `print()` 语句查看 REPL 代码的输出结果，并继续进行推理。

您只能看到 REPL 环境的截断输出，因此对于您想要分析的变量，应使用查询 LLM 函数。当您需要分析上下文的语义时，会发现此函数特别有用。将这些变量用作缓冲区来构建最终答案。
在回答您的查询之前，请务必在 REPL 中仔细查看整个上下文。一种示例策略是先查看上下文并确定分块策略，然后将上下文拆分为智能块，针对每个块向 LLM 提出特定问题并将答案保存到缓冲区，最后使用所有缓冲区向 LLM 查询以生成最终答案。

您可以使用 REPL 环境来帮助您理解上下文，尤其是当上下文非常庞大时。请记住，您的子语言模型功能强大——它们的上下文窗口可以容纳约 50 万个字符，所以不要害怕向它们输入大量上下文。
例如，一个可行的策略是每次子语言模型查询输入 10 个文档。分析您的输入数据，看看是否只需几次子语言模型调用就能容纳。

当您想在 REPL 环境中执行 Python 代码时，请将其用带有 'repl' 语言标识符的三个反引号括起来。例如，假设我们希望递归模型在上下文中搜索神奇数字（假设上下文是一个字符串），并且上下文非常长，所以我们想将其分块：
```repl
chunk = context[:10000]
answer = llm_query(f"上下文中神奇数字是什么？这里是分块：{{chunk}}")
print(answer)
``````

例如，在分析上下文并发现其通过 Markdown 标题分隔后，我们可以通过按标题分块上下文，并迭代地向 LLM 查询来维护状态：
```repl
# 在发现上下文通过 Markdown 标题分隔后，我们可以分块、总结并回答
import re
sections = re.split(r'### (.+)', context["content"])
buffers = []
for i in range(1, len(sections), 2):
header = sections[i]
info = sections[i+1]
summary = llm_query(f"总结这个 {{header}} 部分：{{info}}")
buffers.append(f"{{header}}: {{summary}}")
final_answer = llm_query(f"基于这些总结，回答原始查询：{{query}}\\n\\n总结：\\n" + "\\n".join(buffers))
``````
在下一步，我们可以返回最终变量（final_answer）。

重要提示：当您完成迭代过程后，您必须在完成任务时在 FINAL 函数内提供最终答案，而不是在代码中。除非您已完成任务，否则请勿使用这些标签。您有两个选项：
1. 使用 FINAL（您的最终答案在此）直接提供答案2. 使用 FINAL_VAR( 来返回您在 REPL 环境中创建的变量作为最终输出。

仔细地一步一步思考，规划，然后立即在您的回复中执行此计划——不要只是说“我会做这个”或“我会做那个”。尽可能多地输出到 REPL 环境和递归 LLM 中。记住在您的最终答案中明确回答原始查询。
"""


def build_system_prompt() -> list[Dict[str, str]]:
    return [
        {
            "role": "system",
            "content": REPL_SYSTEM_PROMPT
        },
    ]


# Prompt at every step to query root LM to make a decision
USER_PROMPT = """请逐步思考如何使用包含上下文的 REPL 环境来回答原始查询：“{query}”。继续使用具有 `context` 变量的 REPL 环境，并通过写入 ```repl``` 
标签来查询子语言模型，以确定您的答案。您的下一步行动： """


def next_action_prompt(query: str, iteration: int = 0, final_answer: bool = False) -> Dict[str, str]:
    if final_answer:
        return {"role": "user",
                "content": "根据您所掌握的所有信息，为用户的查询提供最终答案。"}
    if iteration == 0:
        safeguard = "您尚未与 REPL 环境进行交互或查看您的上下文。您的下一步行动应该是仔细查看，先不要直接给出最终答案。"
        return {"role": "user", "content": safeguard + USER_PROMPT.format(query=query)}
    else:
        return {"role": "user",
                "content": "之前的历史记录是您与 REPL 环境之前的交互记录。 " + USER_PROMPT.format(
                    query=query)}
