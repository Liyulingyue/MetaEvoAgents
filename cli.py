import sys
from app.agents.agent import Agent


class AgentCLI:
    def __init__(self):
        self.welcome()

    def welcome(self):
        print("=" * 50)
        print("MetaEvoAgents CLI - 多轮对话模式")
        print("输入 exit 或 quit 退出")
        print("=" * 50)
        print()

    def run(self):
        while True:
            try:
                user_input = input("> ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\n再见!")
                break
            except UnicodeDecodeError:
                print("输入包含无法识别的字符，请重试")
                continue

            if not user_input:
                continue

            if user_input.lower() in ("exit", "quit", "q"):
                print("再见!")
                break

            self.chat(user_input)

    def chat(self, message: str):
        agent = Agent()
        result = agent.run(objective=message, max_steps=10, streaming=True)

        print()


def main():
    cli = AgentCLI()
    cli.run()


if __name__ == "__main__":
    main()
