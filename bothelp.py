default = """Which command list would you like?

Character Management - `dq help character`
Rolling - `dq help rolling`
Using the Dice Pool - `dq help dpool`
GM Stuff - `dq help gm`
Glossary - `dq help glossary`"""


glossary="""`[indicator]`
	characters, moves, and consequences can be selected using the letter ID they display with or with the first several letters of their name
`[dice]`
	something in the format "xdy", eg "3d6" """


character = """`dq add char [name]`
	Adds a new character to the game.
`dq del char`
	Deletes your currently set character.
`dq set char [indicator]`
	Sets which character you're playing as.
`dq rename char [name]`
	Renames your set character to [name].

`dq +m [dice] [name]`
	Add a move or trait to your move list. 
`dq -m [indicator]`
	Remove the indicated move from your move list.

`dq +c [dice] [name]`
	Add a consequence to your pool
`dq -c [indicator]`
	Remove the indicated consequence from your consequence pool.

`dq view char/sheet`
	View the character sheet of your set character.
`dq view dpool/cpool/moves`
	View your dice pool, your consequence pool, or your move list."""


rolling = """`dq + [indicator]`
	Roll and use up the indicated move and add the results to your dice pool
`dq + [dice]`
	Roll and add the results to your dice pool

`dq roll [dice]`
	Roll the dice without adding them to your dice pool
`dq roll [indicator]`
	Roll and use up the indicated move without adding the results to your dice pool
`dq roll cs`
	Roll your consequence pool and clear it"""


dpool = """`dq + [n]`
	Add a specific value to your dice pool
`dq - [n]`
	Remove a specific value from your dice pool

`dq raise [x] [y]`
	Raise with one or two specific values from your dice pool
`dq call [x] [y] [z] ...`
	Counter/block/dodge/hit with one or more specific values from your dice pool."""



gm = """`dq new game [name, name, name...]`
	Archives all existing characters then starts a new game with the new characters listed.

`dq view dpools`
	View all dice pools.

`dq clear dpools`
	Clear all dice pools + set all moves to unused.
`dq clear cpools`
	Clear all consequence pools
`dq clear pools`
	Do both of the above"""

