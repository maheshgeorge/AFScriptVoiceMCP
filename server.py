"""
Mock MCP Server for Salesforce Agentforce.

Scenario: "Where to buy" — find nearby and online retailers that stock a
consumer packaged good (demo products: Heinz Ketchup, Kraft Mac & Cheese, and more).

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
        "Find nearby stores and online retailers that carry Kraft Heinz grocery products "
        "(e.g. Heinz Ketchup, Kraft Mac & Cheese). All data is fake."
    ),
    host=HOST,
    port=PORT,
    stateless_http=True,
    json_response=True,
)


def _seed(*parts: str) -> int:
    raw = "|".join(p.strip().lower() for p in parts)
    return int(hashlib.sha256(raw.encode()).hexdigest(), 16)


# ---------------------------------------------------------------------------
# Output models — FLAT, primitive-only top-level fields (Lightning-resolvable)
# ---------------------------------------------------------------------------
class FindWhereToBuyOutput(BaseModel):
    product: str = Field(description="Resolved product name that was searched.")
    brand: str = Field(description="Product brand.")
    search_postal_code: str = Field(description="Postal/ZIP code used as the search center.")
    radius_miles: float = Field(description="Search radius in miles that was applied.")
    store_count: int = Field(description="Total nearby stores found.")
    in_stock_count: int = Field(description="How many of those stores currently have it in stock.")
    closest_in_stock_store: str = Field(description="Name of the closest store that has it in stock, or 'None nearby'.")
    closest_in_stock_distance_miles: float = Field(description="Distance to that closest in-stock store, in miles (0 if none).")
    closest_in_stock_price_usd: float = Field(description="Shelf price at that closest in-stock store, in USD (0 if none).")
    store_list: str = Field(description="Human-readable list of all nearby stores with distance, stock, price, and size.")
    summary: str = Field(description="One-line natural-language summary of the result.")


class CheckOnlineOutput(BaseModel):
    product: str = Field(description="Resolved product name that was searched.")
    brand: str = Field(description="Product brand.")
    delivery_postal_code: str = Field(description="Delivery postal/ZIP code, or 'not provided'.")
    offer_count: int = Field(description="Number of online offers found.")
    lowest_price_retailer: str = Field(description="Online retailer with the lowest price.")
    lowest_price_usd: float = Field(description="The lowest price found, in USD (0 if none).")
    fastest_delivery_retailer: str = Field(description="Online retailer with the fastest delivery.")
    fastest_delivery_days: int = Field(description="Fastest estimated delivery time, in days (0 if none).")
    offer_list: str = Field(description="Human-readable list of all online offers with price and delivery time.")
    summary: str = Field(description="One-line natural-language summary of the result.")


class ProductDetailsOutput(BaseModel):
    brand: str = Field(description="Product brand.")
    name: str = Field(description="Full product name.")
    category: str = Field(description="Product category.")
    description: str = Field(description="Short marketing description of the product.")
    size_count: int = Field(description="Number of available sizes.")
    smallest_size: str = Field(description="The smallest available pack size.")
    largest_size: str = Field(description="The largest available pack size.")
    sizes_list: str = Field(description="Human-readable list of all sizes with their UPCs.")


# ---------------------------------------------------------------------------
# Mock reference data
# ---------------------------------------------------------------------------
RETAILERS = [
    ("Walmart Supercenter", "2100 N Elston Ave"),
    ("Target", "2656 N Elston Ave"),
    ("Kroger", "3100 Richmond Rd"),
    ("Safeway", "1450 Columbia Pike"),
    ("Costco Wholesale", "2200 4th Ave S"),
    ("Whole Foods Market", "945 Bryant St"),
    ("Publix", "3400 Peachtree Rd NE"),
    ("HEB", "6900 Ranch Rd 620 N"),
    ("Meijer", "3825 Washtenaw Ave"),
    ("Stop & Shop", "318 Washington St"),
]

ONLINE_RETAILERS = [
    ("Amazon.com", True),
    ("Walmart.com", True),
    ("Instacart", True),
    ("Target.com", True),
    ("Kroger Delivery", True),
    ("FreshDirect", True),
    ("Shipt", True),
]

PRODUCTS = {
    "tomato ketchup": {
        "brand": "Heinz", "name": "Heinz Tomato Ketchup",
        "category": "Condiments / Ketchup",
        "description": "Classic tomato ketchup made from sun-ripened tomatoes.",
        "sizes": [
            {"size": "14 oz squeeze", "upc": "0 13000 00010 1"},
            {"size": "20 oz squeeze", "upc": "0 13000 00020 0"},
            {"size": "32 oz squeeze", "upc": "0 13000 00030 9"},
            {"size": "44 oz squeeze", "upc": "0 13000 00040 8"},
        ],
    },
    "no sugar added ketchup": {
        "brand": "Heinz", "name": "Heinz Tomato Ketchup No Sugar Added",
        "category": "Condiments / Ketchup",
        "description": "Same Heinz taste with no added sugar.",
        "sizes": [
            {"size": "13 oz squeeze", "upc": "0 13000 00110 8"},
            {"size": "20 oz squeeze", "upc": "0 13000 00120 7"},
        ],
    },
    "organic ketchup": {
        "brand": "Heinz", "name": "Heinz Organic Tomato Ketchup",
        "category": "Condiments / Ketchup",
        "description": "Certified organic tomato ketchup.",
        "sizes": [
            {"size": "14 oz squeeze", "upc": "0 13000 00210 5"},
            {"size": "24 oz squeeze", "upc": "0 13000 00220 4"},
        ],
    },
    "mac and cheese": {
        "brand": "Kraft", "name": "Kraft Macaroni & Cheese Dinner",
        "category": "Meals / Pasta",
        "description": "The classic blue box mac & cheese — America's favorite since 1937.",
        "sizes": [
            {"size": "7.25 oz box (single)", "upc": "0 21000 65419 4"},
            {"size": "14.5 oz box (2-pack)", "upc": "0 21000 65421 7"},
            {"size": "5-count multipack", "upc": "0 21000 01222 9"},
        ],
    },
    "mac and cheese shapes": {
        "brand": "Kraft", "name": "Kraft Macaroni & Cheese Dinner — SpongeBob Shapes",
        "category": "Meals / Pasta",
        "description": "Fun SpongeBob-shaped pasta with classic Kraft cheese sauce.",
        "sizes": [
            {"size": "5.5 oz box", "upc": "0 21000 65431 6"},
        ],
    },
    "velveeta shells and cheese": {
        "brand": "Velveeta", "name": "Velveeta Shells & Cheese",
        "category": "Meals / Pasta",
        "description": "Creamy Velveeta liquid gold cheese sauce with pasta shells.",
        "sizes": [
            {"size": "12 oz box", "upc": "0 21000 97078 1"},
            {"size": "32 oz family size", "upc": "0 21000 97079 8"},
        ],
    },
    "heinz bbq sauce": {
        "brand": "Heinz", "name": "Heinz Classic BBQ Sauce",
        "category": "Condiments / BBQ Sauce",
        "description": "Rich, smoky BBQ sauce made from Heinz Ketchup.",
        "sizes": [
            {"size": "17.5 oz bottle", "upc": "0 13000 00810 4"},
            {"size": "21.5 oz bottle", "upc": "0 13000 00820 3"},
        ],
    },
    "heinz mustard": {
        "brand": "Heinz", "name": "Heinz Yellow Mustard",
        "category": "Condiments / Mustard",
        "description": "Smooth, tangy yellow mustard — a ballpark and backyard staple.",
        "sizes": [
            {"size": "8 oz squeeze", "upc": "0 13000 00510 6"},
            {"size": "14 oz squeeze", "upc": "0 13000 00520 5"},
            {"size": "20 oz squeeze", "upc": "0 13000 00530 4"},
        ],
    },
    "oscar mayer bologna": {
        "brand": "Oscar Mayer", "name": "Oscar Mayer Classic Bologna",
        "category": "Deli / Luncheon Meat",
        "description": "America's favorite bologna — made with quality pork, chicken, and beef.",
        "sizes": [
            {"size": "12 oz pack", "upc": "0 44700 01234 5"},
            {"size": "16 oz pack", "upc": "0 44700 01235 2"},
        ],
    },
    "jell-o": {
        "brand": "Jell-O", "name": "Jell-O Strawberry Gelatin Dessert",
        "category": "Desserts / Gelatin",
        "description": "Jiggly, fruity fun — the classic Jell-O strawberry flavor.",
        "sizes": [
            {"size": "3 oz box", "upc": "0 43000 28460 2"},
            {"size": "6 oz box (family size)", "upc": "0 43000 28461 9"},
        ],
    },
    "philadelphia cream cheese": {
        "brand": "Philadelphia", "name": "Philadelphia Original Cream Cheese",
        "category": "Dairy / Cream Cheese",
        "description": "Rich, smooth cream cheese — perfect for spreading or baking.",
        "sizes": [
            {"size": "8 oz block", "upc": "0 21000 40806 1"},
            {"size": "16 oz block", "upc": "0 21000 40807 8"},
        ],
    },
}


def _resolve_product(product_name: str) -> dict:
    q = product_name.strip().lower()
    if "no sugar" in q:
        return PRODUCTS["no sugar added ketchup"]
    if "organic" in q:
        return PRODUCTS["organic ketchup"]
    if "velveeta" in q or "shells" in q:
        return PRODUCTS["velveeta shells and cheese"]
    if "mac" in q or "macaroni" in q or "cheese dinner" in q:
        if "sponge" in q or "shape" in q:
            return PRODUCTS["mac and cheese shapes"]
        return PRODUCTS["mac and cheese"]
    if "bbq" in q or "barbecue" in q:
        return PRODUCTS["heinz bbq sauce"]
    if "mustard" in q:
        return PRODUCTS["heinz mustard"]
    if "bologna" in q or "oscar mayer" in q:
        return PRODUCTS["oscar mayer bologna"]
    if "jell" in q or "gelatin" in q:
        return PRODUCTS["jell-o"]
    if "philadelphia" in q or "cream cheese" in q:
        return PRODUCTS["philadelphia cream cheese"]
    return PRODUCTS["tomato ketchup"]


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------
@mcp.tool()
def find_where_to_buy(
    product_name: str, postal_code: str, radius_miles: float = 10.0
) -> FindWhereToBuyOutput:
    """Find nearby physical stores that currently stock a grocery product.

    Use this when a customer asks where they can buy a product near them, or
    which local stores have it in stock. Returns the closest in-stock store and
    a readable list of all nearby stores with distance, stock, price, and size.

    Args:
        product_name: The product to look for (e.g. "Heinz Tomato Ketchup", "Kraft Mac & Cheese").
        postal_code: The customer's ZIP code, used as the search center.
        radius_miles: Maximum search radius in miles (default 10).
    """
    product = _resolve_product(product_name)
    s = _seed(product["name"], postal_code, str(radius_miles))
    count = 3 + (s % 4)
    ranked = sorted(
        range(len(RETAILERS)),
        key=lambda idx: _seed(product["name"], postal_code, RETAILERS[idx][0]),
    )
    rows = []
    for idx in ranked[: min(count, len(RETAILERS))]:
        retailer, street = RETAILERS[idx]
        rs = _seed(product["name"], postal_code, retailer)
        distance = round(0.4 + (rs % int(max(radius_miles, 1) * 10)) / 10.0, 1)
        if distance > radius_miles:
            distance = round(max(radius_miles - (rs % 3) - 0.3, 0.3), 1)
        in_stock = (rs % 5) != 0
        size = product["sizes"][rs % len(product["sizes"])]["size"]
        price = round(2.49 + (rs % 450) / 100.0, 2)
        rows.append({"retailer": retailer, "address": f"{street}, {postal_code}",
                     "distance_miles": distance, "in_stock": in_stock,
                     "price": price, "size": size})
    rows.sort(key=lambda r: r["distance_miles"])

    lines = []
    for r in rows:
        if r["in_stock"]:
            lines.append(f"{r['retailer']} — {r['address']} — {r['distance_miles']} mi — "
                         f"in stock — ${r['price']:.2f} ({r['size']})")
        else:
            lines.append(f"{r['retailer']} — {r['address']} — {r['distance_miles']} mi — out of stock")
    store_list = "\n".join(lines)

    in_stock_rows = [r for r in rows if r["in_stock"]]
    if in_stock_rows:
        c = in_stock_rows[0]
        closest_store, closest_dist, closest_price = c["retailer"], c["distance_miles"], c["price"]
        summary = (f"{len(in_stock_rows)} of {len(rows)} nearby stores have "
                   f"{product['name']} in stock. Closest is {closest_store} "
                   f"({closest_dist} mi) at ${closest_price:.2f}.")
    else:
        closest_store, closest_dist, closest_price = "None nearby", 0.0, 0.0
        summary = f"No nearby store within {radius_miles} miles currently has {product['name']} in stock."

    return FindWhereToBuyOutput(
        product=product["name"], brand=product["brand"],
        search_postal_code=postal_code, radius_miles=radius_miles,
        store_count=len(rows), in_stock_count=len(in_stock_rows),
        closest_in_stock_store=closest_store,
        closest_in_stock_distance_miles=closest_dist,
        closest_in_stock_price_usd=closest_price,
        store_list=store_list, summary=summary,
    )


@mcp.tool()
def check_online_availability(
    product_name: str, postal_code: str = ""
) -> CheckOnlineOutput:
    """Check which online retailers sell a product and can ship or deliver it.

    Use this when a customer would rather buy online, asks about delivery, or
    when no nearby store has the item. Returns the lowest-price and fastest
    options plus a readable list of all online offers.

    Args:
        product_name: The product to look for (e.g. "Heinz Tomato Ketchup", "Kraft Mac & Cheese").
        postal_code: Optional delivery ZIP code to confirm delivery.
    """
    product = _resolve_product(product_name)
    offers = []
    for name, ships in ONLINE_RETAILERS:
        rs = _seed(product["name"], name, postal_code)
        if (rs % 6) == 0:
            continue
        offers.append({"retailer": name, "price": round(2.99 + (rs % 500) / 100.0, 2),
                       "days": 1 + (rs % 5), "pickup": (rs % 2) == 0})

    if offers:
        by_price = sorted(offers, key=lambda o: o["price"])
        by_speed = sorted(offers, key=lambda o: o["days"])
        cheapest, fastest = by_price[0], by_speed[0]
        lines = [f"{o['retailer']} — ${o['price']:.2f} — delivers in {o['days']} day(s)"
                 f"{' — pickup available' if o['pickup'] else ''}" for o in by_price]
        offer_list = "\n".join(lines)
        lowest_retailer, lowest_price = cheapest["retailer"], cheapest["price"]
        fastest_retailer, fastest_days = fastest["retailer"], fastest["days"]
        summary = (f"{len(offers)} online retailers carry {product['name']}. "
                   f"Cheapest is {lowest_retailer} at ${lowest_price:.2f}; "
                   f"fastest is {fastest_retailer} in {fastest_days} day(s).")
    else:
        offer_list, summary = "", f"No online retailer currently lists {product['name']}."
        lowest_retailer, lowest_price, fastest_retailer, fastest_days = "None", 0.0, "None", 0

    return CheckOnlineOutput(
        product=product["name"], brand=product["brand"],
        delivery_postal_code=postal_code or "not provided",
        offer_count=len(offers),
        lowest_price_retailer=lowest_retailer, lowest_price_usd=lowest_price,
        fastest_delivery_retailer=fastest_retailer, fastest_delivery_days=fastest_days,
        offer_list=offer_list, summary=summary,
    )


@mcp.tool()
def get_product_details(product_name: str) -> ProductDetailsOutput:
    """Return catalog details for a product: brand, sizes, UPCs, and category.

    Use this to confirm exactly which product or pack size a customer means
    before searching, or when they ask what variants or sizes exist.

    Args:
        product_name: The product to look up (e.g. "Heinz Tomato Ketchup",
            "Heinz Organic Ketchup", "Heinz No Sugar Added Ketchup",
            "Kraft Mac & Cheese", "Velveeta Shells & Cheese",
            "Oscar Mayer Bologna", "Philadelphia Cream Cheese").
    """
    product = _resolve_product(product_name)
    sizes = product["sizes"]
    sizes_list = "\n".join(f"{s['size']} (UPC {s['upc']})" for s in sizes)
    return ProductDetailsOutput(
        brand=product["brand"], name=product["name"],
        category=product["category"], description=product["description"],
        size_count=len(sizes),
        smallest_size=sizes[0]["size"], largest_size=sizes[-1]["size"],
        sizes_list=sizes_list,
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
    log.info("  MCP endpoint : http://%s:%s/mcp", HOST, PORT)
    log.info("  Health check : http://%s:%s/health", HOST, PORT)
    log.info("  Auth         : %s", "Bearer token required" if API_KEY else "none (open)")
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")
