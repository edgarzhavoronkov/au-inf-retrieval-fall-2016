import csv

import pandas as pd
import sys
from scipy.spatial.distance import pdist, squareform, jaccard
from scipy.sparse import csc_matrix, lil_matrix
from sparsesvd import sparsesvd
import numpy as np
import math
from scipy.sparse.linalg import *

# TODO: re-sample data
#data = pd.read_csv('../data/likedTracks2users.csv', encoding='utf-8')
#data = data.drop('Unnamed: 0', 1)

def signup(username):
    pass

def like(username, track):
    pass

# Helper function to get similarity scores
def getScore(history, similarities):
    return sum(history * similarities) / sum(similarities)

def read_data(filename):
    with open(filename, 'r', encoding='utf-8') as datafile:
        dataReader = csv.reader(datafile, delimiter=',')
        users = dataReader.__next__()[1:]
        songs = []
        result = lil_matrix((len(users), 320495))
        song = 0
        for row in dataReader:
            songs.append(row[0])
            for i in range(0,len(row)-1):
                if row[i+1] == '1':
                    result.rows[i].append(song)
                    result.data[i].append(1)
            song+=1
        return users, songs, result


def recommend_svd(username):
    K = 90
    users, songs, data = read_data("../data/likedTracks2users.csv")
    if username not in users:
        print("No such user in dataframe")
        return

    userindex = users.index(username)

    sparse_data = data.tocsc()

    U, s, Vt = sparsesvd(sparse_data, K)

    dim = (len(s), len(s))
    S = np.zeros(dim, dtype=np.float32)
    for i in range(0, len(s)):
        S[i, i] = math.sqrt(s[i])

    U = csc_matrix(np.transpose(U), dtype=np.float32)
    S = csc_matrix(S, dtype=np.float32)
    Vt = csc_matrix(Vt, dtype=np.float32)

    rightTerm = S * Vt

    prod = U[userindex, :] * rightTerm

    result = []

    # we convert the vector to dense format in order to get the indices of the movies with the best estimated ratings
    estimatedRatings = prod.todense()
    recom = (-estimatedRatings).argsort()[:250]
    for r in recom:
        if data[userindex][r]==0:
            result.append(r)

            if len(result) == 5:
                break

    print([songs[i] for i in result])


def recommend(username):
    if username in data['user']:
        print("No such user in dataframe")
        return

    data_no_user = data.drop('user', 1)

    data_ibs = pd.DataFrame(
        data=squareform(pdist(data_no_user.T, 'jaccard')),
        index=data_no_user.columns,
        columns=data_no_user.columns
    )

    data_ibs = 1 - data_ibs

    data_neighbours = pd.DataFrame(index=data_ibs.columns, columns=range(1, 11))

    for i in range(0, len(data_ibs.columns)):
        data_neighbours.ix[i, :10] = data_ibs.ix[0:, i].sort_values(ascending=False)[:10].index

    data_sims = pd.DataFrame(index=data.index, columns=data.columns)
    data_sims['user'] = data['user']

    for i in range(0, len(data_sims.index)):
        for j in range(0, len(data_sims.columns) - 1):
            user = data_sims.index[i]
            product = data_sims.columns[j]

            if data.ix[i][j] == 1:
                data_sims.ix[i][j] = 0
            else:
                product_top_names = data_neighbours.ix[product][1:10]
                product_top_sims = data_ibs.ix[product].sort_values(ascending=False)[1:10]
                user_purchases = data_no_user.ix[user, product_top_names]

                data_sims.ix[i][j] = getScore(user_purchases, product_top_sims)

    # Get the top songs
    data_recommend = pd.DataFrame(index=data_sims.index, columns=['user', '1', '2', '3', '4', '5', '6'])
    data_recommend.ix[0:, 0] = data_sims.ix[:, 0]

    # Instead of top song scores, we want to see names
    for i in range(0, len(data_sims.index)):
        data_recommend.ix[i, 1:] = data_sims.ix[i, :].sort_values(ascending=False).ix[1:7, ].index.transpose()

    data_recommend['user'] = data['user']
    data_recommend.set_index('user', inplace=True)
    # Print a sample

    print(data_recommend.T[username][:4])


if __name__ == '__main__':
    global data
    username = sys.argv[1]
    recommend_svd(username)
