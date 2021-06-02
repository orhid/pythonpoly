from random import randint

def d6() -> int:
    return randint(1,6)

def result(die0:int, die1:int) -> (int,bool):
    return die0 + die1, die0 == die1

def roll() -> (int,bool):
    return result(d6(), d6())
