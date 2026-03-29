这份 `README.md` 采用了你确定的 **MetaEvoAgents (MEA)** 命名，融合了**黄帝与嫘祖**的中国神话叙事，并清晰地标注了基于 **Bash 完备性**和**元启发式演化**的工程架构。

你可以直接将其放入项目根目录，Copilot 将会根据这份文档的上下文为你生成对应的 Python 代码和目录结构。

---

```markdown
# MetaEvoAgents (MEA) 🚀
> **基于元启发式演化与 Bash 完备性的数字文明模拟器**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)

## 🏮 项目愿景 (Vision)

**MetaEvoAgents (MEA)** 是一个打破单一 Agent 认知死循环的实验性项目。不同于传统的工具型 Agent，MEA 引入了**“数字文明演化”**的概念：
* **始祖设定**：以 Gen 0 为基础，持续演化。
* **演化逻辑**：通过**合育繁育 (Recombination)** 与 **代际传承 (Lineage)**，Agent 在原生 Bash 环境中自主沉淀技能。
* **天道指引**：用户作为“造物主”，通过“神谕 (Oracles)”发布宏观规划，观察族群在生存压力下的自发演化。

---

## 🏗️ 核心架构 (Architecture)

项目采用 **FastAPI** 作为后端引擎，核心逻辑位于 `/app` 目录，确保“天道引擎”与 Agent 运行环境物理隔离。

### 目录规范
*   `📂 /app`: **天道引擎 (Core Engine)**
    *   `core/`: 元启发式算法实现（变异、交叉、寿命管理）。
    *   `agents/`: Agent 驱动层（LLM 接口、Bash 执行器）。
    *   `altar/`: 祭坛 API（处理前端监控与神谕下达）。
*   `📂 /workspace`: **灵台与归墟 (Runtime & Archive)**
    *   `lineage/`: 当前活跃 Agent 的私有工作空间。
    *   `heritage/`: 跨代传承的 `.sh` 脚本、知识库与文明手册。
    *   `guixu/`: 归墟，存放已“坐化” Agent 的历史记录。

---

## 🧬 演化机制 (Evolutionary Mechanics)

1.  **感知 (Sense)**: Agent 通过执行 `ls`, `cat`, `pwd` 等 Bash 命令感知当前文明进度。
2.  **决策 (Action)**: 基于元启发式策略（如 PSO 寻优逻辑），Agent 尝试最有效的路径来达成神谕目标。
3.  **繁育 (Procreation)**: 当 Gen N 到达寿命阈值，系统通过 LLM 提取父辈的“数字基因”，合成 Gen N+1 的初始认知。
4.  **传承 (Inheritance)**: 子代通过 `/workspace/heritage` 继承先辈开发的工具，实现“站在巨人肩膀上”的进化。

---

## 🛠️ 快速开始 (Quick Start)

### 1. 环境准备
```bash
# 克隆仓库
git clone [https://github.com/your-username/MetaEvoAgents.git](https://github.com/your-username/MetaEvoAgents.git)
cd MetaEvoAgents

# 初始化环境
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. 配置天道 (Config)
在根目录创建 `.env` 文件：
```env
OPENAI_API_KEY=your_key_here
BASE_URL=[https://api.your-provider.com/v1](https://api.your-provider.com/v1)
WORKSPACE_ROOT=./workspace
```

### 3. 启动祭坛 (Start)
```bash
python -m app.main
```

## 🛡️ 安全规范 (Security)
*   所有 Agent 仅限于在映射的 `workspace/` 目录下执行 Bash。
*   严禁 Agent 访问 `app/` 核心代码区。
*   建议在 Docker 容器中运行以实现资源硬隔离。
