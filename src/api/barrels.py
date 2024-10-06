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
    
    with db.engine.begin() as connection:
        for barrel in barrels_delivered:    
            if barrel.potion_type == [100, 0, 0, 0]: 
                result = connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = gold - {barrel.price}, num_red_ml = num_red_ml + {barrel.ml_per_barrel}"))
            elif barrel.potion_type == [0, 100, 0, 0]: 
                result = connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = gold - {barrel.price}, num_green_ml = num_green_ml + {barrel.ml_per_barrel}"))
            elif barrel.potion_type == [0, 0, 100, 0]: 
                result = connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = gold - {barrel.price}, num_blue_ml = num_blue_ml + {barrel.ml_per_barrel}"))


    print(f"barrels delievered: {barrels_delivered} order_id: {order_id}")
        
    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    
    print(wholesale_catalog)

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_red_potions, num_green_potions, num_blue_potions, gold FROM global_inventory")).fetchone()

        for barrel in wholesale_catalog:

            max_afford = result.gold // barrel.price
            quantity_of_barrels = min(max_afford, barrel.quantity)

            if barrel.potion_type == [100, 0, 0, 0]: 
                if result.num_red_potions <= result.num_green_potions and result.num_red_potions <= result.num_blue_potions:
                    return [
                                {
                                    "sku": barrel.sku,
                                    "quantity": quantity_of_barrels,
                                }
                    ]
            if barrel.potion_type == [0, 100, 0, 0]:
                if result.num_green_potions <= result.num_red_potions and result.num_green_potions <= result.num_blue_potions:
                    return [
                                {
                                    "sku": barrel.sku,
                                    "quantity": quantity_of_barrels,
                                }
                    ]
            if barrel.potion_type == [0, 0, 100, 0]:
                if result.num_blue_potions <= result.num_red_potions and result.num_blue_potions <= result.num_green_potions:
                    return [
                                {
                                    "sku": barrel.sku,
                                    "quantity": quantity_of_barrels,
                                }
                    ]
                
    return[]

    """


    for barrel in wholesale_catalog:
        if barrel.potion_type == [0, 100, 0, 0]:
            if amountofgold >= barrel.price:
                maxamount = amountofgold // barrel.price
                return [
                            {
                                "sku": "SMALL_GREEN_BARREL",
                                "quantity": maxamount,
                            }
                ]

    """

    
