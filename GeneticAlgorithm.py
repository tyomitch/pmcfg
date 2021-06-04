from Parser import *
import random
from time import perf_counter


class GeneticAlgorithm:
    def __init__(self, pop_size, penalty, mortality):
        self.mortality = mortality
        self.pop_size = pop_size
        self.penalty = penalty
        self.mutate = 0

    def run(self, init_grammar, data):
        start = perf_counter()
        pop = [(init_grammar, self.get_mdl_score(init_grammar, data))]
        self.parse = perf_counter() - start
        for iteration in range(1977):
            scores = [s for g, s in pop]
            print("iteration %d score(%f, %f, %f) parse %f mutate %f" %
                (iteration, scores[0], sum(scores)/len(scores), scores[-1], self.parse, self.mutate))
            if not iteration % 10:
                print(pop[0])
            neighbor_score = None
            while neighbor_score is None:
                print('.', end='', flush=True)
                start = perf_counter()
                neighbor = random.choice(pop)[0].createNeighbor()
                self.mutate += perf_counter() - start
                if neighbor in (g for g, s in pop):
                    continue
                start = perf_counter()
                neighbor_score = self.get_mdl_score(neighbor, data)
                self.parse += perf_counter() - start
            pop.append((neighbor, neighbor_score))
            pop.sort(key=lambda x: x[1])
            while len(pop) > self.pop_size:
                n = len(pop)
                prob = 1.
                for i in range(1, n):
                    prob *= self.mortality
                    if random.random() < prob:
                        pop.pop(n-i)
        print(pop[0])
        return pop[0][0].delete_unreachable_rules()

    def get_mdl_score(self, grammar, data):
        grammar = grammar.delete_unreachable_rules().fix_probabilities()
        g_length = grammar.getEncodingLength()
        d_g_length = 0
        for d in data:
            res = parse(grammar, d)
            if res is None:
                d_g_length += self.penalty # regardless of data length
            else:
                d_g_length += res
        return g_length + d_g_length
