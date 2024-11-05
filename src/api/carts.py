from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
from enum import Enum
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

class search_sort_options(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"

class search_sort_order(str, Enum):
    asc = "asc"
    desc = "desc"   

@router.get("/search/", tags=["search"])
def search_orders(
    customer_name: str = "",
    potion_sku: str = "",
    search_page: str = "",
    sort_col: search_sort_options = search_sort_options.timestamp,
    sort_order: search_sort_order = search_sort_order.desc,
):
    """
    Search for cart line items by customer name and/or potion sku.

    Customer name and potion sku filter to orders that contain the 
    string (case insensitive). If the filters aren't provided, no
    filtering occurs on the respective search term.

    Search page is a cursor for pagination. The response to this
    search endpoint will return previous or next if there is a
    previous or next page of results available. The token passed
    in that search response can be passed in the next search request
    as search page to get that page of results.

    Sort col is which column to sort by and sort order is the direction
    of the search. They default to searching by timestamp of the order
    in descending order.

    The response itself contains a previous and next page token (if
    such pages exist) and the results as an array of line items. Each
    line item contains the line item id (must be unique), item sku, 
    customer name, line item total (in gold), and timestamp of the order.
    Your results must be paginated, the max results you can return at any
    time is 5 total line items.
    """

    return {
        "previous": "",
        "next": "",
        "results": [
            {
                "line_item_id": 1,
                "item_sku": "1 oblivion potion",
                "customer_name": "Scaramouche",
                "line_item_total": 50,
                "timestamp": "2021-01-01T00:00:00Z",
            }
        ],
    }


class Customer(BaseModel):
    customer_name: str
    character_class: str
    level: int

@router.post("/visits/{visit_id}")
def post_visits(visit_id: int, customers: list[Customer]):
    """
    Which customers visited the shop today?
    """

    print(customers)

    return "OK"


@router.post("/")
def create_cart(new_cart: Customer):
    """ """

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("""
            INSERT INTO customer_information (name, level, class) 
            VALUES (:name, :level, :class) Returning id
            """), 
            {"name": new_cart.customer_name, 
             "level": new_cart.level, 
             "class": new_cart.character_class})
        
        cart_id = result.scalar()
        cart_result = connection.execute(sqlalchemy.text("""
            INSERT INTO customer_cart (customer_id) VALUES (:customer_id) RETURNING id"""),
            {"customer_id": cart_id})
        
        cart_id = cart_result.scalar()

    return {"cart_id": cart_id}


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    with db.engine.begin() as connection:
        potion = connection.execute(sqlalchemy.text("""
            SELECT id FROM potion_ledger
            WHERE potion_sku = :sku"""), 
            {"sku": item_sku}).first()

        connection.execute(sqlalchemy.text("""
            INSERT INTO cart_items (cart_id, potion_id, quantity) 
            VALUES (:cid, :pid, :quantity)
            """),
            {"cid": cart_id, 
             "pid": potion.id, 
             "quantity": cart_item.quantity})
       
       
    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    
    instance_potions = 0
    instance_gold = 0
    
    with db.engine.begin() as connection:
        cart = connection.execute(sqlalchemy.text("""
            SELECT 
                cart_items.quantity,
                potion_inventory.id AS potion_id,
                potion_inventory.price AS potion_price,
                potion_inventory.quantity AS potion_stock
            FROM customer_cart
            JOIN cart_items ON customer_cart.id = cart_items.cart_id
            JOIN potion_ledger ON cart_items.potion_id = potion_ledger.id
            WHERE customer_cart.id = :cart_id"""), 
            {"cart_id": cart_id}).fetchall()
        
        for item in cart:
            instance_potions += item.quantity
            instance_gold += item.quantity * item.potion_price

            connection.execute(sqlalchemy.text("""
                INSERT INTO potion_ledger (potion_sku, name, quantity, price, red_ml, green_ml, blue_ml, dark_ml)
                SELECT potion_sku, name, :quantity, price, red_ml, green_ml, blue_ml, dark_ml)
                FROM potion_ledger
                WHERE id = :potion_id
                """), 
                {"quantity": -item.quantity, 
                 "potion_id": item.potion_id})
            
        connection.execute(sqlalchemy.text("""
            INSERT INTO gold_ledger (gold)
            VALUES (:gold)
            """),
            {"gold": instance_gold})
        
        connection.execute(sqlalchemy.text("""
            UPDATE customer_cart 
            SET payment = :payment 
            WHERE id = :cart_id"""), 
            {"payment": cart_checkout.payment,"cart_id": cart_id})

    return {"total_potions_bought": instance_potions, "total_gold_paid": instance_gold}
