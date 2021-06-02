import mono.player as pl
import mono.board as br


# reading csvs

def test_read_fields():
    fields = br._read_fields()
    assert len(fields) == 40
    assert fields[10].category == 'jail'
    assert fields[15].owner == None
    assert fields[16].colour == 'orange'

def test_read_cards():
    chance = br._read_chance_cards()
    assert len(chance) == 16
    assert chance[5].category == 'retreat'
    assert chance[1].advance == 'Pall Mall'
    assert chance[6].capital == -150

    community = br._read_community_cards()
    assert len(community) == 16
    assert community[1].category == 'retreat'
    assert community[1].advance == 'Old Kent Road'
    assert community[6].capital == 100


# cards

board = br.prepare_board(0,0)
plr = pl.initialise_player(200, 'player-test', board)

def test_jail_card():
    card = br.Card(category = 'jail')
    card.evaluate(plr, board)
    assert plr.position == 10
    assert plr.jailed
    plr.jailed = False

def test_jailout_card():
    plr.enjail()
    card = br.Card(category = 'jailout')
    card.evaluate(plr, board)
    plr.try_jailout(board)
    assert not plr.jailed

def test_capital_card_positive():
    plr.capital = 1
    card = br.Card(category = 'capital', capital = 1)
    card.evaluate(plr, board)
    assert plr.capital == 2

def test_capital_card_negative():
    plr.capital = 2
    card = br.Card(category = 'capital', capital = -1)
    card.evaluate(plr, board)
    assert plr.capital == 1

def test_advance_card():
    plr.position = 39
    plr.capital = 1
    card = br.Card(category = 'advance', advance = 'Go')
    card.evaluate(plr, board)
    assert plr.position == 0
    assert plr.capital == 201

def test_retreat_card():
    plr.position = 3
    plr.capital = 1
    card = br.Card(category = 'retreat', advance = -3)
    card.evaluate(plr, board)
    assert plr.position == 0
    assert plr.capital == 1

# estates

def test_board_developable():
    board.houses = 0
    board.hotels = 0
    assert not board.has_houses()
    assert not board.has_hotels()
    board.houses = 1
    board.hotels = 1
    assert board.has_houses()
    assert board.has_hotels()

def test_estate_developable():
    board.houses = 1
    board.hotels = 1
    estate = br.Estate()
    estate.development = 3
    estate.mortgaged = True
    assert not estate.can_be_developed(board)
    estate.mortgaged = False
    assert estate.can_be_developed(board)
    board.houses = 0
    assert not estate.can_be_developed(board)
    estate.development = 4
    assert estate.can_be_developed(board)
    board.hotels = 0
    assert not estate.can_be_developed(board)

def test_estate_develop():
    plr.capital = 3
    board.houses = 1
    board.hotels = 1
    estate = br.Estate(house = 1)
    estate.owner = plr
    estate.development = 3
    estate.develop(board)
    assert plr.capital == 2
    assert board.houses == 0
    assert estate.development == 4
    estate.develop(board)
    assert plr.capital == 1
    assert board.hotels == 0
    assert estate.development == 5

def test_station_rent():
    rent = [25,50,100,200]
    for j in range(1,5):
        plr.estates = {br.Buyable(category = 'station') for _ in range(j)}
        est = br.Buyable(category = 'station')
        est.owner = plr
        assert est.current_rent() == rent[j-1]

def test_utility_rent():
    rent = [16,40]
    for j in range(1,3):
        plr.estates = {br.Buyable(category = 'utility') for _ in range(j)}
        est = br.Buyable(category = 'utility')
        est.owner = plr
        assert est.current_rent(moved = 4) == rent[j-1]
        assert est.current_rent(moved = 'Go') == 0

def test_estate_rent():
    rent = [1,3,4,5,6,7]
    est0 = br.Estate(
            category = 'estate',
            colour = 'blue',
            site = 1,
            single = 3,
            double = 4,
            triple = 5,
            quadruple = 6,
            hotel = 7,
            )
    est0.owner = plr
    est1 = br.Estate(category = 'estate', colour='blue')
    plr.estates = {est0, }
    for j in range(6):
        est0.development = j
        assert est0.current_rent() == rent[j]
    plr.estates = {est0, est1}
    est0.development = 0
    assert est0.current_rent() == 2

def test_selling_houses():
    board.houses = 3
    board.hotels = 0
    est = br.Estate(house = 2)
    est.owner = plr
    est.development = 0
    plr.capital = 0
    plr.estates = {est,}
    assert not est.can_sell_houses(board)

    est.development = 5
    assert not est.can_sell_houses(board)

    board.houses = 4
    assert est.can_sell_houses(board)

    est.sell_house(board)
    assert est.development == 4
    assert plr.capital == 1
    assert board.houses == 0
    assert board.hotels == 1

    assert est.can_sell_houses(board)
    est.sell_house(board)
    assert est.development == 3
    assert plr.capital == 2
    assert board.houses == 1

def test_mortgaging():
    est = br.Buyable(cost = 2, category = 'station')
    est.owner = plr
    plr.capital = 0
    plr.estates = {est,}
    est.mortgage()
    assert plr.capital == 1
    assert est.mortgaged


# board

def test_discard():
    board.players = [
            pl.initialise_player(capital = 1, board = board),
            pl.initialise_player(capital = 0, board = board),
            ]
    board.discard_players()
    assert len(board.players) == 2
    board.players[1]._declare_bankruptcy()
    board.discard_players()
    assert len(board.players) == 1
