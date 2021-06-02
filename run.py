import logging as log
from random import randint

from mono import run_game

NUM_PLAYERS = 4
NUM_HOUSES = 32
NUM_HOTELS = 12
START_CAPITAL = 1500


def run_many_games(num = 72):
    tally = run_single_game().colour_visits
    for _ in range(num-1):
        visits = run_single_game(num_players = randint(2,6)).colour_visits
        for key in tally:
            tally[key] += visits[key]
    total = sum(value for value in iter(tally.values()))
    with open('bounce/tally.csv', 'w') as csv:
        csv.write('colour, tally, prob\n')
        for key in tally:
            csv.write(f'{key}, {tally[key]}, {tally[key]/total:.4f}\n')


def run_single_game(num_players = NUM_PLAYERS):
    return run_game(
            num_players = num_players,
            start_capital = START_CAPITAL,
            houses = NUM_HOUSES,
            hotels = NUM_HOTELS,
            )


if __name__ == '__main__':
    log.basicConfig(
            format='%(message)s',
            filemode='w',
            filename='game.log',
            encoding='utf-8',
            level=log.INFO,
            )
    run_single_game()
#   run_many_games()
