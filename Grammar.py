import copy
import math
import random
import string


class Var:
    def __init__(self, symbol, inputs):
        self.symbol = symbol
        self.inputs = inputs
        self.degree = len(inputs)

    def __repr__(self):
        return self.symbol + str(self.inputs)

    def __eq__(self, other):
        return str(self) == str(other)

    def __hash__(self):
        return hash(str(self))


class PRule:
    def __init__(self, left, right):
        self.left = left
        self.right = right
        self.prob = None
        self.terminating = self.right is None

    def __repr__(self):
        return str(self.left) + " --> " + str(self.right) #+ " : " + str(self.prob)

    def __eq__(self, other):
        return str(self) == str(other)

    def __lt__(self, other):
        return str(self) < str(other)

    def __hash__(self):
        return hash(str(self))


class Grammar:
    def __init__(self, T, N, V, PRules, start="S"):
        self.start = start
        self.terminals = T
        self.non_terminals = N
        self.variables = V
        self.prules = PRules

    def __repr__(self):
        res = ""
        for rule in sorted(self.prules):
            res += str(rule)
            res += "\n"
        return res

    def __eq__(self, other):
        return str(self) == str(other)

    def __hash__(self):
        return hash(str(self))

    def getEncodingLength(self):
        lhs_bits = math.log(2 + len(self.variables) + len(self.terminals), 2)
        rhs_bits = math.log(2 + len(self.variables), 2)
        symbol_bits = math.log(len(self.non_terminals), 2)
        total = 0
        for rule in self.prules:
            symbols = 1  # left non-terminal
            rule_count = len(rule.left.inputs)  # count $ between variables + "#"
            for v in rule.left.inputs:  # count variables on the left side
                rule_count += len(v)
            total += rule_count * lhs_bits
            rule_count = 0
            if rule.right is not None:
                for var in rule.right:
                    symbols += 1  # one symbol
                    rule_count += len(var.inputs) * 2  # x inputs, x-1 $ signs, then #. total 2x signs
            total += rule_count * rhs_bits + symbols * symbol_bits
        total += (len(self.prules) - 1) * rhs_bits  # add extra # between rules
        return total

    def createNeighbor(self):
        neighbor_type = [
            self.concatenate_two_non_terminals,
            self.replace_non_terminal_with_its_expansion,
            self.new_terminating_rule,
            self.add_variable_to_non_terminal_rule,
            self.delete_variable_from_non_terminal_rule,
            self.connect_two_non_terminals,
            self.concatenate_a_vector,
            self.delete_a_rule]

        while True:
            func = random.choice(neighbor_type)
            res = func()
            if res is True:
                break
            if res is not None:
                if len(res) == 1:
                    if res[0] not in self.prules:
                        self.prules.append(res[0])
                        break
                else:
                    if res[1] is not None:
                        if res[1] not in self.prules:
                            self.prules.remove(res[0])
                            self.prules.append(res[1])
                    break
        self.fix_probabilities()
        self.prules = list(set(self.prules))

    def delete_a_rule(self):
        if len(self.prules) < 2:
            return None
        rule = random.choice(self.prules)
        self.prules.remove(rule)
        return True
        signs = {rule.left.symbol}
        if rule.right is not None:
            for var in rule.right:
                signs.add(var.symbol)
                signs |= set(var.inputs)
        for sign in signs:
            if not any(sign in str(prule) for prule in self.prules):
                if sign in self.non_terminals:
                    self.non_terminals.remove(sign)
                elif sign in self.variables:
                    self.variables.remove(sign)

    def replace_non_terminal_with_its_expansion(self):
        possible_expansions = [rule for rule in self.prules if len(rule.left.inputs) == 1 and rule.right is not None]
        if len(possible_expansions) == 0:
            return None
        expansion = random.choice(possible_expansions)
        expanded_rules = [rule for rule in self.prules if rule.right is not None and any(nt.symbol == expansion.left.symbol for nt in rule.right)]
        if len(expanded_rules) == 0:
            return None
        old_rule = random.choice(expanded_rules)
        target = random.choice([nt for nt in old_rule.right if nt.symbol == expansion.left.symbol])
        replacement = expansion.left.inputs[0]
        vars_used = [v for v in replacement if v in self.variables]
        new_vars = []
        for v in vars_used:
             new_var = self.find_unused_var(old_rule, set(new_vars))
             replacement = replacement.replace(v, new_var)
             new_vars.append(new_var)
        vars_dict = dict(zip(vars_used, new_vars))
        rhs = copy.deepcopy(old_rule.right)
        rhs.remove(target)
        rhs += [Var(nt.symbol, [vars_dict[v] for v in nt.inputs]) for nt in expansion.right]
        new_rule = PRule(Var(old_rule.left.symbol,
                             [v.replace(target.inputs[0], replacement) for v in old_rule.left.inputs]),
                         rhs)
        return [old_rule, new_rule]

    def concatenate_a_vector(self):
        vectors = [rule for rule in self.prules if rule.left.degree > 1]
        if len(vectors) < 1:
            return None
        if random.getrandbits(1):
            sym = self.find_unused_sign()
            self.non_terminals.append(sym)
        else:
            scalars = [rule for rule in self.prules if rule.left.degree == 1]
            sym = random.choice(scalars).left.symbol
        vec = random.choice(vectors)
        right_input = vec.left.inputs[:]
        left_input = "".join(right_input)
        random.shuffle(right_input)
        return [PRule(Var(sym, [left_input]), [Var(vec.left.symbol, right_input)])]

    def delete_unreachable_rules(self):
        reachables = [self.start]
        for sym in reachables:
            for rule in self.prules:
                if rule.right is not None:
                    if rule.left.symbol == sym:
                        for var in rule.right:
                            if var.symbol not in reachables:
                                reachables.append(var.symbol)
        self.prules = [rule for rule in self.prules if rule.left.symbol in reachables]
        self.non_terminals = reachables
        used_variables = {sign for rule in self.prules for inp in rule.left.inputs for sign in inp if sign not in self.terminals}
        self.variables = list(used_variables)

    def connect_two_non_terminals(self):
        if len(self.non_terminals) <= 2 or not self.variables:
            return None
        nt1 = random.choice(self.non_terminals)
        nt2 = random.choice(self.non_terminals)
        while nt2 == self.start or nt2 == nt1:
            nt2 = random.choice(self.non_terminals)
        v = self.variables[0]
        new_rule = PRule(Var(nt1, [v]), [Var(nt2, [v])])
        opposite_rule = PRule(Var(nt2, [v]), [Var(nt1, [v])])
        if opposite_rule not in self.prules:
            return [new_rule]

    def delete_variable_from_non_terminal_rule(self):
        nt_rules = [rule for rule in self.prules if rule.right is not None and len(rule.right) > 1]
        if len(nt_rules) == 0:
            return None
        old_rule = random.choice(nt_rules)
        new_rule = copy.deepcopy(old_rule)
        var_to_delete = random.choice(new_rule.right)
        if len(var_to_delete.inputs) == 1:
            v = var_to_delete.inputs[0]
            new_rule.right = [var for var in new_rule.right if var != var_to_delete]
        else:
            v = random.choice(var_to_delete.inputs)
            var_to_delete.inputs = [inp for inp in var_to_delete.inputs if inp != v]
        new_rule.left.inputs = [inp.replace(v, "") for inp in new_rule.left.inputs]
        new_rule.left.inputs = [inp for inp in new_rule.left.inputs if inp != ""]
        if new_rule.right == [new_rule.left]:
            return None
        return [old_rule, new_rule]

    def add_variable_to_non_terminal_rule(self):
        nt_rules = [rule for rule in self.prules if rule.right is not None and len(rule.left.inputs) < 3]
        if len(nt_rules) == 0:
            return None
        new_rule = random.choice(nt_rules)
        v = self.find_unused_var(new_rule)
        if new_rule.left.symbol == self.start:
            nt = random.choice(self.non_terminals)
        else:
            optional_nt = [nt for nt in self.non_terminals if nt != self.start]
            if optional_nt:
                nt = random.choice(optional_nt)
            else:
                return None
        inp = random.randint(0, len(new_rule.left.inputs))
        new_rule.left.inputs.insert(inp, v)
        inp = random.randint(0, len(new_rule.right))
        new_rule.right.insert(inp, Var(nt, [v]))
        if v not in self.variables:
            self.variables.append(v)
        return True

    def concatenate_two_non_terminals(self):
        nt1 = random.choice(self.non_terminals)
        nt2 = random.choice(self.non_terminals)
        if nt1 == self.start or nt2 == self.start:
            sym = self.start
        else:
            sym = random.choice(self.non_terminals)
        while len(self.variables) < 2:
            self.variables.append(self.find_unused_sign())
        var1, var2 = self.variables[0], self.variables[1]
        return [PRule(Var(sym, [var1 + var2]), [Var(nt1, [var1]), Var(nt2, [var2])])]

    def new_terminating_rule(self):
        possible_terminals = {t: 0 for t in self.terminals}
        for rule in self.prules:
            if rule.right is None:
                possible_terminals[rule.left.inputs[0]] += 1
        terminals_list = [t for t, num in possible_terminals.items() if num < 2]
        if len(terminals_list) == 0:
            return None
        t = random.choice(terminals_list)
        if random.getrandbits(1):
            n = self.find_unused_sign()
            self.non_terminals.append(n)
        else:
            n = random.choice(self.non_terminals)
        return [PRule(Var(n, [t]), None)]

    def find_unused_sign(self):
        return next(l for l in string.ascii_uppercase if l not in self.non_terminals and l not in self.variables)

    def find_unused_var(self, rule, claimed=set()):
        used_variables = {sign for inp in rule.left.inputs for sign in inp if sign in self.variables} | claimed
        if len(used_variables) == len(self.variables):
            v = self.find_unused_sign()
            self.variables.append(v)
        else:
            v = next(var for var in self.variables if var not in used_variables)
        return v

    def fix_probabilities(self):
        rules_dict = {n: [] for n in self.non_terminals}
        for rule in self.prules:
            rules_dict[rule.left.symbol].append(rule)
        for rule in self.prules:
            rule.prob = 1 / len(rules_dict[rule.left.symbol])
