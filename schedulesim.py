import math
from random import choice
from functools import reduce

class Task:
    def __init__(self, phase, period, cost, deadline, id):
        self.phase = phase
        self.period = period
        self.cost = cost
        self.deadline = deadline
        self.id = id

    def __str__(self) -> str:
        return "[T " + str(self.id) + ", PHASE " + str(self.phase) + ", PERIOD " + str(self.period) + ", COST " + str(self.cost) + ", DL " + str(self.deadline) + "]"
    
    def __repr__(self) -> str:
        return self.__str__()

class Job:
    def __init__(self, deadline_time, exec_time, task_id):
        self.deadline_time = deadline_time
        self.exec_time = exec_time
        self.task_id = task_id

    def __str__(self) -> str:
        out = "[T " + str(self.task_id) + ", DLT " + str(self.deadline_time) + ", EXT " + str(self.exec_time)
        return out + "]"

    def __repr__(self) -> str:
        return self.__str__()

class ContextSwitch:
    def __init__(self, csc, incoming, task_id, link=None):
        self.incoming = incoming
        self.link = link
        self.task_id = task_id
        self.exec_time = csc

        if incoming: self.link.deadline_time -= csc

    def __str__(self) -> str:
        out = "["
        if self.incoming: out += "IN"
        else: out += "OUT"
        return out + " context switch, T " + str(self.task_id) + ", EXT " + str(self.exec_time) + "]"

    def __repr__(self) -> str:
        return self.__str__()

class Simulator:
    def __init__(self, task_set):
        self.task_set = task_set
        self.task_set.sort(key=lambda i: i.id)
        self.release_times = [(t.period, t.phase) for t in self.task_set]
        self.hyperperiod = reduce(lambda a, b: a * b // math.gcd(a, b), [t.period for t in self.task_set])
        self.max_time = self.hyperperiod + max([t.phase for t in self.task_set]) # time at which task set is determined to be schedulable

    def printState(self):
        out = "time " + str(self.time) + " active "
        for i in range(len(self.active_jobs)):
            if self.active_jobs[i] is not None:
                out += "[" + str(self.active_jobs[i]) + " PROC " + str(i) + "] "
        out += "queued " + str(self.queued_jobs)
        print(out)
        return

    # returns a job, incoming context switch, or outgoing context switch for assignment to active_jobs
    def contextSwitchCheck(self, old_job, new_job):
        if self.context_switch_cost == 0: return new_job
        incoming = ContextSwitch(self.context_switch_cost, True, new_job.task_id, new_job)
        if old_job is None: return incoming
        return ContextSwitch(self.context_switch_cost, False, old_job.task_id, incoming)

    def numContextSwitch(self):
        i = 0
        for job in self.active_jobs:
            if type(job) is ContextSwitch: i += 1
        return i

    def simulate(self, algorithm, num_procs=1, context_switch_cost=0, prin=0, interval1=False):
        self.time = 0 # initialize time
        self.queued_jobs = [] # array of released, inactive jobs
        self.num_procs = num_procs
        self.active_jobs = [None for i in range(self.num_procs)] # currently running jobs
        self.context_switch_cost = context_switch_cost

        # Bin-packing problem implementation
        if algorithm == "PEDF":
            bins = [0 for proc in range(self.num_procs)]
            self.pedf_assignments = [] # stores PEDF processor assignment for each task
            densities = []
            for task in self.task_set:
                self.pedf_assignments.append(-1)
                densities.append((task.cost/min(task.period, task.deadline), task.id))
            densities.sort(reverse=True)
            packing_fail = False
            for density in densities: # FFD heuristic
                i = 0
                while i <= len(bins):
                    if i < len(bins) and (bins[i] + density[0] <= 1 or packing_fail):
                        bins[i] += density[0]
                        self.pedf_assignments[density[1]] = i
                        break
                    elif i == len(bins):
                        packing_fail = True
                        bins[0] += density[0]
                        self.pedf_assignments[density[1]] = 0
                    i += 1
            if packing_fail and prin > 0: print("FFD could not pack the task list!")
            if -1 in self.pedf_assignments:
                raise Exception("A PEDF task was not assigned to a processor!")

        while self.time <= self.max_time:
            self.np_time = False

            for i in range(self.num_procs):
                if self.active_jobs[i] is not None:
                    # remove jobs which have finished executing from active jobs array
                    if self.active_jobs[i].exec_time == 0:
                        self.np_time = True
                        if self.context_switch_cost > 0:
                            if type(self.active_jobs[i]) is ContextSwitch:
                                self.active_jobs[i] = self.active_jobs[i].link
                            else: self.active_jobs[i] = ContextSwitch(self.context_switch_cost, False, self.active_jobs[i].task_id)
                        else: self.active_jobs[i] = None
                    # check if active job has missed deadline
                    elif type(self.active_jobs[i]) is not ContextSwitch and self.active_jobs[i].deadline_time <= 0:
                        if prin > 1: self.printState()
                        if prin > 0: print("Missed deadline at", self.time + self.active_jobs[i].deadline_time)
                        return False
                else: # processor is open for new job
                    self.np_time = True
                
            # check if queued job has missed deadline
            for job in self.queued_jobs:
                if job.deadline_time <= 0:
                    if prin > 1: self.printState()
                    if prin > 0: print("Missed deadline at", self.time + job.deadline_time)
                    return False

            # Check if it is any task's release time. If so, add a job of that task to queued_jobs
            for task in self.task_set:
                if (self.time - task.phase) % task.period == 0:
                    self.queued_jobs.append(Job(task.deadline, task.cost, task.id))

            # Sets task sorting criteria based on scheduling algorithm.
            key = None
            if algorithm in {"EDF", "GEDF", "NPEDF", "GNPEDF", "PEDF"}: key = lambda j: j.deadline_time
            if algorithm == "LLF": key = lambda j: j.deadline_time - j.exec_time
            if algorithm == "RM": key = lambda j: self.task_set[j.task_id].period

            if algorithm == "PEDF":
                # combine (non-none/context switch) active jobs and queued jobs into sorted array
                all_jobs = list(filter(lambda j: j is not None and type(j) is not ContextSwitch, self.active_jobs)) + self.queued_jobs
                all_jobs.sort(key=key)

                if len(self.queued_jobs) > 0:
                    proc_check = [i for i in range(self.num_procs)] # list of unassigned processors
                    i = 0
                    while len(proc_check) > 0 and len(all_jobs) > 0 and i < len(all_jobs):
                        p = self.pedf_assignments[all_jobs[i].task_id] # assigned processor ID of task to be scheduled
                        if p in proc_check:
                            if type(self.active_jobs[p]) is ContextSwitch: i += 1
                            else: self.active_jobs[p] = self.contextSwitchCheck(self.active_jobs[p], all_jobs.pop(i))
                            proc_check.remove(p)
                        else: i += 1
                    self.queued_jobs = all_jobs
          
            elif not (algorithm == "NPEDF" or algorithm == "GNPEDF"):
                # combine (non-none/context switch) active jobs and queued jobs into sorted array
                all_jobs = list(filter(lambda j: j is not None and type(j) is not ContextSwitch, self.active_jobs)) + self.queued_jobs
                all_jobs.sort(key=key)
                ncs = self.numContextSwitch()
                # queued_jobs = each job except the top (num_procs - number of context switches) in priority
                self.queued_jobs = all_jobs[self.num_procs - ncs:]

                intersect = [] # all jobs in both active_jobs and newly sorted queued_jobs
                new_jobs = [] # all newly sorted queued jobs not in intersect
                for job in all_jobs[:self.num_procs - ncs]:
                    if job in self.active_jobs:
                        intersect.append(job)
                    else:
                        new_jobs.append(job)

                if len(new_jobs) > 0:
                    for i in range(self.num_procs):
                        if self.active_jobs[i] not in intersect and type(self.active_jobs[i]) is not ContextSwitch:
                            # active jobs not in intersect are replaced at their current processor
                            self.active_jobs[i] = self.contextSwitchCheck(self.active_jobs[i], new_jobs.pop(0))
                            if len(new_jobs) == 0:
                                break

                if len(new_jobs) > 0:
                    raise Exception("new_jobs still has jobs!")
            elif self.np_time: # assign jobs only if at least one processor is available
                self.queued_jobs.sort(key=key) # always EDF
                if len(self.queued_jobs) > 0:
                    for i in range(len(self.active_jobs)):
                        if self.active_jobs[i] is None:
                            self.active_jobs[i] = self.contextSwitchCheck(None, self.queued_jobs.pop(0))
                            if len(self.queued_jobs) == 0:
                                break

            if prin > 1: self.printState()

            if interval1: interval = 1
            # interval = time until next job release
            else: interval = min([rt[0] - ((self.time - rt[1]) % rt[0]) for rt in self.release_times])
            if algorithm == "LLF" and not interval1 and self.active_jobs[0] is not None and type(self.active_jobs[0]) is not ContextSwitch and len(self.queued_jobs) > 0:
                # interval = min(interval, time until a job's laxity becomes lower than the active job's)
                interval = min(interval, max(1, min([job.deadline_time - job.exec_time for job in self.queued_jobs]) - (self.active_jobs[0].deadline_time - self.active_jobs[0].exec_time)))

            active_non_none = list(filter(lambda j: j is not None, self.active_jobs))
            if len(active_non_none) > 0:
                # interval = min(interval, time until a job/context switch finishes executing or reaches its deadline)
                interval = min(min([min(j.exec_time, j.deadline_time) if type(j) is Job else j.exec_time for j in active_non_none]), interval)
                for job in self.active_jobs:
                    if job is not None:
                        job.exec_time -= interval
                        if type(job) is not ContextSwitch: job.deadline_time -= interval

            for job in self.queued_jobs:
                job.deadline_time -= interval

            interval = max(1, interval)
            self.time += interval
            if prin > 2: input()

        if prin > 0: print("The task set is schedulable!")
        return True

def generate_task_set(phases, periods, costs, num_tasks, deadlines=None):
    task_set = []
    for i in range(num_tasks):
        period = choice(periods)
        deadline = period
        if deadlines is not None:
            deadline = choice(deadlines)
        task_set.append(Task(choice(phases), period, choice(costs), deadline, i))
    return task_set