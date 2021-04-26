from Parser import *
import copy
import random


class SimulatedAnnealing:
    def __init__(self, init_temp, threshold, cool_rate):
        self.init_temp = init_temp
        self.threshold = threshold
        self.cool_rate = cool_rate

    def run(self, init_grammar, data):
        temp = self.init_temp
        current_grammar = init_grammar
        iteration = 0
        while temp >= self.threshold:
            iteration += 1
            current_energy = self.get_mdl_score(current_grammar, data)
            neighbor_energy = None
            while neighbor_energy is None:
                neighbor = None
                while neighbor is None:
                    neighbor = copy.deepcopy(current_grammar)
                    neighbor.createNeighbor()
                    neighbor.fix_probabilities()
                neighbor_energy = neighbor.getEncodingLength()
                for d in data:
                    temp_energy = parse(neighbor, d)
                    if temp_energy is None:
                        neighbor_energy = None
                        break
                    else:
                        neighbor_energy += temp_energy
            delta = neighbor_energy - current_energy
            if delta < 0:
                p = 1
            else:
                p = math.exp(-delta / temp)
            q = random.random()
            if q < p:
                current_grammar = neighbor
            temp = self.cool_rate * temp
        return current_grammar

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
