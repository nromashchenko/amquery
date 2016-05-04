#!/usr/bin/env python3

from iof import read_distance_matrix
import numpy as np
import random
from partial_corr import partial_corr


def choose(dmatrix, keys, keys_idx):
    outer_ix = list(set(np.arange(len(keys))) - set(keys_idx))
    dmx = np.delete(dmatrix, outer_ix, axis=1)
    dmx = np.delete(dmx, keys_idx, axis=0)
    return dmx


def get_total_partcorr(dmatrix, keys, keys_idx):
    dmx = choose(dmatrix, keys, keys_idx)
    corrs = partial_corr(dmx)
    sums = np.apply_along_axis(sum, 1, corrs)
    total_pc = np.apply_along_axis(sum, 0, sums)
    return total_pc


def objective_function(dmatrix, keys, keys_idx):
    return get_total_partcorr(dmatrix, keys, keys_idx)

if __name__ == "__main__":
    # filename = '../../out/w_unifrac/wu_full.txt'
    filename = '../../out/jsd_50/seqs.txt'

    keys, dmatrix = read_distance_matrix(filename)
    dmatrix = np.matrix(dmatrix)

    k = 3
    corrd_sys_idx = random.sample(range(len(keys)), k)
    value = objective_function(dmatrix, keys, corrd_sys_idx)
    print(value)
