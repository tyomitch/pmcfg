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
        return hash(self.symbol + str(self.degree))


class PRule:
    def __init__(self, left, right, prob):
        self.left = left
        self.right = right
        self.prob = prob
        self.terminating = self.right is None

    def __repr__(self):
        return str(self.left) + " --> " + str(self.right) + " : " + str(self.prob)

    def __eq__(self, other):
        return str(self) == str(other)

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
        for rule in self.prules:
            res += str(rule)
            res += "\n"
        return res

    def isValid(self):
        d = {}
        for rule in self.prules:
            if rule.left.symbol not in d:
                d[rule.left.symbol] = rule.prob
            else:
                d[rule.left.symbol] += rule.prob
        for sym, prob in d.items():
            if prob > 1.0 or prob < 0.99999:
                return False
        return True

    def getEncodingLength(self):
        args_to_encode = 2 + len(self.variables) + len(self.terminals) + len(self.non_terminals)
        bits = math.ceil(math.log(args_to_encode, 2))
        total = 0
        probs_to_encode = []
        for rule in self.prules:
            if rule.prob not in probs_to_encode:
                probs_to_encode.append(rule.prob)
            rule_count = 2  # left non-terminal + "#"
            for v in rule.left.inputs:  # count variables on the left side
                rule_count += len(v)
            if len(rule.left.inputs) > 1:  # count $ between variables
                rule_count += len(rule.left.inputs) - 1
            if rule.right is not None:
                for var in rule.right:
                    if len(var.inputs) == 1:
                        rule_count += 2  # one non terminal and one variable
                    else:
                        rule_count += len(var.inputs) * 2  # one symbol, x inputs, x-1 $ signs. total 2x signs
            rule_count = rule_count * bits  # multiply num of signs with num of bits per sign
            total += rule_count
        total += (len(self.prules) - 1) * 2 * bits  # add $$ between rules
        return total

    def createNeighbor(self):
        neighbor_type = ["new terminating rule",
                         "concatenate two non terminals",
                         "add variable to a non-terminal rule",
                         "replace non terminal with its expansion",
                         "delete variable from a rule",
                         "connect two non terminals",
                         "delete unreachable rule",
                         "delete a rule",
                         "concatenate a vector"]
        flag = True
        while flag:
            func = random.choice(neighbor_type)
            res = self.generate_new_rule(func)
            if res is None:
                continue
            else:
                if len(res) == 1:
                    if res[0] not in self.prules:
                        self.prules.append(res[0])
                        flag = False
                else:
                    if res[1] is not None:
                        if res[1] not in self.prules:
                            self.prules.remove(res[0])
                            self.prules.append(res[1])
                    flag = False
        self.fix_probabilities()
        self.remove_duplicated_rules()

    def remove_duplicated_rules(self):
        res = []
        for rule in self.prules:
            if rule not in res:
                res.append(rule)
        self.prules = res

    def generate_new_rule(self, func):
        if func == "concatenate two non terminals":
            return self.concatenate_two_non_terminals()
        elif func == "replace non terminal with its expansion":
            return self.replace_non_terminal_with_its_expansion()
        elif func == "new terminating rule":
            return self.new_terminating_rule()
        elif func == "add variable to a non-terminal rule":
            return self.add_variable_to_non_terminal_rule()
        elif func == "delete variable from a rule":
            return self.delete_variable_from_non_terminal_rule()
        elif func == "connect two non terminals":
            return self.connect_two_non_terminals()
        elif func == "concatenate a vector":
            return self.concatenate_a_vector()
        elif func == "delete a rule":
            return self.delete_a_rule()
        else:
            return self.delete_unreachable_rule()

    def delete_a_rule(self):
        rule = random.choice(self.prules)
        self.prules.remove(rule)
        if rule.right is None:
            nt = rule.left.symbol
            nt_still_exist = False
            for prule in self.prules:
                if nt in str(prule):
                    nt_still_exist = True
                    break
            if not nt_still_exist:
                try:
                    self.non_terminals.remove(nt)
                except:
                    return [None, None]
        else:
            signs = [rule.left.symbol]
            for var in rule.right:
                if var.symbol not in signs:
                    signs.append(var.symbol)
                for v in var.inputs:
                    if v not in signs:
                        signs.append(v)
            for sign in signs:
                still_exist = False
                for prule in self.prules:
                    if sign in str(prule):
                        still_exist = True
                        break
                if still_exist:
                    signs.remove(sign)
                    continue
            if len(signs) > 0:
                for sign in signs:
                    if sign in self.non_terminals:
                        self.non_terminals.remove(sign)
                    elif sign in self.variables:
                        self.variables.remove(sign)
        return [None, None]

    def replace_non_terminal_with_its_expansion(self):
        possible_expansions = [rule for rule in self.prules if rule.right is not None]
        possible_expansions = [rule for rule in possible_expansions if len(rule.left.inputs) == 1 and len(rule.right) == 1]
        if len(possible_expansions) == 0:
            return None
        expansion = random.choice(possible_expansions)
        nt = expansion.left.symbol
        nt_rules = [rule for rule in self.prules if rule.right is not None]
        nt_rules = [rule for rule in nt_rules if len(rule.right) == 1]
        expanded_rules = []
        for rule in nt_rules:
            if rule.right[0].symbol == nt:
                expanded_rules.append(rule)
        if len(expanded_rules) == 0:
            return None
        old_rule = random.choice(expanded_rules)
        v = old_rule.left.inputs[0]
        new_rule = PRule(Var(old_rule.left.symbol, [v]), [Var(expansion.right[0].symbol, [v])], 1.0)
        return [old_rule, new_rule]

    def concatenate_a_vector(self):
        vectors = [rule for rule in self.prules if rule.left.degree > 1]
        if len(vectors) < 1:
            return None
        vec = random.choice(vectors)
        sym = vec.left.symbol
        right_input = vec.left.inputs
        left_input = "".join(vec.left.inputs)
        return [PRule(Var(sym, [left_input]), [Var(sym, right_input)], 1.0)]

    def delete_unreachable_rule(self):
        reachables = [self.start]
        for sym in reachables:
            for rule in self.prules:
                if rule.right is not None:
                    if rule.left.symbol == sym:
                        for var in rule.right:
                            if var.symbol not in reachables:
                                reachables.append(var.symbol)
        unreachables = [nt for nt in self.non_terminals if nt not in reachables]
        if len(unreachables) == 0:
            return None
        else:
            for rule in self.prules:
                if rule.left.symbol in unreachables:
                    return [None, rule]

    def connect_two_non_terminals(self):
        if len(self.non_terminals) <= 2:
            return None
        nt1 = random.choice(self.non_terminals)
        nt2 = random.choice(self.non_terminals)
        while nt2 == self.start or nt2 == nt1:
            nt2 = random.choice(self.non_terminals)
        try:
            v = self.variables[0]
        except:
            return None
        new_rule = PRule(Var(nt1, [v]), [Var(nt2, [v])], 1.0)
        opposite_rule = PRule(Var(nt2, [v]), [Var(nt1, [v])], 1.0)
        if opposite_rule in self.prules:
            return None
        return [new_rule]

    def delete_variable_from_non_terminal_rule(self):
        nt_rules = [rule for rule in self.prules if rule.right is not None]
        nt_rules = [rule for rule in nt_rules if len(rule.right) > 1]
        if len(nt_rules) == 0:
            return None
        old_rule = random.choice(nt_rules)
        new_rule = copy.deepcopy(old_rule)
        i = random.randint(0, len(new_rule.right) - 1)
        var_to_delete = new_rule.right[i]
        if len(var_to_delete.inputs) == 1:
            v = var_to_delete.inputs[0]
            new_rule.right = [var for var in new_rule.right if var != old_rule.right[i]]
        else:
            v = random.choice(var_to_delete.inputs)
            new_rule.right[i].inputs = [inp for inp in new_rule.right[i].inputs if inp != v]
        new_rule.left.inputs = [inp.replace(v, "") for inp in new_rule.left.inputs]
        new_rule.left.inputs = [inp for inp in new_rule.left.inputs if inp != ""]
        if new_rule.right == [new_rule.left]:
            return None
        return [old_rule, new_rule]

    def add_variable_to_non_terminal_rule(self):
        nt_rules = [rule for rule in self.prules if rule.right is not None]
        nt_rules = [rule for rule in nt_rules if len(rule.left.inputs) < 3]
        if len(nt_rules) == 0:
            return None
        new_rule = random.choice(nt_rules)
        if new_rule.left.symbol == self.start:
            return None
        old_rule = copy.deepcopy(new_rule)
        used_variables = self.get_used_variables(new_rule)
        if len(used_variables) == len(self.variables):
            v = self.find_unused_sign()
        else:
            optional_variables = [var for var in self.variables if var not in used_variables]
            if len(optional_variables) == 0:
                return None
            v = optional_variables[0]
        if old_rule.left.symbol == self.start:
            nt = random.choice(self.non_terminals)
        else:
            optional_nt = [nt for nt in self.non_terminals if nt != self.start]
            try:
                nt = random.choice(optional_nt)
            except:
                return None
        inp = random.randint(0, len(new_rule.left.inputs))
        if inp == len(new_rule.left.inputs):
            new_rule.right.append(Var(nt, [v]))
            new_rule.left.inputs.append(v)
        else:
            new_rule.right.insert(inp, Var(nt, [v]))
            new_rule.left.inputs.insert(inp, v)
        if v not in self.variables:
            self.variables.append(v)
        return [old_rule, new_rule]

    def get_used_variables(self, rule):
        res = []
        for inp in rule.left.inputs:
            for sign in inp:
                if sign not in res:
                    res.append(sign)
        return res

    def concatenate_two_non_terminals(self):
        nt1 = random.choice(self.non_terminals)
        nt2 = random.choice(self.non_terminals)
        if nt1 == self.start or nt2 == self.start:
            sym = self.start
        else:
            sym = random.choice(self.non_terminals)
        if len(self.variables) < 2:
            self.variables.append(self.find_unused_sign())
        try:
            var1, var2 = self.variables[0], self.variables[1]
        except:
            self.variables.append(self.find_unused_sign())
            var1, var2 = self.variables[0], self.variables[1]
        new_rule = PRule(Var(sym, [var1 + var2]), [Var(nt1, [var1]), Var(nt2, [var2])], 1.0)
        if new_rule in self.prules:
            return None
        return [new_rule]

    def new_terminating_rule(self):
        nt_choice = random.choice(["new", "old"])
        t = self.get_terminal_for_terminal_rule()
        if t is None:
            return None
        if nt_choice == "new":
            n = self.find_unused_sign()
            new_rule = PRule(Var(n, [t]), None, 1.0)
            self.non_terminals.append(n)
        else:
            possible_nt = [nt for nt in self.non_terminals if nt != self.start]
            if len(possible_nt) == 0:
                return None
            else:
                n = random.choice(possible_nt)
            new_rule = PRule(Var(n, [t]), None, 1.0)
            if new_rule in self.prules:
                return None
        return [new_rule]

    def get_terminal_for_terminal_rule(self):
        possible_terminals = {}
        terminal_rules = [rule for rule in self.prules if rule.right is None]
        for rule in terminal_rules:
            if rule.left.inputs[0] not in possible_terminals:
                possible_terminals[rule.left.inputs[0]] = 1
            else:
                possible_terminals[rule.left.inputs[0]] += 1
        terminals_list = []
        for t, num in possible_terminals.items():
            if num < 2:
                terminals_list.append(t)
        if len(terminals_list) == 0:
            return None
        else:
            return random.choice(terminals_list)

    def find_unused_sign(self):
        letters = list(string.ascii_uppercase)
        letters = [l for l in letters if l not in self.non_terminals and l not in self.variables]
        return letters[0]

    def fix_probabilities(self):
        rules_dict = {}
        for rule in self.prules:
            if rule.left.symbol not in rules_dict:
                rules_dict[rule.left.symbol] = [rule]
            else:
                rules_dict[rule.left.symbol].append(rule)
        probs_dict = {}
        for n, rules in rules_dict.items():
            probs_dict[n] = 1 / len(rules)
        for rule in self.prules:
            rule.prob = probs_dict[rule.left.symbol]

