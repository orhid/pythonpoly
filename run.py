#!/usr/bin/env python3

import logging as log
from random import randint

from mono import run_game

NUM_PLAYERS = 3
NUM_HOUSES = 32
NUM_HOTELS = 12
START_CAPITAL = 1500


def run_many_games(num = 72):
    first = run_single_game()
    tally_c = first.colour_visits
    tally_f = first.field_visits
    for _ in range(num-1):
        more = run_single_game(num_players = randint(2,6))
        visits_c = more.colour_visits
        visits_f = more.field_visits
        for key in tally_c:
            tally_c[key] += visits_c[key]
        for key in tally_f:
            tally_f[key] += visits_f[key]
    total_c = sum(value for value in iter(tally_c.values()))
    total_f = sum(value for value in iter(tally_f.values()))
    with open('bounce/tally_colour.csv', 'w') as csv:
        csv.write('colour, tally, prob\n')
        for key in tally_c:
            csv.write(f'{key}, {tally_c[key]}, {tally_c[key]/total_c:.4f}\n')
    with open('bounce/tally_field.csv', 'w') as csv:
        csv.write('field, tally, prob\n')
        for key in tally_f:
            csv.write(f'{key}, {tally_f[key]}, {tally_f[key]/total_f:.4f}\n')


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
            filename='bounce/game.log',
            encoding='utf-8',
            level=log.INFO,
            )
    run_single_game()
#   run_many_games()
