import pandas as pd
import sys
from scipy.spatial.distance import cosine

# TODO: re-sample data
data = pd.read_csv('../data/sample.csv', encoding='utf-8')

def signup(username):
    pass

def like(username, track):
    pass

# Helper function to get similarity scores
def getScore(history, similarities):
    return sum(history * similarities) / sum(similarities)

# поскольку все дедлайны просраны, то мы используем косинусное расстояние, как было написано в туториале
def recommend(username):
    data_no_user = data.drop('user', 1)
    data_ibs = pd.DataFrame(index=data_no_user.columns, columns=data_no_user.columns)
    rng = range(0, len(data_ibs.columns))
    for i in rng:
        for j in rng:
            data_ibs.ix[i, j] = 1 - cosine(data_no_user.ix[:, i], data_no_user.ix[:, j])

    data_neighbours = pd.DataFrame(index=data_ibs.columns, columns=range(1, 11))

    for i in range(0, len(data_ibs.columns)):
        data_neighbours.ix[i, :10] = data_ibs.ix[0:, i].sort_values(ascending=False)[:10].index

    data_sims = pd.DataFrame(index=data.index, columns=data.columns)
    data_sims.ix[:, :1] = data.ix[:, :1]

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
    recommend(username)
