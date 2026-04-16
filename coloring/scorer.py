from email.policy import default
from math import inf

from data import Data, Subject
from sqlalchemy.orm import Session
from networkx import Graph
from functools import reduce
import numpy as np

default_weights = 4, 3.6

def scorer_factory(db: Data, session: Session, bl_g: Graph, les_g: Graph):
    def get_weight(lesson):
        return les_g.nodes[lesson]['weight'] if lesson in les_g else 0
    
    subjects = [
        [les.id for les in sub.lessons] for sub in session.query(Subject) if len(sub.lessons)
    ]

    def get_params(color, rev_color, uncolored): 
        if len(uncolored):
            uncolored_lessons = sum([get_weight(les) for les in uncolored])
        else:
            uncolored_lessons = 0
        same_day = 0
        for subject in subjects:
            # print(subject)
            weight = get_weight(subject[0])
            days = [0 for _ in range(5)]
            for lesson in subject:
                if lesson not in color:
                    continue
                day = bl_g.nodes[color[lesson][0]]['day']
                same_day += weight * days[day]
                days[day] += 1
        return uncolored_lessons, same_day
    

    return get_params

def minmax(min_max, param):
    # print(param)
    res = []
    for mm, val in zip(min_max, param):
        minimum, maximum = mm
        # print(minimum, maximum, val)
        new_min = min(minimum, val)
        new_max = max(maximum, val)
        res.append([new_min, new_max])
        # print(res)
    return np.array(res)


def rank(data, weigths: list, min_maxes = None):
    # print(data[1][:10])
    # data = solution, params
    # find min and max values of each parameter
    solution, params = zip(*data)
    # print(params[:10])
    min_max = reduce(minmax , params, ((inf, 0) for _ in range(len(params[0]))))
    mins, maxes = np.transpose(min_max)
    if min_maxes:
        pass
    def score(data):
        _, params = data
        total = 0
        for minimum, maximum, val, weigth in zip(mins, maxes, params, weigths):
            if minimum == maximum:
                continue
            # print(minimum, maximum, val, weigth)
            p = weigth * (val - minimum) / (maximum - minimum)
            # print(p)
            total += p
        # print(total)
        return total
        
    data.sort(key=score)
