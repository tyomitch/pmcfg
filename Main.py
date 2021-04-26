from SimulatedAnnealing import *
from Parser import *


def main():
    data_Lcopy = ["aa", "bb", "aaaa", "abab", "baba", "bbbb", "aaaaaa", "babbab", "aabaab", "abaaba", "baabaa",
                  "abbabb", "bbabba", "bbbbbb", "abababab", "aabbaabb", "babababa"
                  ]
    data_Lpal = ["a", "b", "aa", "bb", "aaa", "aba", "bab", "bbb", "aaaa", "abba", "baab", "bbbb",
                 "aabaa", "baaab", "abbba", "abaaba", "abbabba"]

    Gcon = Grammar(["a", "b"], ["P", "S"], ["X", "Y"],
                   [
                       PRule(Var("P", ["a"]), None, 0.333),
                       PRule(Var("P", ["b"]), None, 0.333),
                       PRule(Var("P", ["XY"]), [Var("P", ["X"]), Var("P", ["Y"])], 0.333),
                       PRule(Var("S", ["X"]), [Var("P", ["X"])], 1.0)
                   ])

    SA = SimulatedAnnealing(20, 10**-3, 0.995)
    result = SA.run(Gcon, data_Lcopy)
    print(result)


main()