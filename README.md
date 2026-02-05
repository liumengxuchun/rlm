# RLM (Recursive Language Model) 项目

## 项目简介

RLM (Recursive Language Model) 是一个基于大语言模型的递归处理框架，专门用于处理超长文本上下文。该项目通过REPL（Read-Eval-Print Loop）环境和递归调用机制，能够有效处理百万级别的文本数据，从中提取和分析关键信息。

## 核心特性

- 🔄 **递归处理能力**：支持超长文本的分块处理和递归分析
- 🧠 **智能上下文理解**：通过子语言模型递归查询，深入理解复杂文档结构
- 🔧 **REPL执行环境**：安全的Python代码执行沙箱，支持动态数据分析
- 📊 **多格式支持**：原生支持Word文档(.docx)解析和其他文本格式
- 🎨 **可视化日志**：彩色终端输出和Rich格式的日志显示
- ⚡ **高效性能**：优化的消息传递和状态管理机制

## 技术架构

```
rlm_xm/
├── rlm/                    # 核心模块
│   ├── execute_env/       # REPL执行环境
│   │   └── rlm_env.py     # REPL环境实现
│   ├── logger/            # 日志系统
│   │   ├── root_logger.py # 彩色根日志
│   │   └── repl_logger.py # REPL执行日志
│   ├── utils/             # 工具函数
│   │   ├── llm.py         # LLM客户端
│   │   ├── prompts.py     # 提示词模板
│   │   └── utils.py       # 通用工具
│   ├── rlm.py             # 抽象基类
│   ├── rlm_repl.py        # 主要实现类
│   └── rlm_sub.py         # 子模型实现
├── main.py                # 入口程序
└── requirements.txt       # 依赖包
```

## 环境要求

- **Python版本**：3.11.x
- **操作系统**：Windows 10/11, macOS, Linux
- **内存建议**：8GB以上（处理大文档时）

## 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone https://github.com/liumengxuchun/rlm.git
cd rlm_xm

# 创建conda环境
conda create -n rlm_env python=3.11

# 激活conda环境
conda activate rlm_env
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

创建 `.env` 文件：

```env
OPENAI_API_KEY=your_api_key_here
MAIN_MODEL=your_model_name
OPENAI_BASE_URL=your_base_url
```

### 4. 运行示例

```bash
python main.py
```

## 核心组件详解

### RLMRepl 类
主入口类，负责协调整个递归处理流程：

```python
from rlm.rlm_repl import RLMRepl

rlm = RLMRepl(
    enable_logging=True,
    max_iterations=10
)
result = rlm.completion(context=context, query=query)
```

**主要参数：**
- `api_key`: LLM API密钥
- `model`: 主模型名称
- `recursive_model`: 递归调用模型
- `max_iterations`: 最大迭代次数
- `enable_logging`: 是否启用日志

### REPL执行环境
安全的Python代码执行沙箱，内置以下功能：
- 限制性内置函数访问
- 文件系统隔离
- 执行时间监控
- 标准输出捕获

### 日志系统
双层日志架构：
- **ColorfulLogger**: 彩色终端输出，跟踪模型交互
- **REPLEnvLogger**: Rich格式显示，展示代码执行过程

## 使用示例

### 处理Word文档

```python
from docx import Document
from rlm.rlm_repl import RLMRepl

# 读取Word文档
def read_word_document(file_path: str) -> str:
    doc = Document(file_path)
    content_parts = []
    
    # 读取段落
    for paragraph in doc.paragraphs:
        content_parts.append(paragraph.text)
    
    # 读取表格
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                content_parts.append(cell.text)
    
    return '\n'.join(content_parts)

# 使用示例
context = read_word_document("文档路径.docx")
rlm = RLMRepl(enable_logging=True, max_iterations=10)
query = "帮我找到这个文档里面关于上传文件的API信息"
result = rlm.completion(context=context, query=query)
print(result)
```

### 处理长文本

```python
# 生成大规模测试数据
def generate_massive_context(num_lines: int = 1_000_000) -> str:
    import random
    random_words = ["blah", "random", "text", "data", "content"]
    lines = []
    for _ in range(num_lines):
        num_words = random.randint(3, 8)
        line_words = [random.choice(random_words) for _ in range(num_words)]
        lines.append(" ".join(line_words))
    
    # 插入关键信息
    magic_position = random.randint(400000, 600000)
    lines[magic_position] = "The magic number is 1298418"
    
    return "\n".join(lines)

# 使用大规模上下文
context = generate_massive_context()
result = rlm.completion(context=context, query="找到magic number")
```

## 提示词设计

系统使用精心设计的中文提示词，指导模型：

1. **初始分析**：检查上下文内容和结构
2. **分块策略**：制定合理的文本分割方案
3. **递归查询**：使用子模型处理各个片段
4. **结果整合**：汇总分析结果得出最终答案

## 安全特性

- ✅ 禁用危险内置函数（eval, exec等）
- ✅ 临时目录隔离执行环境
- ✅ 输出长度限制防止溢出
- ✅ 异常处理和错误恢复

## 性能优化

- **消息压缩**：自动截断过长的中间结果
- **缓存机制**：避免重复计算
- **并发控制**：线程安全的执行环境
- **资源清理**：自动释放临时文件

## 开发指南

### 项目结构扩展

```python
# 自定义REPL环境
class CustomREPLEnv(REPLEnv):
    def __init__(self, custom_functions=None):
        super().__init__()
        if custom_functions:
            self.globals.update(custom_functions)

# 自定义日志处理器
class CustomLogger(ColorfulLogger):
    def log_custom_event(self, event_type: str, data: dict):
        # 实现自定义日志逻辑
        pass
```

### 测试建议

```python
# 单元测试示例
def test_basic_completion():
    rlm = RLMRepl(max_iterations=5)
    context = "简单的测试文本"
    query = "这是什么？"
    result = rlm.completion(context, query)
    assert isinstance(result, str)
    assert len(result) > 0
```

## 故障排除

### 常见问题

1. **API密钥错误**
   ```
   ValueError: 缺少LLM必要参数
   ```
   解决：检查.env文件配置

2. **模型超时**
   ```
   TimeoutError: 请求超时
   ```
   解决：增加timeout参数或检查网络连接

3. **内存不足**
   ```
   MemoryError: 内存溢出
   ```
   解决：减少max_iterations或分批处理

### 调试技巧

```python
# 启用详细日志
rlm = RLMRepl(enable_logging=True)

# 查看中间状态
print(f"当前迭代次数: {iteration}")
print(f"消息历史长度: {len(messages)}")
```

## 贡献指南

欢迎提交Issue和Pull Request！

### 开发环境设置

```bash
# 安装开发依赖
pip install pytest black flake8

# 运行测试
pytest tests/

# 代码格式化
black .
```

## 许可证

MIT License

## 联系方式

如有问题，请提交GitHub Issue或联系项目维护者。