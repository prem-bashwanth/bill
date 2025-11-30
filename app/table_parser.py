# app/table_parser.py
from typing import List
import numpy as np

def guess_column_x_positions(rows: List[List[dict]], n_columns: int = 5):
    """
    Given OCR rows (list of lists of token dicts with 'cx' and 'text'),
    return approximate x positions (centers) of columns by clustering token cx positions.
    Simple heuristic: collect all cx of tokens in rows and KMeans-like clustering (via numpy).
    This is a light-weight helper for column alignment.
    """
    xs = []
    for r in rows:
        for w in r:
            xs.append(w['cx'])
    if not xs:
        return []
    xs = np.array(xs).reshape(-1, 1)
    # simple initialization: choose evenly spaced centers across min..max
    min_x, max_x = xs.min(), xs.max()
    centers = np.linspace(min_x, max_x, num=n_columns)
    # do a few iterations of kmeans-like assignment/update
    for _ in range(4):
        clusters = {i: [] for i in range(len(centers))}
        for v in xs:
            diffs = [abs(v[0] - c) for c in centers]
            idx = int(np.argmin(diffs))
            clusters[idx].append(v[0])
        for i in range(len(centers)):
            if clusters[i]:
                centers[i] = sum(clusters[i]) / len(clusters[i])
    return sorted(list(centers))
