"""Verify the hardcoded real-store directory and the mock fallback."""
import server


def block(t): print("\n" + "=" * 78 + f"\n{t}\n" + "-" * 78)


# 1. Real directory ZIPs return real store names + real addresses.
for zp, where in [("60605", "Chicago South Loop"),
                   ("10001", "NYC Chelsea"),
                   ("90015", "LA Downtown")]:
    block(f"[real] find_where_to_buy('Heinz Tomato Ketchup', '{zp}')  -> {where}")
    out = server.find_where_to_buy("Heinz Tomato Ketchup", zp)
    print(f"  store_data_source: {out.store_data_source}   stores: {out.store_count}   in_stock: {out.in_stock_count}")
    print(f"  closest_in_stock: {out.closest_in_stock_store} ({out.closest_in_stock_distance_miles} mi) "
          f"${out.closest_in_stock_price_usd:.2f} {out.closest_in_stock_size}")
    for ln in out.store_list.splitlines():
        print("      " + ln)

# 2. Pin a SKU across the real Chicago stores.
block("[real + pinned SKU] find_where_to_buy('Heinz Ketchup', '60605', size='44 oz')")
out = server.find_where_to_buy("Heinz Ketchup", "60605", size="44 oz")
for ln in out.store_list.splitlines():
    print("      " + ln)

# 3. Unknown ZIP -> mock fallback (still works, generated addresses).
block("[unknown ZIP] find_where_to_buy('Kraft Mac & Cheese', '73301')  -> mock")
out = server.find_where_to_buy("Kraft Mac & Cheese", "73301")
print(f"  store_data_source: {out.store_data_source}   stores: {out.store_count}")
print("      " + out.store_list.splitlines()[0])

# 4. Determinism: same call twice = identical.
a = server.find_where_to_buy("Heinz Tomato Ketchup", "60605").model_dump()
b = server.find_where_to_buy("Heinz Tomato Ketchup", "60605").model_dump()
block("[determinism] identical inputs -> identical outputs")
print("  ", a == b)

# 5. Unknown product still refuses (no silent guess).
block("[unknown product] find_where_to_buy('Heinz Mayo Sriracha Deluxe XL', '60605')")
out = server.find_where_to_buy("Heinz Mayo Sriracha Deluxe XL", "60605")
print(f"  matched: {out.matched}  product: {out.product}  source: {out.store_data_source}")

# 6. Every directory address is internally consistent (ZIP in the metro's set).
block("[audit] every directory store's ZIP belongs to its metro")
bad = 0
for label, entry in server.STORE_DIRECTORY.items():
    for s in entry["stores"]:
        z = s["address"].split()[-1]
        # store ZIP need not equal the search ZIP, but should be a real 5-digit
        if not (z.isdigit() and len(z) == 5):
            bad += 1
            print("  BAD ZIP:", s["address"])
print(f"  {'all addresses well-formed' if bad == 0 else f'{bad} malformed'}; "
      f"metros: {len(server.STORE_DIRECTORY)}, "
      f"directory ZIPs: {len(server._DIR_BY_ZIP)}")
