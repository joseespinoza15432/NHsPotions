from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

potion_types = [
            {"type": [100, 0, 0, 0], "name": "Red Potion"},
            {"type": [0, 100, 0, 0], "name": "Green Potion"},
            {"type": [0, 0, 100, 0], "name": "Blue Potion"},
            {"type": [0, 0, 0, 100], "name": "Dark Potion"},
            {"type": [0, 50, 0, 50], "name": "Purple Potion"},
            {"type": [0, 50, 50, 0], "name": "Yellow Potion"},
        ]

potion_map = {
    (100, 0, 0, 0): {"sku": "nh_red_potion", "name": "red_potion"},
    (0, 100, 0, 0): {"sku": "nh_green_potion", "name": "green_potion"},
    (0, 0, 100, 0): {"sku": "nh_blue_potion", "name": "blue_potion"},
    (0, 0, 0, 100): {"sku": "nh_dark_potion", "name": "dark_potion"},
    (0, 50, 0, 50): {"sku": "nh_purple_potion", "name": "purple_potion"},
    (0, 50, 50, 0): {"sku": "nh_yellow_potion", "name": "yellow_potion"}
}

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

            potion_type = tuple(potion.potion_type)

            used_red_ml = potion.potion_type[0] * potion.quantity
            used_green_ml = potion.potion_type[1] * potion.quantity
            used_blue_ml = potion.potion_type[2] * potion.quantity
            used_dark_ml = potion.potion_type[3] * potion.quantity

            connection.execute(sqlalchemy.text("""
                INSERT INTO ml_ledger (red_ml, green_ml, blue_ml, dark_ml)
                VALUES (:red_ml, :green_ml, :blue_ml, :dark_ml)
                """),
                {
                    "red_ml": -used_red_ml, 
                    "green_ml": -used_green_ml,
                    "blue_ml": -used_blue_ml, 
                    "dark_ml": -used_dark_ml
                })
            
            
            if potion_type in potion_map:
                potion_info = potion_map[potion_type]
                connection.execute(sqlalchemy.text("""
                    INSERT INTO potion_ledger (potion_sku, name, quantity, price, red_ml, green_ml, blue_ml, dark_ml)
                    VALUES (:potion_sku, :name, :quantity, :price, :red_ml, :green_ml, :blue_ml, :dark_ml)
                    """),
                    {
                        "potion_sku": potion_info["sku"],
                        "name": potion_info["name"],
                        "quantity": potion.quantity,
                        "price": 40,
                        "red_ml": used_red_ml, 
                        "green_ml": used_green_ml,
                        "blue_ml": used_blue_ml, 
                        "dark_ml": used_dark_ml
                    })

        
        
    print(f"potions delievered: {potions_delivered} order_id: {order_id}")

    return "OK"

@router.post("/plan")
def get_bottle_plan():

    bottle_plan = []
    potion_counts = {potion["name"]: 0 for potion in potion_types} 

    with db.engine.begin() as connection:
        result_potions = connection.execute(sqlalchemy.text("""
            SELECT COALESCE(SUM(quantity), 0) AS total_potions
            FROM potion_ledger
        """)).first()
        total_potions = result_potions.total_potions

        storage_capacity = connection.execute(sqlalchemy.text("""
            SELECT amount
            FROM storage
            WHERE name = 'potions'
        """)).scalar()

        if total_potions >= storage_capacity:
            print(f"Potion storage full: {total_potions}/{storage_capacity}. No bottling planned")
            return bottle_plan  

        result = connection.execute(sqlalchemy.text("""
            SELECT 
                COALESCE(SUM(red_ml), 0) AS red_ml, 
                COALESCE(SUM(green_ml), 0) AS green_ml, 
                COALESCE(SUM(blue_ml), 0) AS blue_ml, 
                COALESCE(SUM(dark_ml), 0) AS dark_ml
            FROM ml_ledger
        """)).first()

        available_ml = [result.red_ml, result.green_ml, result.blue_ml, result.dark_ml]

        potion_index = 0  
        while sum(available_ml) >= 100 and total_potions < storage_capacity:
            potion = potion_types[potion_index]
            potion_type = potion["type"]
            
            if all(available_ml[i] >= potion_type[i] for i in range(4)):
                if total_potions + 1 > storage_capacity:
                    print(f"Skipping bottling {potion['name']}: Exceeds storage capacity")
                    break

                
                bottle_plan.append({
                    "potion_type": potion_type,
                    "quantity": 1
                })
                total_potions += 1
                available_ml = [available_ml[i] - potion_type[i] for i in range(4)]
                potion_counts[potion["name"]] += 1

                print(f"Bottled {potion['name']}. Updated total potions: {total_potions}, Available ML: {available_ml}")
            else:
                print(f"Not enough ML for {potion['name']}")

            potion_index = (potion_index + 1) % len(potion_types)

    print(f"Bottle plan created: {bottle_plan}")
    print(f"Potion distribution: {potion_counts}")
    return bottle_plan

if __name__ == "__main__":
    print(get_bottle_plan())



