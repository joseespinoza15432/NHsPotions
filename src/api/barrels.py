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
    print(wholesale_catalog)
    barrel_plan = []

    with db.engine.begin() as connection:
        gold = connection.execute(sqlalchemy.text("""
            SELECT COALESCE(SUM(gold), 0) AS total_gold
            FROM gold_ledger
            """)).scalar()

        result = connection.execute(sqlalchemy.text("""
            SELECT 
                COALESCE(SUM(red_ml), 0) AS red_ml, 
                COALESCE(SUM(green_ml), 0) AS green_ml,
                COALESCE(SUM(blue_ml), 0) AS blue_ml,
                COALESCE(SUM(dark_ml), 0) AS dark_ml
            FROM ml_ledger
            """)).first()

        ml_storage = connection.execute(sqlalchemy.text("""
            SELECT amount
            FROM storage
            WHERE name = 'ml'
            """)).scalar()

        ml_levels = {
            "red_ml": result.red_ml,
            "green_ml": result.green_ml,
            "blue_ml": result.blue_ml,
            "dark_ml": result.dark_ml
        }

        sorted_ml_levels = sorted(ml_levels.items(), key=lambda x: x[1])
        sorted_catalog = sorted(wholesale_catalog, key=lambda barrel: barrel.ml_per_barrel / barrel.price, reverse=True)

        for potion, current_ml in sorted_ml_levels:
            potion_index = ["red_ml", "green_ml", "blue_ml", "dark_ml"].index(potion)

            for barrel in sorted_catalog:
                if barrel.potion_type[potion_index] == 1 and gold >= barrel.price:
                    potential_new_ml = current_ml + barrel.ml_per_barrel

                    if potential_new_ml <= ml_storage:
                        barrel_plan.append({"sku": barrel.sku, "quantity": 1})
                        gold -= barrel.price
                        ml_levels[potion] += barrel.ml_per_barrel
                        break
                    else:
                        print(f"Skip {barrel.sku}: too much ml.")

            if gold <= 0:
                print("not enough gold :(")
                break
            
        print(barrel_plan)
    return barrel_plan