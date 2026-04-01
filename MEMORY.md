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
- **内核 (Kernel)**: 位于 `app/assets/templates/default/kernel.py`，是 Agent 的逻辑大脑。包含 LLM 调用、工具执行（Bash/文件操作）、自省（修改指令集）。
- **谱系目录 (Lineage Workspace)**: 位于 `workspace/lineages/<id>/`，包含：
    - `kernel.py`: 该谱系的独立运行逻辑。
    - `vault/`: 私有工作目录。
    - `instruction.md`: 核心指令/灵魂。
    - `memory.log`: 行为日志。
    - `tools/`: 扩展工具集。

## 4. 开发约定
- **解耦原则**: `app/` 下的代码严禁包含具体的 Agent 思考或工具实现逻辑。
- **Standalone 内核**: `kernel.py` 必须能够在其所属目录下通过 `python kernel.py` 独立运行。
- **通信协议**:
    - `Gateway -> Kernel`: `{"type": "run", "objective": "...", "session_id": "...", "max_steps": n}`
    - `Kernel -> Gateway`: `{"type": "step", ...}` / `{"type": "result", ...}` / `{"type": "error", ...}`
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
