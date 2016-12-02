from sys import argv

import numpy as np
import math as mt
import csv
from sparsesvd import sparsesvd
from scipy.sparse import csr_matrix, csc_matrix
from sklearn.metrics.pairwise import cosine_similarity
from random import random
from sys import float_info

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
    return urm[nbrs]


def top_n(vectors, n, user_items):
    recs = np.bincount(vectors.nonzero()[1]).argsort()[::-1]
    result = []
    for rec in recs:
        if rec not in user_items:
            result.append(rec)
        if len(result) >= n:
            break
    return result if len(result) <= n else result[:n]


def recommend_user_raw(user_idx, similarities, urm, nbr_size, N):
    nbr_vectors = get_neighbors(user_idx, similarities, urm, nbr_size)
    return top_n(nbr_vectors, N, set(urm[user_idx].nonzero()[1]))


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


def f1(recs, test):
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
        return 0.0
    return 2 * precision * recall / (precision + recall)

def run_test(nbr_size):
    train, test = read_sets("../data/urm.csv", 0.6)
    sims = cosine_similarities(train)
    sum_f1 = 0.0
    overall = 0
    for i in range(MAX_USERID):
        test_recs = test[i].nonzero()[1]
        local_N = len(test_recs)
        if local_N == 0:
            continue
        usr_recommendations = recommend_user_raw(i, sims, train, nbr_size, local_N)
        sum_f1 += f1(usr_recommendations, test_recs)
        overall += 1
    print(sum_f1 / overall)

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

if __name__ == '__main__':
    if (argv[1] == "test"):
        run_test(int(argv[2]))
        # learn_nbrs_size(65, 140, 5) - 70 is optimal (3.2%)
    else:
        print(get_single_recommendation(argv[1]))



