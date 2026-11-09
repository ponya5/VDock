"""DL-165: a button's confirm override survives save/load; junk falls back to 'default'."""
from models.button import Button


def test_confirm_override_round_trips():
    b = Button.from_dict({'id': 'b1', 'label': 'Push', 'confirm': 'always'})
    assert Button.from_dict(b.to_dict()).confirm == 'always'


def test_unknown_confirm_value_is_default():
    assert Button.from_dict({'id': 'b2', 'confirm': 'sometimes'}).confirm == 'default'
    assert Button.from_dict({'id': 'b3'}).confirm == 'default'
