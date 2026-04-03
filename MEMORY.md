# MetaEvoAgents - 项目概览

## 1. 项目使命
构建一个基于“谱系（Lineage）”概念的数字文明演化框架。每个 Agent 谱系都是一个独立的自治生命体，拥有自己的指令集（灵魂）、任务空间（Vault）和执行内核（Kernel）。框架的目标是实现 Agent 的完全去中心化和进程化，使其能够独立进化。

## 2. 技术栈
- **后端框架**: FastAPI (Python 3.10+)
- **前端框架**: React + Vite + TypeScript (位于 `web/` 目录)
- **Agent 通信**: 子进程标准输入输出 (subprocess stdin/stdout) 使用 JSON 通信
- **大模型**: OpenAI 兼容 API
- **配置管理**: Pydantic Settings + .env

## 3. 核心架构：纯网关模式 (Pure Gateway)
项目采用“内核即本体”的重构策略：
- **主框架 (Gateway)**: 位于 `app/`，仅作为进程管理器。负责启动、停止子进程并转发 JSON 消息。不感知 Agent 的思考逻辑。
- **内核 (Engine)**: 位于 `app/assets/templates/default/engine.py`，是 Agent 的逻辑大脑。包含 LLM 调用、工具执行（Bash/文件操作）、自省（修改指令集）。
- **谱系目录 (Lineage Workspace)**: 位于 `workspace/lineages/<id>/`，包含：
    - `engine.py`: 该谱系的独立运行逻辑。
    - `vault/`: 私有工作目录。
    - `instruction.md`: 核心指令/灵魂。
    - `memory.log`: 行为日志。
    - `tools/`: 扩展工具集。

## 4. 开发约定
- **解耦原则**: `app/` 下的代码严禁包含具体的 Agent 思考或工具实现逻辑。
- **注释规范 (CRITICAL)**: 在编写、修改 `app/` 或 `kernel/` 的核心代码（尤其是涉及进程交互、JSON 协议、状态转换等复杂逻辑）时，**必须** 编写清晰的中文注释，说明函数意图、参数含义及潜在的侧面影响。这对于长期的文明演化维护至关重要。
- **Standalone 引擎**: `engine.py` 必须能够在其所属目录下通过 `python engine.py` 独立运行。
- **通信协议**:
    - `Gateway -> Engine`: `{"type": "run", "objective": "...", "session_id": "...", "max_steps": n}`
    - `Engine -> Gateway`: `{"type": "step", ...}` / `{"type": "result", ...}` / `{"type": "error", ...}`
- **文件引用**: 在主框架中引用文件必须使用绝对路径或基于 `settings.workspace_root` 的路径。

## 5. 目的地图 (Roadmap)
- [x] 重构主框架为极简网关。
- [x] 实现基于子进程的 Standalone Kernel。
- [x] CLI 支持进程化通信。
- [ ] 完善 `kernel.py` 的自修改（Self-mutation）能力。
- [ ] 增加谱系间的通信总线（Shrine）。
- [ ] 前端适配流式 JSON 显示。

## 6. 最近变更 (Last Changes)
- **2026-04-01**: 完成“纯网关”模式重构，废弃了 `InnerAgent` 类及其相关的类引用。
- **2026-04-01**: 将 `kernel.py` 移至资产模板，谱系创建时会自动分发独立内核。
- **2026-04-01**: 修复了 CLI 在处理新版字典返回格式时的 `AttributeError`。
- **2026-04-02**: 清理 `app/agents/lineage/entity.py` 中的冗余。删除了 `_write_env` 方法及冗余的配置参数，正式移交环境初始化职责给 `Manager.bootstrap`。加强了**开发约定**中关于“必须编写注释”的规范（针对复杂核逻辑与协议转换）。
- **2026-04-02**: 全局将 `kernel.py` 重命名为 `engine.py`，统一了“引擎（Engine）”这一术语，以更好地描述其作为 Agent 逻辑驱动源的角色。
- **2026-04-02**: 实现了基于 **.genome (生殖细胞)** 的自主繁衍机制。Agent 可以通过 `birth` 工具自行复制其 DNA 模板到新目录，并向网关发送 `born_notification` 消息完成“出生登记”。这标志着 Agent 拥有了生理性继承的能力。
- **2026-04-03**: 引入 **“自治状态面板 (Billboard)”** 机制。Agent 会在各自目录下维护 `status.json`，自主声明 `IDLE` 或 `BUSY` 状态。
- **2026-04-03**: 实现 **指令模式 (Dispatch Mode)**。主框架现在可以作为“任务大厅”，通过观察 Agent 的状态面板自动将后台任务分发给最优先工作的空闲 Agent。
- **2026-04-03**: 建立概念区分：**宗祠 (Shrine)** 仅用于归档逝去血脉；**祭坛 (Altar)** 作为实时交互枢纽。
    - `/altar/oracle.md`: 上帝下达的神谕（Markdown 格式）。
    - `/altar/offerings/`: 物品台，上帝分发文件或 Agent 供奉成果。
    - `/altar/prayers.md`: 众生祈祷书。
- **2026-04-03**: 引入 **守护进程模式 (Daemon Mode)**：主框架启动即唤醒所有存活的 Agent，实现零启动延迟与持续自省能力。
- **2026-04-03**: 确立 **合力协作 (Co-evolution)** 愿景：后续将支持多 Agent 共享任务 ID，通过 `altar` 进行分工与成果汇聚。

## 7. 协议更新 (Protocol Updates)
- **Engine -> Gateway**: 
    - `{"type": "status_update", "status": "...", "lineage_id": "...", "timestamp": "..."}`
- **Billboard (Physical File)**:
    - 文件路径: `lineages/<id>/status.json`
    - 结构: `{"status": "IDLE/BUSY", "last_update": "...", "pid": 1234, "objective": "..."}`
- **Altar Interaction Tools**:
    - `offer_to_altar(file_name, description)`: 供奉实物。
    - `collect_from_altar(file_name, is_from_oracle)`: 领取物资或阅读神谕。
    - `pray_to_altar(content)`: 纯文字心愿上报。
