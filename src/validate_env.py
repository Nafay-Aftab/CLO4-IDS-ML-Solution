"""Phase 0 acceptance check: dependencies import and both UNSW-NB15 partitions are readable."""
import importlib
import sys

from src.config import TEST_CSV, TRAIN_CSV

MODULES = ["pandas", "numpy", "sklearn", "scipy", "matplotlib", "seaborn", "docx",
           "joblib", "lightgbm", "fastapi", "uvicorn", "multipart", "nbformat", "nbclient"]


def main() -> int:
    for name in MODULES:
        mod = importlib.import_module(name)
        print(f"  [OK] {name:<11} {getattr(mod, '__version__', '')}")
    print("All dependencies verified successfully.")

    import pandas as pd
    for path in (TRAIN_CSV, TEST_CSV):
        df = pd.read_csv(path, encoding="utf-8-sig")
        print(f"  [OK] {path.name:<32} rows={len(df):>7,}  cols={df.shape[1]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
