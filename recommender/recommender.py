import csv
import math
import sys
from sparsesvd import sparsesvd

import numpy as np
from scipy.sparse import csc_matrix


def signup(username):
    pass


def like(username, track):
    pass


MAX_TRACKID = 320495
MAX_USERID = 1517


def read_data():
    data = read_urm('../data/urm.csv')
    tracks = read_tracks('../data/trackname2Id.csv')
    users = read_users('../data/username2Id.csv')
    return users, tracks, data


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
    return csc_matrix(urm, dtype=np.float32)


# TODO: estimate rank of decomposition!
def recommend_svd(username):
    K = 90
    users, tracks, data = read_data()
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

    result = []

    estimatedRatings = prod.todense()
    recom = ((-estimatedRatings).argsort()[:250]).tolist()[0]
    for r in recom:
        if data[user_index, r] == 0:
            result.append(r)

            if len(result) == 5:
                break

    print([tracks[i] for i in result])


if __name__ == '__main__':
    global data
    username = sys.argv[1]
    recommend_svd(username)
