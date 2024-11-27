from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """

    inventory_catalog = []

    with db.engine.begin() as connection:
        
        #result = connection.execute(sqlalchemy.text("SELECT potion_sku, name, price, quantity, red_ml, green_ml, blue_ml, dark_ml FROM potion_inventory WHERE quantity > 0")).fetchall()

        result = connection.execute(sqlalchemy.text("""
            SELECT
                potion_sku,
                name,
                price,
                SUM(quantity) AS quantity,
                red_ml,
                green_ml,
                blue_ml,
                dark_ml
            FROM potion_ledger
            GROUP BY potion_sku, name, price, red_ml, green_ml, blue_ml, dark_ml
            HAVING SUM(quantity) > 0    
        """)).fetchall()
                            
        for potion in result:
            item_sku = potion.potion_sku
            item_name = potion.name
            price = potion.price
            quantity = potion.quantity
            red_ml = potion.red_ml
            green_ml = potion.green_ml
            blue_ml = potion.blue_ml
            dark_ml = potion.dark_ml

            inventory_catalog.append(
            {
                "sku": item_sku,
                "name": item_name,
                "quantity": quantity,
                "price": 30,
                "potion_type": [red_ml, green_ml, blue_ml, dark_ml]
            }
            )
        
    return inventory_catalog
