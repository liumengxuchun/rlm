"""
RLM REPL 客户端的实用工具函数。
"""

import re
from typing import List, Dict, Optional, Tuple, Any


def find_code_blocks(text: str) -> List[str]:
    """
    查找文本中用三重反引号包装的 REPL 代码块并返回内容列表。
    如果未找到代码块则返回 None。
    """
    pattern = r'```repl\s*\n(.*?)\n```'
    results = []

    for match in re.finditer(pattern, text, re.DOTALL):
        code_content = match.group(1).strip()
        results.append(code_content)

    return results


def find_final_answer(text: str) -> Optional[Tuple[str, str]]:
    """
    查找响应中的 FINAL(...) 或 FINAL_VAR(...) 语句并返回 (类型, 内容)。
    如果未找到任何模式则返回 None。
    """
    # Check for FINAL_VAR pattern first - must be at start of line
    final_var_pattern = r'^\s*FINAL_VAR\((.*?)\)'
    match = re.search(final_var_pattern, text, re.MULTILINE | re.DOTALL)
    if match:
        return 'FINAL_VAR', match.group(1).strip()

    # Check for FINAL pattern - must be at start of line
    final_pattern = r'^\s*FINAL\((.*?)\)'
    match = re.search(final_pattern, text, re.MULTILINE | re.DOTALL)
    if match:
        return 'FINAL', match.group(1).strip()

    return None


def add_execution_result_to_messages(messages: List[Dict[str, str]],
                                     code: str,
                                     result: str,
                                     max_character_length: int = 100000,
                                     ) -> List[Dict[str, str]]:
    """
    将代码执行结果添加到对话消息中。

    Args:
        messages: 当前对话消息
        code: 已执行的代码
        result: 代码执行结果
        max_character_length: 结果的最大字符长度

    Returns:
        更新的消息列表
    """
    # Truncate result if it exceeds 100k characters
    if len(result) > max_character_length:
        result = result[:max_character_length] + "..."

    # Add the code execution result
    execution_message = {
        "role": "user",
        "content": f"代码 执行:\n```python\n{code}\n```\n\nREPL 输出:\n{result}"
    }
    messages.append(execution_message)
    return messages


def format_execution_result(
        stdout: str,
        stderr: str,
        locals_dict: Dict[str, Any],
        truncate_length: int = 100
) -> str:
    """
    将执行结果格式化为字符串以供显示。

    Args:
        stdout: 执行的标准输出
        stderr: 执行的标准错误输出
        locals_dict: 执行后的局部变量
        truncate_length: 每个变量显示的最大长度
    """
    result_parts = []

    if stdout:
        result_parts.append(f"\n{stdout}")

    if stderr:
        result_parts.append(f"\n{stderr}")

    # Show some key variables (excluding internal ones)
    important_vars = {}
    for key, value in locals_dict.items():
        if not key.startswith('_') and key not in ['__builtins__', '__name__', '__doc__']:
            try:
                # Only show simple types or short representations
                if isinstance(value, (str, int, float, bool, list, dict, tuple)):
                    if isinstance(value, str) and len(value) > truncate_length:
                        important_vars[key] = f"'{value[:truncate_length]}...'"
                    else:
                        important_vars[key] = repr(value)
            except (TypeError, ValueError, AttributeError):
                important_vars[key] = f"<{type(value).__name__}>"

    if important_vars:
        result_parts.append(f"REPL variables: {list(important_vars.keys())}\n")

    return "\n\n".join(result_parts) if result_parts else "No output"


def execute_code(repl_env, code: str, repl_env_logger, logger) -> str:
    """
    在 REPL 环境中执行代码并返回格式化的结果。

    参数:
        repl_env: REPL 环境
        code: 要执行的 Python 代码
        repl_env_logger: 执行环境的日志记录器
        logger: 主日志记录器
        state_logger: 可选的状态日志记录器

    返回:
        格式化的执行结果
    """
    try:
        result = repl_env.code_execution(code)

        formatted_result = format_execution_result(
            result.stdout, result.stderr, result.locals
        )
        repl_env_logger.log_execution(code, result.stdout, result.stderr, result.execution_time)
        repl_env_logger.display_last()

        # 打印工具执行到根目录
        logger.log_tool_execution("CODE_EXECUTION", formatted_result)

        return formatted_result

    except Exception as e:
        error_msg = f"执行代码时出错: {str(e)}"
        return error_msg


def process_code_execution(
        response: str,
        messages: List[Dict[str, str]],
        repl_env,
        repl_env_logger,
        logger,
) -> List[Dict[str, str]]:
    """
    处理来自模型响应的代码执行。如果递归被禁用，我们应该
    返回整个 stdout 块。

    参数:
        response: 包含代码的模型响应
        messages: 当前对话消息
        repl_env: REPL 环境
        repl_env_logger: 执行环境的日志记录器
        logger: 主日志记录器

    返回:
        更新的消息列表
    """
    # 从响应中提取代码块
    code_blocks = find_code_blocks(response)

    if code_blocks:
        # 执行每个代码块
        for code in code_blocks:
            execution_result = execute_code(repl_env, code, repl_env_logger, logger)

            # 将执行结果添加到对话中
            messages = add_execution_result_to_messages(
                messages, code, execution_result,
            )

    return messages


def check_for_final_answer(response: str, repl_env, logger) -> Optional[str]:
    """检查响应是否包含最终答案。"""
    result = find_final_answer(response)
    if result is None:
        return None

    answer_type, content = result
    variable_name = None  # 初始化变量

    if answer_type == 'FINAL':
        return content
    elif answer_type == 'FINAL_VAR':
        # 直接从 REPL 环境获取变量
        try:
            # 去除变量名中的空格、引号和换行符
            variable_name = content.strip().strip('"').strip("'").strip('\n').strip('\r')

            # 检查变量是否存在于 REPL 环境的局部变量中
            if variable_name in repl_env.locals:
                variable_value = repl_env.locals[variable_name]
                return str(variable_value)
            else:
                error_msg = f"变量 '{variable_name}' 在 REPL 环境中未找到"
                logger.log_tool_execution("FINAL_VAR", error_msg)
                return None
        except Exception as e:
            error_msg = f"检索变量 '{variable_name}' 时出错: {str(e)}"
            print('错误信息', error_msg)
            logger.log_tool_execution("FINAL_VAR", error_msg)
            return None
    else:
        # 处理未知的 answer_type
        error_msg = f"未知的答案类型 '{answer_type}': {content}"
        logger.log_tool_execution("UNKNOWN_ANSWER_TYPE", error_msg)
        return None


def convert_context_for_repl(context):
    """
    将 REPL 上下文转换为某些内容
    """
    if isinstance(context, dict):
        context_data = context
        context_str = None
    elif isinstance(context, str):
        context_data = None
        context_str = context
    elif isinstance(context, list):
        if len(context) > 0 and isinstance(context[0], dict):
            if "content" in context[0]:
                context_data = [msg.get("content", "") for msg in context]
            else:
                context_data = context
            context_str = None
        else:
            context_data = context
            context_str = None
    else:
        context_data = context
        context_str = None

    return context_data, context_str
