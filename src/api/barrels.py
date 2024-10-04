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
            result = connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = gold - :price, num_green_ml = num_green_ml + :ml_per_barrel"), {"price": barrel.price, "ml_per_barrel": barrel.ml_per_barrel})

    print(f"barrels delievered: {barrels_delivered} order_id: {order_id}")
        
    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    
    print(wholesale_catalog)

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_green_potions, gold FROM global_inventory")).fetchone()
    
    #row = result.fetchone()

    numberofpotions = result['num_green_potion']
    amountofgold = result['gold']

    #greenpotion = wholesale_catalog[0]

    purchase_plan = []

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
    if numberofpotions < 10 and amountofgold > greenpotion.price and greenpotion.potion_type[0, 100, 0, 0]:
        maxamount = amountofgold // greenpotion.price
        return [
            {
                "sku": "SMALL_GREEN_BARREL",
                "quantity": maxamount,
            }
        ]"""
    

#in barrels/plan, you need to loop through the list of barrels given in wholesale catalog and buy barrels of the color you need and within an affordable price, 
# right now you just look at the first barrel price, not even the color of that barrel, you need to loop though that lis, check if it green, check if you can afford, then plan to buy
