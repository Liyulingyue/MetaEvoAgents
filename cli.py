import sys
from app.agents.agent import ShrineRegistry, ShrineKeeper


class AgentCLI:
    def __init__(self):
        self.shrine_registry = ShrineRegistry()
        self.active_shrine = "Shrine-01"
        self._load_shrines()
        self.welcome()

    def _load_shrines(self):
        for shrine_id in ["Shrine-01", "Shrine-02"]:
            keeper = self.shrine_registry.load(shrine_id)
            print(f"Loaded shrine: {shrine_id} (UID: {keeper.metadata['uid']})")

    def welcome(self):
        print("=" * 50)
        print("MetaEvoAgents CLI - 宗祠驱动的多轮对话")
        print("用法:")
        print("  /shrine <id>    切换执行 Shrine")
        print("  /list            列出所有宗祠")
        print("  /vault           查看当前 Shrine 的 vault")
        print("  exit 或 quit     退出")
        print("=" * 50)
        print(f"当前 Shrine: {self.active_shrine}")
        print()

    def parse_input(self, raw: str):
        raw = raw.strip()
        if not raw:
            return None, None

        if raw.startswith("/shrine "):
            return ("shrine", raw[len("/shrine "):].strip())

        if raw.startswith("/list"):
            return ("list", None)

        if raw.startswith("/vault"):
            return ("vault", None)

        if raw.startswith("/"):
            return ("help", raw)

        if ":" in raw:
            parts = raw.split(":", 1)
            shrine_id = parts[0].strip()
            message = parts[1].strip()
            if self.shrine_registry.exists(shrine_id):
                return ("execute", (shrine_id, message))
            return ("execute", (self.active_shrine, raw))

        return ("execute", (self.active_shrine, raw))

    def run(self):
        while True:
            try:
                user_input = input(f"[{self.active_shrine}]> ").strip()
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

            if cmd == "shrine":
                shrine_id = str(data)
                if self.shrine_registry.exists(shrine_id):
                    self.active_shrine = shrine_id
                    print(f"已切换到 Shrine: {shrine_id}")
                else:
                    print(f"Shrine '{shrine_id}' 不存在，输入 /list 查看可用 Shrine")
                continue

            if cmd == "list":
                for shrine_id in self.shrine_registry.all():
                    marker = " <-- active" if shrine_id == self.active_shrine else ""
                    keeper = self.shrine_registry.all()[shrine_id]
                    print(f"  {shrine_id} (UID: {keeper.metadata['uid']}){marker}")
                continue

            if cmd == "vault":
                keeper = self.shrine_registry.all()[self.active_shrine]
                vault_list = list(keeper.vault_path.iterdir()) if keeper.vault_path.exists() else []
                print(f"Vault of {self.active_shrine}:")
                print(f"  Path: {keeper.vault_path}")
                print(f"  Contents: {[x.name for x in vault_list]}")
                continue

            if cmd == "help":
                print("未知命令，请使用 /list 查看可用命令")
                continue

            if cmd == "execute":
                assert isinstance(data, tuple) and len(data) == 2
                shrine_id, message = data
                self._execute(shrine_id, message)

    def _execute(self, shrine_id: str, message: str):
        keeper = self.shrine_registry.load(shrine_id)
        self.active_shrine = shrine_id
        print(f"==> {shrine_id} 执行中...")
        result = keeper.run(objective=message, max_steps=10, streaming=True)
        print()
        print(f"=== 执行完成 ({result.session_id}) ===")
        vault_list = list(keeper.vault_path.iterdir()) if keeper.vault_path.exists() else []
        print(f"Vault 状态: {[x.name for x in vault_list]}")


def main():
    cli = AgentCLI()
    cli.run()


if __name__ == "__main__":
    main()
