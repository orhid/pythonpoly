project **Monopoly**
*by Filip Oskar Przybycień*

## rules
The following rules were changed to make implementation easier:

+ Trading cards and estates not implemented.
+ Bidding on estates not implemented. Players can only acquire estates by landing on the appropriate field.
+ Players can only develop their estates at the beginning of their turn.
+ When a player goes bankrupt, their mortgaged estates are disowned, but remain mortgaged. Remaining players can then buy the mortgaged if they land on the respective field. This is due to not being able to trade estates.
+ Players will not sell their estates unless they need to pay someone money. Selling to buy a more valuable estate is not implemented.

Cards are never put back into the decks.
Houses and hotels are finite.
Both taxes are at a flat rate.

## running
Install dependencies via `pip install -r requirements.txt`.
Then run `run.py`.

Currently `run.py` runs a single game and logs it to a file in `bounce/game.log`.
It can also be changed to run many games and save the colour and field tallies to `bounce/tally_colour.csv` and `bounce/tally_field.csv`.

In the future I would probably like to see this module hooked up to a machine learning algorithm, which would learn different strategies to play the game.

The following variables are available:

```
NUM_PLAYERS : number of players in the game
NUM_HOUSES : number of available houses
NUM_HOTELS : number of available hotels
START_CAPITAL : amount of money each player has at the start of the game
```

## strategies
The strategies are chosen randomly at the start of each game.
It would be cool to add strategies that cosider the expected return on investment, that is the value of the field, not just visiting frequency.

### valuing estates

+ counter : will check which vields were visited in the current game so far
+ expert : will consider which fields were visited the most over a number of previous games
+ None : considers fields more valuable if they are further up the board

### buying estates

+ buyall : will always buy if can
+ safenet : will buy if current capital is above `mono.player._SAFENET = 648`
+ None : will never buy

### developing estates

+ safenet : will develop if current capital is above `mono.player._SAFENET = 648`
+ None : will always develop as much as they can

### taking chances

+ chance : will always take the chance card if possible
+ None : will pay fine if possible
