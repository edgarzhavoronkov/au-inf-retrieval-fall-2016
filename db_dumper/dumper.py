import csv
import sqlite3

conn = sqlite3.connect('../data/onlyLikedTracks1.sqlite')


def get_users(sqlite_conn):
    users = []
    c = conn.cursor()
    c.execute("SELECT DISTINCT USERNAME FROM LIKEDTRACK2USER ORDER BY USERNAME")
    for row in c.fetchall():
        users.append(row[0])
    return users


def get_tracks(sqlite_conn):
    tracks = []
    c = conn.cursor()
    c.execute("SELECT DISTINCT TRACKNAME FROM LIKEDTRACK2USER ORDER BY TRACKNAME")
    for row in c.fetchall():
        tracks.append(row[0])
    return tracks


def get_user_liked_tracks(sqlite_conn, username):
    liked = []
    c = sqlite_conn.cursor()
    c.execute("SELECT TRACKNAME FROM LIKEDTRACK2USER WHERE USERNAME=?", (username,))
    for row in c.fetchall():
        liked.append(row[0])
    return liked


if __name__ == "__main__":
    global conn
    all_users = get_users(conn)
    users = []
    tracks = get_tracks(conn)

    for user in all_users:
        liked_tracks = get_user_liked_tracks(conn, user)
        if len(liked_tracks) > 10:
            users.append(user)

    with open('../data/username2Id.csv', 'w', newline='', encoding='utf-8') as users_file:
        user_writer = csv.writer(users_file, delimiter=';')
        for i in range(len(users)):
            user_writer.writerow([i, users[i]])

    with open('../data/trackname2Id.csv', 'w', newline='', encoding='utf-8') as tracks_file:
        track_writer = csv.writer(tracks_file, delimiter=';')
        for i in range(len(tracks)):
            track_writer.writerow([i, tracks[i]])

    with open('../data/urm.csv', 'w', newline='', encoding='utf-8') as user_track_file:
        user_track_writer = csv.writer(user_track_file, delimiter=';')
        for i in range(len(users)):
            liked_tracks = get_user_liked_tracks(conn, users[i])
            for track in liked_tracks:
                track_id = tracks.index(track)
                user_track_writer.writerow([i, track_id])