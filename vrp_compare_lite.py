# This script expects to be run inside a Python virtual environment
# with the required dependencies installed (see requirements.txt).

try:
    import vrplib
except ImportError as e:
    print("Error: failed to import 'vrplib'.")
    print("Make sure you have activated your virtual environment and installed"
          " the required packages (e.g. `pip install -r requirements.txt`).")
    raise

import random
import time
import math
import os
import sys


# =====================================================
# VRP INSTANCE
# =====================================================

class VRPInstance:

    def __init__(self, path):

        data = vrplib.read_instance(path)

        self.dimension = data["dimension"]
        self.capacity = data["capacity"]
        self.demands = data["demand"]
        self.coords = data["node_coord"]

        self.distance_matrix = self.compute_distance_matrix()

    def compute_distance_matrix(self):

        n = self.dimension
        matrix = [[0]*n for _ in range(n)]

        for i in range(n):
            for j in range(n):

                # vrplib ya usa indices desde 0
                x1, y1 = self.coords[i]
                x2, y2 = self.coords[j]

                matrix[i][j] = round(
                    math.sqrt((x1-x2)**2 + (y1-y2)**2)
                )

        return matrix
# =====================================================
# COST FUNCTIONS
# =====================================================

def route_cost(route, dist):

    cost = 0

    for i in range(len(route)-1):
        cost += dist[route[i]][route[i+1]]

    return cost


def solution_cost(solution, dist):

    total = 0

    for r in solution:
        total += route_cost(r, dist)

    return total


# =====================================================
# RANDOM SOLUTION
# =====================================================

def random_solution(instance):

    customers = list(range(1, instance.dimension))
    random.shuffle(customers)

    routes = []
    route = [0]
    load = 0

    for c in customers:

        demand = instance.demands[c]

        if load + demand <= instance.capacity:

            route.append(c)
            load += demand

        else:

            route.append(0)
            routes.append(route)

            route = [0, c]
            load = demand

    route.append(0)
    routes.append(route)

    return routes


# =====================================================
# NEIGHBOR
# =====================================================

def neighbor(solution):

    sol = [r.copy() for r in solution]

    r1, r2 = random.sample(range(len(sol)), 2)

    if len(sol[r1]) <= 3:
        return sol

    pos = random.randint(1, len(sol[r1])-2)

    customer = sol[r1].pop(pos)

    insert = random.randint(1, len(sol[r2])-1)

    sol[r2].insert(insert, customer)

    return sol


# =====================================================
# ABC
# =====================================================

class ABC:

    def __init__(self, instance, colony_size=20, limit=40):

        self.instance = instance
        self.food_sources = colony_size // 2
        self.limit = limit

    def run(self, time_budget):

        solutions = []
        trials = []

        best_cost = float("inf")

        for _ in range(self.food_sources):

            sol = random_solution(self.instance)
            solutions.append(sol)
            trials.append(0)

        start = time.time()

        while time.time() - start < time_budget:

            for i in range(self.food_sources):

                new = neighbor(solutions[i])

                old_cost = solution_cost(
                    solutions[i],
                    self.instance.distance_matrix
                )

                new_cost = solution_cost(
                    new,
                    self.instance.distance_matrix
                )

                if new_cost < old_cost:

                    solutions[i] = new
                    trials[i] = 0

                else:

                    trials[i] += 1

                if new_cost < best_cost:
                    best_cost = new_cost

        return best_cost


# =====================================================
# ACO (simplified)
# =====================================================

class ACO:

    def __init__(self, instance, ants=20, alpha=1, beta=3, rho=0.5):

        self.instance = instance
        self.ants = ants
        self.alpha = alpha
        self.beta = beta
        self.rho = rho

        n = instance.dimension
        self.pheromone = [[1]*n for _ in range(n)]

    def run(self, time_budget):

        best_cost = float("inf")

        start = time.time()

        while time.time() - start < time_budget:

            for _ in range(self.ants):

                sol = random_solution(self.instance)

                cost = solution_cost(
                    sol,
                    self.instance.distance_matrix
                )

                if cost < best_cost:
                    best_cost = cost

        return best_cost


# =====================================================
# CBGA (simplified)
# =====================================================

class CBGA:

    def __init__(self, instance, pop_size=30):

        self.instance = instance
        self.pop_size = pop_size

    def crossover(self, p1, p2):

        child = p1.copy()

        if random.random() < 0.5:
            child = p2.copy()

        return child

    def run(self, time_budget):

        population = [
            random_solution(self.instance)
            for _ in range(self.pop_size)
        ]

        best_cost = float("inf")

        start = time.time()

        while time.time() - start < time_budget:

            p1, p2 = random.sample(population, 2)

            child = self.crossover(p1, p2)

            child = neighbor(child)

            cost = solution_cost(
                child,
                self.instance.distance_matrix
            )

            if cost < best_cost:
                best_cost = cost

        return best_cost


# =====================================================
# EXPERIMENT
# =====================================================

def run_experiment(algorithm, instance, seeds=10, time_budget=5):

    results = []

    for s in range(seeds):

        random.seed(s)

        algo = algorithm(instance)

        cost = algo.run(time_budget)

        results.append(cost)

        print(f"Seed {s} -> {cost}")

    mean = sum(results)/len(results)

    print("Mean:", mean)
    print("Best:", min(results))
    print("Worst:", max(results))


# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":

    # choose instance from CLI and check existence
    if len(sys.argv) < 2:
        print("Usage: python vrp_compare_lite.py <instance_file>")
        sys.exit(1)

    instance_path = sys.argv[1]
    if not os.path.isfile(instance_path):
        print(f"Instance file {instance_path!r} not found.")
        sys.exit(1)

    instance = VRPInstance(instance_path)

    print("\n=== ABC ===")
    run_experiment(ABC, instance)

    print("\n=== ACO ===")
    run_experiment(ACO, instance)

    print("\n=== CBGA ===")
    run_experiment(CBGA, instance)