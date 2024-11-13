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

        print("# of potions: ", total_potions, "# of ml: ", total_liquid, "# of gold: ", total_gold)
    return {"number_of_potions": total_potions, "ml_in_barrels": total_liquid, "gold": total_gold}

# Gets called once a da
@router.post("/plan")
def get_capacity_plan():
    """
    Determine the capacity purchase plan for potions and ml.
    Each capacity costs 1000 gold.
    """
    potion_capacity = 0
    ml_capacity = 0

    with db.engine.begin() as connection:
    
        result = connection.execute(sqlalchemy.text("""
            SELECT name, capacity, amount
            FROM storage
            """)).fetchall()
        
        result_gold = connection.execute(sqlalchemy.text("""
            SELECT COALESCE(SUM(gold), 0) AS total_gold
            FROM gold_ledger
            """)).first()

        total_gold = result_gold.total_gold

        
        if total_gold >= 2000:
            for row in result:
                if row.name == "potions" and total_gold >= 2000:
                    potion_capacity = 1
                    total_gold -= 1000
                if row.name == "ml" and total_gold >= 2000:
                    ml_capacity = 1
                    total_gold -= 1000

    return {
        "potion_capacity": potion_capacity,
        "ml_capacity": ml_capacity
    }

class CapacityPurchase(BaseModel):
    potion_capacity: int
    ml_capacity: int

@router.post("/deliver/{order_id}")
def deliver_capacity_plan(capacity_purchase: CapacityPurchase, order_id: int):
    """
    Deliver the purchased capacities back to the shop.
    """
    with db.engine.begin() as connection:
        if capacity_purchase.potion_capacity > 0:
            connection.execute(sqlalchemy.text("""
                UPDATE storage
                SET capacity = capacity + :added_capacity,
                    amount = amount + (:added_capacity * 50)
                WHERE name = 'potions'
                """), {"added_capacity": capacity_purchase.potion_capacity})

        if capacity_purchase.ml_capacity > 0:
            connection.execute(sqlalchemy.text("""
                UPDATE storage
                SET capacity = capacity + :added_capacity,
                    amount = amount + (:added_capacity * 10000)
                WHERE name = 'ml'
                """), {"added_capacity": capacity_purchase.ml_capacity})

        total_cost = (capacity_purchase.potion_capacity + capacity_purchase.ml_capacity) * 1000
        connection.execute(sqlalchemy.text("""
            INSERT INTO gold_ledger (gold)
            VALUES (:cost)
            """), {"cost": -total_cost})

    return {"message": "Capacity updated successfully"}