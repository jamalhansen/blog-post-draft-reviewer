from pathlib import Path

def load_rubric(path: str = "checklist.md") -> str:
    rubric_path = Path(path)
    if not rubric_path.exists():
        return "Rubric not found."
    return rubric_path.read_text()
