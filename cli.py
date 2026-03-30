from app.agents.lineage import LineageManager, LineageAgent


class AgentCLI:
    def __init__(self):
        self.lineage_manager = LineageManager()
        self.active_lineage = "Lineage-01"
        self._load_lineages()
        self.welcome()

    def _load_lineages(self):
        for lineage_id in ["Lineage-01", "Lineage-02"]:
            agent = self.lineage_manager.load(lineage_id)
            print(f"Loaded lineage: {lineage_id} (UID: {agent.metadata['uid']})")

    def welcome(self):
        print("=" * 50)
        print("MetaEvoAgents CLI - Lineage 驱动的多轮对话")
        print("用法:")
        print("  /lineage <id>  切换执行 Lineage")
        print("  /list           列出所有 Lineage")
        print("  /vault          查看当前 Lineage 的 vault")
        print("  exit 或 quit    退出")
        print("=" * 50)
        print(f"当前 Lineage: {self.active_lineage}")
        print()

    def parse_input(self, raw: str):
        raw = raw.strip()
        if not raw:
            return None, None

        if raw.startswith("/lineage "):
            return ("lineage", raw[len("/lineage "):].strip())

        if raw.startswith("/list"):
            return ("list", None)

        if raw.startswith("/vault"):
            return ("vault", None)

        if raw.startswith("/"):
            return ("help", raw)

        if ":" in raw:
            parts = raw.split(":", 1)
            lineage_id = parts[0].strip()
            message = parts[1].strip()
            if self.lineage_manager.exists(lineage_id):
                return ("execute", (lineage_id, message))
            return ("execute", (self.active_lineage, raw))

        return ("execute", (self.active_lineage, raw))

    def run(self):
        while True:
            try:
                user_input = input(f"[{self.active_lineage}]> ").strip()
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

            if cmd == "lineage":
                lineage_id = str(data)
                if self.lineage_manager.exists(lineage_id):
                    self.active_lineage = lineage_id
                    print(f"已切换到 Lineage: {lineage_id}")
                else:
                    print(f"Lineage '{lineage_id}' 不存在，输入 /list 查看可用 Lineage")
                continue

            if cmd == "list":
                for lineage_id in self.lineage_manager.all():
                    marker = " <-- active" if lineage_id == self.active_lineage else ""
                    agent = self.lineage_manager.all()[lineage_id]
                    print(f"  {lineage_id} (UID: {agent.metadata['uid']}){marker}")
                continue

            if cmd == "vault":
                agent = self.lineage_manager.all()[self.active_lineage]
                vault_list = list(agent.vault_path.iterdir()) if agent.vault_path.exists() else []
                print(f"Vault of {self.active_lineage}:")
                print(f"  Path: {agent.vault_path}")
                print(f"  Contents: {[x.name for x in vault_list]}")
                continue

            if cmd == "help":
                print("未知命令，请使用 /list 查看可用命令")
                continue

            if cmd == "execute":
                assert isinstance(data, tuple) and len(data) == 2
                lineage_id, message = data
                self._execute(lineage_id, message)

    def _execute(self, lineage_id: str, message: str):
        agent = self.lineage_manager.load(lineage_id)
        self.active_lineage = lineage_id
        print(f"==> {lineage_id} 执行中...")
        result = agent.run(objective=message, max_steps=10, streaming=True)
        print()
        print(f"=== 执行完成 ({result.session_id}) ===")
        vault_list = list(agent.vault_path.iterdir()) if agent.vault_path.exists() else []
        print(f"Vault 状态: {[x.name for x in vault_list]}")


def main():
    cli = AgentCLI()
    cli.run()


if __name__ == "__main__":
    main()
