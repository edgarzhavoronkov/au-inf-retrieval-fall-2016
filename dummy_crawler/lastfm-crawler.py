import json
import os
import sqlite3
import sys
import time
from urllib.request import urlopen

# Global vars
db = None
conn = None
crawl_order = []
max_top_track_pages = 10
SLEEP_BETWEEN_TOPTRACKS = 5  # seconds
SLEEP_BETWEEN_FRIENDS = 5  # seconds
SLEEP_BETWEEN_USERS = 10  # seconds


def do_crawl(user_queue: list, sqlite_conn):
    while len(user_queue) > 0:
        current_user = user_queue.pop(0)
        print("Finding user {0}".format(current_user))
        is_user_new, user_id = write_or_find_user(current_user, sqlite_conn)
        if not is_user_new:
            print("User found< continue to the next one")
            continue
        print("User {0} got id {1}".format(current_user, user_id))

        crawl_user_tracks(current_user, user_id, sqlite_conn)
        crawl_user_liked_tracks(current_user, user_id, sqlite_conn)

        user_queue += get_user_friends(current_user)

        print("Pausing before next user. You can interrupt crawling now.")
        time.sleep(SLEEP_BETWEEN_USERS)
        print("Proceeding to the next user.")


def write_or_find_user(username, conn):
    c = conn.cursor()
    c.execute("SELECT * FROM USERS WHERE NAME=?", (username,))
    if c.rowcount > 0:
        return False, 0
    c.execute("INSERT INTO USERS (NAME) VALUES (?)", (username,))
    user_id = c.lastrowid
    conn.commit()
    return True, user_id


def crawl_user_tracks(username, user_id, conn):
    top_tracks = get_user_top_tracks(username)
    write_tracks(top_tracks, conn)


def crawl_user_liked_tracks(username, user_id, conn):
    liked_tracks = get_user_liked_tracks(username)
    write_liked_tracks_to_user(liked_tracks, user_id, conn)


def get_number_of_user_top_tracks(username):
    total_tracks_url = get_url("user.gettoptracks", username)
    print("Getting user's {0} number of tracks".format(username))
    data = urlopen(total_tracks_url).read().decode("utf-8")
    result = json.loads(data)["toptracks"]["@attr"]["total"]
    print("User {0} has {1} tracks total".format(username, result))
    return result


def get_user_top_tracks(username):
    tracks = []
    user_tracks_count = get_number_of_user_top_tracks(username)

    print("Getting 10% of top tracks of user {0} ".format(username))
    top_tracks_url = get_url("user.gettoptracks", username, "&limit={0}".format(min((int)(user_tracks_count) // 10 + 1, 5000)))
    data = urlopen(top_tracks_url).read().decode("utf-8")
    result = json.loads(data)
    for track in result["toptracks"]["track"]:
        tracks.append({
            "name": track["name"],
            # "mbid": track["mbid"]
        })
    time.sleep(SLEEP_BETWEEN_TOPTRACKS)
    return tracks


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
                # "mbid": track["mbid"]
            })
        if int(result["lovedtracks"]["@attr"]["totalPages"]) == i + 1:
            break
        time.sleep(SLEEP_BETWEEN_TOPTRACKS)
    return liked


def write_tracks(tracks, conn):
    c = conn.cursor()
    c.executemany("INSERT INTO TRACKS (NAME) VALUES (:name)", tracks)
    conn.commit()


def write_liked_tracks_to_user(tracks, user_id, conn):
    c = conn.cursor()
    for track in tracks:
        c.execute("SELECT ID FROM TRACKS WHERE NAME=?", (track["name"],))
        for row in c.fetchall():
            track_id = row[0]
            c.execute("INSERT INTO LIKEDTRACK2USER(USERID, TRACKID) VALUES (?, ?)", (user_id, track_id))
            conn.commit()


def get_user_friends(user):
    i = 1
    result = []
    while True:
        print("Getting friends of {0}, page {1}".format(user, i))
        friends_url = get_url("user.getFriends", user)
        data = urlopen(friends_url).read().decode("utf-8")
        data_obj = json.loads(data)
        if "friends" in data_obj:
            for user in data_obj["friends"]["user"]:
                if "name" in user:
                    result.append(user["name"])
            if int(data_obj["friends"]["@attr"]["totalPages"]) < i:
                i += 1
                time.sleep(SLEEP_BETWEEN_FRIENDS)
            else:
                break
        else:
            break
    return result


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
        conn.execute('''CREATE TABLE USERS (ID INTEGER PRIMARY KEY AUTOINCREMENT, NAME TEXT NOT NULL)''')

        conn.execute('''CREATE TABLE TRACKS (ID INTEGER PRIMARY KEY AUTOINCREMENT, NAME TEXT UNIQUE ON CONFLICT IGNORE NOT NULL)''')

        conn.execute('''CREATE TABLE LIKEDTRACK2USER (USERID INT NOT NULL, TRACKID INT NOT NULL,
        FOREIGN KEY(USERID) REFERENCES USERS(ID), FOREIGN KEY(TRACKID) REFERENCES TRACKS(ID))''')

    return conn


if __name__ == "__main__":
    # main()
    global conn
    conn = initialize_db("onlyTracks.sqlite")
    do_crawl(["EdgarSeal"], conn)
    conn.close()
