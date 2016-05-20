from typing import Sequence, Callable
import multiprocessing as mp
import itertools

import numpy as np
import scipy.spatial.distance

from .work import N_JOBS


def pwmatrix(func: Callable, data: Sequence) -> np.ndarray:
    pairs = list(itertools.combinations(data, 2))
    results = scipy.spatial.distance.squareform(workers.starmap(func, pairs))
    results = scipy.spatial.distance.squareform(map(func, pairs))
    return results


if __name__ == "__main__":
    raise RuntimeError
else:
    workers = mp.Pool(processes=N_JOBS)
