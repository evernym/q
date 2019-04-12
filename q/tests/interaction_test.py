import os
import pytest
import tempfile

from ..interaction import *

@pytest.fixture
def scratch_file_path() -> str:
    x = tempfile.TemporaryDirectory()
    yield os.path.join(x.name, '.x')
    x.cleanup()

@pytest.fixture
def db(scratch_file_path) -> Database:
    yield Database(scratch_file_path)

@pytest.fixture
def inter():
    return Interaction.from_row(('abcxyz', 9, 8, '{\n"a": 1\n}'))

def test_interaction_from_row():
    x = Interaction.from_row(('12345', 0, 1, None))
    assert x.thid == '12345'
    assert x.last_received_t == 0
    assert x.last_sent_t == 1
    assert x.data == None
    assert x.db_fresh_t > 0

def test_new_db(db):
    assert db.last_cleanup_t > 1555037743

def test_get_no_such_interaction(db):
    i = db.get_interaction('abcxyz')
    assert i is None

def test_db_persistence(scratch_file_path, inter):
    with Database(scratch_file_path) as db:
        db.set_interaction(inter)
    with Database(scratch_file_path) as db:
        inter2 = db.get_interaction('abcxyz')
    assert str(inter) == str(inter2)

def test_delete_no_such_interaction(db):
    db.delete_interaction('abcxyz')

def test_upsert(db, inter):
    inter.db_fresh_t = 1
    db.set_interaction(inter)
    assert inter.db_fresh_t > 1
    inter2 = db.get_interaction(inter.thid)
    assert inter2.db_fresh_t == inter.db_fresh_t
    db.set_interaction(inter2)
    inter3 = db.get_interaction(inter.thid)
    # Rarely, there might be a 1-second difference between 2 and 3.
    # If so, compensate.
    if inter3.db_fresh_t > inter2.db_fresh_t:
        inter3.db_fresh_t -= 1
    assert str(inter3) == str(inter2)
