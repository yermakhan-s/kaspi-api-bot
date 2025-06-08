import datetime as dt
from decimal import Decimal
import redis

from .kaspi import fetch_active_orders
from .sheets import sales_ws
from .settings import settings, FINAL_STATUSES

r = redis.from_url(settings.REDIS_URL)


def _format_items(entries):
    parts = []
    for e in entries:
        name = e.get("name", "item")
        qty  = e.get("quantity", 1)
        parts.append(f"{name} × {qty}")
    return "; ".join(parts)


def process() -> None:
    orders = fetch_active_orders()

    for order in orders:
        attrs = order["attributes"]
        oid = order["id"]
        status = attrs["status"]
        total  = Decimal(str(attrs["totalPrice"]))

        fee = (total * Decimal("0.05")).quantize(Decimal("0.01"))
        net = total - fee

        created_at = dt.datetime.fromtimestamp(
            int(attrs["creationDate"]) / 1000
        ).strftime("%Y-%m-%d %H:%M")

        cust = attrs.get("customer", {})
        customer_name = f"{cust.get('firstName','')} {cust.get('lastName','')}".strip()
        items_cell = _format_items(attrs.get("entries", []))

        # row exists?
        if r.hexists("order_row", oid):
            row_idx = int(r.hget("order_row", oid))
            prev_status = sales_ws.cell(row_idx, 8).value
            if status != prev_status or status in FINAL_STATUSES:
                # update row
                if status in ("CANCELLED", "RETURNED"):
                    fee = net = Decimal("0")
                sales_ws.update(
                    f"C{row_idx}:H{row_idx}",
                    [[customer_name, items_cell, str(total), str(fee), str(net), status]]
                )
                if status in FINAL_STATUSES:
                    r.srem("open_orders", oid)
            continue

        # new row
        row = [created_at, oid, customer_name, items_cell,
               str(total), str(fee), str(net), status]
        sales_ws.append_row(row, value_input_option="USER_ENTERED")
        new_idx = len(sales_ws.get_all_values())
        r.hset("order_row", oid, new_idx)
        if status not in FINAL_STATUSES:
            r.sadd("open_orders", oid)