from data import LessonBlockDB, Lesson
from queue import PriorityQueue
from itertools import count
from random import choice, randint, shuffle
from networkx import Graph
from collections.abc import Callable
# from db_config import settings

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
    # initialize data structures
    colors = {}
    rev_colors = {}
    adj_colors = {}
    uncolored = []
    
    queue = PriorityQueue()

    counter = count()
    for lesson, data in les_g.nodes.items():
        adj_colors[lesson] = set()
        # order them randomly
        queue.put((randint(1, 2*len(les_g.nodes)), next(counter), (lesson, data)))


    # greedily color the graph
    while queue.qsize():
        lesson, data = queue.get()[-1]

        shuffle(feas[lesson])
        for color in feas[lesson]:
            # point in space and time is occupied
            if color in rev_colors:
                continue
            block, classroom = color
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

            break 

        # failed to place lesson in the plan
        if lesson not in colors:
            uncolored.append(lesson)

    return colors, rev_colors, uncolored

def legalize_batch(params, queue, scorer):
    les_g, bl_g, feas, batch = params
    legalized = []
    report_size = 50
    i = 0
    for solution in batch:
        legalized.append(mutate(les_g, bl_g, feas, *solution[0], scorer, mutate=False))
        i += 1
        if i > report_size:
            queue.put(('progress', legalized))
            legalized = []
            i = 0
    queue.put(('done', legalized))

    

def mutate_batch(params, queue, scorer, pop_size, cutoff):
    les_g, bl_g, feas, survivors = params
    num_of_children = int(pop_size/cutoff)
    children = []
    for survivor in survivors:
        for _ in range(num_of_children):
            children.append(mutate(les_g, bl_g, feas, *survivor[0], scorer))
    queue.put(('done', children))

def mutate(les_g, bl_g, feas, coloring: dict, rev_coloring: dict, uncolored: list, scorer, mutate=True) -> tuple[dict, int]:
    child = coloring.copy()
    rev_child = rev_coloring.copy()
    child_uncolored = uncolored.copy()

    def uncolor(lesson):
        child_uncolored.append(lesson)
        if lesson not in child:
            return
        cl = child.pop(lesson)
        if cl in rev_child:
            _ = rev_child.pop(cl)
    
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

    def viable_factory(lesson) -> Callable[[int, int], bool]:
        adj_cols = []
        for neighbour in les_g[lesson]:
            # won't interfere if uncolored
            if neighbour not in child:
                continue
            n_block, n_classroom = child[neighbour]
            if n_block not in bl_g:
                continue
            adj_cols.append(n_block)
            adj_cols.extend(bl_g[n_block])
        

        def is_viable(color) -> bool:
            # not feasible in the first place
            if color not in feas[lesson]:
                return False
            # place in space time occupied
            if color in rev_child:
                return False
            block, classroom = color
            if block not in bl_g:
                return False
            # other lesson interferes
            if block in adj_cols:
                return False
            # classroom is occupied
            for n_bl in bl_g[block]:
                if (n_bl, classroom) in rev_child:
                    return False
            return True
        return is_viable
    
    if mutate:
        for _ in range(randint(0, 6)):
            if len(child_uncolored):
                lesson = choice(child_uncolored)
                child_uncolored.remove(lesson)
            else:
                lesson = choice(list(child.keys()))
                uncolor(lesson)
            # find random uncolored lesson
            # force it randomly into solution
            color = choice(feas[lesson])
            set_color(lesson, color)
            block, classroom = color
            # uncolor all nodes unhappy about it
            for neighbour in les_g[lesson]:
                # already uncolored
                if neighbour not in child:
                    continue
                # collision
                n_color = child[neighbour]
                n_block, n_classroom = n_color
                if n_block == block or n_block in bl_g[block]:
                    uncolor(neighbour)
                    continue
                
            
            # classroom is occupied
            for overlapping_block in bl_g[block]:
                color = (overlapping_block, classroom)
                if color in rev_child:
                    uncolor(rev_child[color])
        # switch rooms
        for _ in range(randint(5,10)):
            lesson, color = choice(list(child.items()))
            block, classroom = color
            is_viable = viable_factory(lesson)
            other_classrooms = [
                cl for cl in feas[lesson] if 
                (cl[1] == classroom) and is_viable(cl)
            ]
            if not len(other_classrooms):
                continue
            set_color(lesson, choice(other_classrooms))
    else:
        # child_uncolored = set(child_uncolored)
        #legalize
        for lesson in les_g:
            if lesson not in child:
                child_uncolored.append(lesson)
        to_remove = []
        to_uncolor = []
        for lesson, color in child.items():
            # if color[0] == 261:
            #     print(f'dupa: {lesson}, {261 in bl_g}')
            #     to_uncolor.append(lesson)
            #     continue
            if lesson not in les_g:
                to_remove.append(lesson)
                continue
            if not viable_factory(lesson)(color):
                # print(color)
                to_uncolor.append(lesson)

        for lesson in to_remove:
            uncolor(lesson)
            child.pop(lesson)
        for lesson in to_uncolor:
            uncolor(lesson)

        # get rid of unwanted lessons in uncolored set
        child_uncolored = [les for les in child_uncolored if les in les_g]

    # try to fit uncolored lessons
    child_uncolored.sort(key= lambda l: len(feas[l]))
    for lesson in child_uncolored[::-1]:
        
        is_viable = viable_factory(lesson)
                # my_days = []
        # subject = les_g.nodes[lesson]['subject']
        for color in feas[lesson]:
            if not is_viable(color):
                continue
            
            set_color(lesson, color)
            child_uncolored.remove(lesson)
            break

    # calculate score
    params = scorer(child, rev_child, child_uncolored)
    return (child, rev_child, child_uncolored), params

