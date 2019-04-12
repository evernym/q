import pytest
import random

from .. import game
from .. import ai


@pytest.fixture
def g():
    return game.Game()

def test_first(g):
    assert g.first is None
    g['b3'] = 'x'
    assert 'X' == g.first

def test_turns_enforced(g):
    g['b1'] = 'o'
    ok = True
    try:
        g['b2'] = 'o'
        ok = False
    except:
        pass
    if not ok:
        pytest.fail('Expected game not to allow two turns in row by same person.')

def test_get_item_from_empty(g):
    assert g['a1'] is None

def test_simple_set_item(g):
    g['a1'] = 'x'
    assert 'X' == g['a1']
    g['c3'] = 'o'
    assert 'O' == g['c3']
    g['b2'] = 'X'
    assert 'X' == g['b2']
    g['a3'] = 'O'
    assert 'O' == g['a3']

def test_set_item_with_bad_value(g):
    bad_values = ['',None,'*','0',1,0]
    for bad in bad_values:
        g = game.Game() # reset state
        with pytest.raises(ValueError) as ex:
            g['a1'] = bad

def test_bad_key(g):
    bad_keys = ['1a','a4','d1','a1 ',' a1','a0','a01',11,None,'a12','aa1']
    for bad in bad_keys:
        with pytest.raises(KeyError) as ex:
            g[bad]

def test_cant_clobber_existing_cell(g):
    g['c3'] = 'o'
    with pytest.raises(Exception) as ex:
        g['c3'] = 'x'

def test_winner1(g):
    g['b2'] = 'o'
    g['a2'] = 'x'
    g['b1'] = 'o'
    g['b3'] = 'x'
    g['c3'] = 'o'
    assert g.winner() is None

def test_winner2(g):
    g['a1'] = 'x'
    g['b2'] = 'o'
    g['b1'] = 'x'
    g['a2'] = 'o'
    g['c2'] = 'x'
    assert g.winner() is None
    g['c3'] = 'o'
    g['c1'] = 'x'
    assert 'X' == g.winner()

def test_bad_idx_to_key(g):
    bad_idx = [0,9,-1,'0',None,'a','a1']
    for bad in bad_idx:
        with pytest.raises(ValueError) as ex:
            game.idx_to_key(bad_idx)

def test_good_idx_to_key(g):
    def all_good_idx():
        for r in '123':
            for c in 'ABC':
                yield c + r
    expected = 0
    for idx in all_good_idx():
        assert idx == game.idx_to_key(expected)
        expected += 1

def test_good_other_player(g):
    opposites = 'xXoO'
    for player in opposites:
        opposite = opposites[(opposites.index(player) + 2) % 4].upper()
        assert opposite == game.other_player(player)

def test_bad_other_player(g):
    bad_players = ['fred',None,'',0,1,-1,'xx','xo','Ox']
    for bad in bad_players:
        with pytest.raises(ValueError) as ex:
            game.other_player(bad)

def test_load_and_dump(g):
    moves = 'X:B2,O:C3,X:B1,O:B3,X:A3'.split(',')
    g.load(moves)
    dumped = g.dump()
    assert len(dumped) == len(moves)
    for m in moves:
        assert m in dumped

def test_turns_not_enforced_during_load(g):
    moves = ["X:B1", "X:B2", "O:C2", "O:B3", "x:a3"]
    g.load(moves)


def test_line_winnable():
    for line in game.LINES:
        cells = [None]*9
        assert 3 == ai.winnable_in_n_moves(line, cells, 'x')
        assert 3 == ai.winnable_in_n_moves(line, cells, 'o')
        cells[line[0]] = 'X'
        assert 2 == ai.winnable_in_n_moves(line, cells, 'X')
        assert ai.winnable_in_n_moves(line, cells, 'O') is None
        cells[line[0]] = 'O'
        cells[line[1]] = 'O'
        assert ai.winnable_in_n_moves(line, cells, 'X') is None
        assert 1 == ai.winnable_in_n_moves(line, cells, 'O')
        cells[line[0]] = 'X'
        cells[line[1]] = 'X'
        cells[line[2]] = 'X'
        assert 0 == ai.winnable_in_n_moves(line, cells, 'X')
        assert ai.winnable_in_n_moves(line, cells, 'O') is None

def test_first_move(g):
    assert 'B2' == ai.next_move(g, 'x')

def test_head_to_head():
    # Make the AI play against itself a bunch of times. Randomize which
    # side starts. Every game should take a full 9 moves, and every gamee
    # should end with a draw.
    for i in range(100):
        g = game.Game()
        player = random.choice('XO')
        n = 0
        while True:
            cell = ai.next_move(g, player)
            g[cell] = player
            n += 1
            w = g.winner()
            if w and (w != 'none'):
                if w != g.first or n != 9:
                    pytest.fail('Game won unexpectedly:\n%s.' % str(g))
                break
            if n == 9:
                break
            player = game.other_player(player)
