from schedulesim import Task, Job, Simulator, generate_task_set
import json

def getInt(question, name, min):
    out = input(question)
    while (not out.isdigit()) or int(out) < min:
        print(name + " must be an integer greater than or equal to " + min + ".")
        out = input(question)
    return int(out)

def manualTaskSet():
    id = 0
    manual_ts = []
    while(True):
        q = "Task " + str(id) + " "
        phase = getInt(q + "phase: ", "Phase", 0)
        period = getInt(q + "period: ", "Period", 1)
        cost = getInt(q + "cost: ", "Cost", 1)
        while cost > period:
            print("Cost must be less than or equal to the task's period of", period)
            cost = getInt(q + "cost: ", "Cost", 1)
        deadline = getInt(q + "deadline: ", "Deadline", 1)
        while cost > deadline:
            print("Deadline must be greater than or equal to the task's cost of", cost)
            cost = getInt(q + "deadline: ", "Deadline", 1)
        print(Task(phase, period, cost, deadline, id))

        print("Would you like to [a]dd another task, [r]edo the current task, or [c]omplete the task set?")
        next_task = input()
        while next_task not in {"a", "r", "c"}:
            print("Invalid. Please enter \"a\", \"r\", or \"c\".")
            next_task = input()

        if next_task == "a":
            manual_ts.append(Task(phase, period, cost, deadline, id))
            id += 1
        elif next_task == "r": continue
        elif next_task == "c":
            manual_ts.append(Task(phase, period, cost, deadline, id))
            return manual_ts

def loadTaskSet():
    file = open("task_set.json")
    data = json.load(file)
    loaded_ts = []
    id = 0
    for task in data["tasks"]:
        if task["phase"] < 0:
            raise Exception("Load task set error: Task", str(id) + "'s phase is less than 0")
        if task["period"] < 1:
            raise Exception("Load task set error: Task", str(id) + "'s phase is less than 1")
        if task["cost"] < 1:
            raise Exception("Load task set error: Task", str(id) + "'s cost is less than 1")
        if task["cost"] > task["period"]:
            raise Exception("Load task set error: Task", str(id) + "'s cost is greater than its period")
        if task["deadline"] < 1:
            raise Exception("Load task set error: Task", str(id) + "'s deadline is less than 1")
        if task["cost"] > task["deadline"]:
            raise Exception("Load task set error: Task", str(id) + "'s cost is greater than its deadline")
        loaded_ts.append(Task(task["phase"], task["period"], task["cost"], task["deadline"], id))
        id += 1

    file.close()
    return loaded_ts

def randomTaskSet():
    num_tasks = getInt("How many tasks should the random task set contain? ", "The number of tasks", 1)
    return generate_task_set(phases=[0, 2, 3, 5, 7], periods=[10, 20, 30, 40, 50], costs=[2, 4, 6, 8, 10], num_tasks=num_tasks)

print("Welcome to Eli Zachary's scheduling simulator.")

print("Would you like to [m]anually enter a task set, [l]oad a task set from task_set.json, [r]andomly generate a single task set, or randomly generate multiple task [s]ets until a schedulable one is found?")
task_set_status = input()
while task_set_status not in {"m", "l", "r", "s"}:
    print("Invalid. Please enter \"m\", \"l\", \"r\", or \"s\".")
    task_set_status = input()

task_set = []

if task_set_status == "m": task_set = manualTaskSet()
if task_set_status == "l": task_set = loadTaskSet()
if task_set_status == "r": task_set = randomTaskSet()
if task_set_status != "s":
    print(task_set)

    s = Simulator(task_set)
    next = "q"

while task_set_status != "s":
    if next != "r":
        num_procs = 1
        print("Which scheduling algorithm would you like to use?")
        algorithms = {"EDF", "NPEDF", "RM", "LLF", "GEDF", "GNPEDF", "PEDF"}
        print("Options include:", algorithms)
        algorithm = str.upper(input())
        while algorithm not in algorithms:
            print("Input a valid algorithm from the given list.")
            algorithm = str.upper(input())
        
        if algorithm in {"GEDF", "GNPEDF", "PEDF"}:
            num_procs = getInt("Number of processors: ", "The number of processors", 1)

        csc = getInt("Context-switching cost: ", "The context-switching cost", 0)

        print("Select print mode.")
        print("0: Print nothing at all. 1: Print whether the task set is schedulable under the chosen algorithm. 2: Print the schedule at all decision points.")
        print("3. Pause simulation at each decision point..")
        
        prin = input()
        while (not prin.isdigit()) or int(prin) < 0 or int(prin) > 5:
            prin = input("Enter a valid print number: ")
        prin = int(prin)

    s.simulate(algorithm, num_procs, csc, prin)

    print("Would you like to [q]uit, [r]erun the simulation with the same parameters, or [e]dit the simulation parameters?")
    next = input()
    while next not in {"q", "r", "e"}:
        next = "Invalid. Enter \"q\", \"r\", or \"e\"."
    if next == "q": break

if task_set_status == "s":
    max_iter = getInt("What is the maximum number of task sets which you would like to simulate? ", "n", 1)
    num_tasks = getInt("How many tasks would you like your task sets to contain? ", "The number of tasks", 1)
    print("Which scheduling algorithm would you like to use?")
    algorithms = {"EDF", "NPEDF", "RM", "LLF", "GEDF", "GNPEDF", "PEDF"}
    print("Options include:", algorithms)
    algorithm = str.upper(input())
    while algorithm not in algorithms:
        print("Input a valid algorithm from the given list.")
        algorithm = str.upper(input())
    
    num_procs = 1
    if algorithm in {"GEDF", "GNPEDF", "PEDF"}:
        num_procs = getInt("Number of processors: ", "The number of processors", 1)

    csc = getInt("Context-switching cost: ", "The context-switching cost", 0)
    for i in range(max_iter):
        task_set = generate_task_set(phases=[0, 2, 3, 5, 7], periods=[10, 20, 30, 40, 50], costs=[2, 4, 6, 8, 10], num_tasks=num_tasks)
        s = Simulator(task_set)
        if s.simulate(algorithm, num_procs, csc, 0):
            print(task_set)
            s.simulate(algorithm, num_procs, csc, 2)
            print("Iteration", i)
            break
        if i == max_iter - 1:
            print("No schedulable task set under these parameters was found.")