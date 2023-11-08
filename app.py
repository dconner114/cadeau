import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    data = portfolio(session['user_id'])
    return render_template("index.html", data=data, cash=usd(getCash(session['user_id'])), total=usd(getTotal(session['user_id'])))


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":

        stock = lookup(request.form.get("symbol"))
        try:
            qty = float(request.form.get("shares"))
        except ValueError:
            return apology("Quantity must be a positive integer")

        if not stock:
            return apology("Symbol does not exist")




        username = db.execute("SELECT username FROM users WHERE id = ?", session['user_id'])[0]['username']
        name = stock['name']
        symbol = stock['symbol']
        price = stock['price']
        currentBalance = db.execute("SELECT cash FROM users WHERE username = ?", username)[0]['cash']

        if (currentBalance - (price * qty)) > 0:
            db.execute("INSERT INTO transactions (username, symbol, shares, price) VALUES (?, ?, ?, ?)", username, symbol, qty, price)
            db.execute("UPDATE users SET cash = ? WHERE username=?", currentBalance - price * qty, username)
            return render_template("index.html", data=portfolio(session['user_id']), cash=getCash(session['user_id']), total=getTotal(session['user_id']))
        else:
            return apology("Not enough funds to purchase")

    return render_template("buy.html")


def portfolio(user_id):
    """return a summary of stocks and net value for user (used in index.html)"""
    # extract portfolio symbols and quantities from transactions database
    data = db.execute("SELECT symbol, SUM(shares) AS shares FROM transactions WHERE username = ? GROUP BY symbol", db.execute("SELECT username FROM users WHERE id = ?", session['user_id'])[0]['username'])
    # for each stock, add the symbol name, current price, and total value based on lookup
    for row in data:
        stockInfo = lookup(row['symbol'])
        row['name'] = row['symbol']
        row['price'] = stockInfo['price']
        row['total'] = row['shares'] * row['price']
    return data

def getCash(user_id):
    return db.execute("SELECT cash FROM users WHERE id = ?",session['user_id'])[0]['cash']

def getTotal(user_id):
    data = portfolio(session['user_id'])
    total = 0
    for row in data:
        total += row['total']
    total += getCash(user_id)
    return total


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    return render_template("history.html", data=getHistory(session['user_id']))

def getHistory(user_id):
    username = db.execute("SELECT username FROM users WHERE id = ?", user_id)[0]['username']
    return db.execute("Select * FROM transactions WHERE username = ? ORDER BY time", username)

@app.route("/password", methods=["GET", "POST"])
@login_required
def password_change():
    """Allow user to change password"""
    if request.method == "POST":
        password = request.form.get("password")
        password_again = request.form.get("password_again")
        if password == password_again:
            if len(password) > 5:
                db.execute("UPDATE users SET hash = ? WHERE id = ?", generate_password_hash(password), session['user_id'])
                render_template("index.html")
            else:
                return apology("password must be greater than 5 characters")
        else:
            return apology("passwords do not match")
    return render_template("password.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.form.get("symbol"):
        symbol = lookup(request.form.get("symbol").strip())
    else:
        symbol = None

    if request.method == "POST" and symbol == None:
        return apology("Symbol not found")
    elif request.method == "POST":
        return render_template("quoted.html", data=symbol)

    return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")
        password_again = request.form.get("confirmation")

        rows = db.execute('SELECT * FROM users WHERE username = ?', username)


        if not username:
            return apology("Username must not be blank")
        elif len(rows) > 0:
            return apology("Username already exists")
        elif (password != password_again):
            return apology("Passwords do not match")
        elif (len(password) < 1 or len(password_again) < 1 or len(username) < 1):
            return apology("All fields must be populated")
        else:

            # Add user to password database
            db.execute("INSERT INTO users (username, hash, cash) VALUES (?, ?, ?)", username, generate_password_hash(password), 10000.00)

            # Redirect user to home page
            return redirect("/")
    else:
        return render_template("register.html")



@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "POST":

        symbol = request.form.get("symbol")
        qty = float(request.form.get("shares"))
        username = db.execute("SELECT username FROM users WHERE id = ?", session['user_id'])[0]['username']
        price = lookup(symbol)['price']
        # calculate number of stocks the user owns to ensure they own enough to sell
        userStockQTY = db.execute("SELECT SUM(shares) AS shares FROM transactions WHERE username = ? AND symbol = ?", username, symbol)[0]['shares']


        if userStockQTY >= qty:
            # log transaction as negative trade
            db.execute("INSERT INTO transactions (username, symbol, shares, price) VALUES (?, ?, ?, ?)", username, symbol, -(qty), price)
            # update cash balance
            db.execute("UPDATE users SET cash = ? WHERE username=?", getCash(session['user_id']) + price * qty, username)
            return render_template("index.html", data=portfolio(session['user_id']), cash=usd(getCash(session['user_id'])), total=usd(getTotal(session['user_id'])))
        else:
            return apology("You don't own that many shares")

    return render_template("sell.html", symbols=getSymbols(session['user_id']))

def getSymbols(user_id):
    """Returns a list of the unique stocks a user owns"""
    return db.execute("Select DISTINCT symbol FROM transactions WHERE username = ?", db.execute("SELECT username FROM users WHERE id = ?", session['user_id'])[0]['username'])
