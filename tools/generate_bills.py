"""
Generate 30 random grocery bills (PDFs) for the same person
across different days with different items.
"""
import os
import random
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT

# ---------- Customer (same person across all bills) ----------
CUSTOMER = {
    "name": "James Mitchell",
    "phone": "+1 (555) 820-4421",
    "address": "Apt 12B, 4820 Maple Ave, Austin, TX 78701",
    "loyalty_id": "LM-7842910",
}

# ---------- Pool of stores (bills come from different stores too) ----------
STORES = [
    {"name": "Whole Foods Market", "addr": "525 N Lamar Blvd, Austin, TX 78703",
     "ein": "52-1138801", "phone": "(512) 542-2200"},
    {"name": "H-E-B Grocery", "addr": "1000 E 41st St, Austin, TX 78751",
     "ein": "74-1433439", "phone": "(512) 459-7111"},
    {"name": "Kroger Fresh Fare", "addr": "3908 N IH-35, Austin, TX 78722",
     "ein": "31-0345740", "phone": "(512) 452-1018"},
    {"name": "Trader Joe's", "addr": "4001 N Lamar Blvd, Austin, TX 78756",
     "ein": "95-3759016", "phone": "(512) 206-1817"},
    {"name": "Walmart Supercenter", "addr": "9300 S IH-35, Austin, TX 78748",
     "ein": "71-0415188", "phone": "(512) 282-0450"},
]

# ---------- Item catalog: (name, unit, price_range) ----------
ITEMS = [
    # Staples
    ("Jasmine Rice 2lb",       "bag", (3.99,  6.99)),
    ("Lentils 1lb",            "bag", (1.99,  3.49)),
    ("All-Purpose Flour 5lb",  "bag", (3.49,  5.99)),
    ("Granulated Sugar 4lb",   "bag", (2.99,  4.49)),
    ("Iodized Salt 26oz",      "ctn", (0.99,  1.79)),
    ("Vegetable Oil 48oz",     "btl", (4.99,  7.99)),
    ("Olive Oil 16.9oz",       "btl", (6.99, 12.99)),
    # Dairy
    ("Whole Milk 1 gal",       "jug", (3.49,  4.99)),
    ("Greek Yogurt 32oz",      "tub", (4.99,  7.49)),
    ("Mozzarella 16oz",        "pkt", (4.49,  6.99)),
    ("Unsalted Butter 1lb",    "box", (3.99,  5.99)),
    ("Cheddar Slices 12oz",    "pkt", (3.49,  5.49)),
    # Produce
    ("Roma Tomatoes 1lb",       "lb", (1.29,  2.99)),
    ("Yellow Onions 3lb",      "bag", (2.49,  3.99)),
    ("Russet Potatoes 5lb",    "bag", (3.99,  5.49)),
    ("Bananas 1 bunch",        "bch", (1.29,  1.99)),
    ("Gala Apples 3lb",        "bag", (4.99,  7.99)),
    ("Baby Spinach 5oz",       "bag", (2.99,  4.49)),
    ("Carrots 1lb",             "lb", (0.99,  1.99)),
    ("English Cucumber",       "ea.",  (0.99,  1.79)),
    # Bakery & breakfast
    ("Whole Wheat Bread",     "loaf", (2.99,  4.99)),
    ("Large Eggs 1 dozen",     "doz", (2.99,  5.49)),
    ("Cheerios 18oz",          "box", (4.49,  6.99)),
    ("Old Fashioned Oats 42oz","ctn", (4.99,  7.49)),
    # Snacks & beverages
    ("Ramen Noodles 4-pack",   "pkt", (2.49,  4.49)),
    ("Lay's Classic Chips",    "bag", (3.99,  5.49)),
    ("Oreo Cookies 14.3oz",    "pkt", (3.99,  5.99)),
    ("Lipton Tea 100ct",       "box", (4.99,  7.99)),
    ("Folgers Coffee 22.6oz",  "can", (8.99, 13.99)),
    ("Coca-Cola 2L",           "btl", (1.99,  2.99)),
    # Household
    ("Tide Pods 42ct",         "bag", (12.99, 19.99)),
    ("Dawn Dish Soap 21.6oz",  "btl", (3.49,  5.49)),
    ("Lysol Spray 12.5oz",     "can", (4.99,  7.99)),
    ("Colgate Toothpaste 6oz", "tub", (3.49,  5.49)),
    ("Dove Body Wash 22oz",    "btl", (5.99,  8.99)),
    ("Bounty Paper Towels 6pk","pkt", (8.99, 13.99)),
]

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def make_bill(bill_no: int, date: datetime, store: dict, out_path: str):
    items_in_bill = random.sample(ITEMS, k=random.randint(6, 14))
    rows = [["#", "Item", "Unit", "Qty", "Rate ($)", "Amount ($)"]]
    subtotal = 0.0
    for i, (name, unit, (lo, hi)) in enumerate(items_in_bill, start=1):
        qty = random.choice([1, 1, 1, 2, 2, 3])
        rate = round(random.uniform(lo, hi), 2)
        amount = round(qty * rate, 2)
        subtotal += amount
        rows.append([str(i), name, unit, str(qty), f"{rate:.2f}", f"{amount:.2f}"])

    # Discount + Sales Tax (TX state rate 8.25%)
    discount_pct = random.choice([0, 0, 2, 5, 7, 10])
    discount = round(subtotal * discount_pct / 100, 2)
    taxable = subtotal - discount
    sales_tax = round(taxable * 0.0825, 2)
    total = round(taxable + sales_tax, 2)
    paid = round(total + random.uniform(0, 1), 2)
    paid = round(round(paid / 0.25) * 0.25, 2)  # round to nearest quarter
    change = round(paid - total, 2)

    # ---------- Build PDF ----------
    doc = SimpleDocTemplate(
        out_path, pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=15 * mm, bottomMargin=15 * mm,
    )
    styles = getSampleStyleSheet()
    center = ParagraphStyle("c", parent=styles["Normal"], alignment=TA_CENTER)
    center_b = ParagraphStyle("cb", parent=styles["Heading2"], alignment=TA_CENTER)
    right = ParagraphStyle("r", parent=styles["Normal"], alignment=TA_RIGHT)
    small = ParagraphStyle("s", parent=styles["Normal"], fontSize=8, textColor=colors.grey)

    story = []
    story.append(Paragraph(f"<b>{store['name']}</b>", center_b))
    story.append(Paragraph(store["addr"], center))
    story.append(Paragraph(f"Phone: {store['phone']} | EIN: {store['ein']}", center))
    story.append(Spacer(1, 6))
    story.append(Paragraph("<b>TAX INVOICE / RETAIL BILL</b>", center))
    story.append(Spacer(1, 8))

    # Bill metadata
    meta = [
        [f"Bill No: {bill_no:05d}", f"Date: {date.strftime('%d-%b-%Y')}"],
        [f"Cashier: {random.choice(['Ashley', 'Mike', 'Jennifer', 'Tyler', 'Sarah'])}",
         f"Time: {date.strftime('%I:%M %p')}"],
    ]
    meta_tbl = Table(meta, colWidths=[90 * mm, 80 * mm])
    meta_tbl.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    story.append(meta_tbl)
    story.append(Spacer(1, 4))

    # Customer
    cust = [
        [f"<b>Customer:</b> {CUSTOMER['name']}"],
        [f"<b>Phone:</b> {CUSTOMER['phone']}  |  <b>Loyalty ID:</b> {CUSTOMER['loyalty_id']}"],
        [f"<b>Address:</b> {CUSTOMER['address']}"],
    ]
    for line in cust:
        story.append(Paragraph(line[0], styles["Normal"]))
    story.append(Spacer(1, 8))

    # Items table
    item_tbl = Table(rows, colWidths=[10 * mm, 70 * mm, 15 * mm, 15 * mm, 25 * mm, 30 * mm],
                     repeatRows=1)
    item_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
        ("ALIGN", (1, 0), (1, -1), "LEFT"),
        ("ALIGN", (1, 0), (1, 0), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#f5f5f5")]),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(item_tbl)
    story.append(Spacer(1, 6))

    # Totals
    totals = [
        ["Subtotal:", f"$ {subtotal:.2f}"],
        [f"Discount ({discount_pct}%):", f"– $ {discount:.2f}"],
        ["Sales Tax @ 8.25%:", f"$ {sales_tax:.2f}"],
        ["GRAND TOTAL:", f"$ {total:.2f}"],
        [f"Paid ({random.choice(['Cash', 'Debit', 'Credit', 'Debit', 'Credit'])}):",
         f"$ {paid:.2f}"],
        ["Change / Balance:", f"$ {change:.2f}"],
    ]
    tot_tbl = Table(totals, colWidths=[120 * mm, 45 * mm])
    tot_tbl.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
        ("FONTNAME", (0, 3), (-1, 3), "Helvetica-Bold"),
        ("LINEABOVE", (0, 3), (-1, 3), 0.6, colors.black),
        ("LINEBELOW", (0, 3), (-1, 3), 0.6, colors.black),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
    ]))
    story.append(tot_tbl)
    story.append(Spacer(1, 14))

    story.append(Paragraph(
        f"Items: {len(items_in_bill)}  |  Total Qty: "
        f"{sum(int(r[3]) for r in rows[1:])}",
        center))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "Thank you for shopping with us! Goods once sold cannot be returned.", center))
    story.append(Paragraph(
        "*** This is a computer-generated bill — no signature required. ***", small))

    doc.build(story)


def main():
    random.seed(42)  # reproducible
    start_date = datetime(2025, 1, 5, 10, 0)
    used_dates = set()

    for i in range(1, 31):
        # pick a unique date within ~10 months
        while True:
            offset_days = random.randint(0, 300)
            d = start_date + timedelta(days=offset_days,
                                       hours=random.randint(-2, 8),
                                       minutes=random.randint(0, 59))
            if d.date() not in used_dates:
                used_dates.add(d.date())
                break

        store = random.choice(STORES)
        fname = f"bill_{i:02d}_{d.strftime('%Y-%m-%d')}.pdf"
        path = os.path.join(OUTPUT_DIR, fname)
        make_bill(bill_no=10000 + i, date=d, store=store, out_path=path)

    print(f"Generated {len(os.listdir(OUTPUT_DIR))} bills in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
