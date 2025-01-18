import os
from cs50 import SQL
from flask import Flask, redirect, render_template, request, session, jsonify
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from auth import apology, login_required

# Configure application
app = Flask(__name__)

months = {
    1: 'January',
    2: 'February',
    3: 'March',
    4: 'April',
    5: 'May',
    6: 'June',
    7: 'July',
    8: 'August',
    9: 'September',
    10: 'October',
    11: 'November',
    12: 'December'
}

def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"

def date(value):
    """Format date as month(non-numeric), date year"""
    y, m, d = value.split("-")
    return f"{months[int(m)]} {d}, {y}"

# Custom filters
app.jinja_env.filters["usd"] = usd
app.add_template_filter(date)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///cadeau.db")

def getUpcoming(user_id):
    """return a list of wishlists that the user has access to"""
    data = db.execute("""
                      SELECT w.*, u.first_name, u.last_name
                      FROM Wishlists w
                      JOIN UserWishLists uw ON w.wishlist_id = uw.wishlist_id
                      JOIN Users u ON w.user_id = u.user_id
                      WHERE uw.user_id = ?
                      ORDER BY event_date""",
                      user_id)
    return data


def getMyWishlists(user_id):
    """return a list of wishlists that the users owns"""
    data = db.execute("SELECT * FROM Wishlists WHERE user_id = ?  ORDER BY event_date""",
                      user_id)
    return data

def getWishlist(wishlist_id):
    """return row of a specific wishlist"""
    data = db.execute("SELECT * FROM Wishlists WHERE wishlist_id = ?",
                     wishlist_id)[0]
    owner = db.execute("SELECT first_name, last_name FROM Users u JOIN Wishlists w ON u.user_id = w.user_id WHERE wishlist_id = ?",
                      wishlist_id)[0]
    data["owner"] = f"{owner["first_name"]} {owner["last_name"]}"
    return data

def get_shared_users(wishlist_id):
    """return list of users a wishlist is shared with"""
    data = db.execute("SELECT first_name, last_name FROM Users u JOIN UserWishlists w ON u.user_id = w.user_id WHERE wishlist_id =?",
                      wishlist_id)
    return data

def getItems(wishlist_id):
    """return matrix of items for a wishlist"""
    owner_id = db.execute("SELECT user_id FROM Wishlists WHERE wishlist_id = ?",
                          wishlist_id)[0]
    # order list with unpurchased items first if someone else is viewing the list
    if owner_id["user_id"] != session["user_id"]:
        data = db.execute("SELECT * FROM Items WHERE wishlist_id = ? ORDER BY purchased ASC, price DESC",
                      wishlist_id)
    else:
        data = db.execute("SELECT * FROM Items WHERE wishlist_id = ? ORDER BY price DESC",
                      wishlist_id)
    return data

def getItem(item_id):
    """return values for item by id"""
    data = db.execute("SELECT * FROM Items WHERE item_id = ?",
                      item_id)[0]
    return data

def getUserInfo(user_id):
    return db.execute("SELECT username, first_name, last_name, email, birthday FROM Users WHERE user_id = ?", user_id)[0]

def apology(message, code=400):
    """Render message as an apology to user."""
    return render_template("apology.html", code=code, message=message), code



@app.route("/")
@login_required
def index():
    """Show overview of wishlists the user has access to"""
    upcoming=getUpcoming(session["user_id"])
    my_wishlists=getMyWishlists(session["user_id"])
    return render_template(
        "index.html",
        upcoming=upcoming,
        my_wishlists=my_wishlists)


@app.route("/auth/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("Must Provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("Must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("Invalid username and/or password", 403)

        print("successful login")
        # Remember which user has logged in
        session["user_id"] = rows[0]["user_id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("auth/login.html")


@app.route("/auth/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        username = request.form.get("username").strip()
        email = request.form.get("email").strip()
        first_name = request.form.get("first_name").strip()
        last_name = request.form.get("last_name").strip()
        birthday = request.form.get("birthday")
        password = request.form.get("password")
        password_again = request.form.get("confirmation")

        # check if username already exists
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)

        if not username:
            return apology("Username must not be blank")
        elif len(rows) > 0:
            return apology("Username already exists")
        elif password != password_again:
            return apology("Passwords do not match")
        elif len(password) < 1 or len(password_again) < 1 or len(username) < 1:
            return apology("All fields must be populated")
        elif not email:
            return apology("must provide valid email", 403)
        else:
            # Add user to password database
            db.execute(
                "INSERT INTO users (username, hash, email, first_name, last_name, birthday) VALUES (?, ?, ?, ?, ?, ?)",
                username,
                generate_password_hash(password),
                email,
                first_name,
                last_name,
                birthday
            )

            # Redirect user to home page
            return redirect("/")
    else:
        return render_template("auth/register.html")

@app.route("/auth/change_password", methods=["GET", "POST"])
def change_password():
    """Allow user to change password"""
    if request.method == "POST":
        # pull user input from form
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        password_again = request.form.get("password_again")

        rows = db.execute("SELECT hash FROM users WHERE user_id = ?",
                          session["user_id"])[0]
        hash = rows['hash']

        if not new_password == password_again:
            return apology("New passwords do not match")
        elif not (current_password or new_password or password_again):
            return apology("Please fill out all forms")
        elif not check_password_hash(hash, current_password):
            return apology("Existing password is incorrect")
        else:
            # Add user to password database
            db.execute(
                "UPDATE users SET hash = ? WHERE user_id = ?",
                generate_password_hash(new_password),
                session["user_id"]
            )

            # Redirect user to home page
            return redirect("/profile")
    else:
        return render_template("auth/change_password.html")


@app.route("/auth/logout")
def logout():
    """Log user out"""

    session.clear()
    # Clear the user_id from the session
    session.pop("user_id", None)

    # Redirect user to login form
    return redirect("/")


@app.route("/profile", methods=["GET"])
@login_required
def profile():
    """Register user"""
    return render_template("/profile.html",
                           data=getUserInfo(session["user_id"]))

@app.route("/auth/edit_profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    if request.method == "POST":
        first_name = request.form.get("first_name").strip()
        last_name = request.form.get("last_name").strip()
        birthday = request.form.get("birthday")

        # Change user details
        db.execute(
            "UPDATE users SET first_name = ?, last_name = ?, birthday = ? WHERE user_id = ?",
            first_name,
            last_name,
            birthday,
            session["user_id"]
        )

        # Redirect user to profile page
        return redirect("/profile")
    else:
        return render_template("/auth/edit_profile.html",
                               data=getUserInfo(session["user_id"]))


@app.route("/view_list/<int:wishlist_id>")
@login_required
def view_list(wishlist_id):
    """Show summary of list"""
    name = db.execute("SELECT first_name FROM users WHERE user_id = ?",
                     session['user_id'])[0]["first_name"]
    wishlist = getWishlist(wishlist_id)
    items = getItems(wishlist_id)

    data = db.execute("SELECT user_id FROM Wishlists WHERE wishlist_id = ?",
                      wishlist_id)[0]
    wishlist_owner = data["user_id"]
    is_owner = wishlist_owner == session["user_id"]
    purchaser_list = db.execute("SELECT user_id, first_name FROM users")
    purchasers = {purchaser["user_id"]: purchaser["first_name"] for purchaser in purchaser_list}
    shared_with = get_shared_users(wishlist_id)

    return render_template(
        "view_list.html",
        wishlist=wishlist,
        items=items,
        is_owner=is_owner,
        purchasers=purchasers,
        shared_with=shared_with,
        name=name)


@app.route("/add_list", methods=["GET", "POST"])
def add_list():
    """Add item to a list"""
    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        date = request.form.get("event_date")
        occasion = request.form.get("occasion")

        if not title:
            return apology("Title required")
        elif not date:
            return apology("Date required")
        else:
            # Add item to items database
            wishlist_id = db.execute("INSERT INTO Wishlists (title, description, user_id, event_date, occasion) VALUES (?, ?, ?, ?, ?)",
                          title,
                          description,
                          session["user_id"],
                          date,
                          occasion)

        # Redirect user to wishlist viewing page
        return redirect(f"/view_list/{wishlist_id}")
    else:
        return render_template("/add_list.html")

@app.route("/delete_wishlist/<int:wishlist_id>", methods=["GET"])
@login_required
def delete_wishlist(wishlist_id):
    # Check if the user has the right to delete the wishlist
    wishlist_owner = db.execute("SELECT user_id FROM Wishlists WHERE wishlist_id = ?", wishlist_id)[0]["user_id"]

    if wishlist_owner != session["user_id"]:
        return apology("You don't have permission to delete this wishlist")

    # Perform the deletion in the database
    db.execute("DELETE FROM Items WHERE wishlist_id = ?", wishlist_id)
    db.execute("DELETE FROM Wishlists WHERE wishlist_id = ?", wishlist_id)

    # Redirect the user to the home page or any other appropriate page
    return redirect("/")

@app.route("/delete_item/<int:item_id>", methods=["GET"])
@login_required
def delete_item(item_id):
    # record wishlist_id for redirect
    wishlist_id = db.execute("SELECT wishlist_id FROM Items WHERE item_id = ?", item_id)[0]['wishlist_id']

    # Perform the deletion in the database
    db.execute("DELETE FROM Items WHERE item_id = ?", item_id)

    # Redirect the user to the wishlist page
    return redirect(f"/view_list/{wishlist_id}")

@app.route("/share_list/<int:wishlist_id>", methods=["POST"])
def share_list(wishlist_id):
    """Share list with another user"""
    email = request.form.get("shared_email")
    try:
        shared_user_id = db.execute("SELECT user_id FROM Users WHERE email = ?",
                                email)[0]
        shared_user_id = shared_user_id["user_id"]
    except:
        return apology("This email is not registered with Cadeau", 403)
    # Prevent user from sharing with themself
    if shared_user_id == session["user_id"]:
        return apology("Cannot share with yourself")
    elif db.execute("SELECT * FROM UserWishlists WHERE user_id = ? AND wishlist_id = ?",
                    shared_user_id,
                    wishlist_id):
        return apology("This list is already shared with that user")
    else:
        # Add record of sharing this wishlist
        db.execute("INSERT INTO UserWishlists (user_id, wishlist_id) VALUES (?, ?)",
                        shared_user_id,
                        wishlist_id)

    # Redirect user to wishlist viewing page
    return redirect(f"/view_list/{wishlist_id}")


@app.route("/add_item/<int:wishlist_id>", methods=["GET", "POST"])
def add_item(wishlist_id):
    """Add item to a list"""
    if request.method == "POST":
        name = request.form.get("name")
        description = request.form.get("description")
        try:
            price = float(request.form.get("price"))
        except:
            price = 0.0
        link = request.form.get("link")

        if not name:
            return apology("Name")
        else:
            # Add item to items database
            db.execute("INSERT INTO Items (wishlist_id, name, description, price, link) VALUES (?, ?, ?, ?, ?)",
                          wishlist_id,
                          name,
                          description,
                          price,
                          link)
        # Redirect user to wishlist viewing page
        return redirect(f"/view_list/{wishlist_id}")
    else:
        return render_template(f"/add_item.html",
                               wishlist_id=wishlist_id)


@app.route("/edit_item/<int:item_id>", methods=["GET", "POST"])
def edit_item(item_id):
    """Add item to a list"""
    if request.method == "POST":
        name = request.form.get("name")
        description = request.form.get("description")
        price = float(request.form.get("price"))
        link = request.form.get("link")

        wishlist_id = db.execute("SELECT wishlist_id FROM items WHERE item_id = ?",
                                 item_id)[0]
        wishlist_id = wishlist_id["wishlist_id"]

        if not name:
            return apology("Name")
        else:
            # Add item to items database
            db.execute("UPDATE Items SET name = ?, description = ?, price = ?, link = ? WHERE item_id = ?",
                          name,
                          description,
                          price,
                          link,
                          item_id)
        # Redirect user to wishlist viewing page
        return redirect(f"/view_list/{wishlist_id}")
    else:
        item = getItem(item_id)
        return render_template(f"/edit_item.html",
                               item_id=item_id,
                               item=item)

@app.route("/buy_item/<int:item_id>", methods=["GET"])
def buy_item(item_id):
    """Share list with another user"""
    db.execute("UPDATE Items SET purchased = 1, purchaser_id = ? WHERE item_id = ?",
               session["user_id"],
               item_id)
    wishlist_id = db.execute("SELECT wishlist_id FROM Items WHERE item_id = ?",
                             item_id)[0]["wishlist_id"]
    # Redirect user to wishlist viewing page
    return redirect(f"/view_list/{wishlist_id}")

@app.route("/unbuy_item/<int:item_id>", methods=["GET"])
def unbuy_item(item_id):
    """Share list with another user"""
    db.execute("UPDATE Items SET purchased = 0, purchaser_id = NULL WHERE item_id = ?",
               item_id)
    wishlist_id = db.execute("SELECT wishlist_id FROM Items WHERE item_id = ?",
                             item_id)[0]["wishlist_id"]
    # Redirect user to wishlist viewing page
    return redirect(f"/view_list/{wishlist_id}")
