from fastapi import APIRouter

import sqlalchemy
from src import database as db

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """

    inventory_catalog = []

    with db.engine.begin() as connection:

        result = connection.execute(sqlalchemy.text("SELECT num_red_potions, num_green_potions, num_blue_potions FROM global_inventory")).fetchone()
        
        if result.num_red_potions > 0:
            inventory_catalog.append(
                {
                    "sku": "red_POTION_0",
                    "name": "green potion",
                    "quantity": result.num_red_potions,
                    "price": 50,
                    "potion_type": [100, 0, 0, 0],
                }
            )
        if result.num_green_potions > 0:
            inventory_catalog.append(
                {
                    "sku": "green_POTION_0",
                    "name": "green potion",
                    "quantity": result.num_green_potions,
                    "price": 50,
                    "potion_type": [0, 100, 0, 0],
                }
            )
        if result.num_blue_potions > 0:
            inventory_catalog.append(
                {
                    "sku": "blue_POTION_0",
                    "name": "green potion",
                    "quantity": result.num_blue_potions,
                    "price": 50,
                    "potion_type": [0, 0, 100, 0],
                }
            )
    return inventory_catalog
