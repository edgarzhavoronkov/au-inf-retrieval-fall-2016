import os
import pickle
import sqlite3
import sys

import numpy as np
from scipy.sparse import csr_matrix
from sklearn.metrics import pairwise_distances

conn = sqlite3.connect('../data/data.sqlite')

def signup(username):
    pass


def like(username, track):
    pass


def get_max_uid(conn):
    c = conn.cursor()
    c.execute("SELECT COUNT(ID) FROM USERS")
    for row in c.fetchall():
        return row[0]

def get_max_trackid(conn):
    c = conn.cursor()
    c.execute("SELECT COUNT(ID) FROM TRACKS")
    for row in c.fetchall():
        return row[0]


MAX_TRACKID = get_max_trackid(conn) + 1
MAX_USERID = get_max_uid(conn) + 1


def read_data(conn):
    data = read_urm(conn)
    tracks = read_tracks(conn)
    users = read_users(conn)
    return users, tracks, data


def read_users(conn):
    users = [''] * MAX_USERID
    c = conn.cursor()
    c.execute("SELECT ID, NAME FROM USERS")
    for row in c.fetchall():
        users[int(row[0])] = row[1]
    return users


def read_tracks(conn):
    tracks = [''] * MAX_TRACKID
    c = conn.cursor()
    c.execute("SELECT ID, NAME FROM TRACKS")
    for row in c.fetchall():
        tracks[int(row[0])] = row[1]
    return tracks


def read_urm(conn):
    c = conn.cursor()
    urm = np.zeros(shape=(MAX_USERID, MAX_TRACKID), dtype=np.double)
    c.execute("SELECT * FROM LIKEDTRACK2USER")
    for row in c.fetchall():
        urm[int(row[0]), int(row[1])] = 1.0
    return csr_matrix(urm, dtype=np.double)


def init_dist_if_need(data, filename):
    if not os.path.exists(filename):
        dist = pairwise_distances(data, metric='cosine')
        pickle.dump(dist, open('../data/dist.dat', 'wb'))
        return dist
    else:
        return pickle.load(open(filename, 'rb'))


def get_user_id(name, conn):
    c = conn.cursor()
    c.execute("SELECT ID FROM USERS WHERE NAME=?", (name,))
    for row in c.fetchall():
        return row[0]


def get_track_name(tid, conn):
    c = conn.cursor()
    c.execute("SELECT NAME FROM TRACKS WHERE ID=?", (int(tid),))
    for row in c.fetchall():
        return row[0]


def get_similar_users_ids(dist, user_id, count, conn):
    dists = dist[user_id,  : ]
    sorted = np.argsort(dists)
    res = []
    for i in range(count + 1):
        uid = sorted[i]
        if (uid != user_id):
            res.append(uid)
    return res


def get_liked_tracks_ids(user_id, conn):
    c = conn.cursor()
    c.execute("SELECT TRACKID from LIKEDTRACK2USER JOIN USERS ON USERID=USERS.ID WHERE ID=?", (str(user_id),))
    res = []
    for row in c.fetchall():
        res.append(int(row[0]))
    return res


def get_frequencies(similar_users_ids, conn):
    res = [0] * MAX_TRACKID
    for uid in similar_users_ids:
        liked_tracks = get_liked_tracks_ids(uid, conn)
        for trackid in liked_tracks:
            res[int(trackid)] += 1
    return res


def get_artist_name(track_id, conn):
    c = conn.cursor()
    c.execute("SELECT ARTISTS.NAME FROM ARTISTS JOIN TRACKS ON ARTISTS.ID = TRACKS.ARTISTID WHERE TRACKS.ID=?", (int(track_id),))
    for row in c.fetchall():
        return row[0]


if __name__ == '__main__':
    global conn
    username = sys.argv[1]

    users, tracks, data = read_data(conn)
    dist = init_dist_if_need(data, '../data/dist.dat')

    user_id = get_user_id(username, conn)
    liked_tracks_ids = get_liked_tracks_ids(user_id, conn)
    similar_users_ids = get_similar_users_ids(dist, user_id, 100, conn)
    frequencies = get_frequencies(similar_users_ids, conn)

    for track_id in liked_tracks_ids:
        frequencies[track_id] = 0

    res_ids = np.argsort(frequencies)[0 : 10]
    for res_id in res_ids:
        if (res_id != 0):
            artist_name = get_artist_name(res_id, conn)
            track_name = get_track_name(res_id, conn)
            print(artist_name + " - " + track_name)
        