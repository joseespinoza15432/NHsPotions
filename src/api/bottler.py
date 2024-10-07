from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth

import sqlalchemy
from src import database as db


router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_bottles(potions_delivered: list[PotionInventory], order_id: int):
    
    with db.engine.begin() as connection:
        for potion in potions_delivered:

            if potion.potion_type == [100, 0, 0, 0]:
                result = connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_potions = num_red_potions + {potion.quantity}, num_red_ml = num_red_ml - {potion.quantity*100}"))
            if potion.potion_type == [0, 100, 0, 0]:
                result = connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_potions = num_green_potions + {potion.quantity}, num_green_ml = num_green_ml - {potion.quantity*100}"))
            if potion.potion_type == [0, 0, 100, 0]:
                result = connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_blue_potions = num_blue_potions + {potion.quantity}, num_blue_ml = num_blue_ml - {potion.quantity*100}"))

    print(f"potions delievered: {potions_delivered} order_id: {order_id}")

    return "OK"

@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.
    # Initial logic: bottle all barrels into red potions.

    bottle_plan = []

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_red_ml, num_green_ml, num_blue_ml FROM global_inventory")).fetchone()
        
        if result.num_red_ml > 100:
            bottle_plan.append(
                {
                    "potion_type": [100, 0, 0, 0],
                    "quantity": result.num_red_ml // 100,
                }
            )
        if result.num_green_ml > 100:
            bottle_plan(
                {
                    "potion_type": [0, 100, 0, 0],
                    "quantity": result.num_green_ml // 100,
                }
            )
        if result.num_blue_ml > 100:
            bottle_plan(
                {
                    "potion_type": [0, 0, 100, 0],
                    "quantity": result.num_blue_ml // 100,
                }
            )
    return bottle_plan

if __name__ == "__main__":
    print(get_bottle_plan())



