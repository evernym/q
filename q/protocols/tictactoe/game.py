import re

_move_split_pat = re.compile(r'\s*,\s*|\s*')


# Python's built-in KeyError class doesn't allow a rich statement about
# what's wrong with a key. It just returns the key value as the string of
# the exception, without comment. Override this behavior -- return a
# KeyError, but one that renders better.
class MyKeyError(KeyError):
    def __init__(self, args):
        KeyError.__init__(self, args)
    def __str__(self):
        return self.args[0]


def key_to_idx(key):
    bad_key = (not isinstance(key, str)) or len(key) != 2
    if not bad_key:
        c = key[0].upper()
        if c not in 'ABC':
            bad_key = True
        try:
            r = int(key[1])
            if r < 1 or r > 3:
                bad_key = True
        except:
            bad_key = True
    if bad_key:
        raise MyKeyError('Bad key "%s". Expected A1 through C3.' % key)
    return ((r - 1) * 3) + 'ABC'.index(c)


def idx_to_key(i):
    if (not isinstance(i, int)) or i < 0 or i > 8:
        raise ValueError('Bad cell index %s. Expected a number between 0 and 8, inclusive.' % i)
    return 'ABC'[i % 3] + str(int(1 + (i / 3)))


def other_player(player:str):
    if (not isinstance(player, str)) or (len(player) != 1) or (player not in 'xoXO'):
        raise ValueError('Bad player "%s" Expected X or O.' % player)
    if player in 'xX':
        return 'O'
    return 'X'


ROW1 = [0, 1, 2]
ROW2 = [3, 4, 5]
ROW3 = [6, 7, 8]
COL1 = [0, 3, 6]
COL2 = [1, 4, 7]
COL3 = [2, 5, 8]
DIAG1 = [0, 4, 8]
DIAG2 = [2, 4, 6]
LINES = [ROW1, ROW2, ROW3, COL1, COL2, COL3, DIAG1, DIAG2]


class Game:
    def __init__(self):
        self.cells = [None]*9
        self.first = None
        self._enforce_turns = True
        
    def __getitem__(self, key):
        return self.cells[key_to_idx(key)]
    
    def __setitem__(self, key, x_or_o):
        if (not isinstance(x_or_o, str)) or (len(x_or_o) != 1) or (x_or_o not in 'xoXO') :
            raise ValueError('Bad value. Expected X or O.')
        x_or_o = x_or_o.upper()
        if not self.first:
            self.first = x_or_o
        else:
            whose_turn = self.whose_turn()
            if self._enforce_turns and (x_or_o != whose_turn):
                raise ValueError("Bad value. Expected %s, since it is that player's turn." % whose_turn)
        i = key_to_idx(key)
        if self.cells[i] is not None:
            raise Exception("Can't reuse square %s. It already has an %s in it." % (x_or_o, self.cells[i]))
        self.cells[i] = x_or_o
        
    def whose_turn(self):
        if self.first:
            xs = self.cells.count('X')
            os = self.cells.count('O')
            if xs > os:
                return 'O'
            elif os > xs:
                return 'X'
            return self.first
        
    def __str__(self):
        s = '  A B C\n'
        for row in range(3):
            s += str(row + 1)
            for col in range(3):
                c = self.cells[row * 3 + col]
                s += ' '
                if c is None: c = '-'
                s += c
            if row != 2:
                s += '\n'
        return s
    
    def winner(self):
        """
        Search for a winner. Return None if game isn't over, "X" if player X won,
        "O" if player O won, and 'none' if it's a draw.
        """
        draw = True
        for line in LINES:
            c1 = self.cells[line[0]]
            if c1:
                c2 = self.cells[line[1]]
                c3 = self.cells[line[2]]
                if c1 == c2 and c1 == c3:
                    return c1
                if (not c2) or (not c3):
                    draw = False
            else:
                draw = False
        if draw:
            return 'none'
        
    def load(self, moves):
        """Load an array of moves like "X:A1" into a game."""
        # Suspend the enforcement of turn-taking, since we don't
        # know whether the array of moves will be in alternating order.
        self._enforce_turns = False
        try:
            for m in moves:
                self[m[2:]] = m[0]
        finally:
            self._enforce_turns = True
            
    def dump(self):
        """Convert a game into an array of moves like "X:A1"."""
        moves = []
        for i in range(9):
            c = self.cells[i]
            if c:
                moves.append('%s:%s' % (c, idx_to_key(i)))
        return moves


if __name__ == '__main__':
    import random
    import sys

    import ai
    try:
        while True:
            print("\nYou be Xs, I'll be Os.")
            g = Game()
            player = random.choice('XO')
            if player == 'O':
                print("I'll go first.")
            w = None
            for i in range(9):
                if player == 'O':
                    choice = ai.next_move(g, player)
                    print('My move: %s' % choice)
                    g[choice] = player
                else:
                    print(str(g))
                    sys.stdout.write('Your move: ')
                    x = input().strip()
                    g[x] = 'X'
                w = g.winner()
                if w:
                    break
                player = other_player(player)
            print(str(g))
            if w == 'X':
                print('You win!')
            elif w == 'O':
                print('I win.')
            else:
                print('Draw.')
    except KeyboardInterrupt:
        print()
        sys.exit(0)