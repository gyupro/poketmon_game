"""Tests for the shop system."""

import pytest

from src.shop import Shop, ShopItem


class TestShop:
    """Tests for Shop buy and sell logic."""

    def test_buy_deducts_money(self):
        """Buying 1 potion at 300 from 1000 leaves 700 and bag has 1."""
        shop = Shop(inventory=[ShopItem(item_id="potion", price=300)])
        bag: dict[str, int] = {}
        remaining = shop.buy("potion", 1, 1000, bag)
        assert remaining == 700
        assert bag["potion"] == 1

    def test_buy_insufficient_funds(self):
        """Buying at 300 with only 100 returns money unchanged."""
        shop = Shop(inventory=[ShopItem(item_id="potion", price=300)])
        bag: dict[str, int] = {}
        remaining = shop.buy("potion", 1, 100, bag)
        assert remaining == 100
        assert "potion" not in bag

    def test_sell_gives_half_price(self):
        """Selling 1 potion at sell_price=150 from 3 gives money+150 and bag has 2."""
        shop = Shop(inventory=[ShopItem(item_id="potion", price=300)])
        bag: dict[str, int] = {"potion": 3}
        new_money = shop.sell("potion", 1, 500, bag, sell_price=150)
        assert new_money == 650
        assert bag["potion"] == 2

    def test_buy_multiple(self):
        """Buying 5 pokeballs at 200 from 2000 leaves 1000 and bag has 5."""
        shop = Shop(inventory=[ShopItem(item_id="pokeball", price=200)])
        bag: dict[str, int] = {}
        remaining = shop.buy("pokeball", 5, 2000, bag)
        assert remaining == 1000
        assert bag["pokeball"] == 5
