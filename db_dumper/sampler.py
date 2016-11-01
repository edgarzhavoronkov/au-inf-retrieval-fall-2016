import pandas as pd

data = pd.read_csv('../data/tracks2users2_wo_zeros.csv', index_col='track')

# берем выборку из ста случайных песен
data = data.sample(200)
data = data.transpose()
# и ста случайных пользователей
# data = data.sample(200)


data['user'] = data.index
data.index = range(len(data['user']))
# убираем из выборки этого чувака, потому что он какой-то неадекватный
data = data[data.user != 'Unnamed: 0']

data.to_csv('../data/sample.csv', encoding='utf-8')
