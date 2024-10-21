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
        result = connection.execute(sqlalchemy.text("SELECT gold, num_red_ml, num_green_ml, num_blue_ml, num_dark_ml FROM global_inventory")).first()

        red_ml = result.num_red_ml
        green_ml = result.num_green_ml
        blue_ml = result.num_blue_ml
        dark_ml = result.num_dark_ml
        gold_in_instance = result.gold

        for barrel in barrels_delivered:
            if barrel.potion_type == [1, 0, 0, 0]:
                red_ml += barrel.ml_per_barrel * barrel.quantity
                gold_in_instance -= barrel.price * barrel.quantity
            if barrel.potion_type == [0, 1, 0, 0]:
                green_ml += barrel.ml_per_barrel * barrel.quantity
                gold_in_instance -= barrel.price * barrel.quantity
            if barrel.potion_type == [0, 0, 1, 0]:
                blue_ml += barrel.ml_per_barrel * barrel.quantity
                gold_in_instance -= barrel.price * barrel.quantity
            if barrel.potion_type == [0, 0, 0, 1]:
                dark_ml += barrel.ml_per_barrel * barrel.quantity
                gold_in_instance -= barrel.price * barrel.quantity

        connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = :g, num_red_ml = :rml, num_green_ml = :gml, num_blue_ml = :bml, num_dark_ml = :dml"), {"g": gold_in_instance, "rml" : red_ml, "gml" : green_ml, "bml" : blue_ml, "dml" : dark_ml})

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    
    print(wholesale_catalog)

    barrel_plan = []

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_red_ml, num_green_ml, num_blue_ml, num_dark_ml, gold FROM global_inventory")).first()

        red_ml = result.num_red_ml
        green_ml = result.num_green_ml
        blue_ml = result.num_blue_ml
        dark_ml = result.num_dark_ml
        gold_in_instance = result.gold

        potion_levels = [
            {"type": 1, "ml": red_ml},
            {"type": 2, "ml": green_ml},
            {"type": 3, "ml": blue_ml},
            {"type": 4, "ml": dark_ml}
        ]

        potion_levels.sort(key = lambda x: x["ml"])

        for potion in potion_levels:
            potion_type = potion["type"]

            for barrel in wholesale_catalog:
                if barrel.potion_type[potion_type - 1] == 1:
                    max_afford = gold_in_instance // barrel.price
                    quantity_of_barrels = min(max_afford, barrel.quantity)

                    if quantity_of_barrels > 0:
                        barrel_plan.append(
                            {
                                "sku": barrel.sku,
                                "quantity": quantity_of_barrels
                            }
                        )
                        gold_in_instance -= barrel.price * quantity_of_barrels

                    if gold_in_instance <= 0:
                        break
            if gold_in_instance <= 0:
                break
        
    return barrel_plan
    