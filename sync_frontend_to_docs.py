from pathlib import Path
import shutil


ROOT_DIR = Path(__file__).resolve().parent
SOURCE_FILE = ROOT_DIR / "frontend" / "index.html"
DOCS_DIR = ROOT_DIR / "docs"
TARGET_FILE = DOCS_DIR / "index.html"


def main() -> None:
    if not SOURCE_FILE.is_file():
        raise SystemExit(f"Source file not found: {SOURCE_FILE}")

    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SOURCE_FILE, TARGET_FILE)
    print("Synced frontend/index.html to docs/index.html successfully.")


if __name__ == "__main__":
    main()
