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

        result = connection.execute(sqlalchemy.text("SELECT potion_id, price, potion_type_red, potion_type_green, potion_type_blue, potion_type_dark, potion_quantity FROM custom_potions")).fetchall()

        for potion in result:
            red_ml = potion.num_red_ml
            green_ml = potion.num_green_ml
            blue_ml = potion.num_blue_ml
            dark_ml = potion.num_dark_ml
            cost = potion.price
            quantity = potion.potion_quantity

            inventory_catalog.append(
            {
                "sku": f"NHsCustomPotion_{potion.potion_id}",
                "name": "Custom Potion",
                "quantity": quantity,
                "price": cost,
                "potion_type": [red_ml, green_ml, blue_ml, dark_ml]
            }
            )
        
    return inventory_catalog
