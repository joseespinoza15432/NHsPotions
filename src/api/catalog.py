from fastapi import APIRouter

import sqlalchemy
from src import database as db

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory"))

    
    row = result.fetchone()
    numpotions = row['num_green_potions']

    if numpotions > 0:
        return [
            {
                "sku": "green_POTION_0",
                "name": "green potion",
                "quantity": 1,
                "price": 30,
                "potion_type": [0, 100, 0, 0],
            }
        ]
