from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def load_agent_documents():
    """Return a dictionary of agent_name -> list of document text."""
    agents = {
        "billing": BASE_DIR / "billing",
        "support": BASE_DIR / "support",
        "technical": BASE_DIR / "technical",
    }

    documents = {}
    for agent_name, folder in agents.items():
        files = sorted(folder.glob("*.md"))
        documents[agent_name] = []
        for file in files:
            documents[agent_name].append({
                "name": file.name,
                "path": str(file),
                "text": file.read_text(encoding="utf-8"),
            })

    return documents


if __name__ == "__main__":
    docs = load_agent_documents()
    for agent, entries in docs.items():
        print(f"{agent}: {len(entries)} files")
        for entry in entries:
            print(f" - {entry['name']}")
