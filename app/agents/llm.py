import openai
from dotenv import load_dotenv
from openai.types.chat.chat_completion import ChatCompletionMessage

from app.core.config import settings

load_dotenv()

client = openai.OpenAI(
    api_key=settings.openai_api_key,
    base_url=settings.openai_url,
)


class LLMClient:
    def __init__(self, model: str = None, tools: list | None = None):
        self.model = model or settings.openai_model_name
        self.tools = tools

    def run(self, messages: list) -> ChatCompletionMessage:
        from app.agents.inner.tools import TOOL_SCHEMAS

        resp = client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=self.tools if self.tools is not None else TOOL_SCHEMAS,
            temperature=0.7,
        )
        return resp.choices[0].message
