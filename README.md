# MetaEvoAgents (MEA) 🚀

> **基于 Lineage 磁盘锚定与内核自举的数字文明模拟器**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)

---

## 项目愿景

**MetaEvoAgents (MEA)** 是一个打破单一 Agent 认知死循环的实验性项目。不同于传统的工具型 Agent，MEA 引入了**"数字文明演化"**的概念：

- **始祖设定**：以 Gen 0 为基础，持续演化。
- **Lineage 锚定**：每个 Agent 的身份、灵魂与资产在磁盘上持久化，不随进程存亡。
- **内核自举**：每个 Lineage 目录自带 `kernel.py`，可脱离主框架独立运行。
- **演化逻辑**：通过**合育繁育 (Recombination)** 与 **Lineage 传承**，Agent 在原生 Bash 环境中自主沉淀技能。

### 指令模式 vs 天道指引

MEA 在开发过程中采用**指令模式**工作：

- **指令 (Instruction)**：用户（造物主）直接向 LineageAgent 下达具体任务，例如"写一个快速排序"。这是当前已实施的工作模式。

**天道指引 (Divine Guidance)** 是 MEA 的长期愿景：

- **指引 (Oracle)**：用户作为"造物主"，通过神谕发布宏观规划，观察族群在生存压力下的自发演化与文明演进。指引不指定具体实现路径，而是设定目标、约束与演化方向，由 Agent 自主决策与协作。
- 指引与指令的本质区别：**指令**告诉 Agent"怎么做"，**指引**告诉 Agent"为什么要做以及在什么方向上做"。

> 目前天道指引尚未实施，处于概念设计阶段，待 Agent 具备一定自主性与协作能力后再行引入。

---

## 核心理念

传统的 Agent 系统以**纯内存对象**运行——进程结束则 Agent 消亡，所有上下文、记忆、产出随风而逝。

MEA 引入了 **Lineage** 范式：

- 每个 Agent 拥有**物理磁盘上的根目录**（Lineage 空间），对应现实中的"族谱"。
- 身份（UID）、灵魂（Prompt）、记忆（Memory）、资产（Vault）、内核（Kernel）全部**固化在磁盘**，不随进程存亡。
- Agent 重启后通过路径重新实例化，自动恢复完整的上下文与家底。
- 每个 Lineage 自带 `kernel.py`，可在任意有 Python 环境的机器上独立运行。

---

## 核心架构

项目采用 **FastAPI** 作为后端引擎，核心逻辑位于 `/app` 目录，确保"天道引擎"与 Agent 运行环境物理隔离。

```
MetaEvoAgents/
├── app/
│   ├── agents/                   # Agent 驱动层
│   │   ├── inner/              # Inner 子系统（自包含）
│   │   │   ├── agent.py       # InnerAgent
│   │   │   ├── tools.py       # 工具系统
│   │   │   ├── llm.py         # LLM 接口
│   │   │   └── __init__.py
│   │   ├── lineage/            # Lineage 子系统（演化体系）
│   │   │   ├── entity.py      # LineageAgent（纯 launcher）
│   │   │   ├── manager.py     # LineageManager（生命周期管理）
│   │   │   └── __init__.py
│   │   ├── result.py           # AgentResult + message_to_dict（共享）
│   │   └── __init__.py        # 统一导出
│   ├── assets/
│   │   └── templates/
│   │       └── default/        # Lineage 模板包（含 kernel.py）
│   ├── core/
│   │   └── config.py          # 配置管理
│   └── routes/                # FastAPI 路由
├── cli.py                       # Lineage 驱动的 CLI 入口
├── workspace/
│   ├── lineages/               # Lineage 区（演化体系，持久化）
│   ├── academy/                # 族学区（跨代传承）
│   └── inner/                  # 框架内部（InnerAgent 临时目录）
├── requirements.txt
└── .env
```

---

## Lineage 结构（The Lineage Structure）

每个 Lineage 遵循以下物理结构：

```
workspace/lineages/{lineage_id}/
├── .metadata.json      # 身份档案：UID、创建时间、模板来源
├── instruction.md      # 灵魂模板：System Prompt（Agent 可自主修改）
├── kernel.py         # 独立内核：动态加载 tools/，可脱离主框架独立运行
├── memory.log        # 核心记忆：出生记录、自省快照、演化履历
├── tools/           # 工具实现：Agent 的工具定义（自治，框架零认知）
│   ├── __init__.py  # TOOL_DEFINITIONS 工具清单
│   ├── bash.py       # execute_bash
│   ├── file_ops.py   # read_file / write_file / list_files
│   ├── search.py     # search_files
│   └── instruction.py # update_instruction
├── vault/           # 资产区：Agent 所有运行时产出
└── logs/           # 会话日志：每次 run() 的执行轨迹
```

| 文件 | 作用 | 可被 Agent 修改 |
|------|------|----------------|
| `.metadata.json` | 不可变身份档案 | 否 |
| `instruction.md` | Agent 的 System Prompt | **是**（通过 `update_instruction` 工具） |
| `kernel.py` | 独立内核，可 `python kernel.py` 直接运行 | 否（模板固定） |
| `tools/` | 工具实现，框架零认知 | **是**（Agent 可自主增删工具） |
| `memory.log` | 累积记忆快照 | 是（由系统与 Agent 共同追加） |
| `vault/` | 作业目录，`execute_bash` 的 `cwd` 被锁定于此 | 是 |
| `logs/` | 自动管理的会话记录 | 否（系统生成） |

### 内核自举（Kernel Bootstrap）

`kernel.py` 是 Lineage 的自包含运行核心，位于 Lineage 目录内部。它具备以下特性：

- **零框架依赖**：只依赖 Python 标准库 + `openai` SDK + `python-dotenv`
- **动态工具加载**：运行时从 `tools/` 目录动态加载工具实现，不预设工具列表
- **实时灵魂读取**：每次执行工具后重新读取 `instruction.md`，感知自身变化
- **独立运行**：`python kernel.py "目标"` 或 `python kernel.py` 交互模式

```bash
# 直接运行 Lineage（绕过主框架）
cd workspace/lineages/Lineage-01
python kernel.py "写一个快速排序"

# 交互模式
python kernel.py
```

---

## 核心类（Core Classes）

### `LineageAgent` — Lineage 代理类（框架侧）

主框架侧的核心类。**禁止随机初始化**，必须接受一个 `lineage_root`。

```python
from app.agents import LineageAgent

agent = LineageAgent("workspace/lineages/Lineage-01")
# 若路径不存在，自动从 app/assets/templates/default/ 拷贝并"降世"
```

#### 生命周期

1. **`__init__(lineage_root)`** — 接受路径，非空检查
2. **`_bootstrap_from_template()`** — 自愈加载：路径不存在时从模板初始化，写入出生记录到 `memory.log`
3. **`_load_identity()`** — 实时读取 `instruction.md` 构建 `system_prompt`（无缓存）
4. **`_introspect()`** — 感知 vault 内容，写入 `memory.log`
5. **`run(objective, ...)`** — **加载 workspace 中的 kernel 并委托执行**，框架零认知工具实现

#### Sync-to-Disk 契约

`LineageAgent` 作为 launcher 仅同步身份档案，工具执行由 kernel 内部处理：

```python
def sync_to_disk(self):
    self._write_metadata(self.metadata)
```

#### 实例属性

```python
agent.lineage_root    # Lineage 根目录路径
agent.lineage_id     # Lineage 标识符
agent.vault_path     # 资产目录路径
agent.system_prompt  # 当前生效的 System Prompt（实时读取）
agent.metadata       # 身份档案 dict
agent.kernel_path    # kernel.py 路径
agent.run("目标", max_steps=10, streaming=True)
```

### `LineageManager` — Lineage 登记簿

管理多个 Lineage 的加载与缓存。

```python
from app.agents.agent import LineageManager

mgr = LineageManager()
agent = mgr.load("Lineage-01")   # 首次加载则降世
agent = mgr.load("Lineage-01")   # 后续加载命中缓存
mgr.exists("Lineage-01")          # 检查物理路径是否存在
mgr.all()                         # 返回 {lineage_id: LineageAgent}
```

### `InnerAgent` — 框架内部 Agent

框架内部使用，不参与演化体系。随机 session_id，无持久化，FastAPI 路由使用此类。

```python
from app.agents import InnerAgent

agent = InnerAgent()
result = agent.run("目标")
```

---

## 演化机制（Evolutionary Mechanics）

1. **感知 (Sense)**: LineageAgent 通过执行 `ls`, `cat`, `pwd` 等 Bash 命令感知当前文明进度。
2. **决策 (Action)**: 基于元启发式策略（如 PSO 寻优逻辑），Agent 尝试最有效的路径来达成神谕目标。
3. **繁育 (Procreation)**: 当 Gen N 到达寿命阈值，系统通过 LLM 提取父辈的"数字基因"，合成 Gen N+1 的初始认知。
4. **传承 (Inheritance)**: 子代通过 `workspace/academy` 继承先辈开发的工具，实现"站在巨人肩膀上"的进化。

---

## 工具系统（Tools）

Lineage 的工具定义在 `workspace/lineages/{id}/tools/`，由 `kernel.py` 动态加载。框架对工具**零认知**，真正实现自治。

| 工具名 | 描述 |
|--------|------|
| `execute_bash` | 在 `vault/` 下执行 Bash 命令（cwd 锁定） |
| `read_file` | 读取文件内容 |
| `write_file` | 写入文件到 `vault/` |
| `list_files` | 列出 `vault/` 目录 |
| `search_files` | 在 `vault/` 下全文搜索 |
| `update_instruction` | 重写 `instruction.md`，演化 Agent 的灵魂 |

`app/agents/inner/tools.py` 是 `InnerAgent` 的工具实现，与 Lineage 工具系统完全独立。

---

## CLI 使用

```bash
python cli.py
```

### 命令语法

```
# 指定 Lineage 执行任务
Lineage-01: 写一个快速排序算法

# 切换当前 Lineage
/lineage Lineage-02

# 列出所有已加载的 Lineage
/list

# 查看当前 Lineage 的 vault 内容
/vault

# 退出
exit / quit
```

### 启动输出示例

```
Loaded lineage: Lineage-01 (UID: 76106f41)
Loaded lineage: Lineage-02 (UID: c8283d02)
==================================================
MetaEvoAgents CLI - Lineage 驱动的多轮对话
用法:
  /lineage <id>  切换执行 Lineage
  /list           列出所有 Lineage
  /vault          查看当前 Lineage 的 vault
  exit 或 quit    退出
==================================================
当前 Lineage: Lineage-01
```

---

## 快速开始

### 1. 环境准备

```bash
git clone https://github.com/your-username/MetaEvoAgents.git
cd MetaEvoAgents
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. 配置

在根目录创建 `.env` 文件：

```env
OPENAI_API_KEY=your_key_here
BASE_URL=https://api.your-provider.com/v1
WORKSPACE_ROOT=./workspace
TEMPLATES_ROOT=./app/assets/templates/default
```

`app/core/config.py` 中的 `Settings` 类配置项：

| 字段 | 默认值 | 说明 |
|------|--------|------|
| `workspace_root` | `./workspace` | 工作区根目录 |
| `templates_root` | `app/assets/templates/default` | Lineage 模板包路径 |
| `lineages_root` | `workspace_root/lineages` | Lineage 区根路径（计算属性） |
| `academy_root` | `workspace_root/academy` | 族学区根路径（计算属性） |
| `inner_root` | `workspace_root/inner` | 框架内部根路径（计算属性） |
| `openai_api_key` | `""` | LLM API Key |
| `openai_url` | `https://api.openai.com/v1` | API 端点 |
| `openai_model_name` | `gpt-4o-mini` | 模型名称 |

### 3. 启动

```bash
# CLI 模式（Lineage 驱动）
python cli.py

# API 模式
python -m app.main

# 直接运行某个 Lineage（绕过主框架）
cd workspace/lineages/Lineage-01
python kernel.py "写一个快速排序"
```

### 4. 在 CLI 中执行

```
Lineage-01: 用 Python 写一个计算器
Lineage-02: 分析这段代码的性能
/lineage Lineage-01
```

---

## API 接口

FastAPI 服务由 `app/main.py` 驱动，路由定义在 `app/routes/`。

| 端点 | 方法 | 说明 |
|------|------|------|
| `/agent/chat` | POST | 发起一轮 Agent 对话 |
| `/agent/health` | GET | 健康检查 |

---

## 开发规范

项目使用 **ruff** 进行代码检查与格式化（配置见 `pyproject.toml`）。

```bash
# 安装 ruff
pip install ruff

# 检查
ruff check .

# 自动修复
ruff check --fix .

# 格式化
ruff format .

# 推荐：lint + format
ruff check . && ruff format .
```

**延迟加载抑制**：`PLC0415`（import 应在顶层）是开启的检查项。当代码中有合理的函数内 import（如动态加载）时，使用以下方式标记：

**方法 1 — 行级抑制（推荐）**
```python
from app.agents.inner.llm import LLMClient  # noqa: PLC0415
```

**方法 2 — 文件级抑制**
```python
# ruff: noqa: PLC0415
from app.agents.inner.llm import LLMClient
```

> 注：`I001`（import 排序）已加入忽略列表，函数内 import 是延迟加载的合理模式。

---

## 安全规范

- 所有 Agent 仅限于在映射的 `workspace/lineages/{id}/vault/` 目录下执行 Bash。
- `kernel.py` 独立运行时会读取 `.env` 中的 `OPENAI_API_KEY`，确保 `.env` 文件安全。
- 严禁 Agent 访问 `app/` 核心代码区。
- 建议在 Docker 容器中运行以实现资源硬隔离。
