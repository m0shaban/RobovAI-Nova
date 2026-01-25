from typing import Dict, Any
from .base import BaseTool

class FeasibilityTool(BaseTool):
    @property
    def name(self) -> str:
        return "/feasibility"

    @property
    def description(self) -> str:
        return "Generates mini-feasibility studies for projects."

    @property
    def cost(self) -> int:
        return 1

    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        return {
            "status": "success",
            "output": f"## Feasibility Study: {user_input}\n\n| Item | Estimated Cost |\n|---|---|\n| Dev | 50,000 EGP |\n| Marketing | 20,000 EGP |",
            "tokens_deducted": self.cost
        }

class CalcRoiTool(BaseTool):
    @property
    def name(self) -> str:
        return "/calc_roi"

    @property
    def description(self) -> str:
        return "Calculates Digital Transformation ROI."

    @property
    def cost(self) -> int:
        return 1

    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        return {
            "status": "success",
            "output": f"## ROI Calculation\nFor input: {user_input}\n\nExpected efficiency gain: 30%\nAnnual Saving: 120,000 EGP.",
            "tokens_deducted": self.cost
        }
