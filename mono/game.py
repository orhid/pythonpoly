"""
Game handling.
"""

import logging as log

from mono.dice import roll
from mono.board import prepare_board
from mono.player import numstring, initialise_player


def turn(board, player):
    """Simulate a single player's turn."""
    log.info('Beginning turn of player %s.', player.name)
    if player.jailed:
        player.try_jailout(board)
    else:
        player.consider_developing(board)
        diceroll, doubles = roll()
        player.advance(diceroll, board)
        if doubles and not player.jailed and not player.bankrupt:
            diceroll, doubles = roll()
            player.advance(diceroll, board)
            if doubles:
                player.enjail()

def lap(board):
    """Simulate a single round of play."""
    log.info('Beginning round %d.', board.laps)
    for player in board.players:
        turn(board, player)
    board.discard_players()
    if len(board.players) == 1:
        return board.players[0]
    board.laps += 1
    return None


def announce_winner(winner, board):
    """Declare the winner of the game."""
    if winner:
        log.info('Player %s won the game with %d£in capital.', winner.name, winner.capital)
    else:
        log.info('Nobody won and now your family hates you or choosing this game.')
    log.info('Game ended after %d laps.', board.laps)
    board.log_visitations()

def run_game(num_players:int = 1, start_capital:int = 1, houses:int = 0, hotels:int = 0):
    """Prepare game and run loop."""
    log.info('Initialising game on %d players.',num_players)
    board = prepare_board(houses, hotels)
    board.players = [initialise_player(
        name = f'player-{numstring(j)}',
        capital = start_capital,
        board = board,
        ) for j in range(num_players)]
    winner = None
    while winner is None and board.laps < 1296:
        winner = lap(board)
    announce_winner(winner, board)
    return board
