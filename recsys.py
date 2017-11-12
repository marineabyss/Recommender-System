import pandas as pd
import math
import collections
import json
import requests as re


def get_average(lst):
    return sum(lst)/len(lst)


def probability_func(lst):
    return sum(1 for [s,c] in lst if s > 2 if c is False)/len(lst)

def is_weekend(day):
    return day.strip() in ['Sat', 'Sun']


# Считывание данных из файла
df = pd.read_csv('data.csv', index_col=0)
data = df.transpose().to_dict(orient='series')

cdf = pd.read_csv('context.csv', index_col=0)
context = cdf.transpose().to_dict(orient='series')

for key in data:
    data[key].index = data[key].index.str.strip()
    context[key].index = context[key].index.str.strip()


# Расчет метрики сходства
similarity = collections.defaultdict(dict)
user = 'User 39'
for second_user in set(data).symmetric_difference([user]):
    scores = [[fv,sv] for ((kf,fv), (ks,sv)) in [[(kf,fv), (ks,sv)] for (kf, fv) in data[user].items() if fv > - 1 for (ks, sv) in data[second_user].items() if sv > -1] if kf==ks]
    coeff = sum(s[0] * s[1] for s in scores) / (math.sqrt(sum(s[0] * s[0] for s in scores)) * math.sqrt(sum(s[1] * s[1] for s in scores)))
    similarity[user][second_user] = round(coeff, 3)

# Расчет оценок
res = collections.defaultdict(dict)
recommendation = collections.defaultdict(dict)
c = collections.Counter(similarity[user]).most_common()
user_avg = get_average(list(v for k, v in data[user].items() if v > -1))
for movie in (k for k, v in data[user].items() if v == -1):
    predicted_rating = user_avg
    neigh_numerator = 0
    neigh_denominator = 0
    for neighbour in list(u for u, v in c)[:5]:
        if data[neighbour][movie] > -1:
            neighbour_avg = get_average(list(v for k, v in data[neighbour].items() if v > -1))
            neigh_numerator += similarity[user][neighbour]*(data[neighbour][movie]-neighbour_avg)
            neigh_denominator += abs(similarity[user][neighbour])
    predicted_rating+=neigh_numerator/neigh_denominator
    res[user][movie] = round(predicted_rating, 2)
    probability = probability_func(list([data[u][movie], is_weekend(context[u][movie])] for u, v in c)[:6])
    recommendation[user][movie] = round(probability * res[user][movie], 3)
recommendation[user] = collections.Counter(recommendation[user]).most_common()

# POST-запрос
url = 'https://cit-home1.herokuapp.com/api/rs_homework_1'
headers = {'Content-Type': 'application/json'}
for res_user in res:
    user_res = {}
    user_res['user'] = int(res_user.strip("User "))
    user_res['1'] = {}
    user_res['2'] = {}
    for res_user_movie in res[res_user]:
        user_res['1'][res_user_movie.lower()] = res[res_user][res_user_movie]
    if recommendation[res_user][0][1] != 0:
        user_res['2'][recommendation[res_user][0][0].lower()] = recommendation[res_user][0][1]
    else:
        greatest_res = collections.Counter(res[user]).most_common(1)[0]
        user_res['2'][greatest_res[0].lower()] = greatest_res[1]
    print(json.dumps(user_res, indent=4))
    r = re.post(url, data=json.dumps(user_res), headers=headers)
    print(r)

