from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
from enum import Enum
import sqlalchemy
from src import database as db

car_id = 0
car_dict = {}


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

    global car_id
    car_id += 1

    car_dict[car_id] = {}

    return {"cart_id": car_id}


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """

    cart_in_instance = car_dict[car_id]
    cart_in_instance[item_sku] = cart_item.quantity

    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    cart_in_instance = car_dict[car_id]
    cart_plan = []

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_red_potions, num_green_potions, num_blue_potions, gold FROM global_inventory")).fetchone()

        track_red_potions = result.num_red_potions
        track_green_potions = result.num_green_potions
        track_blue_potions = result.num_blue_potions
        instance_gold = result.gold

        for sku, quantity in cart_in_instance.shop():
            
            if "red" in sku.lower():
                if result.num_red_potions >= quantity:
                    track_red_potions -= quantity
                    instance_gold += 50

            if "green" in sku.lower():
                if result.num_red_potions >= quantity:
                    track_green_potions -= quantity
                    instance_gold += 50

            if "blue" in sku.lower():
                if result.num_red_potions >= quantity:
                    track_blue_potions -= quantity        
                    instance_gold += 50


        
    connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = gold + {instance_gold}, num_red_potions = num_red_potions - {track_red_potions}, num_green_potions = num_green_potions - {track_green_potions}, num_blue_potions = num_blue_potions - {track_blue_potions}"))

    return {"total_potions_bought": quantity, "total_gold_paid": instance_gold}
