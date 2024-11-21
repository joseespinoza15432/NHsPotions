from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db


router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int):
    
    print(f"barrels delievered: {barrels_delivered} order_id: {order_id}")

    with db.engine.begin() as connection:
        
        red_ml = 0
        green_ml = 0
        blue_ml = 0
        dark_ml = 0
        gold = 0

        for barrel in barrels_delivered:
            red_ml += (barrel.potion_type[0] * barrel.ml_per_barrel * barrel.quantity)
            green_ml += (barrel.potion_type[1] * barrel.ml_per_barrel * barrel.quantity)
            blue_ml += (barrel.potion_type[2] * barrel.ml_per_barrel * barrel.quantity)
            dark_ml += (barrel.potion_type[3] * barrel.ml_per_barrel * barrel.quantity)
            gold -= barrel.price * barrel.quantity

        
        connection.execute(sqlalchemy.text("""
            INSERT INTO ml_ledger (red_ml, green_ml, blue_ml, dark_ml)
            VALUES (:red_ml, :green_ml, :blue_ml, :dark_ml)
            """),
            {
                "red_ml": red_ml, 
                "green_ml" : green_ml, 
                "blue_ml" : blue_ml, 
                "dark_ml" : dark_ml
            })
        
        connection.execute(sqlalchemy.text("""
            INSERT INTO gold_ledger (gold)
            VALUES (:gold)
            """),
            {"gold": gold})
                                           
    return "OK"

@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    print("Wholesale catalog:", wholesale_catalog)
    barrel_plan = []

    with db.engine.begin() as connection:
        gold = connection.execute(sqlalchemy.text("""
            SELECT COALESCE(SUM(gold), 0) AS total_gold
            FROM gold_ledger
        """)).scalar()

        ml_storage_capacity = connection.execute(sqlalchemy.text("""
            SELECT amount
            FROM storage
            WHERE name = 'ml'
        """)).scalar()

        result = connection.execute(sqlalchemy.text("""
            SELECT 
                COALESCE(SUM(red_ml), 0) AS red_ml, 
                COALESCE(SUM(green_ml), 0) AS green_ml,
                COALESCE(SUM(blue_ml), 0) AS blue_ml,
                COALESCE(SUM(dark_ml), 0) AS dark_ml
            FROM ml_ledger
        """)).first()

        ml_levels = {
            "red_ml": result.red_ml,
            "green_ml": result.green_ml,
            "blue_ml": result.blue_ml,
            "dark_ml": result.dark_ml,
        }

        current_total_ml = sum(ml_levels.values())
        print("Initial gold:", gold)
        print("Initial ml levels:", ml_levels)
        print(f"Current total ml: {current_total_ml}, Maximum ml storage capacity: {ml_storage_capacity}")

        barrel_quantity_map = {barrel.sku: barrel.quantity for barrel in wholesale_catalog}

        sorted_ml_levels = sorted(ml_levels.items(), key=lambda x: x[1])
        sorted_catalog = sorted(wholesale_catalog, key=lambda barrel: barrel.ml_per_barrel, reverse=True)

        for potion, current_ml in sorted_ml_levels:
            potion_index = ["red_ml", "green_ml", "blue_ml", "dark_ml"].index(potion)
            print(f"Processing potion type: {potion}, Current ml: {current_ml}")

            for barrel in sorted_catalog:
                if barrel.potion_type[potion_index] == 1 and barrel_quantity_map[barrel.sku] > 0:
                    potential_new_ml = current_ml + barrel.ml_per_barrel
                    potential_total_ml = current_total_ml + barrel.ml_per_barrel

                    print(f"Evaluating barrel: {barrel.sku}, "
                          f"Potential {potion} ml: {potential_new_ml}, "
                          f"Potential total ml: {potential_total_ml}, "
                          f"Gold left: {gold}, Barrels remaining: {barrel_quantity_map[barrel.sku]}")

                    if gold >= barrel.price and potential_total_ml <= ml_storage_capacity:
                        if barrel.sku in [b["sku"] for b in barrel_plan]:
                            for b in barrel_plan:
                                if b["sku"] == barrel.sku:
                                    b["quantity"] += 1
                                    break
                        else:
                            barrel_plan.append({"sku": barrel.sku, "quantity": 1})

                        gold -= barrel.price
                        ml_levels[potion] += barrel.ml_per_barrel
                        current_ml += barrel.ml_per_barrel
                        current_total_ml += barrel.ml_per_barrel
                        barrel_quantity_map[barrel.sku] -= 1

                        print(f"Added {barrel.sku} to plan. Updated gold: {gold}, "
                              f"Updated {potion} ml: {ml_levels[potion]}, "
                              f"Remaining barrels of {barrel.sku}: {barrel_quantity_map[barrel.sku]}")
                    elif barrel_quantity_map[barrel.sku] == 0:
                        print(f"Skipped {barrel.sku}: No barrels remaining.")
                    elif potential_total_ml > ml_storage_capacity:
                        print(f"Skipped {barrel.sku}: Exceeds maximum ml storage capacity.")
                    elif gold < barrel.price:
                        print(f"Skipped {barrel.sku}: Insufficient gold.")

            if gold <= 0:
                print("Not enough gold to continue purchasing.")
                break

        barrel_plan = [{"sku": sku, "quantity": quantity} for sku, quantity in barrel_quantity_map.items() if quantity > 0]

        print("Final gold:", gold)
        print("Final ml levels:", ml_levels)
        print("Final total ml:", current_total_ml)
        print("Planned barrels:", barrel_plan)
        print("Available ml storage capacity:", ml_storage_capacity)

    return barrel_plan


