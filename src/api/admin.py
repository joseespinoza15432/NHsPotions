from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.post("/reset")
def reset():
    """
    Reset the game state. Gold goes to 100, all potions are removed from
    inventory, and all barrels are removed from inventory. Carts are all reset.
    """

    
    with db.engine.begin() as connection:
        connection.execeute(sqlalchemy.text("""
            DELETE FROM gold_ledger;
            DELETE FROM ml_ledger;
            DELETE FROM potion_ledger;          
            DELETE FROM customer_information
            DELETE FROM customer_cart
            DELETE FROM cart_items
            """))

        result = connection.execute(sqlalchemy.text("""
            INSERT INTO gold_ledger (gold)
            VALUES (100)
            """))
       
    return "OK"

