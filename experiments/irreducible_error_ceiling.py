"""Irreducible-error analysis: identical feature vectors with conflicting labels."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # run from repo root: python experiments/<script>.py
import numpy as np
import pandas as pd
from src.data import load_raw, split_xy, stratified_split

df = load_raw()
X, y, cat = split_xy(df)
key = pd.util.hash_pandas_object(X, index=False)
g = pd.DataFrame({"key": key.values, "y": y.values})
stats = g.groupby("key").y.agg(["size", "sum"])
stats["minority"] = np.minimum(stats["sum"], stats["size"] - stats["sum"])
conf = stats[stats.minority > 0]
print(f"rows total {len(df):,}")
print(f"conflicting groups {len(conf):,} covering {conf['size'].sum():,} rows")
print(f"oracle (majority-per-vector) irreducible errors: {conf.minority.sum():,} "
      f"= {conf.minority.sum()/len(df):.3%} of all rows -> max accuracy {1-conf.minority.sum()/len(df):.4%}")
# minority split by type: normal-labelled minority (would be FP) vs attack-labelled minority (would be FN)
g = g.join(stats[["size", "sum"]], on="key")
g["maj"] = (g["sum"] * 2 >= g["size"]).astype(int)
fp_irr = ((g.y == 0) & (g.maj == 1)).sum(); fn_irr = ((g.y == 1) & (g.maj == 0)).sum()
print(f"irreducible FP (normal rows sharing majority-attack vector): {fp_irr:,} -> min FPR {fp_irr/(y==0).sum():.3%}")
print(f"irreducible FN (attack rows sharing majority-normal vector): {fn_irr:,} -> min FNR {fn_irr/(y==1).sum():.3%}")
top = conf.sort_values("size", ascending=False).head(8)
print(top)
# which families sit inside conflicting groups
g["cat"] = cat.values
inconf = g[g.key.isin(conf.index)]
print(inconf.groupby("cat").size().sort_values(ascending=False))

# test-fold view
X_tr, X_te, y_tr, y_te, c_tr, c_te = stratified_split(X, y, cat)
kte = pd.util.hash_pandas_object(X_te, index=False)
te = pd.DataFrame({"key": kte.values, "y": y_te.values}).join(stats[["size", "sum"]], on="key")
te["maj"] = (te["sum"] * 2 >= te["size"]).astype(int)
err = (te.y != te.maj)
print(f"test rows {len(te):,}; oracle errors {err.sum():,} -> oracle acc {1-err.mean():.4%}; "
      f"oracle FPR {((te.y==0)&(te.maj==1)).sum()/(te.y==0).sum():.3%}; "
      f"oracle recall {((te.y==1)&(te.maj==1)).sum()/(te.y==1).sum():.3%}")
ktr = set(pd.util.hash_pandas_object(X_tr, index=False).values)
print(f"test rows whose exact feature vector also occurs in train: {te.key.isin(ktr).mean():.2%}")
