import numpy as np
import math as mt
import csv
from sparsesvd import sparsesvd
from scipy.sparse import csr_matrix, csc_matrix

MAX_TRACKID = 320495
MAX_USERID = 1742

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


def computeSVD(urm, rank):
    U, s, Vt = sparsesvd(urm, rank)

    dim = (len(s), len(s))
    S = np.zeros(dim, dtype=np.float32)
    for i in range(0, len(s)):
        S[i, i] = mt.sqrt(s[i])

    U = csr_matrix(np.transpose(U), dtype=np.float32)
    S = csr_matrix(S, dtype=np.float32)
    Vt = csr_matrix(Vt, dtype=np.float32)

    return U, S, Vt

def readUsersTest():
    uTest = dict()
    with open("../data/testSample.csv", 'r', encoding='utf-8') as testFile:
        testReader = csv.reader(testFile, delimiter=';')
        for row in testReader:
            uTest[int(row[0])] = list()

    return uTest


def getTracksLiked():
    tracksLiked = dict()
    with open("./trainSample.csv", 'r', encoding='utf-8') as trainFile:
        urmReader = csv.reader(trainFile, delimiter=';')
        for row in urmReader:
            try:
                tracksLiked[int(row[0])].append(int(row[1]))
            except:
                tracksLiked[int(row[0])] = list()
                tracksLiked[int(row[0])].append(int(row[1]))

    return tracksLiked

if __name__ == '__main__':
    urm = readURM()
    users = readUsers()
    tracks = readTracks()
    U, S, Vt = computeSVD(urm, 50)
    uTest = readUsersTest()
    print(S.shape)


