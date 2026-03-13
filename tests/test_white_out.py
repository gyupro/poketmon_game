"""Tests for the white-out (all Pokemon fainted) flow."""

from src.player import Player
from src.pokemon import create_pokemon_from_species


class TestWhiteOut:
    def test_all_fainted_detected(self):
        player = Player("Ash", 10, 10)
        pkmn = create_pokemon_from_species(4, 5)
        pkmn.current_hp = 0
        player.pokemon_team = [pkmn]
        assert player.all_fainted()

    def test_not_all_fainted(self):
        player = Player("Ash", 10, 10)
        pkmn = create_pokemon_from_species(4, 5)
        player.pokemon_team = [pkmn]
        assert not player.all_fainted()

    def test_empty_team_not_fainted(self):
        player = Player("Ash", 10, 10)
        player.pokemon_team = []
        assert not player.all_fainted()

    def test_money_halved_on_whiteout(self):
        player = Player("Ash", 10, 10)
        player.money = 1000
        player.apply_whiteout_penalty()
        assert player.money == 500

    def test_money_floor_zero(self):
        player = Player("Ash", 10, 10)
        player.money = 1
        player.apply_whiteout_penalty()
        assert player.money == 0
