import json
import os
import sqlite3
import sys
import time
import pickle
from urllib.request import urlopen

# Global vars
db = None
conn = None
crawl_order = []
max_top_track_pages = 10
max_friends_pages = 10
SLEEP_BETWEEN_TOPTRACKS = 1  # seconds
SLEEP_BETWEEN_FRIENDS = 5  # seconds
SLEEP_BETWEEN_USERS = 2  # seconds

user_queue = []


def do_crawl(user_queue, sqlite_conn):
    while len(user_queue) > 0:
        current_user = user_queue.pop(0)
        print("Crawling user {0}".format(current_user))
        crawl_user(current_user, sqlite_conn)
        #user_queue += get_user_friends(current_user)
        pickle.dump(user_queue, open('../data/users_queue2.dat', 'wb'))
        print("User queue dumped on disk. Length - {0}".format(len(user_queue)))
        print("Pausing before next user. You can interrupt crawling now.")
        time.sleep(SLEEP_BETWEEN_USERS)
        print("Proceeding to the next user.")


def crawl_user(username, conn):
    liked_tracks = get_user_liked_tracks(username)
    write_artists(liked_tracks, conn)
    write_tracks(liked_tracks, conn)
    write_user(username, conn)
    write_liked_tracks_to_user(liked_tracks, username, conn)


def get_user_liked_tracks(username):
    liked = []
    for i in range(max_top_track_pages):
        print("Getting liked tracks of user {0} page {1}".format(username, i))
        liked_tracks_url = get_url("user.getlovedtracks", username, "&limit=200&page={0}".format(i + 1))
        data = urlopen(liked_tracks_url).read().decode("utf-8")
        result = json.loads(data)
        for track in result["lovedtracks"]["track"]:
            liked.append({
                "name": track["name"],
                "artist": track["artist"]
            })
        if int(result["lovedtracks"]["@attr"]["totalPages"]) == i + 1:
            break
        time.sleep(SLEEP_BETWEEN_TOPTRACKS)
    return liked


def write_tracks(tracks, conn):
    c = conn.cursor()
    for entry in tracks:
        track = entry["name"]
        artist_name = entry["artist"]["name"]
        artist_id = get_artist_id(artist_name, conn)
        c.execute("INSERT INTO TRACKS(NAME, ARTISTID) VALUES (?, ?)", (track, artist_id))
        conn.commit()


def write_artists(tracks_artists, conn):
    c = conn.cursor()
    for entry in tracks_artists:
        artist = entry["artist"]["name"]
        c.execute("INSERT INTO ARTISTS(NAME) VALUES (?)", (artist,))
        conn.commit()


def write_user(username, conn):
    c = conn.cursor()
    c.execute("INSERT INTO USERS(NAME) VALUES  (?)", (username,))
    conn.commit()


def write_liked_tracks_to_user(tracks_data, username, conn):
    c = conn.cursor()
    for track in tracks_data:
        trackname = track["name"]
        artist_name = track["artist"]["name"]
        trackid = get_track_id(trackname, artist_name, conn)
        userid = get_user_id(username, conn)
        c.execute("INSERT INTO LIKEDTRACK2USER(USERID, TRACKID) VALUES(?, ?)", (userid, trackid))
        conn.commit()



def get_artist_id(name, conn):
    c = conn.cursor()
    c.execute("SELECT ID FROM ARTISTS WHERE NAME=?", (name,))
    for row in c.fetchall():
        return row[0]

def get_track_id(name, artist_name, conn):
    c = conn.cursor()
    artist_id = get_artist_id(artist_name, conn)
    c.execute("SELECT ID FROM TRACKS WHERE NAME=? AND ARTISTID=?", (name, artist_id))
    for row in c.fetchall():
        return row[0]

def get_user_id(name, conn):
    c = conn.cursor()
    c.execute("SELECT ID FROM USERS WHERE NAME=?", (name,))
    for row in c.fetchall():
        return row[0]


def get_user_friends(username):
    friends = []
    for i in range(max_friends_pages):
        print("Getting friends of {0}, page {1}".format(username, i))
        friends_url = get_url("user.getfriends", username)
        data = urlopen(friends_url).read().decode("utf-8")
        result = json.loads(data)
        for user in result["friends"]["user"]:
            if "name" in user:
                friends.append(user["name"])
        if int(result["friends"]["@attr"]["totalPages"]) == i + 1:
            break
        time.sleep(SLEEP_BETWEEN_FRIENDS)
    return friends


def get_url(cmd, login, params=""):
    api_key = '19a67cbeccdc5fe7c26adcf34cf5a4f8'
    url = "http://ws.audioscrobbler.com/2.0/?method={0}&user={1}&api_key={2}&format=json{3}".format(cmd, login, api_key,
                                                                                                    params)
    url = url.replace(" ", "%20")
    return url


# Called when CTRL+C is pressed or there is an error
def flush_db(signal="", frame=""):
    global conn
    print("Crawling finished. Closing DB.")
    conn.close()
    sys.exit(0)


def initialize_db(filename):
    tables_init_needed = not os.path.exists(filename)
    conn = sqlite3.connect(filename)
    if tables_init_needed:
        conn.execute('''CREATE TABLE USERS (
                        ID INTEGER PRIMARY KEY AUTOINCREMENT,
                        NAME TEXT NOT NULL)''')

        conn.execute('''CREATE TABLE ARTISTS (
                        ID INTEGER PRIMARY KEY AUTOINCREMENT,
                        NAME TEXT NOT NULL,
                        UNIQUE (NAME) ON CONFLICT IGNORE)''')

        conn.execute('''CREATE TABLE LIKEDTRACK2USER (
                        USERID TEXT NOT NULL,
                        TRACKID TEXT NOT NULL,
                        UNIQUE (USERID, TRACKID) ON CONFLICT IGNORE)''')

        conn.execute('''CREATE TABLE TRACKS (
                        ID INTEGER PRIMARY KEY AUTOINCREMENT,
                        NAME TEXT NOT NULL,
                        ARTISTID INTEGER,
                        FOREIGN KEY(ARTISTID) REFERENCES ARTISTS(ID))''')

    return conn


def initialize_queue(filename):
    if not os.path.exists(filename):
        return ['rj']
    else:
        return pickle.load(open(filename, 'rb'))

# For debug - get all liked tracks of user by name
# SELECT ARTISTS.NAME, t.NAME FROM ARTISTS JOIN (SELECT NAME, ARTISTID FROM TRACKS JOIN (SELECT TRACKID from LIKEDTRACK2USER JOIN USERS ON USERID=USERS.ID WHERE NAME='EdgarSeal') ON TRACKS.ID = TRACKID) as t ON ARTISTS.ID=ARTISTID

if __name__ == "__main__":
    global conn, user_queue
    user_queue = initialize_queue('../data/users_queue2.dat')
    conn = initialize_db("../data/data.sqlite")
    do_crawl(user_queue, conn)
    conn.close()