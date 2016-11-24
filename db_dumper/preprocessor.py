import numpy as np
import csv
import random
from scipy.sparse import csc_matrix

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


def readURM():
    urm = np.zeros(shape=(MAX_USERID, MAX_TRACKID), dtype=np.float32)
    with open('../data/urm.csv', 'r', encoding='utf-8') as dataset_file:
        urm_reader = csv.reader(dataset_file, delimiter=';')
        for row in urm_reader:
            urm[int(row[0]), int(row[1])] = float(1.0)
    return csc_matrix(urm, dtype=np.float32)



train_set_size = int(0.8 * MAX_TRACKID)
test_set_size = MAX_TRACKID - train_set_size

if __name__ == '__main__':
    tracks = readTracks()
    users = readUsers()
    urm = readURM()

    training_indices = random.sample(range(len(tracks)), train_set_size)


    print(training_indices)


