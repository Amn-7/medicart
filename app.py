from flask import Flask, flash, render_template, session, redirect, url_for, request
import json
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret-key"

# Load medicine list
def load_medicines():
    with open("medicines.json", "r") as file:
        return json.load(file)

# Create SQLite DB (only once)
def init_db():
    if not os.path.exists("orders.db"):
        conn = sqlite3.connect("orders.db")
        c = conn.cursor()
        c.execute('''
            CREATE TABLE orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT,
                items TEXT,
                total INTEGER,
                created_at TEXT
            )
        ''')
        conn.commit()
        conn.close()

init_db()

# Home
@app.route("/")
def home():
    medicines = load_medicines()
    search_query = request.args.get("search", "").lower()
    selected_category = request.args.get("category", "")

    if search_query:
        medicines = [med for med in medicines if search_query in med["name"].lower()]
    if selected_category:
        medicines = [med for med in medicines if med["category"] == selected_category]

    categories = sorted(list(set(med["category"] for med in load_medicines())))
    cart_count = sum(session.get("cart", {}).values())

    return render_template("home.html", medicines=medicines, categories=categories,
                           selected_category=selected_category, cart_count=cart_count)

# Save address
@app.route("/save_address", methods=["POST"])
def save_address():
    session["address"] = request.form.get("address")
    session["city"] = request.form.get("city")
    return redirect(url_for("home"))

# Add to cart
@app.route("/add_to_cart", methods=["POST"])
def add_to_cart():
    med_id = int(request.form.get("med_id"))
    quantity = int(request.form.get("quantity", 1))

    if "cart" not in session:
        session["cart"] = {}

    cart = session["cart"]
    if str(med_id) in cart:
        cart[str(med_id)] += quantity
    else:
        cart[str(med_id)] = quantity

    session["cart"] = cart
    flash("✅ Added to cart successfully!")
    return redirect(url_for("home"))

# Remove from cart
@app.route("/remove_from_cart/<int:med_id>")
def remove_from_cart(med_id):
    if "cart" in session:
        session["cart"].pop(str(med_id), None)
    return redirect(url_for("view_cart"))

# Cart
@app.route("/cart")
def view_cart():
    medicines = load_medicines()
    cart_data = session.get("cart", {})
    cart_items = []
    total = 0

    for med in medicines:
        med_id_str = str(med["id"])
        if med_id_str in cart_data:
            qty = cart_data[med_id_str]
            med_copy = med.copy()
            med_copy["quantity"] = qty
            med_copy["subtotal"] = med["price"] * qty
            cart_items.append(med_copy)
            total += med_copy["subtotal"]

    cart_count = sum(cart_data.values())
    return render_template("cart.html", cart=cart_items, total=total, cart_count=cart_count)

# Checkout
@app.route("/checkout")
def checkout():
    medicines = load_medicines()
    cart_data = session.get("cart", {})
    cart_items = []
    total = 0

    for med in medicines:
        med_id_str = str(med["id"])
        if med_id_str in cart_data:
            qty = cart_data[med_id_str]
            med_copy = med.copy()
            med_copy["quantity"] = qty
            med_copy["subtotal"] = med["price"] * qty
            cart_items.append(med_copy)
            total += med_copy["subtotal"]

    items_list = ", ".join([f'{med["name"]} (x{med["quantity"]})' for med in cart_items])

    if session.get("user"):
        conn = sqlite3.connect("orders.db")
        c = conn.cursor()
        c.execute("INSERT INTO orders (email, items, total, created_at) VALUES (?, ?, ?, ?)",
                  (session["user"], items_list, total, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()

    session.pop("cart", None)
    return render_template("checkout.html", items=items_list, total=total, cart_count=0)

# Signup
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        session["user"] = request.form.get("email")
        flash("🎉 Signup successful! Welcome!")
        return redirect(url_for("home"))
    cart_count = sum(session.get("cart", {}).values())
    return render_template("signup.html", cart_count=cart_count)

# Login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        session["user"] = request.form.get("email")
        flash("👋 Welcome back!")
        return redirect(url_for("home"))
    cart_count = sum(session.get("cart", {}).values())
    return render_template("login.html", cart_count=cart_count)

# Logout
@app.route("/logout")
def logout():
    session.pop("user", None)
    session.pop("cart", None)
    flash("👋 Logged out successfully.")
    return redirect(url_for("home"))

# Invoice
@app.route("/invoice")
def invoice():
    if not session.get("user"):
        return redirect(url_for("login"))
    conn = sqlite3.connect("orders.db")
    c = conn.cursor()
    c.execute("SELECT items, total, created_at FROM orders WHERE email = ? ORDER BY id DESC LIMIT 1", (session["user"],))
    order = c.fetchone()
    conn.close()
    cart_count = sum(session.get("cart", {}).values())
    return render_template("invoice.html", order=order, address=session.get("address", "Not Provided"),
                           user=session["user"], cart_count=cart_count)

# Order Summary
@app.route("/order_summary")
def order_summary():
    if not session.get("user"):
        return redirect(url_for("login"))
    conn = sqlite3.connect("orders.db")
    c = conn.cursor()
    c.execute("SELECT items, total, created_at FROM orders WHERE email = ? ORDER BY id DESC LIMIT 1", (session["user"],))
    order = c.fetchone()
    conn.close()
    cart_count = sum(session.get("cart", {}).values())
    return render_template("order_summary.html", order=order, address=session.get("address", "Not Provided"),
                           cart_count=cart_count)

# Order Status
@app.route("/order_status")
def order_status():
    if not session.get("user"):
        return redirect(url_for("login"))
    cart_count = sum(session.get("cart", {}).values())
    return render_template("order_status.html", cart_count=cart_count)

# My Orders
@app.route("/my_orders")
def my_orders():
    if not session.get("user"):
        return redirect(url_for("login"))
    conn = sqlite3.connect("orders.db")
    c = conn.cursor()
    c.execute("SELECT items, total, created_at FROM orders WHERE email = ?", (session["user"],))
    orders = c.fetchall()
    conn.close()
    cart_count = sum(session.get("cart", {}).values())
    return render_template("my_orders.html", orders=orders, cart_count=cart_count)

# Run the app
if __name__ == "__main__":
    app.run(debug=True)
