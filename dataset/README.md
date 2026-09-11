# Dataset Setup — UNSW-NB15

This project uses the official **UNSW-NB15** partitioned CSVs published by the
Australian Centre for Cyber Security (UNSW Canberra).

| File | Rows | Committed | Purpose |
|---|---:|:---:|---|
| `UNSW_NB15_training-set.csv` | 82,332 | Yes | Official partition (merged, then re-split 80/20 stratified) |
| `UNSW_NB15_testing-set.csv` | 175,341 | Yes | Official partition (merged, then re-split 80/20 stratified) |
| `NUSW-NB15_features.csv` | 49 | Yes | Feature dictionary |
| `UNSW-NB15_LIST_EVENTS.csv` | — | Yes | Attack event taxonomy |
| `UNSW-NB15_1.csv` … `UNSW-NB15_4.csv` | ~2.54 M | **No** (`.gitignore`) | Raw full-capture dumps (~590 MB); not required |

The two partition CSVs are committed so the notebook and dashboard run out of the box.
If they are missing, download them from the official source and place them in this folder:

- https://research.unsw.edu.au/projects/unsw-nb15-dataset

> Reference: N. Moustafa and J. Slay, "UNSW-NB15: a comprehensive data set for network
> intrusion detection systems," *MilCIS*, 2015.
