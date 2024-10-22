from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
import random

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

        result = connection.execute(sqlalchemy.text("SELECT num_red_ml, num_green_ml, num_blue_ml, num_dark_ml FROM global_inventory")).first()
        current_ml = [result.num_red_ml, result.num_green_ml, result.num_blue_ml, result.num_dark_ml]
       

        for potion in potions_delivered:
            
            current_ml[0] -= potion.potion_type[0] * potion.quantity
            current_ml[1] -= potion.potion_type[1] * potion.quantity
            current_ml[2] -= potion.potion_type[2] * potion.quantity
            current_ml[3] -= potion.potion_type[3] * potion.quantity

            connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_ml = :rml, num_green_ml = :gml, num_blue_ml = :bml, num_dark_ml = :dml"), {"rml" : current_ml[0], "gml" : current_ml[1], "bml" : current_ml[2], "dml" : current_ml[3]})

            if potion.potion_type == [100, 0, 0, 0]:  
                potion_id = 1
            elif potion.potion_type == [0, 100, 0, 0]:  
                potion_id = 2
            elif potion.potion_type == [0, 0, 100, 0]: 
                potion_id = 3
            elif potion.potion_type == [0, 0, 0, 100]:  
                potion_id = 4
            elif potion.potion_type == [50, 0, 50, 0]:  
                potion_id = 5
            elif potion.potion_type == [50, 50, 0, 0]:  
                potion_id = 6

            connection.execute(sqlalchemy.text("UPDATE potion_inventory SET quantity = quantity + :qty WHERE potion_id = :pid"), {"qty" : potion.quantity, "pid" : potion_id})
            
    print(f"potions delievered: {potions_delivered} order_id: {order_id}")

    return "OK"

@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    bottle_plan = []

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_red_ml, num_green_ml, num_blue_ml, num_dark_ml FROM global_inventory")).first()
        
        available_ml = [result.num_red_ml, result.num_green_ml, result.num_blue_ml, result.num_dark_ml]

        yellow_potion = [50, 50, 0, 0]
        purple_potion = [50, 0, 50, 0]
        red_potion = [100, 0, 0, 0]
        green_potion = [0, 100, 0, 0]
        blue_potion = [0, 0, 100, 0]
        dark_potion = [0, 0, 0, 100]

        while sum(available_ml) >= 100:

            if available_ml[0] >= 50 and available_ml[1] >= 50:
                bottle_plan.append(
                    {
                        "potion_type": yellow_potion,
                        "quantity": 1
                    }
                )
                available_ml[0] -= 50
                available_ml[1] -= 50

            elif available_ml[0] >= 50 and available_ml[2] >= 50:
                bottle_plan.append(
                    {
                        "potion_type": purple_potion,
                        "quantity": 1
                    }
                )
                available_ml[0] -= 50
                available_ml[2] -= 50
                
            elif available_ml[0] >= 100:
                bottle_plan.append(
                    {
                        "potion_type": red_potion,
                        "quantity": 1
                    }
                )
                available_ml[0] -= 100

            elif available_ml[1] >= 100:
                bottle_plan.append(
                    {
                        "potion_type": green_potion,
                        "quantity": 1
                    }
                )
                available_ml[1] -= 100

            elif available_ml[2] >= 100:
                bottle_plan.append(
                    {
                        "potion_type": blue_potion,
                        "quantity": 1
                    }
                )
                available_ml[2] -= 100

            elif available_ml[3] >= 100:
                bottle_plan.append(
                    {
                        "potion_type": dark_potion,
                        "quantity": 1
                    }
                )
                available_ml[3] -= 100

            else:
                print("not enough ml :(")
                break

    return bottle_plan

"""
def potion_type_creator(available_ml):
    total_ml = 100
    potion_type = [0, 0, 0, 0]

    colors = [i for i, ml in enumerate(available_ml) if ml > 0]

    for i in range (3):
        if colors:
            idx = random.choice(colors)
            max_ml = min(total_ml, available_ml[idx])
            potion_type[idx] = random.randint(0, max_ml)
            total_ml -= potion_type[idx]

            if available_ml[idx] - potion_type[idx] == 0:
                colors.remove(idx)

    remaining_color = random.choice(colors)
    potion_type[remaining_color] = total_ml

    if get_create_potion(potion_type, available_ml):
        return potion_type
    else:
        return None


def get_create_potion(potion_type, available_ml):
    for i in range(4):
        if available_ml[i] < potion_type[i]:
            return False
    return True


def create_potion(potion_type, available_ml):
    for i in range(4):
        available_ml[i] -= potion_type[i]
    print("Potion Created, updated ml: ", available_ml)
"""

if __name__ == "__main__":
    print(get_bottle_plan())



