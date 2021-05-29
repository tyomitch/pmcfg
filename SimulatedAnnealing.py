from Parser import *
import copy
import random
from time import perf_counter


class SimulatedAnnealing:
    def __init__(self, init_temp, threshold, cool_rate):
        self.init_temp = init_temp
        self.threshold = threshold
        self.cool_rate = cool_rate
        self.parse = 0
        self.mutate = 0

    def run(self, init_grammar, data):
        temp = self.init_temp
        current_grammar = init_grammar
        best_grammar = init_grammar
        best_energy = 2**31
        iteration = 0
        while temp >= self.threshold:
            iteration += 1
            start = perf_counter()
            current_energy = self.get_mdl_score(current_grammar, data)
            self.parse += perf_counter() - start
            print("iteration %d energy %f parse %f mutate %f" % (iteration, current_energy, self.parse, self.mutate))
            neighbor_energy = None
            while neighbor_energy is None:
                start = perf_counter()
                neighbor = copy.deepcopy(current_grammar)
                neighbor.createNeighbor()
                neighbor.fix_probabilities()
                self.mutate += perf_counter() - start
                start = perf_counter()
                neighbor_energy = self.get_mdl_score(neighbor, data)
                self.parse += perf_counter() - start
            delta = neighbor_energy - current_energy
            if delta < 0:
                p = 1
            else:
                p = math.exp(-delta / temp)
            q = random.random()
            if q < p:
                current_grammar = neighbor
            if best_energy > neighbor_energy:
                best_energy = neighbor_energy
                best_grammar = neighbor
            temp = self.cool_rate * temp
        print(best_energy)
        return best_grammar

    def get_mdl_score(self, grammar, data):
        g_length = grammar.getEncodingLength()
        d_g_length = 0
        for d in data:
            res = parse(grammar, d)
            if res is None:
                return None
            else:
                d_g_length += res
        return g_length + d_g_length
