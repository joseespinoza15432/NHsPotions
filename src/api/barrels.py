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
    """ """
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_potions = num_green_potions + 1"))

    print(f"barrels delievered: {barrels_delivered} order_id: {order_id}")

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """

    #with db.engine.begin() as connection:
    #    result = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory, WHERE num_green_potions < 10"))
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory"))

    row = result.fetchone()
    if row:
        greenpotioninventory = row['num_green_potions']
        #print(greenpotioninventory)

    print(wholesale_catalog)

    if greenpotioninventory < 10:
        return [
            {
                "sku": "SMALL_GREEN_BARREL",
                "quantity": 1,
            }
        ]

"""
from sqlalchemy import text

# Execute the SQL query directly
with db.engine.begin() as connection:
    result = connection.execute(text("SELECT column_name FROM table_name WHERE condition"))

# Fetch the result and assign it to a variable
row = result.fetchone()  # Fetch one row
if row:
    variable_name = row['column_name']  # Access the column by name
    print(variable_name)
"""