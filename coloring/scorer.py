from email.policy import default
from math import inf

from data import Data, Subject
from sqlalchemy.orm import Session
from networkx import Graph
from functools import reduce
import numpy as np

default_weights = 4, 3.6
param_names = ['Nieprzypisane lekcje', 'Lekcje w ten sam dzień']

def scorer_factory(db: Data, session: Session, bl_g: Graph, les_g: Graph):
    def get_weight(lesson):
        return les_g.nodes[lesson]['weight'] if lesson in les_g else 0
    
    min_same_day_param = 0
    subjects = []
    for subject in session.query(Subject):
        n_of_lessons = len(subject.lessons)
        days_av = subject.teacher.days_available()
        if n_of_lessons > days_av:
            w = len(subject.students)
            cost =  w * (n_of_lessons-days_av)
            print(n_of_lessons, days_av)
            print(w, cost)
            min_same_day_param += cost
        lessons = []
        days = [0 for _ in range(5)]
        print(days)
        for lesson in subject.lessons:
            lessons.append(lesson.id)
            if lesson.block:
                print(f'incrementing {lesson.block.day} ({days[lesson.block.day]})')
                days[lesson.block.day] += 1
        print(lessons, days)
        subjects.append((lessons, days))
    print(min_same_day_param)

    def get_params(color, rev_color, uncolored): 
        if len(uncolored):
            uncolored_lessons = sum([get_weight(les) for les in uncolored])
        else:
            uncolored_lessons = 0
        same_day = 0
        for subject in subjects:
            lessons, days = subject
            days = days.copy()
            if not len(lessons):
                continue
            weight = get_weight(lessons[0])
            for lesson in lessons:
                if lesson not in color:
                    continue
                day = bl_g.nodes[color[lesson][0]]['day']
                same_day += weight * days[day]
                days[day] += 1
        return uncolored_lessons, same_day-min_same_day_param
    

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


def rank(data, weigths: list, all_params: list, min_maxes = None):
    # print(data[1][:10])
    # data = solution, params
    # find min and max values of each parameter
    solution, params = zip(*data)
    # print(params[:10])
    min_max = reduce(minmax , params, ((inf, 0) for _ in params[0]))
    mins, maxes = np.transpose(min_max)
    if min_maxes:
        pass
    pop_params = [[] for _ in weigths]
    def score(data):
        _, params = data
        total = 0
        i = 0
        for minimum, maximum, val, weigth in zip(mins, maxes, params, weigths):
            if minimum == maximum:
                continue
            # print(minimum, maximum, val, weigth)
            p = weigth * (val - minimum) / (maximum - minimum)
            # print(p)
            pop_params[i].append(val)
            total += p
            i+=1
        # print(total)
        return total
    for old, new in zip(all_params, pop_params):
        old.append(new)
        
    data.sort(key=score)
