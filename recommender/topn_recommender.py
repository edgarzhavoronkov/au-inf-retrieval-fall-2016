from sys import argv

import numpy as np
import math as mt
import csv
from sparsesvd import sparsesvd
from scipy.sparse import csr_matrix, csc_matrix
from sklearn.metrics.pairwise import cosine_similarity
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


def cosine_similarities(urm):
    return cosine_similarity(urm)


def get_neighbors(center_idx, similarities, urm, nbr_size):
    most_similar = similarities[center_idx].argsort()[::-1]
    nbrs = most_similar[most_similar != center_idx][:nbr_size]
    values = similarities[center_idx][nbrs]
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

def top_n_both(vectors, vec_weights, n, user_items):
    result = np.zeros(shape=(MAX_TRACKID,))
    for nbr, weight in zip(vectors, vec_weights):
        result += nbr * weight
    result = result.argsort().tolist()[0][::-1]
    # recs = np.bincount(vectors.nonzero()[1]).argsort()[::-1]
    filtered = []
    for rec in result:
        if rec not in user_items:
            filtered.append(rec)
        if len(filtered) >= n:
            break
    return filtered if len(filtered) <= n else filtered[:n]


def recommend_user_raw(user_idx, similarities, urm, nbr_size, N, equiv_weights = False):
    nbr_indices, nbr_dists = get_neighbors(user_idx, similarities, urm, nbr_size)
    return top_n(nbr_indices,
                 nbr_dists if not equiv_weights else np.ones(shape=nbr_dists.shape),
                 N,
                 set(urm[user_idx].nonzero()[1]))

def recommend_user_raw_both(user_idx, similarities, urm, nbr_size, N):
    nbr_indices, nbr_dists = get_neighbors(user_idx, similarities, urm, nbr_size)
    return top_n_both(nbr_indices,
                 nbr_dists,
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

def average_metrics(train, test, sims, nbr_size):
    sum_f1 = 0.0
    sum_pr = 0.0
    sum_rc = 0.0
    overall = 0
    for i in range(MAX_USERID):
        test_recs = test[i].nonzero()[1]
        local_N = len(test_recs)
        if local_N == 0:
            continue
        usr_recommendations = recommend_user_raw(i, sims, train, nbr_size, local_N)
        (f1, pr, rc) = metrics(usr_recommendations, test_recs)
        sum_f1 += f1
        sum_pr += pr
        sum_rc += rc
        overall += 1
    return {'f1': (sum_f1 / overall), 'pr': sum_pr / overall, 'rc':sum_rc / overall}

def run_test(nbr_size, train_ratio=0.6):
    train, test = read_sets("../data/urm.csv", train_ratio)
    sims = cosine_similarities(train)
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
    sims = cosine_similarities(train)
    prs = []
    rcs = []
    for nbr_size in nbr_sizes:
        average = average_metrics(train, test, sims, nbr_size)
        prs.append(average["pr"])
        rcs.append(average["rc"])
    plt.plot(nbr_sizes, prs, "g-")
    plt.plot(nbr_sizes, rcs, "r-")
    plt.legend(['precision', 'recall'], loc='upper left')
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




