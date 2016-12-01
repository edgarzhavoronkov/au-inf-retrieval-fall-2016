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


def top_n(vectors, n):
    return np.bincount(vectors.nonzero()[1]).argsort()[::-1][:n]


def recommend_user_raw(user_idx, similarities, urm, nbr_size, N):
    nbr_vectors = get_neighbors(user_idx, similarities, urm, nbr_size)
    return top_n(nbr_vectors, N)


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

def run_test(nbr_size, N):
    train, test = read_sets("../data/urm.csv", 0.8)
    sims = cosine_similarities(train)
    sum_f1 = 0.0
    for i in range(MAX_USERID):
        usr_recommendations = recommend_user_raw(i, sims, train, nbr_size, N)
        sum_f1 += f1(usr_recommendations, test[i].nonzero()[1])
    print(sum_f1 / MAX_USERID)

def get_single_recommendation(username):
    urm = readURM()
    users = readUsers()
    tracks = readTracks()

if __name__ == '__main__':
    if (argv[1] == "test"):
        run_test(int(argv[2]), int(argv[3]))
    else:
        get_single_recommendation(argv[0])



