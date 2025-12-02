from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field

# -----------------------------
# Pretty Output Formatter
# -----------------------------
def pretty_format(text: str) -> str:
    return f"""
# 🔍 Patent Novelty Check Result

{text.strip()}

---

🛠 Powered by: Patent Novelty Checker Tool
""".strip()


class PatentCheckToolInput(BaseModel):
    """Input schema for PatentCheckTool."""
    invention_summary: str = Field(..., description="Brief description of the invention to check novelty.")


class PatentCheckTool(BaseTool):
    name: str = "Patent Novelty Checker"
    description: str = (
        "Checks the novelty of an invention summary against known patent data (mock implementation)."
    )
    args_schema: Type[BaseModel] = PatentCheckToolInput

    def _run(self, invention_summary: str) -> str:
        # Dummy example implementation
        if "blockchain" in invention_summary.lower():
            raw_output = "Potential novelty found in blockchain-related technologies."
        else:
            raw_output = "No obvious novelty conflicts detected based on the given summary."

        # Return formatted output
        return pretty_format(raw_output)
