"""
Board handling.
"""

import csv
import logging as log
from random import shuffle

_CAT_FIELD = {'go','jail','parking','gojail','tax','chance','community'}
_CAT_BUYABLE = {'utility','station'}
FIELD_POSITION = {
        'Go' : 0,
        'Pall Mall' : 11,
        'Marylebone Station' : 15,
        'Trafalgar Square' : 24,
        'Mayfair' : 39,
        'Old Kent Road' : 1,
        }


# fields

class Field():
    """A single field on the board."""
    def __init__(self, name:str = None, position:int = 0, category:str = None):
        self.name = name
        self.position = position
        self.category = category

    def __repr__(self):
        return self.name

class Buyable(Field):
    """A field which can be purchased."""
    def __init__(self, cost:int = 0, **kwds):
        super().__init__(**kwds)
        self.cost = self._evaluate_cost(cost)
        self.owner = None
        self.mortgaged = False

    def __hash__(self) -> int:
        # only hashable objects can be elements of sets
        # sets instead of lists for O(1) lookup
        return hash(self.name)

    def _evaluate_cost(self, cost:int = 0) -> int:
        if cost:
            return cost
        if self.category == 'utility':
            return 150
        if self.category == 'station':
            return 200
        return 0

    def can_sell_houses(self, board) -> bool:
        """Check whether houses can be sold off of this estate."""
        return False

    def current_rent(self, moved = None) -> int:
        """Calculate owned rent for landing at field."""
        if not self.mortgaged:
            if self.category == 'station':
                return 25 * 2 ** (self.owner.count_owned_stations() - 1)
            if self.category == 'utility':
                if isinstance(moved, int):
                    return abs(moved) * (self.owner.count_owned_utilities() * 6 - 2)
        return 0

    def mortgage(self):
        """Mortgage this estate."""
        self.mortgaged = True
        self.cost = self.cost // 2
        self.owner.capital += self.cost
        log.info('Player %s mortgages %s and receives %d£.',
                self.owner.name, self.name, self.cost)

    def demortgage(self, board):
        """Pay the mortgage."""
        self.owner.pay(self.cost + self.cost // 10, board)
        self.mortgaged = False
        self.cost = self.cost * 2
        log.info('Player %s pays the mortgage on %s.', self.owner.name, self.name)


class Estate(Buyable):
    """A field which allows for development of huosing."""
    def __init__(
            self,
            colour:str = None,
            house:int = None,
            site:int = None,
            single:int = None,
            double:int = None,
            triple:int = None,
            quadruple:int = None,
            hotel:int = None,
            **kwds,
            ):
        super().__init__(**kwds)
        self.colour = colour
        self.house = house
        self.rent = (site, single, double, triple, quadruple, hotel)
        self.development = 0

    def current_rent(self) -> int:
        """Calculate owned rent for landing at field."""
        if not self.mortgaged:
            flush = self.owner.can_develop(self.colour)
            if self.development == 0:
                return max(2 * flush, 1) * self.rent[self.development]
            return self.rent[self.development]
        return 0

    def can_sell_houses(self, board) -> bool:
        """Check whether houses can be sold off of this estate."""
        if self.development == 5:
            return board.houses > 3
        return self.development > 0

    def can_be_developed(self, board) -> bool:
        """Check whether this estate can be further developed."""
        if self.development < 4:
            return board.has_houses() and not self.mortgaged
        return self.development < 5 and board.has_hotels() and not self.mortgaged

    def sell_house(self, board):
        """Sell a house off of this estate."""
        self.owner.capital += self.house // 2
        if self.development == 5:
            board.houses -= 4
            board.hotels += 1
        else:
            board.houses += 1
        self.development -= 1
        log.info('Player %s sells a house from %s for %d£.',
                self.owner.name, self.name, self.house // 2)

    def develop(self, board):
        """Place houses or hotels onto estate."""
        log.info('Developing estate at %s', self.name)
        self.owner.pay(self.house, board)
        if self.development < 4:
            board.houses -= 1
            log.info('Player %s builds a house on %s.', self.owner.name, self.name)
        else:
            board.hotels -= 1
            board.houses += 4
            log.info('Player %s builds a hotel on %s!', self.owner.name, self.name)
        self.development = self.development + 1


def _read_fields() -> dict:
    log.info('Reading London fields.')
    fields = dict()
    with open('static/board.csv', newline='') as fieldss:
        for row in csv.DictReader(fieldss):
            if row['category'] in _CAT_FIELD:
                fields.update({int(row['position']):Field(
                    name = row['name'],
                    position = int(row['position']),
                    category = row['category'],
                    ), })
            elif row['category'] in _CAT_BUYABLE:
                fields.update({int(row['position']):Buyable(
                    name = row['name'],
                    position = int(row['position']),
                    category = row['category'],
                    cost = 200 if row['category'] == 'station' else 150,
                    ), })
            else:
                continue
    with open('static/estate.csv', newline='') as properties:
        for row in csv.DictReader(properties):
            fields.update({int(row['position']):Estate(
                name = row['name'],
                position = int(row['position']),
                category = 'estate',
                cost = int(row['cost']),
                colour = row['colour'],
                house = int(row['house']),
                site = int(row['site']),
                single = int(row['single']),
                double = int(row['double']),
                triple = int(row['triple']),
                quadruple = int(row['quadruple']),
                hotel = int(row['hotel']),
                ), })
    return fields


# cards

def _read_advance(advance:str):
    try:
        return int(advance)
    except Exception:
        if advance is None:
            return ''
        return advance

def _read_capital(capital:str) -> int:
    try:
        return int(capital)
    except Exception:
        return 0

class Card():
    """Chance or Community card."""
    def __init__(self,
            name:str = None,
            category:str = None,
            advance = None,
            capital:int = 0
            ):
        self.name = name
        self.category = category
        self.advance = _read_advance(advance)
        self.capital = _read_capital(capital)

    def evaluate(self, player, board):
        """Evaluate card description."""
        log.info('Player %s draws a card.', player.name)
        if self.category == 'advance':
            player.advance(self.advance, board)
        elif self.category == 'retreat':
            player.retreat(self.advance, board)
        elif self.category == 'capital':
            if self.capital > 0:
                player.capital += self.capital
                log.info('Player %s receives %d£.', player.name, self.capital)
            else:
                player.pay(-self.capital, board)
        elif self.category == 'jail':
            player.enjail()
        elif self.category == 'jailout':
            player.jailoutcard = True
            log.info('Player %s draws the Get Out of Jail card.', player.name)
        else:
            if self.name == 'birthday':
                birthday = sum(plr.pay(10) for plr in board.players)
                player.capital += birthday
                log.info('Player %s receives %d£.', player.name, birthday)
            elif self.name == 'takechance':
                if player.capital < 10 or 'chance' in player.strategies:
                    player.draw_card('chance', board)
                else:
                    player.pay(10, board)
            else:
                house_rent = 25 if self.name == 'houserent' else 40
                hotel_rent = 100 if self.name == 'houserent' else 115
                player.pay(house_rent * player.count_owned_houses + \
                        hotel_rent * player.count_owned_hotels)

def _read_cards(path:str) -> list:
    with open(f'static/{path}.csv', newline='') as cards:
        return [
                Card(card['name'], card['category'], card['advance'], card['capital'])
                for card in csv.DictReader(cards)
                ]

def _read_chance_cards() -> list:
    return _read_cards('chance')

def _read_community_cards() -> list:
    return _read_cards('community')


# board

class Board():
    """Board with fields, cards and bank."""
    def __init__(self, houses, hotels):
        self.fields = _read_fields()
        self.chance = _read_chance_cards()
        self.community = _read_community_cards()
        self.houses = houses
        self.hotels = hotels
        self.players = None
        self.laps = 0
        self.field_visits = {j:0 for j in range(40)}
        self.category_visits = {field.category:0 for field in iter(self.fields.values())}
        self.colour_visits = {field.colour:0 for field in iter(self.fields.values())
            if field.category == 'estate'}
        self.colour_visits.update({'utility':0, 'station':0})

    def has_houses(self) -> bool:
        """Check is houses can be built on the board."""
        return self.houses > 0

    def has_hotels(self) -> bool:
        """Check is hotels can be built on the board."""
        return self.hotels > 0

    def shuffle_decks(self):
        """Shuffle both decks."""
        shuffle(self.chance)
        shuffle(self.community)

    def discard_players(self):
        """Eliminate players with no capital."""
        total = len(self.players)
        self.players = [player for player in self.players if not player.bankrupt]
        log.info('%d players eliminated.', total - len(self.players))

    def log_position(self, position):
        """Take note of where the player landed."""
        self.field_visits[position] += 1
        self.category_visits[self.fields[position].category] += 1
        try:
            self.colour_visits[self.fields[position].colour] += 1
        except Exception:
            try:
                self.colour_visits[self.fields[position].category] += 1
            except Exception:
                pass

    def _log_visited_fields(self):
        total = sum(value for value in iter(self.field_visits.values()))
        log.info('The following fields were visited:')
        for field in iter(self.fields.values()):
            log.info('  %s : %d times, so with %.4f probability.',
                    field.name, self.field_visits[field.position],
                    self.field_visits[field.position] / total)

    def _log_visited_categories(self):
        total = sum(value for value in iter(self.category_visits.values()))
        log.info('The following categories were visited:')
        for category in self.category_visits:
            log.info('  %s : %d times, so with %.4f probability.',
                    category, self.category_visits[category],
                    self.category_visits[category] / total)

    def _log_visited_colours(self):
        total = sum(value for value in iter(self.colour_visits.values()))
        log.info('The following estates were visited:')
        for colour in self.colour_visits:
            log.info('  %s : %d times, so with %.4f probability.',
                    colour, self.colour_visits[colour],
                    self.colour_visits[colour] / total)

    def log_visitations(self):
        pass
        """Print out visited fields."""
        self._log_visited_fields()
        self._log_visited_categories()
        self._log_visited_colours()


def prepare_board(houses, hotels) -> Board:
    """Prepare London board for play."""
    log.info('Preparing London board.')
    board = Board(houses, hotels)
    board.shuffle_decks()
    return board
