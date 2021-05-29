from Grammar import *
import itertools
from time import perf_counter


def parse(grammar, string):
    chart = {n: {} for n in grammar.non_terminals}   # sym -> {Pred -> prob}
    agenda = {}  # Pred -> prob
    goal = Pred(grammar.start, [(0, len(string))])
    scan(grammar, string, agenda)
    start = perf_counter()
    while agenda and goal not in chart[grammar.start] and perf_counter() < start+5:
        (current_best, weight) = max(agenda.items(), key=lambda x: x[1])
        chart[current_best.symbol][current_best] = weight
        del agenda[current_best]
        update_agenda(grammar, agenda, chart, current_best)
    if goal not in chart[grammar.start]:
        if perf_counter() > start+5:
            print("Agenda: ", agenda, "\nGrammar: ", grammar, "\nString: ", string)
        return None
    else:
        return -chart[grammar.start][goal]


def update_agenda(grammar, agenda, chart, new_item):
    for rule in grammar.prules:
        if not rule.terminating:
            right = list(rule.right)
            for perm in itertools.product(*(chart[v.symbol].keys() for v in right)):
                if new_item in perm:
                  sat = satisfies(perm, rule.left, right, chart)
                  if sat is not None:
                      sat[1] += rule.prob
                      if isNew(sat[0], chart, agenda, sat[1]):
                          agenda[sat[0]] = sat[1]


def satisfies(perm, left, right, chart):
    inp_conv = {}
    new_prob = 0
    for i in range(len(right)):
        for j in range(len(perm[i].inputs)):
            inp_conv[right[i].inputs[j]] = perm[i].inputs[j]
        new_prob += chart[perm[i].symbol][perm[i]]
    new_res = []
    for r in left.inputs:
        if len(r) == 1:
            new_res.append(inp_conv[r])
        else:
            lst = [inp_conv[c] for c in r]
            for k in range(len(lst)-1):
                if lst[k][1] != lst[k+1][0]:
                    return None
            new_res.append((lst[0][0], lst[-1][1]))
    if len(new_res) > 1:
        for i in range(len(new_res) - 1):
            if new_res[i][1] > new_res[i+1][0]:
                return None
    return [Pred(left.symbol, new_res), new_prob]


def isNew(v, chart, agenda, new_prob):
    if v in chart[v.symbol]:
        return False
    else:
        return (v not in agenda) or (agenda[v] != new_prob)


def scan(grammar, string, agenda):
    for i in range(len(string)):
        for rule in grammar.prules:
            if rule.terminating:
                if rule.left.inputs[0] == string[i]:
                    agenda[Pred(rule.left.symbol, [(i, i+1)])] = rule.prob
