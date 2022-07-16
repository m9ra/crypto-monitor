from pathlib import Path

PROJECT_PATH = Path(__file__).parent.parent
DATA_PATH = PROJECT_PATH / 'data'

DATA_PATH.mkdir(parents=True, exist_ok=True)
