from data import Data, LessonBlockDB, Lesson
from queue import PriorityQueue
from itertools import count
from random import choice, randint, shuffle
from networkx import Graph
from db_config import settings

def random_coloring(params, queue):
    lg, bg, feas, chunk_size = params
    data = []
    report_size = chunk_size/7
    i=0
    for _ in range(chunk_size):
        coloring = crazy(lg, bg, feas)
        cost = sum([lg.nodes[les]['weight'] for les, block in coloring.items() if block[0] is None])
        data.append((coloring, cost))
        i += 1
        if i > report_size:
            queue.put(('progess', data))
            data = []
            i = 0

    queue.put(('done', data))




def crazy(les_g: Graph, bl_g, feas) -> dict[Lesson, LessonBlockDB]:
    # print(len(bl_g))
    # print('dupa')
    
            
    # initialize data structures
    colors = {}
    days = {}
    adj_colors = {}
    # uncolored = set()
    queue = PriorityQueue()

    counter = count()
    # lessons = les_g.nodes.items()
    # shuffle(lessons)
    for lesson, data in les_g.nodes.items():
        # print(lesson)
        # print(data)
        if data['subject'] not in days:
            days[data['subject']] = []
        days[data['subject']].append(bl_g)
        adj_colors[lesson] = set()
        # first lessons with fewer feasible blocks
        # if tied, longer lessons go first
        queue.put((randint(1, 2*len(les_g.nodes)), next(counter), (lesson, data)))
        # queue.put((len(feas[lesson]), -lesson.length, next(counter), lesson))


    # greedily color the graph
    while queue.qsize():
        lesson, data = queue.get()[-1]

        # get first feasible block
        # first_feasible = None
        shuffle(feas[lesson])
        colors[lesson] = (None, None)
        for block, classroom in feas[lesson]:
            # print(block)
            # print(bl_g.nodes[block])
            if bl_g.nodes[block]['day'] in days[data['subject']]:
                continue
            if block in adj_colors[lesson]:
                continue

            colors[lesson] = (block, classroom)
            for neighbour in les_g[lesson]:
                adj_colors[neighbour].add(block)
                adj_colors[neighbour].update(bl_g[block])
            days[data['subject']].append(bl_g.nodes[block]['day'])

            break 
            
    return colors

def mutate_batch(params, queue):
    les_g, bl_g, feas, survivors = params
    # print(f'starting batch: {len(survivors)}')
    pop_size = settings.pop_size
    cutoff = int(settings.cutoff*pop_size)
    num_of_children = int(pop_size/cutoff)
    children = []
    for survivor in survivors:
        for _ in range(num_of_children):
            children.append(mutate(les_g, bl_g, feas, survivor[0]))
    queue.put(('done', children))

def mutate(les_g, bl_g, feas, coloring: dict) -> tuple[dict, int]:
    # print('mutating')
    child = coloring.copy()
    # find random uncolored lesson
    # print(f'child {child}')
    uncolored = {les for les, blo in child.items() if blo[0] is None}
    # print(uncolored)
    if not len(uncolored):  
        # print('already perfect')
        return coloring, 0

    for _ in range(randint(0,4)):
        lesson = uncolored.pop()
        # force it randomly into solution
        color = choice(feas[lesson])
        child[lesson] = color
        block, classroom = color
        # uncolor all nodes unhappy about it
        my_subject = les_g.nodes[lesson]['subject']
        my_day = bl_g.nodes[block]['day']
        for neighbour in les_g[lesson]:
            n_block, n_classroom = child[neighbour]
            # already uncolored
            if not n_block:
                continue
            # collision
            if n_block == block or n_block in bl_g[block]:
                child[neighbour] = (None, None)
                uncolored.add(neighbour)
            # same day
            n_subject =  les_g.nodes[neighbour]['subject']
            n_day = bl_g.nodes[n_block]['day']
            if  n_subject == my_subject and my_day == n_day:
                child[neighbour] = (None, None)
                uncolored.add(neighbour)
        # for other_lesson in lesson.subject.lessons:
        #     if other_lesson == lesson:
        #         continue
        #     if other_lesson in child:
        #         child[other_lesson] = None
        #         uncolored.append(other_lesson)
            # if other_lesson not in
        
    # try to fit uncolored lessons in
    queue = []
    # print(len(uncolored))
    # uncolored = {les for les, blo in child.items() if blo is None}
    # print(len(uncolored)) 
    for lesson in uncolored:
        queue.append((lesson, len(feas[lesson])))
    queue.sort(key=lambda x: x[1])
    # print(len(queue))
    for lesson, _ in queue:
        # if lesson.block_locked:
            # print('dupa')
        adj_cols = []
        for neighbour in les_g[lesson]:
            n_block, n_classroom = child[neighbour]
            if not n_block:
                continue
            adj_cols.append(n_block)
            adj_cols.extend(bl_g[n_block])
        
        m_days = []
        subject = les_g.nodes[lesson]['subject']
        for other_lesson in [l for l in les_g[lesson] if les_g.nodes[l]['subject'] == subject]:
            block, classroom = child[other_lesson]
            # else:
            #     block = other_lesson.block
            if block:
                m_days.append(bl_g.nodes[block]['day'])
        # f = [bl for bl in feas[lesson] if not (bl in adj_cols or bl.day in m_days)]
        # if len(f):
        #     child[lesson] = f
        for block, classroom in feas[lesson]:
            if block in adj_cols:
                continue
            # print(block.day, m_days)
            day = bl_g.nodes[block]['day']
            if day in m_days:
                continue
            child[lesson] = block, classroom
            break

    # calculate score
    # print(uncolored)
    score = sum([les_g.nodes[les]['weight'] for les in uncolored])
    # print('finished mutating')
    return child, score

