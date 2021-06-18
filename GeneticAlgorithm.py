from Parser import *
import random
from time import perf_counter


class GeneticAlgorithm:
    def __init__(self, steps, pop_size, penalty, mortality, mutation):
        self.mutation = mutation
        self.mortality = mortality
        self.pop_size = pop_size
        self.penalty = penalty
        self.mutate = 0
        self.steps = steps

    def run(self, init_grammar, data):
        start = perf_counter()
        pop = [(init_grammar, self.get_mdl_score(init_grammar, data))]
        self.parse = perf_counter() - start
        for iteration in range(self.steps):
            scores = [s for g, s in pop]
            print("iteration %d score(%f, %f, %f) parse %f mutate %f" %
                (iteration, scores[0], sum(scores)/len(scores), scores[-1], self.parse, self.mutate))
            if not iteration % 10:
                print(pop[0])
            neighbor_score = None
            while neighbor_score is None:
                print('.', end='', flush=True)
                #neighbor = random.choice(pop)[0]
                mate1 = int(random.expovariate(2./len(pop))) % len(pop)
                if random.random() < .2: #random.getrandbits(1):
                    mate2 = int(random.expovariate(2./len(pop))) % len(pop)
                    mate1 = pop[mate1][0]
                    mate2 = pop[mate2][0]
                    rules1 = list(mate1.prules)
                    rules2 = list(mate2.prules)
                    crossover = random.randint(1, min(len(rules1), len(rules2)))
                    merged = rules1[:crossover] + rules2[crossover:]
                    non_terminals = ({rule.left.symbol for rule in merged} |
                                     {pred.symbol for rule in merged if not rule.terminating for pred in rule.right})
                    variables = {i for rule in merged if not rule.terminating for pred in rule.right for i in pred.inputs}
                    neighbor = Grammar(mate1.terminals, non_terminals, variables, merged, mate1.start)
                    if neighbor.validate():
                        continue
                    print('x', end='', flush=True)
                else:
                    neighbor = pop[mate1][0]
                start = perf_counter()
                while random.random() < self.mutation:
                    print('!', end='', flush=True)
                    neighbor = neighbor.createNeighbor()
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
        g_length = grammar.getEncodingLength()
        grammar = grammar.delete_unreachable_rules().fix_probabilities()
        pure_length = grammar.getEncodingLength()
        d_g_length = 0
        for d in data:
            res = parse(grammar, d)
            if res is None:
                d_g_length += self.penalty # regardless of data length
            else:
                d_g_length += res
        return pure_length + (g_length - pure_length) / 100 + 3 * d_g_length
