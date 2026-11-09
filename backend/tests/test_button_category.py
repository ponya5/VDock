"""DL-166: a button's agent-category override survives save/load; missing means auto ('')."""
from models.button import Button


def test_category_round_trips():
    b = Button.from_dict({'id': 'b1', 'label': 'Review', 'category': 'review'})
    assert b.to_dict()['category'] == 'review'
    assert Button.from_dict(b.to_dict()).category == 'review'


def test_missing_or_empty_category_is_auto():
    assert Button.from_dict({'id': 'b2'}).category == ''
    assert Button.from_dict({'id': 'b3', 'category': None}).category == ''
    assert Button.from_dict({'id': 'b4', 'category': ''}).to_dict()['category'] == ''
