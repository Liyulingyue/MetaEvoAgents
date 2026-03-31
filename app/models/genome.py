from pydantic import BaseModel


class Gene(BaseModel):
    name: str
    description: str
    scripts: list[str] = []


class AgentGenome(BaseModel):
    generation: int
    parent_id: str | None = None
    genes: list[Gene] = []
    skills: list[str] = []


class AgentState(BaseModel):
    id: str
    genome: AgentGenome
    step: int = 0
    done: bool = False
    memory: list[str] = []
    workspace_path: str = ""
