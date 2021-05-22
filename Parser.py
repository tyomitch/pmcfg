from Grammar import *
import math
import itertools
from time import perf_counter


def parse(grammar, string):
    chart = {}
    agenda = {}
    goal = Var(grammar.start, [(0, len(string))])
    scan(grammar, string, agenda)
    start = perf_counter()
    while agenda and goal not in chart and perf_counter() < start+20:
        (current_best, weight) = max(agenda.items(), key=lambda x: x[1])
        chart[current_best] = weight
        del agenda[current_best]
        update_agenda(grammar, agenda, chart, current_best)
    if goal not in chart:
        return None
    else:
        return -chart[goal]


def update_agenda(grammar, agenda, chart, new_item):
    for rule in grammar.prules:
        if not rule.terminating:
            if len(chart) < len(rule.right):
                continue
            for perm in itertools.permutations(chart.keys(), len(rule.right)):
                if new_item in perm:
                  sat = satisfies(perm, rule, chart)
                  if sat is not None:
                      if isNew(sat[0], chart, agenda, sat[1]):
                          agenda[sat[0]] = sat[1]


def satisfies(perm, rule, chart):
    inp_conv = {}
    new_prob = math.log(rule.prob, 2)
    for i in range(len(rule.right)):
        if perm[i].symbol != rule.right[i].symbol:
            return None
        if perm[i].degree != rule.right[i].degree:
            return None
        for j in range(len(perm[i].inputs)):
            inp_conv[rule.right[i].inputs[j]] = perm[i].inputs[j]
        new_prob += chart[perm[i]]
    new_res = []
    for r in rule.left.inputs:
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
    return [Var(rule.left.symbol, new_res), new_prob]


def isNew(v, chart, agenda, new_prob):
    if v in chart:
        return False
    else:
        return (v not in agenda) or (agenda[v] != new_prob)


def scan(grammar, string, agenda):
    for i in range(len(string)):
        for rule in grammar.prules:
            if rule.terminating:
                if rule.left.inputs[0] == string[i]:
                    prob = math.log(rule.prob, 2)
                    agenda[Var(rule.left.symbol, [(i, i+1)])] = prob
