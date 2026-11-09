# app.py - the Flask routes.
from flask import Flask, flash, redirect, render_template, request, url_for

import db

app = Flask(__name__)
app.secret_key = "any-secret-text"


def check_form(form):
    """Check the form values. Returns a list of error messages (empty = OK)."""
    errors = []

    if form["name"].strip() == "":
        errors.append("Product name is required.")

    try:
        quantity = int(form["quantity"])
        if quantity < 0:
            errors.append("Quantity cannot be negative.")
        elif quantity > 1000000:
            errors.append("Quantity is too large.")
    except ValueError:
        errors.append("Quantity must be a whole number.")

    try:
        price = float(form["price"])
        if price < 0:
            errors.append("Price cannot be negative.")
        elif not price <= 1000000:  # also catches "nan" and "inf"
            errors.append("Price is too large or not valid.")
    except ValueError:
        errors.append("Price must be a number.")

    return errors


@app.route("/")
def dashboard():
    products = db.get_products()
    total_products = len(products)
    total_units = sum(p["quantity"] for p in products)
    low_stock = [p for p in products if p["quantity"] < db.LOW_STOCK_LIMIT]
    recent = sorted(products, key=lambda p: p["id"], reverse=True)[:5]
    return render_template("dashboard.html", total_products=total_products,
                           total_units=total_units, low_stock=low_stock,
                           recent=recent, limit=db.LOW_STOCK_LIMIT)


@app.route("/products")
def products():
    search = request.args.get("q", "")
    show_low_only = request.args.get("filter") == "low"

    all_products = db.get_products(search)
    low_stock = [p for p in all_products if p["quantity"] < db.LOW_STOCK_LIMIT]
    # "Show only low stock" link: show just the low-stock products
    shown = low_stock if show_low_only else all_products

    return render_template("products.html", products=shown, low_stock=low_stock,
                           show_low_only=show_low_only, search=search,
                           limit=db.LOW_STOCK_LIMIT)


@app.route("/products/add", methods=["GET", "POST"])
def add_product():
    if request.method == "POST":
        errors = check_form(request.form)
        if errors:
            for message in errors:
                flash(message, "danger")
            return render_template("add_product.html", product=request.form,
                                   editing=False), 400
        db.add_product(request.form["name"].strip(), request.form["category"],
                       int(request.form["quantity"]), float(request.form["price"]))
        flash("Product added.", "success")
        return redirect(url_for("products"))
    return render_template("add_product.html", product={}, editing=False)


@app.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
def edit_product(product_id):
    product = db.get_product(product_id)
    if product is None:
        return redirect(url_for("products"))

    if request.method == "POST":
        errors = check_form(request.form)
        if errors:
            for message in errors:
                flash(message, "danger")
            return render_template("add_product.html", product=request.form,
                                   editing=True), 400
        db.update_product(product_id, request.form["name"].strip(),
                          request.form["category"],
                          int(request.form["quantity"]), float(request.form["price"]))
        flash("Product updated.", "success")
        return redirect(url_for("products"))
    return render_template("add_product.html", product=product, editing=True)


@app.route("/products/<int:product_id>/delete", methods=["POST"])
def delete_product(product_id):
    db.delete_product(product_id)
    flash("Product deleted.", "success")
    return redirect(url_for("products"))


if __name__ == "__main__":
    app.run(debug=True)
