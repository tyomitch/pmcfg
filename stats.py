import nltk, itertools, matplotlib.pyplot as plt

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
#      print("shift projected word", sent[0], sent.label())
    else:
#      print("shift word", sent[0], sent.label())
      stack.append(sent.label())
  elif sent[0].label() == sent.label():
    for s in sent:
      parse(s, stack)

    for s in sent:
      stack.pop()

    if stack and stack[-1] == "(" + sent.label() + ")":
      stack.pop()
#      print("complete bottom-up projected", production(sent))
    else:
      stack.append(sent.label())
#      print("complete bottom-up", production(sent))

  else:
    parse(sent[0], stack)

    stack.pop()

    if stack and stack[-1] == "(" + sent.label() + ")":
      stack.pop()
#      print("project and complete", production(sent))
    else:
#      print("project", production(sent))
      pass

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
#    print("complete projected:", production(sent))

  report(stack)


overall = {}

#fig, axes = plt.subplots(7, sharex=True)
axes = plt.figure().add_gridspec(7, hspace=0).subplots(sharex=True)

nltk.data.path.append(r"C:\Users\tyomitch\Documents\ontonotes-release-5.0\data\files\data\english\annotations")

corpora = {"bc": "Broadcast Conversation", "bn": "Broadcast News", "mz": "Magazine", "nw": "Newswire",
           "pt": "Pivot", "tc": "Telephone Conversation", "wb": "Web Text"}

for corpus, axis in zip(corpora, axes):
   axis.set_title(corpora[corpus], y=1.0, pad=-14)
   axis.label_outer()

   treebank = nltk.corpus.util.LazyCorpusLoader(corpus, nltk.corpus.BracketParseCorpusReader, r".*\.parse", nltk_data_subdir="")

   processed = 0

   for i, sent in enumerate(treebank.parsed_sents()):

      try:
        if len(sent)==2 and sent[0].label() in ("XX", "``"):
           sent = sent[1]
        else:
           assert(sent.label() == 'TOP' and (len(sent)==1 or (len(sent)==2 and sent[1].label()==".")))
           sent = sent[0]

        if sent.label() in ('FW', 'CODE', 'WHNP', 'WHPP',
                            'WHADVP', 'WHADJP','META', 'XX', 'PRN', 'LST', '.', ','):
           continue

        for pos in sent.treepositions():
           n = sent[pos]
           if isinstance(n, nltk.tree.Tree):
              n.set_label(n.label().split("-")[0])

        if sent.label() in ('FRAG', 'NP', 'PP', 'ADVP', 'X', 'SBAR',
                            'VP', 'UCP', 'ADJP', 'INTJ'):
           continue

        stack = []
        parse(sent, stack)
        assert(stack in (['S'], ['SINV'], ['SBARQ'], ['SQ']))
        processed += 1
      except:
        print(corpus, i)
        raise

   stats = list(stats.items())
   stats.sort(key = lambda x: -x[1])

   print(processed, "sentences processed, out of", i, "total")
   print("Most frequent stacks:")
   print("\n".join(" ".join(reversed(s))+": "+str(freq) for s, freq in stats[:10]))

   for s, freq in stats:
      if s in overall:
         overall[s] += freq
      else:
         overall[s] = freq

   bins = max(len(s) for s, freq in stats)
   #print(bins, "bins")
   #uniplot.histogram(list(itertools.chain.from_iterable([len(s)]*freq for s, freq in stats)), bins=bins-1, bins_min=(11+bins)/12, bins_max=(1+bins*11)/12, width=100, y_gridlines=[])
   axis.hist(list(itertools.chain.from_iterable([len(s)]*freq for s, freq in stats)), bins=bins-1, log=True)
   #print(np.histogram(uniplot.multi_series.MultiSeries(ys=sum(([len(s)]*freq for s, freq in stats), [])).ys[0], bins=bins-1, range=(1, bins)))

   #stats = [(len(s), freq) for s, freq in stats]
   #keys = {l for l, freq in stats}
   #stats = {l: sum(freq for ll, freq in stats if ll==l) for l in keys}
   #print(stats)
   stats = {}

plt.show()

overall = list(overall.items())
overall.sort(key = lambda x: -x[1])
print("Overall most frequent stacks:")
print("\n".join(" ".join(reversed(s))+": "+str(freq) for s, freq in overall[:10]))
