from Grammar import *
import math
import itertools


def parse(grammar, string):
    chart = {}
    agenda = {}
    goal = Var(grammar.start, [(0, len(string))])
    scan(grammar, string, agenda)
    while len(agenda) > 0 and goal not in chart.keys():
        current_best = max(agenda.items(), key=lambda x: x[1])
        chart[current_best[0]] = agenda[current_best[0]]
        del agenda[current_best[0]]
        update_agenda(grammar, agenda, chart, current_best[0])
    if goal not in chart.keys():
        return None
    else:
        return -chart[goal]


def update_agenda(grammar, agenda, chart, new_item):
    for rule in grammar.prules:
        if not rule.terminating:
            if len(chart) < len(rule.right):
                continue
            chart_perms = list(itertools.permutations(chart.keys(), len(rule.right)))
            chart_perms = [perm for perm in chart_perms if new_item in perm]
            for perm in chart_perms:
                sat = satisfies(perm, rule, chart)
                if sat is not None:
                    if isNew(sat[0], chart, agenda, sat[1]):
                        agenda[sat[0]] = sat[1]


def satisfies(perm, rule, chart):
    inp_conv = {}
    new_prob = math.log(rule.prob, 10)
    for i in range(len(rule.right)):
        if perm[i].symbol != rule.right[i].symbol:
            return None
        if perm[i].degree != rule.right[i].degree:
            return None
        for j in range(len(perm[i].inputs)):
            if rule.right[i].symbol != perm[i].symbol:
                return None
            inp_conv[rule.right[i].inputs[j]] = perm[i].inputs[j]
        new_prob += chart[perm[i]]
    res = rule.left.inputs
    new_res = []
    for r in res:
        if len(r) == 1:
            new_res.append(inp_conv[r])
        else:
            try:
                lst = [inp_conv[c] for c in r]
                for k in range(len(lst)-1):
                    if lst[k][1] != lst[k+1][0]:
                        return None
                new_res.append((lst[0][0], lst[-1][1]))
            except:
                return None
    if len(new_res) > 1:
        for i in range(len(new_res) - 1):
            if new_res[i][1] > new_res[i+1][0]:
                return None
    return [Var(rule.left.symbol, new_res), new_prob]


def isNew(v, chart, agenda, new_prob):
    if v not in chart:
        if v not in agenda:
            return True
        else:
            for k in agenda.keys():
                if k == v:
                    if k.inputs == v.inputs:
                        if agenda[k] == new_prob:
                            return False
            return True
    else:
        for k in chart.keys():
            if k == v:
                if k.inputs == v.inputs:
                    return False
        return True


def scan(grammar, string, agenda):
    for i in range(len(string)):
        for rule in grammar.prules:
            if rule.right is None:
                if rule.left.inputs[0] == string[i]:
                    prob = math.log(rule.prob, 10)
                    agenda[Var(rule.left.symbol, [(i, i+1)])] = prob