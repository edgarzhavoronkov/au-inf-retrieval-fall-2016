import csv
import math
import random
from sparsesvd import sparsesvd

import numpy as np
from scipy.sparse import lil_matrix, csc_matrix


MAX_TRACKID = 320495
MAX_USERID = 1517

test_set_size = int(0.2 * MAX_TRACKID)
train_set_size = MAX_TRACKID - test_set_size
test_indices = random.sample(range(MAX_TRACKID), test_set_size)


def read_users(filename):
    users = [''] * MAX_USERID
    with open(filename, 'r', encoding='utf-8') as users_file:
        users_reader = csv.reader(users_file, delimiter=';')
        for row in users_reader:
            users[int(row[0])] = row[1]
    return users


def read_tracks(filename):
    tracks = [''] * MAX_TRACKID
    with open(filename, 'r', encoding='utf-8') as tracks_file:
        tracks_reader = csv.reader(tracks_file, delimiter=';')
        for row in tracks_reader:
            tracks[int(row[0])] = row[1]
    return tracks


def read_urm(filename):
    urm = np.zeros(shape=(MAX_USERID, MAX_TRACKID), dtype=np.float32)
    with open(filename, 'r', encoding='utf-8') as dataset_file:
        urm_reader = csv.reader(dataset_file, delimiter=';')
        for row in urm_reader:
            urm[int(row[0]), int(row[1])] = float(1.0)
    return lil_matrix(urm, dtype=np.float32)


def read_data():
    data = read_urm('../data/urm.csv')
    tracks = read_tracks('../data/trackname2Id.csv')
    users = read_users('../data/username2Id.csv')
    return users, tracks, data


def estimate_rates(users, data, username):
    K = 90
    if username not in users:
        print("No such user in dataframe")
        return

    user_index = users.index(username)

    U, s, Vt = sparsesvd(data, K)

    dim = (len(s), len(s))
    S = np.zeros(dim, dtype=np.float32)
    for i in range(0, len(s)):
        S[i, i] = math.sqrt(s[i])

    U = csc_matrix(np.transpose(U), dtype=np.float32)
    S = csc_matrix(S, dtype=np.float32)
    Vt = csc_matrix(Vt, dtype=np.float32)

    rightTerm = S * Vt

    prod = U[user_index, :] * rightTerm

    return prod.todense()


def prepare_data(data):
    res = data.copy()
    for i in range(MAX_USERID):
        for j in test_indices:
            if data[i, j] != 0:
                res[i,j] = 0
    return res


def compute_error(estimated, actual):
    pass


if __name__ == '__main__':
    users, songs, data = read_data()
    prepared_data = prepare_data(data)
    res = []
    for i in range(len(users)):
        user = users[i]
        estimated_ratings = estimate_rates(users, prepared_data, user)
        error = compute_error(estimated_ratings, data[i, :])
        pass
        # get estimated ratings
        # compute error
        # append to result
    # save result to file