from math import inf
from data import Data, Subject, Teacher, Student, LessonBlockDB, Lesson, Classroom, Distance, Metadata
from sqlalchemy.orm import Session
from networkx import Graph
from functools import reduce
import numpy as np

# default_weights = 4, 3.8, 3, 3
# param_names = ['Nieprzypisane lekcje', 'Rozłozenie lekcji w tygodniu', 'Pojedyncze lekcje nauczyciela', 'Bieganie uczniów']
# MAX_BREAK = 4 # * 5 minutes: max length of a break for lessons to be considered grouped

def scorer_factory(db: Data, session: Session, bl_g: Graph, les_g: Graph):
    def get_weight(lesson):
        return les_g.nodes[lesson]['weight'] if lesson in les_g else 0
    def get_distance(cl1, cl2):
        gr_1 = cl_groups[cl1]
        gr_2 = cl_groups[cl2]
        if gr_1 == gr_2:
            return 0
        return distances[(gr_1, gr_2)]
    
    settings = session.query(Metadata).first()
    MAX_BREAK = settings.max_break
    
    
    teachers = []
    for teacher in session.query(Teacher):
        t = []
        for subject in teacher.subjects:
            t.extend([l.id for l in subject.lessons])
        teachers.append(t)
    
    students = []
    for student in session.query(Student):
        s = []
        for subject in student.subjects:
            s.extend([l.id for l in subject.lessons])
        students.append(s)
    print(teachers)
    print(students)

    blocks = {bl.id: (bl.day, bl.start, bl.length) for bl in session.query(LessonBlockDB)}
    pinned_lessons = {l.id: (l.block_id, l.classroom_id) for l in session.query(Lesson) if l.block and l.block_locked}
    cl_groups = {cl.id: cl.group_id for cl in session.query(Classroom)}
    distances = {(dist.start_id, dist.end_id): dist.distance for dist in session.query(Distance)}

    min_same_day_param = 0
    subjects = []
    for subject in session.query(Subject):
        # n_of_lessons = len(subject.lessons)
        # days_av = subject.teacher.days_available()
        # w = len(subject.students)
        # if n_of_lessons > days_av:
            # cost =  w * (n_of_lessons-days_av)
            # min_same_day_param += cost
        lessons = []
        days = [[] for _ in range(5)]
        for lesson in subject.lessons:
            lessons.append(lesson.id)
            if lesson.block and lesson.block_locked:
                start = lesson.block.start
                end = start + lesson.block.length
                day = lesson.block.day
                # min_same_day_param += w * len(days[day])
                days[day].append((start, end))
        subjects.append((lessons, days, subject.target_block_length))

    def get_params(color, rev_color, uncolored): 
        # lessons not in the plan
        if len(uncolored):
            uncolored_lessons = sum([get_weight(les) for les in uncolored])
        else:
            uncolored_lessons = 0
        lesson_distribution = 0
        # multiple lessons on the same day
        # same_day = -min_same_day_param
        for subject in subjects:
            lessons, days, target_bl_len = subject
            days = [day.copy() for day in days]
            # print(days)
            if not len(lessons):
                continue
            weight = get_weight(lessons[0])
            for lesson in lessons:
                if lesson not in color:
                    continue
                bl_id = color[lesson][0]
                day, start, length = blocks[bl_id]
                if target_bl_len == 1:
                    lesson_distribution += weight * len(days[day])
                days[day].append((start, length+start))

            if target_bl_len < 2:
                continue
            # number of lessons not placeable in blocks
            cost = - (len(lessons)%target_bl_len)
            
            for day in days:
                if not len(day):
                    continue
                # print(day)
                lesson_groupings = []
                day.sort(key= lambda x: x[0])
                block_end = day[0][1]
                group_length = 1
                for block in day[1:]:
                    if block[0] > block_end + MAX_BREAK:
                        lesson_groupings.append(group_length)
                    else:
                        group_length += 1
                    block_end = block[1]
                lesson_groupings.append(group_length)
                d_cost = sum(lesson_groupings)
                if target_bl_len in lesson_groupings or target_bl_len<max(lesson_groupings):
                    d_cost -= target_bl_len
                cost += d_cost * (d_cost+1) // 2
                

            # add cost
            if cost > 0:
                lesson_distribution += cost

        # teacher
        single_lessons = 0
        teachers_running_around = 0
        for teacher in teachers:
            days = [[] for _ in range(5)]
            for lesson in teacher:
                # try:
                if lesson in pinned_lessons:
                    block, clrm = pinned_lessons[lesson]
                elif lesson in color:
                    block, clrm = color[lesson]
                else:
                    continue
                # except:
                    # print(session.query(Lesson).filter_by(id=lesson).first().name_and_time())
                day, start, length = blocks[block]
                days[day].append((start, length, clrm))

            teacher_running = 0
            runs = 0
            for day in days:
                if not len(day):
                    continue
                if len(day) == 1:
                    single_lessons += 1
                day.sort(key=lambda les: les[0])
                start, length, clrm = day[0]
                for lesson in day[1:]:
                    next_start, next_length, next_clrm = lesson
                    break_length = next_start - (start + length)
                    # print(break_length)
                    if break_length > MAX_BREAK:
                        continue
                    runs += 1
                    teacher_running += get_distance(clrm, next_clrm)/break_length
                    start, length, clrm = next_start, next_length, next_clrm
            if runs:
                teachers_running_around += teacher_running/runs
        
        # students running around
        students_running_around = 0
        for student in students:
            days = [[] for _ in range(5)]
            for lesson in student:
                if lesson in pinned_lessons:
                    block, clrm = pinned_lessons[lesson]
                elif lesson in color:
                    block, clrm = color[lesson]
                else:
                    continue
                day, start, length = blocks[block]
                days[day].append((start, length, clrm))

            student_running = 0
            runs = 0
            for day in days:
                if not len(day):
                    continue
                day.sort(key=lambda les: les[0])
                start, length, clrm = day[0]
                for lesson in day[1:]:
                    next_start, next_length, next_clrm = lesson
                    break_length = next_start - (start + length)
                    # print(break_length)
                    if break_length > MAX_BREAK:
                        continue
                    runs += 1
                    student_running += get_distance(clrm, next_clrm)/break_length
                    start, length, clrm = next_start, next_length, next_clrm
            if runs:
                students_running_around += student_running/runs


        return uncolored_lessons, lesson_distribution, single_lessons, students_running_around, teachers_running_around
    

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


def rank(data, weigths: list, all_params: list, min_maxes = None, note_results=True):
    # print(data[0])
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
    if note_results:
        for old, new in zip(all_params, pop_params):
            old.append(new)
        
    data.sort(key=score)
