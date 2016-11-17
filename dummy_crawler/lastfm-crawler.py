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
        crawl_user_liked_tracks(current_user, sqlite_conn)
        #user_queue += get_user_friends(current_user)
        pickle.dump(user_queue, open('../data/user_queue.dat', 'wb'))
        print("User queue dumped on disk. Length - {0}".format(len(user_queue)))
        print("Pausing before next user. You can interrupt crawling now.")
        time.sleep(SLEEP_BETWEEN_USERS)
        print("Proceeding to the next user.")


def crawl_user_liked_tracks(username, conn):
    liked_tracks = get_user_liked_tracks(username)
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
                # "mbid": track["mbid"]
            })
        if int(result["lovedtracks"]["@attr"]["totalPages"]) == i + 1:
            break
        time.sleep(SLEEP_BETWEEN_TOPTRACKS)
    return liked


def write_liked_tracks_to_user(tracks, username, conn):
    c = conn.cursor()
    for track in tracks:
        c.execute("INSERT INTO LIKEDTRACK2USER(USERNAME, TRACKNAME) VALUES (?, ?)", (username, track["name"]))
        conn.commit()


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
        conn.execute('''CREATE TABLE LIKEDTRACK2USER (
                        USERNAME TEXT NOT NULL,
                        TRACKNAME TEXT NOT NULL,
                        UNIQUE (USERNAME, TRACKNAME) ON CONFLICT IGNORE)''')

    return conn


def initialize_queue(filename):
    if not os.path.exists(filename):
        return ['rj']
    else:
        return pickle.load(open(filename, 'rb'))


if __name__ == "__main__":
    global conn, user_queue
    user_queue = initialize_queue('../data/user_queue.dat')
    conn = initialize_db("../data/onlyLikedTracks1.sqlite")
    do_crawl(user_queue, conn)
    conn.close()
