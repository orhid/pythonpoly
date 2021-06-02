"""
Player handling.
"""

import logging as log
from random import choice

from mono.dice import roll
from mono.board import FIELD_POSITION

_NUMSTR = {0:'zero', 1:'one', 2:'two',
        3:'three', 4:'four', 5:'five'}
_NAIVE_CLR = ['blue', 'green', 'yellow', 'red', 'orange',
        'pink', 'cyan', 'brown', 'station', 'utility']
_SAFENET = 648

def numstring(number:int) -> str:
    """Converts a number into a word."""
    # I know there is some module for that
    # but for small numbers this is quicker than importing
    # also a game should never have more than six players
    if number < 7:
        return _NUMSTR[number]
    raise Exception('Number of players too large,')

def numestate_incolour(colour:str) -> int:
    """Return the number of fields in given colour."""
    if colour in {'brown','blue'}:
        return 2
    return 3


class Player():
    """A player in the game."""
    def __init__(self, name = None, capital:int = 0, strategies:set = None, board = None):
        self.name = name
        self.capital = capital
        self.position = 0
        self.estates = set()
        self.jailed = False
        self.jailoutcard = False
        self.jailouttries = 0
        self.strategies = strategies
        self.bankrupt = False
        self.colour_priorities = self._establish_colour_priorities(board)

    def _establish_colour_priorities(self, board):
        if 'counter' in self.strategies:
            return sorted([colour for colour in board.colour_visits],
                    key = lambda x: board.colour_visits[x], reverse = True)
        if 'expert' in self.strategies:
            try:
                with open('bounce/tally_colour.csv', newline='') as tallycsv:
                    colours = {row['colour']:row['tally'] for row in csv.DictReader(tallycsv)}
                    return sorted([colour for colour in colours],
                            key = lambda x: colours[x], reverse = True)
            except Exception:
                return _NAIVE_CLR

        return _NAIVE_CLR

    # counting

    def count_owned_houses(self) -> int:
        """Count houses owned by player."""
        return sum(estate.development
                for estate in self.estates
                if hasattr(estate,'development') and estate.development < 5)

    def count_owned_hotels(self) -> int:
        """Count hotels owned by player."""
        return sum(1 for estate in self.estates
                if hasattr(estate,'development') and estate.development == 5)

    def count_owned_utilities(self) -> int:
        """Count utilities owned by player."""
        return sum(1 for estate in self.estates
                if estate.category == 'utility')

    def count_owned_stations(self) -> int:
        """Count utilities owned by player."""
        return sum(1 for estate in self.estates
                if estate.category == 'station')

    def can_develop(self, colour:str) -> bool:
        """Checks whether the player has all estates of the given colour."""
        return sum(1 for estate in self.estates
                if estate.category == 'estate' and
                estate.colour == colour) == numestate_incolour(colour)

    # moving

    def _move(self, arg, board):
        if isinstance(arg, int):
            self.position = (self.position + arg) % 40
        elif isinstance(arg, str):
            self.position = FIELD_POSITION[arg]
        log.info('Player %s moves to %s', self.name, board.fields[self.position].name)
        board.log_position(self.position)

    def advance(self, arg, board):
        """Advance player on the board."""
        prev_pos = self.position
        self._move(arg, board)
        if self.position < prev_pos:
            self.capital = self.capital + 200
            log.info('Player %s gets 200£ for passing Go.', self.name)
        self._evaluate_position(board, arg)

    def retreat(self, arg, board):
        """Move player on the board without passing Go bonus."""
        self._move(arg, board)
        self._evaluate_position(board, 0)

    def _evaluate_position(self, board, moved):
        """Take action on the newly found position of the player."""
        field = board.fields[self.position]
        if field.category == 'tax':
            if field.name == 'Income Tax':
                self.pay(200, board)
            else:
                self.pay(100, board)
        elif field.category == 'gojail':
            self.enjail()
        elif field.category in {'station', 'utility', 'estate'}:
            self._evaluate_at_estate(board, field, moved)
        elif field.category in {'community', 'chance'}:
            self.draw_card(field.category, board)

    def _evaluate_at_estate(self, board, field, moved):
        if field.owner is None:
            self._consider_buy(field, board)
        elif field.owner == self or field.mortgaged:
            pass
        else:
            rent = 0
            if field.category == 'estate':
                rent = field.current_rent()
            else:
                rent = field.current_rent(moved)
            field.owner.capital += self.pay(rent, board)
            log.info('Player %s receives %d£ in rent.', field.owner.name, rent)

    # jailing

    def enjail(self):
        """Put player in jail."""
        self.position = 10
        self.jailed = True
        log.info('Player %s lands in jail!', self.name)

    def try_jailout(self, board):
        """Attempt to get out of jail."""
        if self.jailoutcard:
            self.jailed = False
            self.jailoutcard = False
            log.info('Player %s uses the Get Out of Jail card.', self.name)
        elif self.jailouttries > 2:
            self.pay(50, board)
            self.jailed = False
            self.jailouttries = 0
            log.info('Player %s pays their way out of jail.', self.name)
        else:
            _, doubles = roll()
            if not doubles:
                self.jailouttries = self.jailouttries + 1
                log.info('Player %s remains in jail.', self.name)
            else:
                log.info('Player %s gets out of jail.', self.name)
                self.jailouttries = 0
            self.jailed = self.jailed and not doubles

    # actions
    ## developing

    def consider_developing(self, board):
        """Develop the players properties."""
        if 'counter' in self.strategies:
            self.colour_priorities = self._establish_colour_priorities(board)

        can_develop = True
        if 'safenet' in self.strategies:
            while self.capital > _SAFENET and can_develop:
                can_develop = self._develop_estates(board)
        else:
            while can_develop:
                can_develop = self._develop_estates(board)


    def _develop_estates(self, board):
        for colour in self.colour_priorities:
            estates = [estate for estate in self.estates
                    if estate.category == colour or
                    estate.category == 'estate' and estate.colour == colour]
            if any(estate.mortgaged for estate in estates):
                for estate in estates:
                    if estate.mortgaged and not self.capital < (estate.cost + estate.cost // 10):
                        estate.demortgage(board)
                        return True
            estates = [estate for estate in estates if estate.category == 'estate']
            if any(estate.can_be_developed(board)
                    for estate in estates) and self.can_develop(colour):
                estates.sort(key = lambda x: x.development)
                if estates[0].can_be_developed(board) and not self.capital < estates[0].house:
                    estates[0].develop(board)
                    return True
                else:
                    continue
        return False

    ## buying

    def _consider_buy(self, field, board):
        if not field.cost > self.capital:
            if 'buyall' in self.strategies:
                self._buy(field, board)
            elif 'safenet' in self.strategies and self.capital > _SAFENET:
                self._buy(field, board)


    def _buy(self, field, board):
        self.pay(field.cost, board)
        field.owner = self
        self.estates |= {field, }
        log.info('Player %s buys %s.', self.name, board.fields[self.position].name)


    ## paying

    def _declare_bankruptcy(self):
        for estate in self.estates:
            estate.owner = None
        self.estates = set()
        self.bankrupt = True
        log.info('Player %s declares bankruptcy!', self.name)

    def _sell(self, board):
        for colour in reversed(self.colour_priorities):
            estates = [estate for estate in self.estates
                    if estate.category == colour or
                    estate.category == 'estate' and estate.colour == colour]
            if len(estates) > 0:
                if colour not in {'utility', 'station'}:
                    estates.sort(key = lambda x: x.development)
                    if any(estate.can_sell_houses(board) for estate in estates):
                        for estate in reversed(estates):
                            # first one can be a hotel with unsuficient houses in bank
                            if estate.can_sell_houses(board):
                                estate.sell_house(board)
                                return
                estates.sort(key = lambda x: x.mortgaged, reverse=True)
                if any(not estate.mortgaged for estate in estates):
                    estates[-1].mortgage()
                    return
            else:
                continue
        self._declare_bankruptcy()

    def pay(self, amount:int, board) -> int:
        """Subtract amount from capital if possible."""
        while self.capital < amount and not self.bankrupt:
            self._sell(board)
        amount_paid = min(self.capital, amount)
        self.capital = self.capital - amount
        log.info('Player %s pays %d£', self.name, amount_paid)
        return amount_paid

    ## other

    def draw_card(self, deck:str, board):
        """Draw a card from the specified deck and evaluate it."""
        try:
            getattr(board, deck).pop().evaluate(self,board)
        except Exception:
            pass


_STRAT_VAL = ('counter', 'expert', None)
_STRAT_BUY = ('buyall', 'safenet', None)
_STRAT_CRD = ('choice', None)

def assign_strategies():
    """Choose strategies randomly."""
    return {choice(_STRAT_VAL), choice(_STRAT_BUY), choice(_STRAT_CRD)}

def initialise_player(capital:int = 0, name:str = None, board = None) -> Player:
    """Construct a new player."""
    log.info('Initialising new player.')
    return Player(
            capital = capital,
            name = name,
            strategies = assign_strategies(),
            board = board,
            )
