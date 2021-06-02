import math
import mono.player as pl
import mono.board as br

import logging as log

board = br.prepare_board(0,0)
plr = pl.Player('player-test', 200, set(), board)

def test_initialise():
    assert plr.capital == 200
    assert plr.name == 'player-test'
    assert plr.estates == set()

def test_enjail():
    plr.enjail()
    assert plr.position == 10
    assert plr.jailed
    plr.jailed = False

def test_jailout():
    # will not work less than once in 144 tries
    plr.jailed = True
    count = int(math.log(1/144)/math.log(5/6))+1
    for _ in range(count):
        plr.try_jailout(board)
        plr.jailouttries = 0
    assert not plr.jailed

    plr.jailed = True
    plr.jailoutcard = True
    plr.try_jailout(board)
    assert not plr.jailed
    assert not plr.jailoutcard

def test_advance():
    plr.position = 39
    plr.capital = 1
    plr.advance(1,board)
    assert plr.position == 0
    assert plr.capital == 201

    plr.position = 39
    plr.capital = 1
    plr.advance('Go',board)
    assert plr.position == 0
    assert plr.capital == 201

def test_retreat():
    plr.position = 1
    plr.capital = 1
    plr.retreat(-1,board)
    assert plr.position == 0
    assert plr.capital == 1

def test_land_on_tax():
    plr.position = 3
    plr.capital = 301
    plr.advance(1,board)
    assert plr.capital == 101
    plr.advance(34,board)
    assert plr.capital == 1

def test_go_to_jail_field():
    plr.position = 29
    plr.advance(1,board)
    assert plr.jailed
    plr.jailed = False

def test_count_houses():
    estate0 = br.Estate()
    estate0.development = 3
    estate1 = br.Estate()
    estate1.development = 1
    util = br.Buyable()
    plr.estates = {estate0, estate1, util}
    assert plr.count_owned_houses() == 4

def test_count_hotels():
    estate0 = br.Estate()
    estate0.development = 3
    estate1 = br.Estate()
    estate1.development = 5
    plr.estates = {estate0, estate1}
    assert plr.count_owned_hotels() == 1

def test_can_develop():
    estate0 = br.Estate(category = 'estate', colour = 'blue')
    plr.estates = {estate0, }
    estate0.owner = plr
    assert not plr.can_develop('blue')
    estate1 = br.Estate(category = 'estate', colour = 'blue')
    plr.estates = {estate0, estate1}
    estate1.owner = plr
    assert plr.can_develop('blue')

    estate0 = br.Estate(category = 'estate', colour = 'green')
    estate1 = br.Estate(category = 'estate', colour = 'green')
    plr.estates = {estate0, estate1}
    assert not plr.can_develop('green')
    estate2 = br.Estate(category = 'estate', colour = 'green')
    plr.estates = {estate0, estate1, estate2}
    assert plr.can_develop('green')

def test_selling():
    est = br.Estate(category = 'estate', colour = 'green', house = 2, cost = 2)
    est.owner = plr
    est.development = 1
    estb = br.Estate(category = 'estate', colour = 'blue', house = 4, cost = 4)
    estb.owner = plr
    estb.development = 2
    plr.capital = 0
    plr.estates = {est, estb}
    plr._sell(board)
    assert est.development == 0
    assert estb.development == 2
    assert plr.capital == 1
    plr._sell(board)
    assert est.mortgaged
    assert estb.development == 2
    assert plr.capital == 2

def test_pay():
    est = br.Estate(category = 'estate', colour = 'green', cost = 4)
    est.owner = plr
    plr.capital = 2
    plr.estates = {est}
    plr.pay(1, board)
    assert plr.capital == 1
    assert not est.mortgaged
    plr.pay(2, board)
    assert plr.capital == 1
    assert est.mortgaged
    plr.pay(1, board)
    assert not plr.bankrupt
    plr.pay(1, board)
    assert plr.bankrupt

def test_buy():
    est = br.Estate(colour = 'green', cost = 1)
    plr.capital = 1
    plr._buy(est, board)
    assert plr.capital == 0
    assert est.owner == plr
    assert est in plr.estates

def test_develop():
    board.houses = 3
    est0 = br.Estate(category = 'estate', colour = 'blue', cost = 100, house = 2)
    est1 = br.Estate(category = 'estate', colour = 'blue', house = 2)
    est2 = br.Estate(category = 'estate', colour = 'green', house = 1)
    est3 = br.Estate(category = 'estate', colour = 'green', house = 1)
    est4 = br.Estate(category = 'estate', colour = 'green', house = 1)
    est1.development = 1
    plr.capital = 11
    plr.estates = {est0,est1,est2,est3,est4}
    est0.owner = plr
    est1.owner = plr
    est0.mortgage()
    assert est0.mortgaged
    assert plr.capital == 61
    plr.consider_developing(board)
    assert est0.development == 2
    assert est1.development == 2
    assert est2.development == 0
    assert est3.development == 0
    assert est4.development == 0
