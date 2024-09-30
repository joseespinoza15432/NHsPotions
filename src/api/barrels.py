from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth

import sqlalchemy
from src import database as db


"""with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM Barrel"))
        for row in result:
            print(row)
"""
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
    """ """
    
    print(f"barrels delievered: {barrels_delivered} order_id: {order_id}")

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_green_potions, num_green_ml, gold, FROM global_inventory, WHERE num_green_potions > 10"))
        
        
    print(wholesale_catalog)

    return [
        {
            "sku": "SMALL_GREEN_BARREL",
            "quantity": 1,
        }
    ]

