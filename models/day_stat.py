class DayStat():
    time_in_school = 0
    time_in_lessons = 0
    free_work_time = 0
    free_work_time_between_lessons = 0


    def __add__(self, stat: 'DayStat'):    
        self.time_in_school += stat.time_in_school
        self.time_in_lessons += stat.time_in_lessons
        self.free_work_time += stat.free_work_time
        self.free_work_time_between_lessons += stat.free_work_time_between_lessons
        return self

    def __truediv__(self, other:int):
        self.time_in_school/=other
        self.time_in_lessons/=other
        self.free_work_time/=other
        self.free_work_time_between_lessons/=other
        return self