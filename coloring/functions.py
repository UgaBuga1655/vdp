from data import Data, LessonBlockDB, Lesson
from queue import PriorityQueue
from itertools import count
from random import choice, randint, shuffle
from networkx import Graph
from db_config import settings

def random_coloring(params, queue, scorer):
    lg, bg, feas, chunk_size = params
    data = []
    report_size = 70
    i=0
    for _ in range(chunk_size):
        solution = crazy(lg, bg, feas)
        params = scorer(*solution)
        data.append((solution, params))
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
    rev_colors = {}
    # days = {}
    adj_colors = {}
    uncolored = []
    
    queue = PriorityQueue()

    counter = count()
    # lessons = les_g.nodes.items()
    # shuffle(lessons)
    for lesson, data in les_g.nodes.items():
        # print(lesson)
        # print(data)
        # if data['subject'] not in days:
        #     days[data['subject']] = []
        # days[data['subject']].append(bl_g)
        adj_colors[lesson] = set()
        # first lessons with fewer feasible blocks
        # if tied, longer lessons go first
        # uncolored.add((lesson, data))
        queue.put((randint(1, 2*len(les_g.nodes)), next(counter), (lesson, data)))
        # queue.put((len(feas[lesson]), -lesson.length, next(counter), lesson))


    # greedily color the graph
    while queue.qsize():
        lesson, data = queue.get()[-1]

        shuffle(feas[lesson])
        for color in feas[lesson]:
            # point in space and time is occupied
            if color in rev_colors:
                continue
            block, classroom = color
            # # other lesson on the same day
            # if bl_g.nodes[block]['day'] in days[data['subject']]:
            #     continue
            # collifing lesson
            if block in adj_colors[lesson]:
                continue
            # classroom occupied by other lesson
            classroom_is_occupied = False
            for n_bl in bl_g[block]:
                if (n_bl, classroom) in rev_colors:
                    classroom_is_occupied = True
                    break
            if classroom_is_occupied:
                continue
            
            color = (block, classroom)
            colors[lesson] = color
            rev_colors[color] = lesson

            for neighbour in les_g[lesson]:
                adj_colors[neighbour].add(block)
                adj_colors[neighbour].update(bl_g[block])
            # days[data['subject']].append(bl_g.nodes[block]['day'])

            break 

        # failed to place lesson in the plan
        if lesson not in colors:
            uncolored.append(lesson)

    return colors, rev_colors, uncolored

def mutate_batch(params, queue, scorer):
    les_g, bl_g, feas, survivors = params
    # print(f'starting batch: {len(survivors)}')
    pop_size = settings.pop_size
    cutoff = int(settings.cutoff*pop_size)
    num_of_children = int(pop_size/cutoff)
    children = []
    for survivor in survivors:
        for _ in range(num_of_children):
            children.append(mutate(les_g, bl_g, feas, *survivor[0], scorer))
    queue.put(('done', children))

def mutate(les_g, bl_g, feas, coloring: dict, rev_coloring: dict, uncolored: list, scorer) -> tuple[dict, int]:
    child = coloring.copy()
    rev_child = rev_coloring.copy()
    child_uncolored = uncolored.copy()
    def uncolor(lesson):
        cl = child.pop(lesson)
        _ = rev_child.pop(cl)
        child_uncolored.append(lesson)
    
    def set_color(lesson, color):
        if lesson in child:
            old_color = child.pop(lesson)
            rev_child.pop(old_color)
        if color in rev_child:
            old_lesson = rev_child.pop(color)
            child_uncolored.append(old_lesson)
            child.pop(old_lesson)
        child[lesson] = color
        rev_child[color] = lesson


    

    
    for _ in range(randint(0, 5)):
        if not (len(child_uncolored)):
            break
        # find random uncolored lesson
        lesson = choice(child_uncolored)
        child_uncolored.remove(lesson)
        # force it randomly into solution
        color = choice(feas[lesson])
        set_color(lesson, color)
        block, classroom = color
        # uncolor all nodes unhappy about it
        my_subject = les_g.nodes[lesson]['subject']
        # my_day = bl_g.nodes[block]['day']
        for neighbour in les_g[lesson]:
            # already uncolored
            if neighbour not in child:
                continue
            # collision
            n_color = child[neighbour]
            # if n_color not in rev_child:
                # print('dupa')
            n_block, n_classroom = n_color
            if n_block == block or n_block in bl_g[block]:
                uncolor(neighbour)
                continue

            # same day
            # n_subject =  les_g.nodes[neighbour]['subject']
            # n_day = bl_g.nodes[n_block]['day']
            # if  n_subject == my_subject and my_day == n_day:
            #     uncolor(neighbour)
            #     continue
        
        # classroom is occupied
        for overlapping_block in bl_g[block]:
            color = (overlapping_block, classroom)
            if color in rev_child:
                uncolor(rev_child[color])
                continue
        

    # try to fit uncolored lessons
    child_uncolored.sort(key= lambda l: len(feas[l]), reverse=True)
    for lesson in child_uncolored:
        adj_cols = []
        for neighbour in les_g[lesson]:
            # won't interfere if uncolored
            if neighbour not in child:
                continue
            n_block, n_classroom = child[neighbour]
            adj_cols.append(n_block)
            adj_cols.extend(bl_g[n_block])
        
        # my_days = []
        subject = les_g.nodes[lesson]['subject']
        # # same day
        # for other_lesson in [l for l in les_g[lesson] if l in child and les_g.nodes[l]['subject'] == subject]:
        #     block, classroom = child[other_lesson]
        #     my_days.append(bl_g.nodes[block]['day'])
        # find first suitable block
        for color in feas[lesson]:
            # place in space time occupied
            if color in rev_child:
                continue
            block, classroom = color
            # other lesson interferes
            if block in adj_cols:
                continue
            # other lesson takes place in the same day
            # day = bl_g.nodes[block]['day']
            # if day in my_days:
            #     continue
            # classroom is occupied
            classroom_is_occupied = False
            for n_bl in bl_g[block]:
                if (n_bl, classroom) in rev_child:
                    classroom_is_occupied = True
                    break
            if classroom_is_occupied:
                continue
            
            set_color(lesson, color)
            child_uncolored.remove(lesson)
            break

    # calculate score
    params = scorer(child, rev_child, child_uncolored)
    # score = sum([les_g.nodes[les]['weight'] for les in child_uncolored])
    return (child, rev_child, child_uncolored), params

