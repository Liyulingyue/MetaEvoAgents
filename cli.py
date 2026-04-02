import sys
import random
import json
import threading
from datetime import datetime
from app.agents.lineage import LineageManager


class AgentCLI:
    def __init__(self):
        self.lineage_manager = LineageManager()
        self.active_lineage = None  # 初始保持为 None，即由 /auto 逻辑接管
        self.dispatch_mode = "random"  # 自动分配模式：random, latest
        self.run_type = "SYNC"  # 运行模式：SYNC (同步等待), ASYNC (后台并发)
        self.background_tasks = []
        self._load_lineages()
        self.welcome()

    def _load_lineages(self):
        # 扫描 lineages 目录下的所有子文件夹
        lineages_dir = self.lineage_manager.settings.workspace_root / "lineages"
        
        # 加载所有已发现的 Lineage
        for path in lineages_dir.iterdir():
            if path.is_dir() and not path.name.startswith("."):
                lineage_id = path.name
                agent = self.lineage_manager.load(lineage_id)
                print(f"Loaded lineage: {lineage_id} (UID: {agent.metadata['uid']})")
        
        print("已进入自动分配模式 (AUTO)")

    def welcome(self):
        print("=" * 60)
        print("MetaEvoAgents CLI - Lineage 驱动的多元进化模拟")
        print("模式切换:")
        print("  /sync           [SYNC] 同步模式：发送指令后等待 Agent 结果")
        print("  /async          [ASYNC] 异步模式：发送后立即返回，Agent 在后台运行")
        print("控制指令:")
        print("  /lineage <id>   手动指定执行某个 Lineage")
        print("  /auto           开启自动模式 (解绑当前固定 Agent)")
        print("  /mode <mode>    切换分配模式 (random, latest)")
        print("  /list           列出所有活跃 Lineage")
        print("  /tasks          查看后台运行中的任务")
        print("世界指令:")
        print("  /see_prayer     阅读祈祷书")
        print("  /write_revelation <msg> 降下神谕")
        print("  /reset          重置整个 workspace")
        print("  /exit           退出")
        print("-" * 60)
        status = self.active_lineage if self.active_lineage else "AUTO (未绑定)"
        print(f"当前模式: [{self.run_type}] | 活跃 Agent: {status}")
        print("=" * 60)
        print()

    def parse_input(self, raw: str):
        raw = raw.strip()
        if not raw:
            return None, None

        if raw.startswith("/lineage "):
            return ("lineage", raw[len("/lineage ") :].strip())

        if raw.startswith("/sync"):
            return ("run_type", "SYNC")

        if raw.startswith("/async"):
            return ("run_type", "ASYNC")

        if raw.startswith("/tasks"):
            return ("tasks", None)

        if raw.startswith("/auto"):
            return ("auto", None)

        if raw.startswith("/new"):
            return ("new", None)

        if raw.startswith("/mode "):
            return ("mode", raw[len("/mode ") :].strip())

        if raw.startswith("/list"):
            return ("list", None)

        if raw.startswith("/sync_env"):
            return ("sync_env", None)

        if raw.startswith("/vault"):
            return ("vault", None)

        if raw.startswith("/see_prayer"):
            return ("see_prayer", None)

        if raw.startswith("/see_revelation"):
            return ("see_revelation", None)

        if raw.startswith("/write_revelation "):
            return ("write_revelation", raw[len("/write_revelation ") :].strip())

        if raw.startswith("/reset"):
            return ("reset", None)

        if raw.startswith("/clear"):
            return ("clear", None)

        if raw.startswith("/exit") or raw.startswith("/quit"):
            return ("exit", None)

        if raw.startswith("/"):
            return ("help", raw)

        # 处理 "ID: Message" 格式
        if ":" in raw:
            parts = raw.split(":", 1)
            lineage_id = parts[0].strip()
            message = parts[1].strip()
            if self.lineage_manager.exists(lineage_id):
                return ("execute", (lineage_id, message))
        
        # 默认执行
        target = self.active_lineage if self.active_lineage else "auto"
        return ("execute", (target, raw))

    def run(self):
        while True:
            try:
                # 动态刷新欢迎状态，展示当前的运行模式和活跃 Agent
                p_agent = self.active_lineage if self.active_lineage else "AUTO"
                prompt_label = f"[{self.run_type}][{p_agent}]"
                user_input = input(f"{prompt_label}> ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\n再见!")
                break
            except UnicodeDecodeError:
                print("输入包含无法识别的字符，请重试")
                continue

            cmd, data = self.parse_input(user_input)

            if cmd is None:
                continue

            if cmd == "exit":
                print("再见!")
                break

            if cmd == "run_type":
                self.run_type = str(data)
                print(f"模式已切换为: {self.run_type}")
                continue

            if cmd == "tasks":
                active_tasks = [t for t in self.background_tasks if t.is_alive()]
                print(f"当前有 {len(active_tasks)} 个任务在后台运行:")
                for t in active_tasks:
                    print(f"  - {t.name}")
                continue

            if cmd == "lineage":
                lineage_id = str(data)
                if self.lineage_manager.exists(lineage_id):
                    self.active_lineage = lineage_id
                    print(f"已手动绑定到 Lineage: {lineage_id}")
                else:
                    print(f"Lineage '{lineage_id}' 不存在，输入 /list 查看可用 Lineage")
                continue

            if cmd == "auto":
                self.active_lineage = None
                print(f"已解除绑定，进入自动分配模式 (AUTO, 模式: {self.dispatch_mode})")
                continue

            if cmd == "new":
                self.active_lineage = None
                print(f"已开启新话题：已解除当前绑定，重置为自动分配模式 (模式: {self.dispatch_mode})。")
                continue

            if cmd == "mode":
                mode = str(data).lower()
                if mode in ["random", "latest"]:
                    self.dispatch_mode = mode
                    print(f"分配模式已切换为: {self.dispatch_mode}")
                else:
                    print(f"不支持的模式: {mode} (可用模式: random, latest)")
                continue

            if cmd == "list":
                for lineage_id in self.lineage_manager.all():
                    marker = ""
                    if self.active_lineage and lineage_id == self.active_lineage:
                        marker = " <-- active (pinned)"
                    agent = self.lineage_manager.all()[lineage_id]
                    print(f"  {lineage_id} (UID: {agent.metadata['uid']}){marker}")
                continue

            if cmd == "sync_env":
                env_path = self.lineage_manager.settings.workspace_root.parent / ".env"
                if not env_path.exists():
                    print("错误：根目录未发现 .env 文件")
                    continue
                
                env_content = env_path.read_text(encoding="utf-8")
                count = 0
                for lineage_id in self.lineage_manager.all():
                    agent = self.lineage_manager.all()[lineage_id]
                    target_env = agent.lineage_root / ".env"
                    target_env.write_text(env_content, encoding="utf-8")
                    # 发送同步指令让 Agent 重新加载 .env (热更新)
                    agent.sync()
                    count += 1
                
                print(f"同步完成：已将 .env 同步至 {count} 个 Lineage 个体。")
                continue

            if cmd == "vault":
                target = self.active_lineage
                if not target:
                    # 如果是自动模式，尝试看最近的一个
                    all_ids = list(self.lineage_manager.all().keys())
                    target = all_ids[-1] if all_ids else None
                
                if target:
                    agent = self.lineage_manager.all()[target]
                    vault_list = list(agent.vault_path.iterdir()) if agent.vault_path.exists() else []
                    print(f"Vault of {target}:")
                    print(f"  Path: {agent.vault_path}")
                    print(f"  Contents: {[x.name for x in vault_list]}")
                else:
                    print("尚未创建任何 Lineage")
                continue

            if cmd == "see_prayer":
                prayer_path = self.lineage_manager.settings.workspace_root / "prayer.md"
                
                print("=" * 40)
                print("祈祷书 (Prayer Book)")
                print("-" * 40)
                if prayer_path.exists():
                    print(prayer_path.read_text(encoding="utf-8").strip())
                else:
                    print("(空)")
                print("=" * 40)
                continue

            if cmd == "see_revelation":
                revelation_path = self.lineage_manager.settings.workspace_root / "revelation.md"
                
                print("=" * 40)
                print("启示录 (The Revelation)")
                print("-" * 40)
                if revelation_path.exists():
                    print(revelation_path.read_text(encoding="utf-8").strip())
                else:
                    print("(空)")
                print("=" * 40)
                continue

            if cmd == "write_revelation":
                msg = str(data)
                revelation_path = self.lineage_manager.settings.workspace_root / "revelation.md"
                timestamp = __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                with open(revelation_path, "a", encoding="utf-8") as f:
                    f.write(f"\n## [{timestamp}] 神之谕令\n")
                    f.write(f"{msg}\n")
                print(f"神谕已降临：{msg}")
                continue

            if cmd == "reset":
                confirm = input("确定要重置整个工作区吗？(y/n): ").strip().lower()
                if confirm == "y":
                    self.lineage_manager.reset()
                    print("Workspace 已重置。正在扫描...")
                    self._load_lineages()
                else:
                    print("操作已取消。")
                continue

            if cmd == "clear":
                confirm = input("确定要清空所有环境吗？此操作不可逆！(y/n): ").strip().lower()
                if confirm == "y":
                    self.lineage_manager.clear()
                    print("Workspace 已清空。程序将退出。")
                    sys.exit(0)
                else:
                    print("操作已取消。")
                continue

            if cmd == "help":
                print("快捷命令:")
                print("  /lineage <id>  固定使用某个 Agent")
                print("  /auto          解除固定，由系统自动分配 Agent")
                print("  /list          列出所有个体")
                print("  /reset         重置工作区")
                print("  /clear         清空文明")
                continue

            if cmd == "execute":
                assert isinstance(data, tuple) and len(data) == 2
                lineage_id, message = data
                
                # 如果当前是 AUTO 模式且没有固定 Lineage
                if lineage_id == "auto":
                    # 自动分配逻辑
                    all_ids = list(self.lineage_manager.all().keys())
                    if not all_ids:
                        print("错误：没有任何活跃的 Lineage")
                        continue
                    
                    if self.dispatch_mode == "random":
                        lineage_id = random.choice(all_ids)
                    else: # latest
                        lineage_id = all_ids[-1]

                    print(f"(系统自动分配[{self.dispatch_mode}]给: {lineage_id})")
                    # 重要：分配后将该个体设为 active_lineage，实现“粘性对话”
                    # 用户可以通过 /auto 或 /new 解除绑定
                    self.active_lineage = lineage_id

                if self.run_type == "ASYNC":
                    t = threading.Thread(
                        target=self._execute,
                        args=(lineage_id, message),
                        name=f"Task-{lineage_id}-{datetime.now().strftime('%H%M%S')}",
                        daemon=True
                    )
                    self.background_tasks.append(t)
                    t.start()
                    print(f"[ASYNC] 任务已在后台启动: {t.name}")
                else:
                    self._execute(lineage_id, message)

    def _execute(self, lineage_id: str, message: str):
        agent = self.lineage_manager.load(lineage_id)
        # 不要通过 _execute 自动绑定，除非用户明确要求。这里保持 transient 响应。
        # self.active_lineage = lineage_id 
        print(f"==> {lineage_id} 请求已发送，等待生命反应...")
        
        def on_step(msg):
            event_type = msg.get("type")
            if event_type == "step":
                tool = msg.get("tool")
                args = msg.get("args")
                result = msg.get("result")
                if tool:
                    if args and not result:
                        print(f"  [Action] 调用工具: {tool}({json.dumps(args, ensure_ascii=False)})")
                    elif result:
                        res_str = str(result)[:100] + "..." if len(str(result)) > 100 else str(result)
                        print(f"  [Result] 工具返回: {res_str}")
                elif msg.get("event") == "start":
                    print(f"  [Status] Engine 已唤醒，思考中...")

        result = agent.run(
            objective=message, 
            max_steps=10,
            on_step=on_step
        )
        
        if "error" in result:
            print(f"Error: {result['error']}")
            return

        print(f"\n[{lineage_id} 回复]:")
        print("-" * 20)
        print(result.get("final_output", "(无输出)"))
        print("-" * 20)
        print(f"=== 执行完成 ({result.get('session_id')}) ===")
        print(f"结果: {result.get('final_output')}")
        vault_list = list(agent.vault_path.iterdir()) if agent.vault_path.exists() else []
        print(f"Vault 状态: {[x.name for x in vault_list]}")

        if self.run_type == "ASYNC":
            print(f"\n[ASYNC] {lineage_id} 任务执行完毕。")
            p_agent = self.active_lineage if self.active_lineage else "AUTO"
            print(f"[{self.run_type}][{p_agent}]> ", end="", flush=True)


def main():
    cli = AgentCLI()
    cli.run()


if __name__ == "__main__":
    main()
