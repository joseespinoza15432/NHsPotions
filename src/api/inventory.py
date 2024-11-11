from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import math
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/inventory",
    tags=["inventory"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.get("/audit")
def get_inventory():
    """ """
    """
    return database values
    """

    total_potions = 0
    total_liquid = 0
    total_gold = 0

    with db.engine.begin() as connection:

        result_potions = connection.execute(sqlalchemy.text("""
            SELECT COALESCE(SUM(quantity), 0) AS total_potions
            FROM potion_ledger
            """)).first()

        result_liquid = connection.execute(sqlalchemy.text("""
            SELECT 
                COALESCE(SUM(red_ml), 0) AS red_ml, 
                COALESCE(SUM(green_ml), 0) AS green_ml, 
                COALESCE(SUM(blue_ml), 0) AS blue_ml, 
                COALESCE(SUM(dark_ml), 0) AS dark_ml
            FROM ml_ledger
            """)).first()
        
        result_gold = connection.execute(sqlalchemy.text("SELECT COALESCE(SUM(gold),0) AS total_gold FROM gold_ledger")).first()
        
        total_potions = result_potions.total_potions
        total_liquid = result_liquid.red_ml + result_liquid.green_ml + result_liquid.blue_ml + result_liquid.dark_ml
        total_gold = result_gold.total_gold

    return {"number_of_potions": total_potions, "ml_in_barrels": total_liquid, "gold": total_gold}

# Gets called once a day
@router.post("/plan")
def get_capacity_plan():
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """

    return {
        "potion_capacity": 0,
        "ml_capacity": 0
        }

class CapacityPurchase(BaseModel):
    potion_capacity: int
    ml_capacity: int

# Gets called once a day
@router.post("/deliver/{order_id}")
def deliver_capacity_plan(capacity_purchase : CapacityPurchase, order_id: int):
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """

    return "OK"
