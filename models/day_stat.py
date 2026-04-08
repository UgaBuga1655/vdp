class DayStat():
    time_in_school = 0
    time_in_lessons = 0
    time_of_free_work = 0

    def __add__(self, stat: 'DayStat'):    
        self.time_in_school += stat.time_in_school
        self.time_in_lessons += stat.time_in_lessons
        self.time_of_free_work += stat.time_of_free_work
        return self

    def __truediv__(self, other):
        self.time_in_school/=other
        self.time_in_lessons/=other
        self.time_of_free_work/=other
        return self