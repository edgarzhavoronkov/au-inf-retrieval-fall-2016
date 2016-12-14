import sqlite3

import numpy as np
from scipy.sparse import csr_matrix

conn = sqlite3.connect('../data/data.sqlite')

current_user = None

def jaccard_similarities(mat):
    cols_sum = mat.getnnz(axis=0)
    ab = mat.T * mat

    # for rows
    aa = np.repeat(cols_sum, ab.getnnz(axis=0))
    # for columns
    bb = cols_sum[ab.indices]

    similarities = ab.copy()
    similarities.data /= (aa + bb - ab.data)

    return similarities

def is_user_present(username, conn):
    c = conn.cursor()
    c.execute("SELECT COUNT(NAME) FROM USERS WHERE NAME=?", (username,))
    for row in c.fetchall():
        return row[0] > 0


def add_user(username, conn):
    c = conn.cursor()
    c.execute("INSERT INTO USERS(NAME) VALUES (?)", (username,))
    conn.commit()

def signup(username, conn):
    global current_user
    add_user(username, conn)
    current_user = username


def like(username, artist, track, conn):
    c = conn.cursor()
    user_id = get_user_id(username, conn)
    track_id = get_track_id(track, artist, conn)
    c.execute("INSERT INTO LIKEDTRACK2USER(USERID, TRACKID) "
              "VALUES (?, ?)", (str(user_id), str(track_id)))
    conn.commit()


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


def get_user_id(name, conn):
    c = conn.cursor()
    c.execute("SELECT ID FROM USERS WHERE NAME=?", (name,))
    for row in c.fetchall():
        return row[0]

def get_track_id(track, artist, conn):
    c = conn.cursor()
    c.execute("SELECT TRACKS.ID "
              "FROM TRACKS JOIN ARTISTS ON TRACKS.ARTISTID = ARTISTS.ID "
              "WHERE ARTISTS.NAME=? AND TRACKS.NAME=? LIMIT 1", (artist, track))
    for row in c.fetchall():
        return row[0]

def get_track_name(tid, conn):
    c = conn.cursor()
    c.execute("SELECT NAME FROM TRACKS WHERE ID=?", (int(tid),))
    for row in c.fetchall():
        return row[0]


def get_similar_users_ids(dist, user_id, count, conn):
    dists = dist[user_id,  : ].toarray()[0]
    sorted = np.flipud(np.argsort(dists.data))
    res = []
    for i in range(count + 1):
        uid = sorted[i]
        if (uid != user_id):
            res.append(uid)
    return res


def get_liked_tracks_ids(user_id, conn):
    c = conn.cursor()
    c.execute("SELECT TRACKID "
              "FROM LIKEDTRACK2USER JOIN USERS "
              "ON USERID=USERS.ID "
              "WHERE ID=?", (str(user_id),))
    res = []
    for row in c.fetchall():
        res.append(int(row[0]))
    return res


def get_frequencies(dist, user_id, similar_users_ids, conn):
    res = [0] * MAX_TRACKID
    for uid in similar_users_ids:
        liked_tracks = get_liked_tracks_ids(uid, conn)
        for trackid in liked_tracks:
            res[int(trackid)] += dist[user_id, uid]
    return res


def get_artist_name(track_id, conn):
    c = conn.cursor()
    c.execute("SELECT ARTISTS.NAME "
              "FROM ARTISTS JOIN TRACKS "
              "ON ARTISTS.ID = TRACKS.ARTISTID "
              "WHERE TRACKS.ID=?", (int(track_id),))
    for row in c.fetchall():
        return row[0]


def recommend_by_user(username, conn):
    users, tracks, data = read_data(conn)
    dist = jaccard_similarities(data.transpose(True).tocsc())

    user_id = get_user_id(username, conn)
    liked_tracks_ids = get_liked_tracks_ids(user_id, conn)

    if len(liked_tracks_ids) == 0:
        recommend_most_popular(conn)
    else:
        similar_users_ids = get_similar_users_ids(dist, user_id, 150, conn)
        frequencies = get_frequencies(dist, user_id, similar_users_ids, conn)

        for track_id in liked_tracks_ids:
            frequencies[track_id] = 0

        res_ids = np.flipud(np.argsort(frequencies))[0 : 10]
        for res_id in res_ids:
            if (res_id != 0):
                artist_name = get_artist_name(res_id, conn)
                track_name = get_track_name(res_id, conn)
                print(artist_name + " - " + track_name + " (" + str(frequencies[res_id]) + ") ")


def recommend_most_popular(conn):
    users, tracks, data = read_data(conn)
    data = data.tocsc()
    freqs = data.sum(0).tolist()[0]
    tops = np.flipud(np.argsort(freqs))[0:10]
    for top in tops:
        if (top != 0):
            artist_name = get_artist_name(top, conn)
            track_name = get_track_name(top, conn)
            print(artist_name + " - " + track_name + " (" + str(freqs[top]) +")")


def get_tracks_by_artist(artist, conn):
    res = []
    c = conn.cursor()
    c.execute("SELECT DISTINCT(TRACKS.NAME) "
              "FROM TRACKS JOIN ARTISTS "
              "ON TRACKS.ARTISTID = ARTISTS.ID "
              "WHERE ARTISTS.NAME=?", (artist,))
    for row in c.fetchall():
        res.append(row[0])
    return res


if __name__ == '__main__':
    print("Tiny recommender engine")
    while True:
        user_input = input(">> ").split(" ")

        if user_input[0] == "signup":
            username = user_input[1]
            if is_user_present(username, conn):
                print("User {0} already present, select another name".format(username))
            else:
                signup(username, conn)
                print("Signed up as {0}".format(username))
        elif user_input[0] == "signin":
            username = user_input[1]
            if is_user_present(username, conn):
                current_user = username
                print("Logged in as {0}".format(username))
            else:
                print("User {0) is not present".format(username))
        elif user_input[0] == "like":
            if current_user is None:
                print("Sign up to like first!")
            else:
                artist = input("\tArtist: ")
                track = input("\tTrack: ")
                like(current_user, artist, track, conn)

        elif user_input[0] == "tracks":
            artist = " ".join(user_input[1:])
            print('\n'.join(get_tracks_by_artist(artist, conn)))

        elif user_input[0] == "recommend":
            if current_user is None:
                recommend_most_popular(conn)
            else:
                recommend_by_user(current_user, conn)

        elif user_input[0] == "liked":
            if current_user is None:
                print("Sign up or sign in to get liked tracks first!")
            else:
                user_id = get_user_id(current_user, conn)
                liked_tracks_ids = get_liked_tracks_ids(user_id, conn)
                for res_id in liked_tracks_ids:
                    if (res_id != 0):
                        artist_name = get_artist_name(res_id, conn)
                        track_name = get_track_name(res_id, conn)
                        print(artist_name + " - " + track_name)

        elif user_input[0] == "exit":
            break

        else:
            print("Unknown command! Please, try again")