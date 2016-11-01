import sqlite3

import pandas as pd
import numpy as np

conn = sqlite3.connect('../data/tracks2users.sqlite')

def get_usernames(sqlite_conn):
    users = []
    c = conn.cursor()
    c.execute("SELECT NAME FROM USERS")
    for row in c.fetchall():
        users.append(row[0])
    return users

def get_tracks(sqlite_conn):
    tracks = []
    c = conn.cursor()
    c.execute("SELECT NAME FROM TRACKS")
    for row in c.fetchall():
        tracks.append(row[0])
    return tracks

# join tables for fuck's sake!
def get_user_liked_tracks(sqlite_conn, username):
    liked = []
    c = sqlite_conn.cursor()
    c.execute("SELECT ID FROM USERS WHERE NAME=?", (username,))
    for row in c.fetchall():
        user_id = row[0]
        c.execute("SELECT TRACKID FROM LIKEDTRACK2USER WHERE USERID=?", (user_id,))
        for another_row in c.fetchall():
            track_id = another_row[0]
            c.execute("SELECT NAME FROM TRACKS WHERE ID=?", (track_id,))
            for yet_another_row in c.fetchall():
                liked.append(yet_another_row[0])
    return liked

def dump(sqlite_conn, output):
    usernames = get_usernames(sqlite_conn)
    tracknames = list(set(get_tracks(sqlite_conn)))
    n_tracks = len(tracknames)
    d = {}
    for username in usernames:
        d.update({username : [0]*n_tracks})
    df = pd.DataFrame(d, index=tracknames)
    for username in usernames:
        liked_tracks = get_user_liked_tracks(sqlite_conn, username)
        for track in liked_tracks:
            df = df.set_value(track, username, 1)

    df.to_csv(output, index_label='track', encoding='utf-8')

if __name__ == "__main__":
    global conn
    dump(conn, '../data/track2users2.csv')