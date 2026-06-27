"""
Mock MCP Server for Salesforce Agentforce.

Scenario: "Where to buy" - find nearby and online retailers that stock a
consumer packaged good (Kraft Heinz demo catalog: Heinz, Kraft, Velveeta,
Oscar Mayer, Philadelphia, Jell-O, Cool Whip, Maxwell House, and more).

Transport: Streamable HTTP (required by the Agentforce MCP Registry).
Endpoint:  http://<host>:<port>/mcp   (default path is /mcp)

OUTPUT DESIGN (important for Agentforce):
Agentforce Builder maps MCP output schemas to Lightning types. Nested objects,
arrays of objects WITH properties, and nullable (any/or) types do NOT resolve,
and render as an EMPTY output on the action. So every tool here returns a flat,
top-level object of PRIMITIVE fields only (string / number / integer / boolean),
plus human-readable "*_list" / "summary" strings that carry the full detail for
the agent to read back. This keeps the Outputs panel populated and the values
usable in variables and conditions.

DATA QUALITY (why this version exists):
1. No silent wrong-product match. Unknown products return matched=False with a
   helpful list of what IS in the catalog, instead of defaulting to ketchup.
2. Addresses are internally consistent - a generated street tied to the searched
   postal code, not a hardcoded real street stapled to an arbitrary ZIP.
3. Prices are anchored to a per-SKU MSRP (bigger packs cost more, clubs are
   cheaper), with small deterministic per-retailer variation - not random noise.
4. Every size is a specific SKU (UPC + retailer item number + MSRP). Callers may
   pin a size to price a single SKU.

All tools return deterministic mock data so demos are repeatable.

Run:  python server.py
Then expose publicly (Render, or `ngrok http 8787`) and register
https://<public-host>/mcp in Setup > Agentforce Registry.

Optional bearer-token auth: set MCP_API_KEY to require
"Authorization: Bearer <key>" on every request. Unset = no auth.
"""

import hashlib
import logging
import os
from typing import Optional

from pydantic import BaseModel, Field

from mcp.server.fastmcp import FastMCP
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
HOST = os.environ.get("MCP_HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", os.environ.get("MCP_PORT", "8787")))
API_KEY = os.environ.get("MCP_API_KEY")  # optional; if unset, no auth

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-5s  %(message)s")
log = logging.getLogger("mock-mcp")

mcp = FastMCP(
    name="mock-wheretobuy-mcp",
    instructions=(
        "Mock 'where to buy' tools for testing Agentforce MCP registration. "
        "Find nearby stores and online retailers that carry Kraft Heinz grocery "
        "products (Heinz Ketchup, Kraft Mac & Cheese, Velveeta, Oscar Mayer, "
        "Philadelphia, Jell-O, Maxwell House, and more). If a product is not "
        "recognized the tools return matched=false with the list of known "
        "products - never guess a different product. All data is fake."
    ),
    host=HOST,
    port=PORT,
    stateless_http=True,
    json_response=True,
)


def _seed(*parts: str) -> int:
    raw = "|".join(p.strip().lower() for p in parts)
    return int(hashlib.sha256(raw.encode()).hexdigest(), 16)


def _norm(text: str) -> str:
    """Lowercase, expand '&'->'and', strip punctuation so 'A.1.'=='a1', 'Mac & Cheese' matches."""
    out = []
    for ch in text.lower():
        if ch == "&":
            out.append(" and ")
        elif ch.isalnum() or ch.isspace():
            out.append(ch)
        else:
            out.append(" ")
    return " ".join("".join(out).split())


# ---------------------------------------------------------------------------
# Output models - FLAT, primitive-only top-level fields (Lightning-resolvable)
# ---------------------------------------------------------------------------
class FindWhereToBuyOutput(BaseModel):
    matched: bool = Field(description="True if the product was recognized. If False, no store data is returned and the agent must NOT guess a different product.")
    requested_product: str = Field(description="The raw product text the customer asked for.")
    product: str = Field(description="Resolved product name that was searched, or 'Not found'.")
    brand: str = Field(description="Product brand, or 'Unknown'.")
    search_postal_code: str = Field(description="Postal/ZIP code used as the search center.")
    radius_miles: float = Field(description="Search radius in miles that was applied.")
    store_count: int = Field(description="Total nearby stores found.")
    in_stock_count: int = Field(description="How many of those stores currently have it in stock.")
    closest_in_stock_store: str = Field(description="Name of the closest store that has it in stock, or 'None nearby'.")
    closest_in_stock_distance_miles: float = Field(description="Distance to that closest in-stock store, in miles (0 if none).")
    closest_in_stock_price_usd: float = Field(description="Shelf price at that closest in-stock store, in USD (0 if none).")
    closest_in_stock_size: str = Field(description="Pack size stocked at that closest in-stock store.")
    closest_in_stock_upc: str = Field(description="UPC of the SKU stocked at that closest in-stock store.")
    closest_in_stock_sku: str = Field(description="Retailer item number (SKU) at that closest in-stock store.")
    store_list: str = Field(description="Human-readable list of all nearby stores with distance, stock, price, size, and SKU.")
    store_data_source: str = Field(description="Where store names/addresses came from: 'directory' (real hardcoded stores for a known metro ZIP), 'mock' (generated for an unknown ZIP), or 'none'.")
    summary: str = Field(description="One-line natural-language summary of the result.")


class CheckOnlineOutput(BaseModel):
    matched: bool = Field(description="True if the product was recognized. If False, no offer data is returned and the agent must NOT guess a different product.")
    requested_product: str = Field(description="The raw product text the customer asked for.")
    product: str = Field(description="Resolved product name that was searched, or 'Not found'.")
    brand: str = Field(description="Product brand, or 'Unknown'.")
    size: str = Field(description="Pack size being priced online.")
    upc: str = Field(description="UPC of the SKU being priced online.")
    sku: str = Field(description="Retailer item number (SKU) being priced online.")
    delivery_postal_code: str = Field(description="Delivery postal/ZIP code, or 'not provided'.")
    offer_count: int = Field(description="Number of online offers found.")
    lowest_price_retailer: str = Field(description="Online retailer with the lowest price.")
    lowest_price_usd: float = Field(description="The lowest price found, in USD (0 if none).")
    fastest_delivery_retailer: str = Field(description="Online retailer with the fastest delivery.")
    fastest_delivery_days: int = Field(description="Fastest estimated delivery time, in days (0 if none).")
    offer_list: str = Field(description="Human-readable list of all online offers with price and delivery time.")
    summary: str = Field(description="One-line natural-language summary of the result.")


class ProductDetailsOutput(BaseModel):
    matched: bool = Field(description="True if the product was recognized. If False, no catalog data is returned and the agent must NOT guess a different product.")
    requested_product: str = Field(description="The raw product text the customer asked for.")
    brand: str = Field(description="Product brand, or 'Unknown'.")
    name: str = Field(description="Full product name, or 'Not found'.")
    category: str = Field(description="Product category.")
    description: str = Field(description="Short marketing description of the product.")
    size_count: int = Field(description="Number of available sizes.")
    smallest_size: str = Field(description="The smallest available pack size.")
    largest_size: str = Field(description="The largest available pack size.")
    default_upc: str = Field(description="UPC of the most common (smallest) size.")
    default_sku: str = Field(description="Retailer item number (SKU) of the most common size.")
    sizes_list: str = Field(description="Human-readable list of all sizes with UPC, SKU, and MSRP.")
    summary: str = Field(description="One-line natural-language summary, or the 'not found' hint listing known products.")


# ---------------------------------------------------------------------------
# Mock reference data
# ---------------------------------------------------------------------------
# Physical retailers (name, kind). kind drives pricing/size behavior:
#   "grocery" | "mass" | "club" (clubs are cheaper and skew to the largest pack)
RETAILERS = [
    ("Walmart Supercenter", "mass"),
    ("Target", "mass"),
    ("Kroger", "grocery"),
    ("Safeway", "grocery"),
    ("Albertsons", "grocery"),
    ("Publix", "grocery"),
    ("H-E-B", "grocery"),
    ("Meijer", "mass"),
    ("Stop & Shop", "grocery"),
    ("Wegmans", "grocery"),
    ("Food Lion", "grocery"),
    ("Giant Eagle", "grocery"),
    ("Ralphs", "grocery"),
    ("Hy-Vee", "grocery"),
    ("ShopRite", "grocery"),
    ("Costco Wholesale", "club"),
    ("Sam's Club", "club"),
    ("BJ's Wholesale", "club"),
]

# Online retailers (name, ships_to_door). Some are pickup/local-delivery only.
ONLINE_RETAILERS = [
    ("Amazon.com", True),
    ("Walmart.com", True),
    ("Target.com", True),
    ("Instacart", True),
    ("Kroger Delivery", True),
    ("Amazon Fresh", True),
    ("FreshDirect", True),
    ("Shipt", True),
    ("Gopuff", True),
    ("Sam's Club Online", True),
    ("Costco.com", True),
    ("Boxed", True),
]

# Street pool for generating internally-consistent (but fake) store addresses.
STREET_POOL = [
    "Main St", "Market St", "Broadway", "Commerce Dr", "Retail Pkwy",
    "Grocery Ln", "Center Ave", "Maple Rd", "Oak St", "Washington Blvd",
    "Sunrise Hwy", "Lincoln Ave", "Riverside Dr", "Park Ave", "Union St",
]

# ---------------------------------------------------------------------------
# Product catalog.
# Each product:
#   brand, name, category, description
#   aliases : specific phrases used for matching (kept multi-word / specific so
#             bare words like "cheese" or "heinz" do NOT cross-match)
#   sizes   : list of SKUs - each has size, upc, sku (retailer item #), price (MSRP)
# ---------------------------------------------------------------------------
PRODUCTS = {
    # ---- Heinz condiments ------------------------------------------------
    "tomato ketchup": {
        "brand": "Heinz", "name": "Heinz Tomato Ketchup",
        "category": "Condiments / Ketchup",
        "description": "Classic tomato ketchup made from sun-ripened tomatoes.",
        "aliases": ["heinz tomato ketchup", "tomato ketchup", "heinz ketchup", "ketchup", "catsup"],
        "sizes": [
            {"size": "14 oz squeeze", "upc": "0 13000 00010 1", "sku": "HNZ-KET-14", "price": 3.49},
            {"size": "20 oz squeeze", "upc": "0 13000 00020 0", "sku": "HNZ-KET-20", "price": 3.99},
            {"size": "32 oz squeeze", "upc": "0 13000 00030 9", "sku": "HNZ-KET-32", "price": 4.99},
            {"size": "44 oz squeeze", "upc": "0 13000 00040 8", "sku": "HNZ-KET-44", "price": 5.99},
            {"size": "64 oz value", "upc": "0 13000 00060 6", "sku": "HNZ-KET-64", "price": 7.49},
        ],
    },
    "no sugar added ketchup": {
        "brand": "Heinz", "name": "Heinz Tomato Ketchup No Sugar Added",
        "category": "Condiments / Ketchup", "priority": 1,
        "description": "Same Heinz taste with no added sugar.",
        "aliases": ["no sugar added ketchup", "ketchup no sugar added", "no sugar ketchup",
                    "ketchup no sugar", "no sugar added", "no sugar", "sugar free ketchup", "heinz no sugar"],
        "sizes": [
            {"size": "13 oz squeeze", "upc": "0 13000 00110 8", "sku": "HNZ-NSA-13", "price": 4.29},
            {"size": "20 oz squeeze", "upc": "0 13000 00120 7", "sku": "HNZ-NSA-20", "price": 4.99},
        ],
    },
    "organic ketchup": {
        "brand": "Heinz", "name": "Heinz Organic Tomato Ketchup",
        "category": "Condiments / Ketchup", "priority": 1,
        "description": "Certified organic tomato ketchup.",
        "aliases": ["organic ketchup", "organic tomato ketchup", "heinz organic"],
        "sizes": [
            {"size": "14 oz squeeze", "upc": "0 13000 00210 5", "sku": "HNZ-ORG-14", "price": 4.49},
            {"size": "24 oz squeeze", "upc": "0 13000 00220 4", "sku": "HNZ-ORG-24", "price": 5.79},
        ],
    },
    "heinz mayonnaise": {
        "brand": "Heinz", "name": "Heinz Real Mayonnaise",
        "category": "Condiments / Mayonnaise",
        "description": "Creamy real mayonnaise made with cage-free eggs.",
        "aliases": ["heinz mayonnaise", "heinz mayo", "real mayonnaise", "mayonnaise", "mayo"],
        "sizes": [
            {"size": "15 oz squeeze", "upc": "0 13000 00710 7", "sku": "HNZ-MAYO-15", "price": 3.99},
            {"size": "30 oz jar", "upc": "0 13000 00720 6", "sku": "HNZ-MAYO-30", "price": 5.99},
        ],
    },
    "heinz bbq sauce": {
        "brand": "Heinz", "name": "Heinz Classic BBQ Sauce",
        "category": "Condiments / BBQ Sauce",
        "description": "Rich, smoky BBQ sauce made from Heinz Ketchup.",
        "aliases": ["heinz bbq sauce", "heinz barbecue sauce", "bbq sauce", "barbecue sauce"],
        "sizes": [
            {"size": "17.5 oz bottle", "upc": "0 13000 00810 4", "sku": "HNZ-BBQ-17", "price": 2.99},
            {"size": "21.5 oz bottle", "upc": "0 13000 00820 3", "sku": "HNZ-BBQ-21", "price": 3.49},
        ],
    },
    "heinz mustard": {
        "brand": "Heinz", "name": "Heinz Yellow Mustard",
        "category": "Condiments / Mustard",
        "description": "Smooth, tangy yellow mustard - a ballpark and backyard staple.",
        "aliases": ["heinz yellow mustard", "heinz mustard", "yellow mustard", "mustard"],
        "sizes": [
            {"size": "8 oz squeeze", "upc": "0 13000 00510 6", "sku": "HNZ-MUS-08", "price": 1.99},
            {"size": "14 oz squeeze", "upc": "0 13000 00520 5", "sku": "HNZ-MUS-14", "price": 2.49},
            {"size": "20 oz squeeze", "upc": "0 13000 00530 4", "sku": "HNZ-MUS-20", "price": 2.99},
        ],
    },
    "heinz 57 sauce": {
        "brand": "Heinz", "name": "Heinz 57 Sauce",
        "category": "Condiments / Steak Sauce",
        "description": "The iconic tangy Heinz 57 sauce for steak and more.",
        "aliases": ["heinz 57 sauce", "heinz 57", "57 sauce"],
        "sizes": [
            {"size": "10 oz bottle", "upc": "0 13000 00910 1", "sku": "HNZ-57-10", "price": 4.29},
            {"size": "15 oz bottle", "upc": "0 13000 00920 0", "sku": "HNZ-57-15", "price": 5.49},
        ],
    },
    "heinz sweet relish": {
        "brand": "Heinz", "name": "Heinz Sweet Relish",
        "category": "Condiments / Relish",
        "description": "Sweet pickle relish for hot dogs, burgers, and salads.",
        "aliases": ["heinz sweet relish", "sweet relish", "pickle relish", "relish"],
        "sizes": [
            {"size": "10 oz squeeze", "upc": "0 13000 01010 7", "sku": "HNZ-REL-10", "price": 2.79},
        ],
    },
    "grey poupon dijon": {
        "brand": "Grey Poupon", "name": "Grey Poupon Dijon Mustard",
        "category": "Condiments / Mustard",
        "description": "Smooth Dijon mustard made with white wine.",
        "aliases": ["grey poupon dijon", "grey poupon", "dijon mustard", "dijon"],
        "sizes": [
            {"size": "8 oz jar", "upc": "0 43000 95210 4", "sku": "GP-DIJ-08", "price": 3.29},
            {"size": "10 oz squeeze", "upc": "0 43000 95220 3", "sku": "GP-DIJ-10", "price": 3.79},
        ],
    },
    "a1 steak sauce": {
        "brand": "A.1.", "name": "A.1. Original Steak Sauce",
        "category": "Condiments / Steak Sauce",
        "description": "Bold, tangy original steak sauce since 1862.",
        "aliases": ["a1 original steak sauce", "a1 steak sauce", "a1 sauce", "a1",
                    "a 1 original steak sauce", "a 1 steak sauce", "a 1 sauce", "a 1", "steak sauce"],
        "sizes": [
            {"size": "10 oz bottle", "upc": "0 52100 01910 5", "sku": "A1-STK-10", "price": 4.49},
            {"size": "15 oz bottle", "upc": "0 52100 01920 4", "sku": "A1-STK-15", "price": 5.99},
        ],
    },
    "lea perrins worcestershire": {
        "brand": "Lea & Perrins", "name": "Lea & Perrins Worcestershire Sauce",
        "category": "Condiments / Worcestershire",
        "description": "The original Worcestershire sauce, aged 18 months.",
        "aliases": ["lea perrins worcestershire", "lea and perrins", "lea perrins", "worcestershire sauce", "worcestershire"],
        "sizes": [
            {"size": "10 oz bottle", "upc": "0 51600 00010 2", "sku": "LP-WOR-10", "price": 4.99},
            {"size": "15 oz bottle", "upc": "0 51600 00020 1", "sku": "LP-WOR-15", "price": 6.49},
        ],
    },

    # ---- Kraft -----------------------------------------------------------
    "mac and cheese": {
        "brand": "Kraft", "name": "Kraft Macaroni & Cheese Dinner",
        "category": "Meals / Pasta",
        "description": "The classic blue box mac & cheese - America's favorite since 1937.",
        "aliases": ["kraft macaroni and cheese", "kraft mac and cheese", "mac and cheese", "macaroni and cheese", "mac cheese", "blue box", "kraft dinner"],
        "sizes": [
            {"size": "7.25 oz box (single)", "upc": "0 21000 65419 4", "sku": "KFT-MAC-1", "price": 1.29},
            {"size": "14.5 oz box (2-pack)", "upc": "0 21000 65421 7", "sku": "KFT-MAC-2", "price": 2.29},
            {"size": "5-count multipack", "upc": "0 21000 01222 9", "sku": "KFT-MAC-5", "price": 5.49},
        ],
    },
    "mac and cheese shapes": {
        "brand": "Kraft", "name": "Kraft Macaroni & Cheese Dinner - SpongeBob Shapes",
        "category": "Meals / Pasta", "priority": 1,
        "description": "Fun SpongeBob-shaped pasta with classic Kraft cheese sauce.",
        "aliases": ["mac and cheese spongebob", "mac and cheese shapes", "spongebob shapes", "spongebob mac", "shapes mac and cheese"],
        "sizes": [
            {"size": "5.5 oz box", "upc": "0 21000 65431 6", "sku": "KFT-MACSB-1", "price": 1.49},
        ],
    },
    "kraft singles": {
        "brand": "Kraft", "name": "Kraft American Singles",
        "category": "Dairy / Cheese",
        "description": "Individually wrapped American cheese slices that melt perfectly.",
        "aliases": ["kraft american singles", "kraft singles", "american singles", "cheese singles", "american cheese slices"],
        "sizes": [
            {"size": "16 slices (12 oz)", "upc": "0 21000 60412 0", "sku": "KFT-SGL-16", "price": 3.49},
            {"size": "24 slices (18 oz)", "upc": "0 21000 60424 3", "sku": "KFT-SGL-24", "price": 4.79},
        ],
    },
    "kraft shredded cheddar": {
        "brand": "Kraft", "name": "Kraft Shredded Sharp Cheddar Cheese",
        "category": "Dairy / Cheese",
        "description": "Sharp cheddar, freshly shredded for melting and topping.",
        "aliases": ["kraft shredded sharp cheddar", "kraft shredded cheddar", "shredded cheddar", "shredded cheese", "kraft cheddar"],
        "sizes": [
            {"size": "8 oz bag", "upc": "0 21000 61300 9", "sku": "KFT-SHR-08", "price": 3.29},
            {"size": "16 oz bag", "upc": "0 21000 61316 0", "sku": "KFT-SHR-16", "price": 5.99},
        ],
    },
    "kraft ranch dressing": {
        "brand": "Kraft", "name": "Kraft Classic Ranch Dressing",
        "category": "Condiments / Salad Dressing",
        "description": "Cool, creamy classic ranch dressing and dip.",
        "aliases": ["kraft classic ranch dressing", "kraft ranch dressing", "kraft ranch", "ranch dressing", "ranch dip"],
        "sizes": [
            {"size": "16 oz bottle", "upc": "0 21000 64710 3", "sku": "KFT-RAN-16", "price": 3.49},
            {"size": "24 oz bottle", "upc": "0 21000 64724 0", "sku": "KFT-RAN-24", "price": 4.49},
        ],
    },
    "kraft zesty italian": {
        "brand": "Kraft", "name": "Kraft Zesty Italian Dressing",
        "category": "Condiments / Salad Dressing",
        "description": "Tangy, herby Italian dressing and marinade.",
        "aliases": ["kraft zesty italian dressing", "kraft zesty italian", "zesty italian", "italian dressing"],
        "sizes": [
            {"size": "16 oz bottle", "upc": "0 21000 64810 0", "sku": "KFT-ITL-16", "price": 3.29},
        ],
    },

    # ---- Velveeta --------------------------------------------------------
    "velveeta shells and cheese": {
        "brand": "Velveeta", "name": "Velveeta Shells & Cheese",
        "category": "Meals / Pasta",
        "description": "Creamy Velveeta liquid gold cheese sauce with pasta shells.",
        "aliases": ["velveeta shells and cheese", "velveeta shells", "shells and cheese", "velveeta pasta"],
        "sizes": [
            {"size": "12 oz box", "upc": "0 21000 97078 1", "sku": "VEL-SHL-12", "price": 2.49},
            {"size": "32 oz family size", "upc": "0 21000 97079 8", "sku": "VEL-SHL-32", "price": 5.49},
        ],
    },
    "velveeta block": {
        "brand": "Velveeta", "name": "Velveeta Original Cheese Block",
        "category": "Dairy / Cheese",
        "description": "The original melty cheese loaf - perfect for queso and dips.",
        "aliases": ["velveeta original cheese block", "velveeta block", "velveeta loaf", "velveeta cheese", "velveeta"],
        "sizes": [
            {"size": "16 oz block", "upc": "0 21000 65100 1", "sku": "VEL-BLK-16", "price": 5.49},
            {"size": "32 oz block", "upc": "0 21000 65132 2", "sku": "VEL-BLK-32", "price": 8.99},
        ],
    },

    # ---- Oscar Mayer -----------------------------------------------------
    "oscar mayer bologna": {
        "brand": "Oscar Mayer", "name": "Oscar Mayer Classic Bologna",
        "category": "Deli / Luncheon Meat",
        "description": "America's favorite bologna - made with quality pork, chicken, and beef.",
        "aliases": ["oscar mayer classic bologna", "oscar mayer bologna", "classic bologna", "bologna"],
        "sizes": [
            {"size": "12 oz pack", "upc": "0 44700 01234 5", "sku": "OM-BOL-12", "price": 3.49},
            {"size": "16 oz pack", "upc": "0 44700 01235 2", "sku": "OM-BOL-16", "price": 4.29},
        ],
    },
    "oscar mayer wieners": {
        "brand": "Oscar Mayer", "name": "Oscar Mayer Classic Wieners",
        "category": "Deli / Hot Dogs",
        "description": "Classic uncured wieners - the original Oscar Mayer hot dog.",
        "aliases": ["oscar mayer classic wieners", "oscar mayer wieners", "oscar mayer hot dogs", "oscar mayer franks", "wieners", "hot dogs", "franks"],
        "sizes": [
            {"size": "10 ct (16 oz)", "upc": "0 44700 02201 6", "sku": "OM-WNR-10", "price": 3.99},
            {"size": "Bun-Length 8 ct", "upc": "0 44700 02208 5", "sku": "OM-WNR-08", "price": 4.49},
        ],
    },
    "oscar mayer bacon": {
        "brand": "Oscar Mayer", "name": "Oscar Mayer Naturally Hardwood Smoked Bacon",
        "category": "Deli / Bacon",
        "description": "Naturally hardwood smoked bacon, thick and savory.",
        "aliases": ["oscar mayer naturally hardwood smoked bacon", "oscar mayer bacon", "hardwood smoked bacon", "bacon"],
        "sizes": [
            {"size": "16 oz pack", "upc": "0 44700 03101 8", "sku": "OM-BAC-16", "price": 6.49},
            {"size": "22 oz family pack", "upc": "0 44700 03122 3", "sku": "OM-BAC-22", "price": 8.99},
        ],
    },

    # ---- Other Kraft Heinz brands ---------------------------------------
    "philadelphia cream cheese": {
        "brand": "Philadelphia", "name": "Philadelphia Original Cream Cheese",
        "category": "Dairy / Cream Cheese",
        "description": "Rich, smooth cream cheese - perfect for spreading or baking.",
        "aliases": ["philadelphia original cream cheese", "philadelphia cream cheese", "philadelphia cheese", "philadelphia", "philly cream cheese", "cream cheese"],
        "sizes": [
            {"size": "8 oz block", "upc": "0 21000 40806 1", "sku": "PHIL-CC-08", "price": 2.99},
            {"size": "16 oz block", "upc": "0 21000 40807 8", "sku": "PHIL-CC-16", "price": 4.99},
            {"size": "12 oz tub (whipped)", "upc": "0 21000 40812 2", "sku": "PHIL-CC-12W", "price": 3.99},
        ],
    },
    "jell-o": {
        "brand": "Jell-O", "name": "Jell-O Strawberry Gelatin Dessert",
        "category": "Desserts / Gelatin",
        "description": "Jiggly, fruity fun - the classic Jell-O strawberry flavor.",
        "aliases": ["jell o strawberry gelatin", "jello strawberry", "jell o", "jello", "gelatin dessert", "gelatin"],
        "sizes": [
            {"size": "3 oz box", "upc": "0 43000 28460 2", "sku": "JLO-STR-03", "price": 1.19},
            {"size": "6 oz box (family size)", "upc": "0 43000 28461 9", "sku": "JLO-STR-06", "price": 1.99},
        ],
    },
    "cool whip": {
        "brand": "Cool Whip", "name": "Cool Whip Original Whipped Topping",
        "category": "Desserts / Whipped Topping",
        "description": "Light, fluffy whipped topping for pies, fruit, and more.",
        "aliases": ["cool whip original whipped topping", "cool whip", "whipped topping", "coolwhip"],
        "sizes": [
            {"size": "8 oz tub", "upc": "0 43000 24200 8", "sku": "CW-ORG-08", "price": 2.49},
            {"size": "16 oz tub", "upc": "0 43000 24216 9", "sku": "CW-ORG-16", "price": 3.99},
        ],
    },
    "maxwell house coffee": {
        "brand": "Maxwell House", "name": "Maxwell House Original Roast Ground Coffee",
        "category": "Beverages / Coffee",
        "description": "Good to the last drop - medium original roast ground coffee.",
        "aliases": ["maxwell house original roast", "maxwell house coffee", "maxwell house", "ground coffee", "coffee"],
        "sizes": [
            {"size": "30.6 oz canister", "upc": "0 43000 04000 3", "sku": "MH-ORG-30", "price": 9.99},
            {"size": "11.5 oz canister", "upc": "0 43000 04011 9", "sku": "MH-ORG-11", "price": 4.99},
        ],
    },
    "capri sun": {
        "brand": "Capri Sun", "name": "Capri Sun Fruit Punch Juice Drink",
        "category": "Beverages / Juice Pouches",
        "description": "Refreshing fruit punch juice drink in the classic foil pouch.",
        "aliases": ["capri sun fruit punch", "capri sun", "caprisun", "juice pouches"],
        "sizes": [
            {"size": "10-pouch box", "upc": "0 87684 00100 4", "sku": "CS-FP-10", "price": 3.49},
            {"size": "40-pouch club box", "upc": "0 87684 00140 0", "sku": "CS-FP-40", "price": 11.49},
        ],
    },
    "kool-aid": {
        "brand": "Kool-Aid", "name": "Kool-Aid Cherry Drink Mix",
        "category": "Beverages / Drink Mix",
        "description": "Oh yeah! Classic cherry powdered drink mix.",
        "aliases": ["kool aid cherry drink mix", "kool aid cherry", "kool aid", "koolaid", "drink mix"],
        "sizes": [
            {"size": "0.13 oz packet", "upc": "0 43000 95510 5", "sku": "KA-CHR-01", "price": 0.25},
            {"size": "19 oz tub (makes 8 qt)", "upc": "0 43000 95519 8", "sku": "KA-CHR-19", "price": 4.49},
        ],
    },
    "lunchables": {
        "brand": "Lunchables", "name": "Lunchables Turkey & Cheddar Cracker Stackers",
        "category": "Meals / Lunch Kits",
        "description": "Build-your-own turkey, cheddar, and cracker stackers.",
        "aliases": ["lunchables turkey and cheddar", "lunchables turkey cheddar", "lunchables", "cracker stackers", "lunch kit"],
        "sizes": [
            {"size": "3.4 oz single tray", "upc": "0 44700 04400 1", "sku": "LUN-TC-1", "price": 2.49},
            {"size": "8-tray club pack", "upc": "0 44700 04408 7", "sku": "LUN-TC-8", "price": 14.99},
        ],
    },
    "ore-ida tater tots": {
        "brand": "Ore-Ida", "name": "Ore-Ida Golden Tater Tots",
        "category": "Frozen / Potatoes",
        "description": "Crispy on the outside, fluffy on the inside golden tater tots.",
        "aliases": ["ore ida golden tater tots", "ore ida tater tots", "ore ida", "tater tots", "tots"],
        "sizes": [
            {"size": "32 oz bag", "upc": "0 13120 00890 2", "sku": "OI-TOT-32", "price": 4.49},
            {"size": "5 lb bag", "upc": "0 13120 00905 3", "sku": "OI-TOT-80", "price": 7.99},
        ],
    },
    "classico pasta sauce": {
        "brand": "Classico", "name": "Classico Tomato & Basil Pasta Sauce",
        "category": "Pantry / Pasta Sauce",
        "description": "Vine-ripened tomatoes and sweet basil in a traditional sauce.",
        "aliases": ["classico tomato and basil pasta sauce", "classico pasta sauce", "classico tomato basil", "classico", "pasta sauce", "marinara"],
        "sizes": [
            {"size": "24 oz jar", "upc": "0 41129 00255 7", "sku": "CLS-TB-24", "price": 3.29},
            {"size": "44 oz jar", "upc": "0 41129 00244 1", "sku": "CLS-TB-44", "price": 4.99},
        ],
    },
}


# ---------------------------------------------------------------------------
# Resolution: scored alias match, no silent fallback.
# ---------------------------------------------------------------------------
def _resolve_product(product_name: str) -> Optional[dict]:
    """Return the catalog entry whose most-specific alias appears in the query.

    Scoring uses the length of the longest matched alias, so
    'no sugar added ketchup' beats the generic 'ketchup', and
    'velveeta shells and cheese' beats 'velveeta'. Returns None when nothing
    matches - callers must surface matched=False rather than guessing.
    """
    q = _norm(product_name)
    if not q:
        return None
    best_key, best_score = None, (-1, 0)
    for key, p in PRODUCTS.items():
        prio = p.get("priority", 0)
        for alias in p["aliases"]:
            a = _norm(alias)
            if a and a in q:
                score = (prio, len(a))
                if score > best_score:
                    best_key, best_score = key, score
    return PRODUCTS[best_key] if best_key else None


def _resolve_size(product: dict, size_hint: str) -> Optional[dict]:
    """Pick a specific SKU from a loose size string ('44', 'family', 'sku HNZ-KET-44')."""
    if not size_hint:
        return None
    h = _norm(size_hint)
    for s in product["sizes"]:
        if _norm(s["sku"]) == h or _norm(s["upc"]) == h:
            return s
    for s in product["sizes"]:
        if h in _norm(s["size"]) or h in _norm(s["sku"]):
            return s
    # token overlap fallback (e.g. "44" -> "44 oz squeeze")
    toks = set(h.split())
    for s in product["sizes"]:
        if toks & set(_norm(s["size"]).split()):
            return s
    return None


def _known_products_hint() -> str:
    """Compact, grouped list of catalog products for 'not found' responses."""
    by_brand: dict = {}
    for p in PRODUCTS.values():
        by_brand.setdefault(p["brand"], []).append(p["name"])
    parts = [f"{brand}: {', '.join(names)}" for brand, names in by_brand.items()]
    return " | ".join(parts)


def _fake_address(retailer: str, postal_code: str) -> str:
    """Deterministic, internally-consistent fake street tied to the searched ZIP."""
    s = _seed(retailer, postal_code, "addr")
    number = 100 + (s % 9900)
    street = STREET_POOL[s % len(STREET_POOL)]
    zip_clean = postal_code.strip() or "00000"
    return f"{number} {street}, {zip_clean}"


def _price_for(size: dict, retailer: str, kind: str, postal_code: str) -> float:
    """MSRP-anchored price with small deterministic per-retailer variation."""
    base = float(size.get("price", 3.99))
    s = _seed(size["sku"], retailer, postal_code)
    jitter = ((s % 121) - 40) / 100.0  # -0.40 .. +0.80
    club_factor = 0.88 if kind == "club" else (0.97 if kind == "mass" else 1.0)
    price = round(base * club_factor + jitter, 2)
    return max(price, 0.49)


# ---------------------------------------------------------------------------
# Store sourcing: REAL hardcoded stores for known metro ZIPs, else deterministic mock.
# Either way returns a list of rows shaped:
#   {retailer, address, distance_miles, kind, store_id}
# Stock / price / SKU are layered on top by the tool (seeded by store_id), so
# they stay stable per store regardless of source.
# ---------------------------------------------------------------------------
_CLUB = ("costco", "sam's club", "sams club", "bj's", "bj’s", "wholesale club")
_MASS = ("walmart", "target", "meijer", "super target", "supercenter")


def _classify_kind(name: str) -> str:
    n = name.lower()
    if any(k in n for k in _CLUB):
        return "club"
    if any(k in n for k in _MASS):
        return "mass"
    return "grocery"


# ---------------------------------------------------------------------------
# REAL store directory - actual, verified store locations for several demo
# metros. A search whose ZIP is in one of these metros returns these real
# names + real street addresses (source='directory'). Any other ZIP falls back
# to the deterministic generated stores (source='mock') so the server still
# works everywhere. Distances are approximate from each metro's downtown core.
#
# To add a metro: add an entry with its ZIPs and real stores. To verify an
# address before adding, check the retailer's own store locator.
# ---------------------------------------------------------------------------
STORE_DIRECTORY = {
    "Chicago, IL (South Loop / Loop)": {
        "zips": {"60601", "60602", "60603", "60604", "60605", "60607", "60616"},
        "stores": [
            {"retailer": "Jewel-Osco", "address": "1224 S Wabash Ave, Chicago, IL 60605", "distance_miles": 0.6},
            {"retailer": "Trader Joe's", "address": "1147 S Wabash Ave, Chicago, IL 60605", "distance_miles": 0.7},
            {"retailer": "Target", "address": "1 S State St, Chicago, IL 60603", "distance_miles": 1.0},
            {"retailer": "Whole Foods Market", "address": "1101 S Canal St, Chicago, IL 60607", "distance_miles": 1.3},
            {"retailer": "Mariano's", "address": "1615 S Clark St, Chicago, IL 60616", "distance_miles": 1.6},
        ],
    },
    "New York, NY (Chelsea / Midtown)": {
        "zips": {"10001", "10010", "10011", "10018", "10120"},
        "stores": [
            {"retailer": "Whole Foods Market", "address": "250 7th Ave, New York, NY 10001", "distance_miles": 0.3},
            {"retailer": "Trader Joe's", "address": "675 6th Ave, New York, NY 10010", "distance_miles": 0.7},
            {"retailer": "Target", "address": "112 W 34th St, New York, NY 10120", "distance_miles": 0.9},
        ],
    },
    "Los Angeles, CA (Downtown)": {
        "zips": {"90013", "90014", "90015", "90017", "90071"},
        "stores": [
            {"retailer": "Ralphs", "address": "645 W 9th St, Los Angeles, CA 90015", "distance_miles": 0.4},
            {"retailer": "Whole Foods Market", "address": "788 S Grand Ave, Los Angeles, CA 90017", "distance_miles": 0.6},
            {"retailer": "Target", "address": "735 S Figueroa St, Los Angeles, CA 90017", "distance_miles": 0.8},
            {"retailer": "Smart & Final", "address": "845 S Figueroa St, Los Angeles, CA 90017", "distance_miles": 0.9},
        ],
    },
}

# Flatten: ZIP -> (metro_label, [stores]) for O(1) lookup at request time.
_DIR_BY_ZIP = {}
for _label, _entry in STORE_DIRECTORY.items():
    for _zip in _entry["zips"]:
        _DIR_BY_ZIP[_zip] = (_label, _entry["stores"])


def _directory_stores(postal_code: str, radius_miles: float):
    """Real hardcoded stores for a known metro ZIP, within radius. None if ZIP unknown."""
    hit = _DIR_BY_ZIP.get(postal_code.strip())
    if not hit:
        return None
    _label, stores = hit
    rows = [
        {"retailer": s["retailer"], "address": s["address"],
         "distance_miles": s["distance_miles"], "kind": _classify_kind(s["retailer"]),
         "store_id": s["address"]}
        for s in stores if s["distance_miles"] <= radius_miles
    ]
    rows.sort(key=lambda r: r["distance_miles"])
    return rows  # may be [] if radius is smaller than the nearest store


def _mock_stores_near(product_name: str, postal_code: str, radius_miles: float):
    """Deterministic generated stores (used only for ZIPs not in the directory)."""
    s = _seed(product_name, postal_code, str(radius_miles))
    count = 3 + (s % 4)
    ranked = sorted(
        range(len(RETAILERS)),
        key=lambda idx: _seed(product_name, postal_code, RETAILERS[idx][0]),
    )
    rows = []
    for idx in ranked[: min(count, len(RETAILERS))]:
        retailer, kind = RETAILERS[idx]
        rs = _seed(product_name, postal_code, retailer)
        distance = round(0.4 + (rs % int(max(radius_miles, 1) * 10)) / 10.0, 1)
        if distance > radius_miles:
            distance = round(max(radius_miles - (rs % 3) - 0.3, 0.3), 1)
        rows.append({
            "retailer": retailer, "address": _fake_address(retailer, postal_code),
            "distance_miles": distance, "kind": kind, "store_id": retailer,
        })
    rows.sort(key=lambda r: r["distance_miles"])
    return rows


def _get_stores(product_name: str, postal_code: str, radius_miles: float):
    """Return (store_rows, source) - real directory stores for known metro ZIPs, else mock."""
    rows = _directory_stores(postal_code, radius_miles)
    if rows is not None:
        return rows, "directory"
    return _mock_stores_near(product_name, postal_code, radius_miles), "mock"


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------
@mcp.tool()
def find_where_to_buy(
    product_name: str, postal_code: str, radius_miles: float = 10.0, size: str = ""
) -> FindWhereToBuyOutput:
    """Find nearby physical stores that currently stock a grocery product.

    Use this when a customer asks where they can buy a product near them, or
    which local stores have it in stock. Returns the closest in-stock store and
    a readable list of all nearby stores with distance, stock, price, size, and
    SKU. For supported metro ZIP codes the store names and addresses are REAL
    (store_data_source='directory'); other ZIPs return generated stores
    (store_data_source='mock'). Stock and price are always deterministic mock.
    If the product is not in the catalog, returns matched=false with the list of
    known products - do NOT answer about a different product.

    Args:
        product_name: The product to look for (e.g. "Heinz Tomato Ketchup", "Kraft Mac & Cheese", "Velveeta Block").
        postal_code: The customer's ZIP code, used as the search center.
        radius_miles: Maximum search radius in miles (default 10).
        size: Optional pack size or SKU to pin (e.g. "44 oz", "HNZ-KET-44"); otherwise each store picks what it stocks.
    """
    product = _resolve_product(product_name)
    if product is None:
        return FindWhereToBuyOutput(
            matched=False, requested_product=product_name, product="Not found",
            brand="Unknown", search_postal_code=postal_code, radius_miles=radius_miles,
            store_count=0, in_stock_count=0, closest_in_stock_store="None nearby",
            closest_in_stock_distance_miles=0.0, closest_in_stock_price_usd=0.0,
            closest_in_stock_size="", closest_in_stock_upc="", closest_in_stock_sku="",
            store_list="", store_data_source="none",
            summary=(f"'{product_name}' is not in the catalog, so no store data was returned. "
                     f"Known products - {_known_products_hint()}"),
        )

    pinned = _resolve_size(product, size)
    store_rows, source = _get_stores(product["name"], postal_code, radius_miles)

    # Layer deterministic mock stock / price / SKU onto whatever stores we got.
    rows = []
    for st in store_rows:
        rs = _seed(product["name"], st["store_id"], postal_code)
        in_stock = (rs % 6) != 0
        if pinned is not None:
            sku = pinned
        elif st["kind"] == "club":
            sku = product["sizes"][-1]  # clubs skew to the largest pack
        else:
            sku = product["sizes"][rs % len(product["sizes"])]
        price = _price_for(sku, st["store_id"], st["kind"], postal_code)
        rows.append({"retailer": st["retailer"], "address": st["address"],
                     "distance_miles": st["distance_miles"], "in_stock": in_stock,
                     "price": price, "size": sku["size"], "upc": sku["upc"], "sku": sku["sku"]})
    rows.sort(key=lambda r: r["distance_miles"])

    lines = []
    for r in rows:
        if r["in_stock"]:
            lines.append(f"{r['retailer']} - {r['address']} - {r['distance_miles']} mi - "
                         f"in stock - ${r['price']:.2f} ({r['size']}, SKU {r['sku']})")
        else:
            lines.append(f"{r['retailer']} - {r['address']} - {r['distance_miles']} mi - out of stock")
    store_list = "\n".join(lines)

    in_stock_rows = [r for r in rows if r["in_stock"]]
    if in_stock_rows:
        c = in_stock_rows[0]
        summary = (f"{len(in_stock_rows)} of {len(rows)} nearby stores have "
                   f"{product['name']} in stock. Closest is {c['retailer']} "
                   f"({c['distance_miles']} mi) at ${c['price']:.2f} for the {c['size']}.")
        return FindWhereToBuyOutput(
            matched=True, requested_product=product_name,
            product=product["name"], brand=product["brand"],
            search_postal_code=postal_code, radius_miles=radius_miles,
            store_count=len(rows), in_stock_count=len(in_stock_rows),
            closest_in_stock_store=c["retailer"],
            closest_in_stock_distance_miles=c["distance_miles"],
            closest_in_stock_price_usd=c["price"],
            closest_in_stock_size=c["size"], closest_in_stock_upc=c["upc"],
            closest_in_stock_sku=c["sku"],
            store_list=store_list, store_data_source=source, summary=summary,
        )

    return FindWhereToBuyOutput(
        matched=True, requested_product=product_name,
        product=product["name"], brand=product["brand"],
        search_postal_code=postal_code, radius_miles=radius_miles,
        store_count=len(rows), in_stock_count=0,
        closest_in_stock_store="None nearby",
        closest_in_stock_distance_miles=0.0, closest_in_stock_price_usd=0.0,
        closest_in_stock_size="", closest_in_stock_upc="", closest_in_stock_sku="",
        store_list=store_list, store_data_source=source,
        summary=f"No nearby store within {radius_miles} miles currently has {product['name']} in stock.",
    )


@mcp.tool()
def check_online_availability(
    product_name: str, postal_code: str = "", size: str = ""
) -> CheckOnlineOutput:
    """Check which online retailers sell a product and can ship or deliver it.

    Use this when a customer would rather buy online, asks about delivery, or
    when no nearby store has the item. Returns the lowest-price and fastest
    options plus a readable list of all online offers. If the product is not in
    the catalog, returns matched=false with the list of known products.

    Args:
        product_name: The product to look for (e.g. "Heinz Tomato Ketchup", "Kraft Mac & Cheese").
        postal_code: Optional delivery ZIP code to confirm delivery.
        size: Optional pack size or SKU to price (e.g. "20 oz", "HNZ-KET-20"); defaults to the most common size.
    """
    product = _resolve_product(product_name)
    if product is None:
        return CheckOnlineOutput(
            matched=False, requested_product=product_name, product="Not found",
            brand="Unknown", size="", upc="", sku="",
            delivery_postal_code=postal_code or "not provided", offer_count=0,
            lowest_price_retailer="None", lowest_price_usd=0.0,
            fastest_delivery_retailer="None", fastest_delivery_days=0, offer_list="",
            summary=(f"'{product_name}' is not in the catalog, so no offers were returned. "
                     f"Known products - {_known_products_hint()}"),
        )

    sku = _resolve_size(product, size) or product["sizes"][0]
    offers = []
    for name, _ships in ONLINE_RETAILERS:
        rs = _seed(product["name"], name, postal_code, sku["sku"])
        if (rs % 7) == 0:
            continue
        base = float(sku.get("price", 3.99))
        price = max(round(base * 1.05 + ((rs % 161) - 50) / 100.0, 2), 0.49)
        offers.append({"retailer": name, "price": price,
                       "days": 1 + (rs % 5), "pickup": (rs % 2) == 0})

    if offers:
        by_price = sorted(offers, key=lambda o: o["price"])
        by_speed = sorted(offers, key=lambda o: o["days"])
        cheapest, fastest = by_price[0], by_speed[0]
        lines = [f"{o['retailer']} - ${o['price']:.2f} - delivers in {o['days']} day(s)"
                 f"{' - pickup available' if o['pickup'] else ''}" for o in by_price]
        offer_list = "\n".join(lines)
        summary = (f"{len(offers)} online retailers carry {product['name']} ({sku['size']}). "
                   f"Cheapest is {cheapest['retailer']} at ${cheapest['price']:.2f}; "
                   f"fastest is {fastest['retailer']} in {fastest['days']} day(s).")
        return CheckOnlineOutput(
            matched=True, requested_product=product_name,
            product=product["name"], brand=product["brand"],
            size=sku["size"], upc=sku["upc"], sku=sku["sku"],
            delivery_postal_code=postal_code or "not provided",
            offer_count=len(offers),
            lowest_price_retailer=cheapest["retailer"], lowest_price_usd=cheapest["price"],
            fastest_delivery_retailer=fastest["retailer"], fastest_delivery_days=fastest["days"],
            offer_list=offer_list, summary=summary,
        )

    return CheckOnlineOutput(
        matched=True, requested_product=product_name,
        product=product["name"], brand=product["brand"],
        size=sku["size"], upc=sku["upc"], sku=sku["sku"],
        delivery_postal_code=postal_code or "not provided", offer_count=0,
        lowest_price_retailer="None", lowest_price_usd=0.0,
        fastest_delivery_retailer="None", fastest_delivery_days=0, offer_list="",
        summary=f"No online retailer currently lists {product['name']}.",
    )


@mcp.tool()
def get_product_details(product_name: str) -> ProductDetailsOutput:
    """Return catalog details for a product: brand, sizes, UPCs, SKUs, and prices.

    Use this to confirm exactly which product or pack size a customer means
    before searching, or when they ask what variants or sizes exist. If the
    product is not in the catalog, returns matched=false with the list of known
    products - do NOT answer about a different product.

    Args:
        product_name: The product to look up (e.g. "Heinz Tomato Ketchup",
            "Heinz Organic Ketchup", "Heinz Mayonnaise", "Kraft Mac & Cheese",
            "Kraft Singles", "Velveeta Shells & Cheese", "Velveeta Block",
            "Oscar Mayer Bologna", "Oscar Mayer Bacon", "Philadelphia Cream Cheese",
            "Maxwell House Coffee", "Capri Sun", "Lunchables").
    """
    product = _resolve_product(product_name)
    if product is None:
        return ProductDetailsOutput(
            matched=False, requested_product=product_name, brand="Unknown",
            name="Not found", category="", description="", size_count=0,
            smallest_size="", largest_size="", default_upc="", default_sku="",
            sizes_list="",
            summary=(f"'{product_name}' is not in the catalog. "
                     f"Known products - {_known_products_hint()}"),
        )

    sizes = product["sizes"]
    sizes_list = "\n".join(
        f"{s['size']} - UPC {s['upc']} - SKU {s['sku']} - MSRP ${float(s['price']):.2f}"
        for s in sizes
    )
    return ProductDetailsOutput(
        matched=True, requested_product=product_name,
        brand=product["brand"], name=product["name"],
        category=product["category"], description=product["description"],
        size_count=len(sizes),
        smallest_size=sizes[0]["size"], largest_size=sizes[-1]["size"],
        default_upc=sizes[0]["upc"], default_sku=sizes[0]["sku"],
        sizes_list=sizes_list,
        summary=(f"{product['name']} ({product['brand']}) - {len(sizes)} size(s), "
                 f"from {sizes[0]['size']} to {sizes[-1]['size']}."),
    )


# ---------------------------------------------------------------------------
# Optional bearer auth + /health
# ---------------------------------------------------------------------------
class BearerAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/health":
            return await call_next(request)
        if API_KEY:
            if request.headers.get("authorization", "") != f"Bearer {API_KEY}":
                log.warning("401 rejected request to %s", request.url.path)
                return JSONResponse({"error": "unauthorized"}, status_code=401)
        return await call_next(request)


async def health(_request):
    return PlainTextResponse("ok")


app = mcp.streamable_http_app()
app.add_middleware(BearerAuthMiddleware)
app.add_route("/health", health, methods=["GET"])


if __name__ == "__main__":
    import uvicorn
    log.info("Mock MCP server starting")
    log.info("  Products     : %d  |  Stores: %d  |  Online: %d",
             len(PRODUCTS), len(RETAILERS), len(ONLINE_RETAILERS))
    log.info("  MCP endpoint : http://%s:%s/mcp", HOST, PORT)
    log.info("  Health check : http://%s:%s/health", HOST, PORT)
    log.info("  Auth         : %s", "Bearer token required" if API_KEY else "none (open)")
    log.info("  Real metros  : %s", " | ".join(STORE_DIRECTORY.keys()))
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")
