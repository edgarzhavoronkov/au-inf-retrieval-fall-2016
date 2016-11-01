import pandas as pd

data = pd.read_csv('../data/track2users2.csv', index_col='track')

# удаляем пользователей, которые ничего не полайкали, им рекоммендуют отдельные алгоритмы
data = data[(data.T != 0).any()]
data = data.transpose()
# то же самое делаем с песнями
data = data[(data.T != 0).any()]
data = data.transpose()

data.to_csv('../data/tracks2users2_wo_zeros.csv', encoding='utf-8', index_col='track')
