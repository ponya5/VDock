"""DL-167: portrait placement fields survive a model round trip and stay absent when unset."""
from models.button import Button
from models.profile import Page

PORTRAIT = {'position': {'row': 2, 'col': 1}, 'size': {'rows': 1, 'cols': 2}}


def test_button_portrait_round_trips():
    b = Button.from_dict({'id': 'b1', 'portrait': PORTRAIT})
    assert Button.from_dict(b.to_dict()).portrait == PORTRAIT


def test_button_without_portrait_omits_key():
    assert 'portrait' not in Button.from_dict({'id': 'b1'}).to_dict()


def test_page_portrait_grid_round_trips_and_is_omitted_when_unset():
    page = Page.from_dict({'id': 'p', 'name': 'P', 'portrait_grid': {'rows': 6, 'cols': 3}})
    assert Page.from_dict(page.to_dict()).portrait_grid == {'rows': 6, 'cols': 3}
    assert 'portrait_grid' not in Page.from_dict({'id': 'p', 'name': 'P'}).to_dict()
