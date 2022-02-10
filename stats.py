import nltk, json, re, uniplot, np, itertools
from nltk.corpus import treebank
"""
rules = sum((t.productions() for t in treebank.parsed_sents()), [])
print(len(rules))
rules = set(rules)
print(len(rules))
cfg = nltk.grammar.CFG(nltk.grammar.Nonterminal('S'), set(prod))
with open(r"grammar.json", "w") as f:
  json.dump({"nts": list({str(p.lhs()) for p in set(prod)}), "rules": str(cfg).split("\n")[1:]}, f, indent=1)
"""
input = json.load(open("grammar.json"))["rules"]
NONTERM_RE = re.compile(r"( [-#$',.0123456789:=ABCDEFGHIJLMNOPQRSTUVWXYZ`|]+ ) \s*", re.VERBOSE)

def nonterm_parser(string, pos):
    m = NONTERM_RE.match(string, pos)
    if not m:
        raise ValueError("Expected a nonterminal, found: " + string[pos:])
    return (nltk.grammar.Nonterminal(m.group(1)), m.end())

start = nltk.grammar.Nonterminal('S')
cfg = nltk.grammar.CFG(start, nltk.grammar.read_grammar(input, nonterm_parser)[1])
print(len(cfg.productions())) # misses # -> '#'


stats = {}

def report(stack):
#  print("stack:", stack)
  key = tuple(stack)
  if key not in stats:
    stats[key] = 1
  else:
    stats[key] += 1

def production(node):
  return node.label() + " -> " + " ".join(n.label() for n in node)

def parse(sent, stack):
  if sent.height() == 2: #only leave(s)
    assert(len(sent) == 1)

    if stack and stack[-1] == "(" + sent.label() + ")":
      stack.pop()
      print("shift projected word", sent[0], sent.label())
    else:
      print("shift word", sent[0], sent.label())
      stack.append(sent.label())
  elif sent[0].label() == sent.label():
    for s in sent:
      parse(s, stack)

    for s in sent:
      stack.pop()

    if stack and stack[-1] == "(" + sent.label() + ")":
      stack.pop()
      print("complete bottom-up projected", production(sent))
    else:
      stack.append(sent.label())
      print("complete bottom-up", production(sent))

  else:
    parse(sent[0], stack)

    stack.pop()

    if stack and stack[-1] == "(" + sent.label() + ")":
      stack.pop()
      print("project and complete", production(sent))
    else:
      print("project", production(sent))

    stack.append("[" + sent.label() + "]")
    for s in reversed(sent[1:]):
      stack.append("(" + s.label() + ")")

    report(stack)

    for s in sent[1:]:
      parse(s, stack)
      stack.pop() # successful prediction

    if stack and stack[-1] == "[" + sent.label() + "]":
      stack.pop()
    stack.append(sent.label())
    print("complete projected:", production(sent))


  report(stack)


treebank = nltk.corpus.util.LazyCorpusLoader("treebank/combined",nltk.corpus.BracketParseCorpusReader,r".*\.mrg",tagset="wsj",encoding="utf-8")


sent = nltk.tree.Tree.fromstring("(S (NP (NP (DT the) (NN horse)) (VP (VBN raced) (PP (IN past) (NP (DT the) (NN barn))))) (VP (VBD fell)))")
processed = 0

for i, sent in enumerate(treebank.parsed_sents()):

   if sent.label() in ('FW', 'CODE', 'WHNP', 'INTJ', 'WHPP', 'UCP', 'ADJP', 'VP') or i==5131:
      continue

   for pos in sent.treepositions():
      n = sent[pos]
      if isinstance(n, nltk.tree.Tree):
         n.set_label(n.label().split("-")[0])

   if sent.label() in ('FRAG', 'NP', 'PP', 'ADVP', 'X', 'SBAR'):
      continue

   stack = []
   parse(sent, stack)
   print(i)
   assert(stack in (['S'], ['SINV'], ['SBARQ'], ['SQ']))
   processed += 1

stats = list(stats.items())
stats.sort(key = lambda x: -x[1])

print(processed, "sentences processed, out of", i, "total")
print("Most frequent stacks:")
print("\n".join(" ".join(reversed(s))+": "+str(freq) for s, freq in stats[:10]))

bins = max(len(s) for s, freq in stats)
print(bins, "bins")
uniplot.histogram(list(itertools.chain.from_iterable([len(s)]*freq for s, freq in stats)), bins=bins-1, bins_min=(11+bins)/12, bins_max=(1+bins*11)/12, width=100, y_gridlines=[])

#print(np.histogram(uniplot.multi_series.MultiSeries(ys=sum(([len(s)]*freq for s, freq in stats), [])).ys[0], bins=bins-1, range=(1, bins)))

stats = [(len(s), freq) for s, freq in stats]
keys = {l for l, freq in stats}
stats = {l: sum(freq for ll, freq in stats if ll==l) for l in keys}
print(stats)
