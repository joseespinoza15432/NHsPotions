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

            result = connection.execute(sqlalchemy.text("SELECT potion_id, potion_quantity FROM custom_potions WHERE potion_type_red = :rml AND potion_type_green = :gml AND potion_type_blue = :bml AND potion_type_dark = :dml"),  {"rml": potion.potion_type[0], "gml": potion.potion_type[1], "bml": potion.potion_type[2], "dml": potion.potion_type[3]}).first()
            
            if result:
                new_inventory = result.potion_quantity + potion.quantity
                connection.execute(sqlalchemy.text("UPDATE custom_potions SET potion_quantity = :inv WHERE potion_id = :pid"), {"inv": new_inventory, "pid": result.potion_id})
                
            else:
                connection.execute(sqlalchemy.text("INSERT INTO custom_potions (potion_type_red, potion_type_green, potion_type_blue, potion_type_dark, potion_quantity, price) VALUES (:rml, :gml, :bml, :dml, :amount, :price) "), {"rml" : potion.potion_type[0], "gml" : potion.potion_type[1], "bml" : potion.potion_type[2], "dml" : potion.potion_type[3], "amount" : potion.quantity, "price" : 50})

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
        
        available_ml = []
        available_ml.append(result.num_red_ml)
        available_ml.append(result.num_green_ml)
        available_ml.append(result.num_blue_ml)
        available_ml.append(result.num_dark_ml)

        while sum(available_ml) >= 100:
            potion_type = potion_type_creator(available_ml)

            if potion_type:
                create_potion(potion_type, available_ml)

                bottle_plan.append(
                    {
                        "potion_type": potion_type,
                        "quantity": 1
                    }
                )
            else:
                print("not enough ml :(")
                break

    return bottle_plan


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


if __name__ == "__main__":
    print(get_bottle_plan())



