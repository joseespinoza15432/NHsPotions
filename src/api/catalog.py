from fastapi import APIRouter

import sqlalchemy
from src import database as db

#with db.engine.begin() as connection:
#        result = connection.execute(sqlalchemy.text(sql_to_execute))

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory"))

    row = result.fetchone()

    if row:
        greenpotioninventory = row['num_green_potions']
        #print(greenpotioninventory)
        
    if greenpotioninventory > 0:
        return [
                {
                    "sku": "green_POTION_0",
                    "name": "green potion",
                    "quantity": 1,
                    "price": 50,
                    "potion_type": [0, 100, 0, 0],
                }
            ]
