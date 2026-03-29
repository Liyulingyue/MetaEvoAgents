from pydantic import BaseModel
from typing import Optional, List


class Gene(BaseModel):
    name: str
    description: str
    scripts: List[str] = []


class AgentGenome(BaseModel):
    generation: int
    parent_id: Optional[str] = None
    genes: List[Gene] = []
    skills: List[str] = []


class AgentState(BaseModel):
    id: str
    genome: AgentGenome
    step: int = 0
    done: bool = False
    memory: List[str] = []
    workspace_path: str = ""
