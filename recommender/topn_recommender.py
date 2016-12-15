from sys import argv

import numpy as np
import math as mt
import csv
from sparsesvd import sparsesvd
from scipy.sparse import csr_matrix, csc_matrix
from sklearn.metrics.pairwise import cosine_similarity
import sklearn.preprocessing as pp
from random import random
from sys import float_info
from matplotlib import pyplot as plt

MAX_TRACKID = 320495
MAX_USERID = 1517


def readUsers():
    users = [''] * MAX_USERID
    with open('../data/username2id.csv', 'r', encoding='utf-8') as users_file:
        users_reader = csv.reader(users_file, delimiter=';')
        for row in users_reader:
            users[int(row[0])] = row[1]
    return users


def readTracks():
    tracks = [''] * MAX_TRACKID
    with open('../data/trackname2id.csv', 'r', encoding='utf-8') as tracks_file:
        tracks_reader = csv.reader(tracks_file, delimiter=';')
        for row in tracks_reader:
            tracks[int(row[0])] = row[1]
    return tracks

# the format is user:song, users are rows

def readURM():
    urm = np.zeros(shape=(MAX_USERID, MAX_TRACKID), dtype=np.float32)
    with open('../data/urm.csv', 'r', encoding='utf-8') as dataset_file:
        urm_reader = csv.reader(dataset_file, delimiter=';')
        for row in urm_reader:
            urm[int(row[0]), int(row[1])] = float(1.0)
    return csc_matrix(urm, dtype=np.float32)


# def cosine_similarities(urm):
#     return cosine_similarity(urm)


def get_neighbors(center_idx, similarities, urm, nbr_size):
    all_neighbors = similarities[center_idx].toarray()[0]
    most_similar = all_neighbors.argsort()[::-1]
    nbrs = most_similar[most_similar != center_idx][:nbr_size]
    values = all_neighbors[nbrs]
    return urm[nbrs], values


def top_n(vectors, vec_weights, n, user_items):
    result = np.zeros(shape=(MAX_TRACKID,))
    for nbr, weight in zip(vectors, vec_weights):
        result += nbr * weight
    result = result.argsort().tolist()[0][::-1]
    filtered = []
    for rec in result:
        if rec not in user_items:
            filtered.append(rec)
        if len(filtered) >= n:
            break
    return filtered if len(filtered) <= n else filtered[:n]


def top_n_update(vectors, vec_weights, n, user_items, rec_vector):
    for nbr, weight in zip(vectors, vec_weights):
        rec_vector += nbr * weight
    result = rec_vector.argsort().tolist()[0][::-1]
    filtered = []
    for rec in result:
        if rec not in user_items:
            filtered.append(rec)
        if len(filtered) >= n:
            break
    return filtered if len(filtered) <= n else filtered[:n]


def recommend_user_raw_many(user_idx, similarities, urm, nbr_sizes, N, equiv_weights = False):
    nbr_indices, nbr_dists = get_neighbors(user_idx, similarities, urm, nbr_sizes[-1])
    recs_vector = np.zeros(shape=(MAX_TRACKID,))
    results = []
    user_items = set(urm[user_idx].nonzero()[1])
    for i in range(len(nbr_sizes) - 1):
        current_nbrs = nbr_indices[nbr_sizes[i]:nbr_sizes[i+1]]
        current_weights = nbr_dists[nbr_sizes[i]:nbr_sizes[i+1]]
        if equiv_weights:
            current_weights = np.ones(shape=current_weights.shape)
        results.append(top_n_update(current_nbrs, current_weights, N, user_items, recs_vector))
    return results


def recommend_user_raw(user_idx, similarities, urm, nbr_size, N, equiv_weights = False):
    nbr_indices, nbr_dists = get_neighbors(user_idx, similarities, urm, nbr_size)
    return top_n(nbr_indices,
                 nbr_dists if not equiv_weights else np.ones(shape=nbr_dists.shape),
                 N,
                 set(urm[user_idx].nonzero()[1]))


def read_sets(filename, train_ratio):
    urm = np.zeros(shape=(MAX_USERID, MAX_TRACKID), dtype=np.float32)
    test_data = np.zeros(shape=(MAX_USERID, MAX_TRACKID), dtype=np.float32)
    with open(filename, 'r', encoding='utf-8') as dataset_file:
        urm_reader = csv.reader(dataset_file, delimiter=';')
        for row in urm_reader:
            if random() < train_ratio:
                urm[int(row[0]), int(row[1])] = float(1.0)
            else:
                test_data[int(row[0]), int(row[1])] = float(1.0)
    return csc_matrix(urm, dtype=np.float32), csc_matrix(test_data, dtype=np.float32)

def cosine_similarities(mat):
    col_normed_mat = pp.normalize(mat, axis=1)
    return col_normed_mat * col_normed_mat.T

def jaccard_similarities(mat):
    rows_sum = mat.getnnz(axis=1)
    ab = mat * mat.T

    # for rows
    aa = np.repeat(rows_sum, ab.getnnz(axis=1))
    # for columns
    bb = rows_sum[ab.indices]

    similarities = ab.copy()
    similarities.data /= (aa + bb - ab.data)

    return similarities


def metrics(recs, test):
    recs_len = len(recs)
    if recs_len == 0:
        return 0.0
    test_len = len(test)
    if test_len == 0:
        return 0.0
    hitset_len = len(set(recs).intersection(set(test)))
    precision = hitset_len / recs_len
    recall = hitset_len / test_len
    if (precision + recall < float_info.epsilon):
        return 0.0, precision, recall
    return 2 * precision * recall / (precision + recall), precision, recall

def average_metrics(train, test, sims, nbr_size, equal_weights=False):
    sum_f1 = 0.0
    sum_pr = 0.0
    sum_rc = 0.0
    overall = 0
    for i in range(MAX_USERID):
        test_recs = test[i].nonzero()[1]
        local_N = len(test_recs)
        if local_N == 0:
            continue
        usr_recommendations = recommend_user_raw(i, sims, train, nbr_size, local_N, equal_weights)
        (f1, pr, rc) = metrics(usr_recommendations, test_recs)
        sum_f1 += f1
        sum_pr += pr
        sum_rc += rc
        overall += 1
    return {'f1': (sum_f1 / overall), 'pr': sum_pr / overall, 'rc':sum_rc / overall}


def average_metrics_many(train, test, sims, nbr_sizes, equal_weights = False):
    sum_f1 = [0.0,] * len(nbr_sizes)
    sum_pr = [0.0,] * len(nbr_sizes)
    sum_rc = [0.0,] *  len(nbr_sizes)
    overall = [0,] *  len(nbr_sizes)
    for i in range(MAX_USERID):
        test_recs = test[i].nonzero()[1]
        local_N = len(test_recs)
        if local_N == 0:
            continue
        usr_recommendations = recommend_user_raw_many(i, sims, train, [0,] + list(nbr_sizes), local_N, equal_weights)
        ms = [metrics(rcm, test_recs) for rcm in usr_recommendations]
        for i in range(len(nbr_sizes)):
            f1, pr, rc = ms[i]
            sum_f1[i] += f1
            sum_pr[i] += pr
            sum_rc[i] += rc
            overall[i] += 1
    for i in range(len(nbr_sizes)):
        sum_f1[i] /= overall[i]
        sum_pr[i] /= overall[i]
        sum_rc[i] /= overall[i]
    return {'f1': sum_f1, 'pr': sum_pr, 'rc': sum_rc}

def run_test(nbr_size, train_ratio=0.6):
    train, test = read_sets("../data/urm.csv", train_ratio)
    sims = jaccard_similarities(train)
    print(average_metrics(train, test, sims, nbr_size))

def learn_nbrs_size(start, end, step):
    for nbrs_size in range(start, end, step):
        print("nbrs: " + str(nbrs_size))
        print("F1: ")
        run_test(nbrs_size)


def get_single_recommendation(username):
    urm = readURM()
    users = readUsers()
    tracks = readTracks()
    user_idx = users.index(username)
    sims = cosine_similarities(urm)
    recs = recommend_user_raw(user_idx, sims, urm, 70, 10)
    return [tracks[rec] for rec in recs]


def plot_single_ratio(train_ratio, nbr_sizes):
    train, test = read_sets("../data/urm.csv", train_ratio)
    # sims = cosine_similarities(train)
    sims = jaccard_similarities(train)

    # for nbr_size in nbr_sizes:
    weighted = average_metrics_many(train, test, sims, nbr_sizes)["f1"]
    # equal = average_metrics_many(train, test, sims2, nbr_sizes)["f1"]

    plt.plot(nbr_sizes, weighted, "g-")
    # plt.plot(nbr_sizes, equal, "r-")
    # plt.legend(['cosine', 'jaccard'], loc='upper left')
    plt.title("Train ratio: " + str(train_ratio))
    plt.show()


def plot_experiments(train_ratios, nbr_sizes):
    for train_ratio in train_ratios:
        plot_single_ratio(train_ratio, nbr_sizes)


if __name__ == '__main__':
    if (argv[1] == "test"):
        run_test(int(argv[2]))
        # learn_nbrs_size(65, 140, 5) - 70 is optimal (3.2%)
    elif argv[1] == "plot":
        train_ratios = [0.5, 0.6, 0.8]
        nbr_sizes = range(int(argv[2]), int(argv[3]), 10)
        plot_experiments(train_ratios, nbr_sizes)
    elif argv[1] == "plotsingle":
        train_ratio = float(argv[2])
        nbr_sizes = range(int(argv[3]), int(argv[4]), 10)
        plot_single_ratio(train_ratio, nbr_sizes)
    else:
        print(get_single_recommendation(argv[1]))




