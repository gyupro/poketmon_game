"""Shop System - Buy and sell items at Pokemon shops."""

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class ShopItem:
    """Represents an item available in a shop."""
    item_id: str
    price: int


class Shop:
    """A shop where players can buy and sell items."""

    def __init__(self, inventory: List[ShopItem]) -> None:
        self._inventory: Dict[str, ShopItem] = {
            item.item_id: item for item in inventory
        }

    def buy(self, item_id: str, quantity: int, money: int, bag: Dict[str, int]) -> int:
        """Buy items from the shop.

        Returns remaining money after purchase, or unchanged money if
        the item is not found or funds are insufficient.
        """
        shop_item = self._inventory.get(item_id)
        if shop_item is None:
            return money

        total_cost = shop_item.price * quantity
        if money < total_cost:
            return money

        bag[item_id] = bag.get(item_id, 0) + quantity
        return money - total_cost

    def sell(self, item_id: str, quantity: int, money: int,
             bag: Dict[str, int], sell_price: int) -> int:
        """Sell items from the bag.

        Returns new money total after sale, or unchanged money if the
        player doesn't have enough of the item.
        """
        current_quantity = bag.get(item_id, 0)
        if current_quantity < quantity:
            return money

        bag[item_id] = current_quantity - quantity
        if bag[item_id] == 0:
            del bag[item_id]

        return money + (sell_price * quantity)
