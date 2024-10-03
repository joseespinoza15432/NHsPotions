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
        result = connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = gold - :price, num_green_ml = numgreenml + :ml_per_barrel"))
    connection.execute(result, {"price": Barrel.price, "ml_per_barrel": Barrel.ml_per_barrel})

    print(f"barrels delievered: {barrels_delivered} order_id: {order_id}")

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    
    print(wholesale_catalog)

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_green_potions, gold FROM global_inventory"))
    
    row = result.fetchone()

    numberofpotions = row['num_green_potion']
    amountofgold = row['gold']

    greenpotion = wholesale_catalog[0]


    if numberofpotions < 10 and amountofgold > greenpotion.price and greenpotion.potion_type == [0, 100, 0, 0]:
        maxamount = amountofgold // greenpotion.price
        return [
            {
                "sku": "SMALL_GREEN_BARREL",
                "quantity": maxamount,
            }
        ]
    