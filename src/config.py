"""Central configuration: paths, seeds and frozen feature definitions (DEC-001 / DEC-004)."""
from pathlib import Path

SEED = 42

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "dataset"
FIG_DIR = ROOT / "figures"
MODEL_DIR = ROOT / "models"
REPORT_DIR = ROOT / "reports"
ARTIFACT_DIR = ROOT / "artifacts"

TRAIN_CSV = DATA_DIR / "UNSW_NB15_training-set.csv"
TEST_CSV = DATA_DIR / "UNSW_NB15_testing-set.csv"

TARGET = "label"
TARGET_CAT = "attack_cat"
ID_COL = "id"

CATEGORICAL = ["proto", "service", "state"]
# Heavy-tailed volume / timing features receiving log1p before robust scaling (Section 5.1).
LOG1P_FEATURES = ["sbytes", "dbytes", "sload", "dload", "dur", "sinpkt", "dinpkt", "sjit", "djit"]

TEST_SIZE = 0.20
FIG_DPI = 300

STUDENT = {
    "name": "Muhammad Nafay Aftab",
    "enrolment": "03-134222-087",
    "class": "BSCS-8A",
    "course": "Information Security",
    "instructor": "Dr. Nadeem Sarwar",
    "assignment": "Assignment 1 Report (CLO 4)",
    "repo": "https://github.com/Nafay-Aftab/CLO4-IDS-ML-Solution",
}

for _d in (FIG_DIR, MODEL_DIR, REPORT_DIR, ARTIFACT_DIR):
    _d.mkdir(exist_ok=True)
