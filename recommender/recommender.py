import pandas as pd
import sys
from scipy.spatial.distance import pdist, squareform, jaccard

# TODO: re-sample data
data = pd.read_csv('../data/sample.csv', encoding='utf-8')
data = data.drop('Unnamed: 0', 1)


def signup(username):
    pass


def like(username, track):
    pass


# Helper function to get similarity scores
def getScore(history, similarities):
    return sum(history * similarities) / sum(similarities)


def filter_data(data, user):
    songmask = data[data['user'] == user].values[0] == 1
    users_with_same_songs = data.T[songmask].sum() >= 1

    songmask[-1] = True # to get username
    selected = data[users_with_same_songs].T[songmask].T
    return selected




def recommend(username):
    global data

    if username not in data['user'].values:
        print("No such user in dataframe")
        return

    data = filter_data(data, username)

    data_no_user = data.drop('user', 1)

    data_ibs = pd.DataFrame(
        data=squareform(pdist(data_no_user.T, 'jaccard')),
        index=data_no_user.columns,
        columns=data_no_user.columns
    )

    data_ibs = 1 - data_ibs

    top_songs_number = min(len(data_ibs.columns), 10)

    data_neighbours = pd.DataFrame(index=data_ibs.columns, columns=range(1, top_songs_number+1 ))

    for i in range(0, len(data_ibs.columns)):
        data_neighbours.ix[i, :top_songs_number] = data_ibs.ix[0:, i].sort_values(ascending=False)[:top_songs_number].index

    data_sims = pd.DataFrame(index=data.index, columns=data.columns)
    data_sims.ix[:, :1] = data.ix[:, :1]

    for i in range(0, len(data_sims.index)):
        for j in range(0, len(data_sims.columns) - 1):
            user = data_sims.index[i]
            product = data_sims.columns[j]

            if data.ix[user][product] == 1:
                data_sims.ix[user][product] = 0
            else:
                product_top_names = data_neighbours.ix[product][1:top_songs_number]
                product_top_sims = data_ibs.ix[product].sort_values(ascending=False)[1:top_songs_number]
                user_purchases = data_no_user.ix[user, product_top_names]

                data_sims.ix[user][product] = getScore(user_purchases, product_top_sims)

    # Get the top songs
    rec_songs_number = min(top_songs_number, 6)
    columns = ['user', ] + [str(i) for i in range(1, rec_songs_number + 1)]
    data_recommend = pd.DataFrame(index=data_sims.index, columns=columns)
    data_recommend.ix[0:, 0] = data_sims.ix[:, 0]

    # Instead of top song scores, we want to see names
    for i in range(0, len(data_sims.index)):
        u = data_sims.index[i]
        data_recommend.ix[u, 1:] = data_sims.ix[u, :-1].sort_values(ascending=False).ix[:(rec_songs_number+1), ].index.transpose()

    data_recommend['user'] = data['user']
    data_recommend.set_index('user', inplace=True)
    # Print a sample

    print(data_recommend.T[username][:rec_songs_number+1])


if __name__ == '__main__':
    global data
    username = sys.argv[1]
    recommend(username)
