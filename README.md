# MetaEvoAgents (MEA) 🚀

> **基于宗祠（Shrine）资产固化与元启发式演化的数字文明模拟器**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)

---

## 项目愿景

**MetaEvoAgents (MEA)** 是一个打破单一 Agent 认知死循环的实验性项目。不同于传统的工具型 Agent，MEA 引入了**"数字文明演化"**的概念：

- **始祖设定**：以 Gen 0 为基础，持续演化。
- **宗祠固化**：每个 Agent 的身份、灵魂与资产在磁盘上持久化，不随进程存亡。
- **演化逻辑**：通过**合育繁育 (Recombination)** 与 **宗祠传承 (Shrine)**，Agent 在原生 Bash 环境中自主沉淀技能。

### 指令模式 vs 天道指引

MEA 在开发过程中采用**指令模式**工作：

- **指令 (Instruction)**：用户（造物主）直接向 ShrineKeeper 下达具体任务，例如"写一个快速排序"。这是当前已实施的工作模式。

**天道指引 (Divine Guidance)** 是 MEA 的长期愿景：

- **指引 (Oracle)**：用户作为"造物主"，通过神谕发布宏观规划，观察族群在生存压力下的自发演化与文明演进。指引不指定具体实现路径，而是设定目标、约束与演化方向，由 Agent 自主决策与协作。
- 指引与指令的本质区别：**指令**告诉 Agent"怎么做"，**指引**告诉 Agent"为什么要做以及在什么方向上做"。

> 目前天道指引尚未实施，处于概念设计阶段，待 Agent 具备一定自主性与协作能力后再行引入。

---

## 核心理念

传统的 Agent 系统以**纯内存对象**运行——进程结束则 Agent 消亡，所有上下文、记忆、产出随风而逝。

MEA 引入了**宗祠（Shrine）**范式：

- 每个 Agent 拥有**物理磁盘上的根目录**，对应现实中的"宗祠"。
- 身份（UID）、灵魂（Prompt）、记忆（Logs）、资产（Vault）全部**固化在磁盘**，不随进程存亡。
- Agent 重启后通过路径"降世"，自动恢复完整的上下文与家底。

---

## 核心架构

项目采用 **FastAPI** 作为后端引擎，核心逻辑位于 `/app` 目录，确保"天道引擎"与 Agent 运行环境物理隔离。

```
MetaEvoAgents/
├── app/
│   ├── agents/                   # Agent 驱动层
│   │   ├── agent.py              # ShrineKeeper / ShrineRegistry / Agent
│   │   ├── tools.py              # 工具系统（vault 绑定）
│   │   ├── llm.py                # LLM 接口
│   │   └── __init__.py           # 统一导出
│   ├── assets/
│   │   └── templates/
│   │       └── default/          # Shrine 模板包（降世原型）
│   ├── core/
│   │   └── config.py             # 配置管理
│   └── routes/                   # FastAPI 路由
├── cli.py                         # Shrine 驱动的 CLI 入口
├── workspace/
│   ├── shrine/                  # 宗祠区（ShrineKeeper 存储）
│   ├── academy/                 # 族学区（跨代传承的知识库）
│   └── lineage/                 # 族谱区（遗留 Agent 存储）
├── requirements.txt
└── .env
```

### 目录语义

| 路径 | 语义 | 说明 |
|------|------|------|
| `app/` | 天道引擎 | 核心代码区，Agent 不可访问 |
| `app/agents/` | 宗祠守护者层 | Agent 驱动、LLM 接口、工具系统 |
| `app/assets/templates/default/` | 族学原型 | 新 Shrine 降世时的模板包 |
| `workspace/shrine/` | 宗祠区 | 所有活跃 Shrine 的物理存储 |
| `workspace/academy/` | 族学区 | 跨代传承的脚本、知识库与文明手册 |
| `workspace/lineage/` | 族谱区 | 遗留 Agent 的私有工作空间 |

---

## 宗祠结构（The Shrine Structure）

每个 Shrine 遵循以下物理结构：

```
workspace/shrine/{shrine_id}/
├── .metadata.json      # 身份档案：UID、创建时间、模板来源
├── instruction.md      # 魂魄模板：System Prompt（Agent 可自主修改）
├── memory.log          # 核心记忆：出生记录、自省快照、演化履历
├── vault/             # 资产区：Agent 所有运行时产出
└── logs/              # 会话日志：每次 run() 的执行轨迹
```

| 文件 | 作用 | 可被 Agent 修改 |
|------|------|----------------|
| `.metadata.json` | 不可变身份档案 | 否 |
| `instruction.md` | Agent 的 System Prompt | **是**（通过 `update_instruction` 工具） |
| `memory.log` | 累积记忆快照 | 是（由系统与 Agent 共同追加） |
| `vault/` | 作业目录，`execute_bash` 的 `cwd 被锁定于此 | 是 |
| `logs/` | 自动管理的会话记录 | 否（系统生成） |

---

## 核心类（Core Classes）

### `ShrineKeeper` — 宗祠守护者

对应 Agent 的核心实现类。**禁止随机初始化**，必须接受一个 `shrine_path`。

```python
from app.agents.agent import ShrineKeeper

keeper = ShrineKeeper("workspace/shrine/Shrine-01")
# 若路径不存在，自动从 app/assets/templates/default/ 拷贝并"降世"
```

#### 生命周期

1. **`__init__(shrine_path)`** — 接受路径，非空检查
2. **`_descend_from_template()`** — 自愈加载：路径不存在时从模板初始化，写入出生记录到 `memory.log`
3. **`_load_identity()`** — 读取 `instruction.md` 构建 `system_prompt`
4. **`_lock_permissions()`** — 锁定 `CodeTools.workspace` 到 `vault/`，注册 Agent 工具
5. **`_introspect()`** — 执行 `ls vault/` 感知自己的家底，写入 `memory.log`
6. **`run(objective, ...)`** — 执行任务，会话结束时追加日志到 `logs/`

#### 实例属性

```python
keeper.system_prompt   # 当前生效的 System Prompt（来自磁盘 instruction.md）
keeper.vault_path      # 资产目录路径
keeper.shrine_path     # 宗祠根目录路径
keeper.metadata        # 身份档案 dict
keeper.run("目标", max_steps=10, streaming=True)
```

### `ShrineRegistry` — 宗祠登记簿

管理多个 Shrine 的加载与缓存。

```python
from app.agents.agent import ShrineRegistry

reg = ShrineRegistry()
keeper = reg.load("Shrine-01")  # 首次加载则降世
keeper = reg.load("Shrine-01")  # 后续加载命中缓存
reg.exists("Shrine-01")         # 检查物理路径是否存在
reg.all()                        # 返回 {shrine_id: ShrineKeeper}
```

### `Agent` — 遗留兼容类

保留原有的随机初始化 `Agent` 类，不使用 Shrine 体系。FastAPI 路由等旧代码不受影响。

---

## 演化机制（Evolutionary Mechanics）

1. **感知 (Sense)**: ShrineKeeper 通过执行 `ls`, `cat`, `pwd` 等 Bash 命令感知当前文明进度。
2. **决策 (Action)**: 基于元启发式策略（如 PSO 寻优逻辑），Agent 尝试最有效的路径来达成神谕目标。
3. **繁育 (Procreation)**: 当 Gen N 到达寿命阈值，系统通过 LLM 提取父辈的"数字基因"，合成 Gen N+1 的初始认知。
4. **传承 (Inheritance)**: 子代通过 `workspace/academy` 继承先辈开发的工具，实现"站在巨人肩膀上"的进化。

---

## 工具系统（Tools）

位于 `app/agents/tools.py`。每个工具都**强制在 Shrine 的 `vault/` 下执行**。

| 工具名 | 描述 |
|--------|------|
| `execute_bash` | 在 `vault/` 下执行 Bash 命令（cwd 锁定） |
| `read_file` | 读取文件内容 |
| `write_file` | 写入文件到 `vault/` |
| `list_files` | 列出 `vault/` 目录 |
| `search_files` | 在 `vault/` 下全文搜索 |
| `update_instruction` | 重写 `instruction.md`，演化 Agent 的灵魂 |

Agent 级别的工具通过 `register_agent_tool(name, func)` 注册，实现工具的 Shrine 隔离。

---

## CLI 使用

```bash
python cli.py
```

### 命令语法

```
# 指定 Shrine 执行任务
Shrine-01: 写一个快速排序算法

# 切换当前 Shrine
/shrine Shrine-02

# 列出所有已加载的 Shrine
/list

# 查看当前 Shrine 的 vault 内容
/vault

# 退出
exit / quit
```

### 启动输出示例

```
Loaded shrine: Shrine-01 (UID: 3b81a32d)
Loaded shrine: Shrine-02 (UID: 5697dfa2)
==================================================
MetaEvoAgents CLI - 宗祠驱动的多轮对话
用法:
  /shrine <id>    切换执行 Shrine
  /list            列出所有宗祠
  /vault           查看当前 Shrine 的 vault
  exit 或 quit     退出
==================================================
当前 Shrine: Shrine-01
```

---

## 快速开始

### 1. 环境准备

```bash
# 克隆仓库
git clone https://github.com/your-username/MetaEvoAgents.git
cd MetaEvoAgents

# 初始化环境
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. 配置天道

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
| `templates_root` | `app/assets/templates/default` | Shrine 模板包路径 |
| `shrine_root` | `workspace_root/shrine` | 宗祠区根路径（计算属性） |
| `academy_root` | `workspace_root/academy` | 族学区根路径（计算属性） |
| `lineage_root` | `workspace_root/lineage` | 族谱区根路径（计算属性） |
| `openai_api_key` | `""` | LLM API Key |
| `openai_url` | `https://api.openai.com/v1` | API 端点 |
| `openai_model_name` | `gpt-4o-mini` | 模型名称 |

通过 `.env` 文件覆盖。

### 3. 启动祭坛

```bash
# CLI 模式（Shrine 驱动）
python cli.py

# API 模式
python -m app.main
```

### 4. 在 CLI 中执行

```
Shrine-01: 用 Python 写一个计算器
Shrine-02: 分析这段代码的性能
/shrine Shrine-01
```

---

## API 接口

FastAPI 服务由 `app/main.py` 驱动，路由定义在 `app/routes/`。

| 端点 | 方法 | 说明 |
|------|------|------|
| `/agent/chat` | POST | 发起一轮 Agent 对话 |
| `/agent/health` | GET | 健康检查 |

---

## 安全规范

- 所有 Agent 仅限于在映射的 `workspace/shrine/{id}/vault/` 目录下执行 Bash。
- 严禁 Agent 访问 `app/` 核心代码区。
- 建议在 Docker 容器中运行以实现资源硬隔离。
