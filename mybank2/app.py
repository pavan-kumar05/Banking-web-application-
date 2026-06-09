from flask import Flask, Response, render_template, request, redirect, session, flash, jsonify
from dbConn import getConnection

app = Flask(__name__)
app.secret_key = "bank_secret_key"


@app.route("/admin/dashboard")
def adminDashboard():
    if "admin" not in session:
        return redirect("/")

    conn = getConnection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM customers")
    customers = cur.fetchall()
    conn.close()

    return render_template("adminDashboard.html", customers=customers)


# ------------------- HOME -------------------
@app.route("/")
def home():
    return render_template("home.html")


# ------------------- SIGNUP -------------------
@app.route("/submit", methods=["POST"])
def submitSignup():
    option = request.form.get("option")   # Admin / User
    email = request.form.get("email")
    user = request.form.get("user")
    password = request.form.get("pass")
    print(option,email,user,password)

    if not option or not email or not user or not password:
        flash("All fields are required", "error")
        return redirect("/")

    conn = getConnection()
    cur = conn.cursor()

    try:
        # ---- ADMIN SIGNUP ----
        if option == "Admin":
            cur.execute("""
                CREATE TABLE IF NOT EXISTS admin (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    email VARCHAR(50) UNIQUE,
                    username VARCHAR(50) UNIQUE,
                    password VARCHAR(50) NOT NULL
                )
            """)

            cur.execute(
                "INSERT INTO admin (email, username, password) VALUES (%s, %s, %s)",
                (email, user, password)
            )

            flash("Admin Registered Successfully", "success")

        # ---- USER SIGNUP ----
        elif option == "User":
            cur.execute("""
                CREATE TABLE IF NOT EXISTS customers (
                    accno INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(50),
                    email VARCHAR(50) UNIQUE,
                    password VARCHAR(50),
                    balance DOUBLE DEFAULT 0
                )
            """)

            cur.execute(
                "INSERT INTO customers (name, email, password) VALUES (%s, %s, %s)",
                (user, email, password)
            )

            flash("Customer Registered Successfully", "success")

        else:
            flash("Please select Admin or User", "error")
            return redirect("/")

        conn.commit()

    except Exception as e:
        conn.rollback()
        flash(f"Signup Failed: {e}", "error")

    finally:
        cur.close()
        conn.close()

    return redirect("/")

# ------------------- LOGIN -------------------
@app.route("/login", methods=["POST"])
def login():
    option = request.form.get("option")
    user_or_acc = request.form.get("user")
    password = request.form.get("pass")

    conn = getConnection()
    cur = conn.cursor(dictionary=True)

    if option == "Admin":
        cur.execute(
            "SELECT * FROM admin WHERE username=%s AND password=%s",
            (user_or_acc, password)
        )
        admin = cur.fetchone()
        conn.close()

        if admin:
            session["admin"] = admin["username"]
            flash("Admin Login Successful", "success")
            return redirect("/admin/dashboard")
        else:
            flash("Invalid Admin Credentials", "error")
            return redirect("/")

    elif option == "User":
        try:
            accno = int(user_or_acc)
        except ValueError:
            flash("Please enter a valid Account Number", "error")
            return redirect("/")

        cur.execute(
            "SELECT * FROM customers WHERE accno=%s AND password=%s",
            (accno, password)
        )
        customer = cur.fetchone()
        conn.close()

        if customer:
            session["customer"] = customer["accno"]
            flash("Customer Login Successful", "success")
            return redirect("/customer/dashboard")
        else:
            flash("Invalid Account Number or Password", "error")
            return redirect("/")

    else:
        conn.close()
        flash("Please select Login Type", "error")
        return redirect("/")

@app.route("/admin/deposit", methods=["POST"])
def adminDeposit():
    acc = request.form["acc"]
    amt = float(request.form["amt"])

    conn = getConnection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE customers SET balance = balance + %s WHERE accno=%s",
        (amt, acc)
    )
    conn.commit()
    conn.close()

    flash("Deposit Successful", "success")
    return redirect("/admin/dashboard")



@app.route("/admin/withdraw", methods=["POST"])
def adminWithdraw():
    acc = request.form["acc"]
    amt = float(request.form["amt"])

    conn = getConnection()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT balance FROM customers WHERE accno=%s", (acc,))
    customer = cur.fetchone()

    if not customer or customer["balance"] < amt:
        flash("Insufficient Balance", "error")
        conn.close()
        return redirect("/admin/dashboard")

    cur.execute(
        "UPDATE customers SET balance = balance - %s WHERE accno=%s",
        (amt, acc)
    )

    conn.commit()
    conn.close()

    flash("Withdraw Successful", "success")
    return redirect("/admin/dashboard")


@app.route("/customer/withdraw", methods=["POST"])
def customerWithdraw():
    accno = session["customer"]
    amt = float(request.form["amount"])

    conn = getConnection()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT balance FROM customers WHERE accno=%s", (accno,))
    bal = cur.fetchone()["balance"]

    if bal < amt:
        flash("Insufficient Balance", "error")
        return redirect("/customer/dashboard")

    newbal = bal - amt

    cur.execute("UPDATE customers SET balance=%s WHERE accno=%s", (newbal, accno))
    cur.execute("""
        INSERT INTO transactions(accno,type,amount,balance)
        VALUES(%s,'WITHDRAW',%s,%s)
    """, (accno, amt, newbal))

    conn.commit()
    conn.close()
    return redirect("/customer/dashboard")

    
@app.route("/customer/deposit", methods=["POST"])
def customerDeposit():
    accno = session["customer"]
    amt = float(request.form["amount"])

    conn = getConnection()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT balance FROM customers WHERE accno=%s", (accno,))
    bal = cur.fetchone()["balance"]
    newbal = bal + amt

    cur.execute("UPDATE customers SET balance=%s WHERE accno=%s", (newbal, accno))
    cur.execute("""
        INSERT INTO transactions(accno,type,amount,balance)
        VALUES(%s,'DEPOSIT',%s,%s)
    """, (accno, amt, newbal))

    conn.commit()
    conn.close()
    return redirect("/customer/dashboard")


@app.route("/admin/transfer", methods=["POST"])
def adminTransfer():
    sender = request.form["sender"]
    receiver = request.form["receiver"]
    amt = float(request.form["amt"])

    conn = getConnection()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT balance FROM customers WHERE accno=%s", (sender,))
    s = cur.fetchone()

    cur.execute("SELECT balance FROM customers WHERE accno=%s", (receiver,))
    r = cur.fetchone()

    if not s or not r or s["balance"] < amt:
        flash("Transfer Failed", "error")
        conn.close()
        return redirect("/admin/dashboard")

    cur.execute(
        "UPDATE customers SET balance = balance - %s WHERE accno=%s",
        (amt, sender)
    )
    cur.execute(
        "UPDATE customers SET balance = balance + %s WHERE accno=%s",
        (amt, receiver)
    )

    conn.commit()
    conn.close()

    flash("Transfer Successful", "success")
    return redirect("/admin/dashboard")


    


# ------------------- ADMIN DASHBOARD -------------------


# ------------------- CREATE CUSTOMER -------------------
@app.route("/admin/createCustomer", methods=["POST"])
def createCustomer():
    accno = request.form.get("accno")
    name = request.form.get("name")
    mobile = request.form.get("mobile")
    email = request.form.get("email")
    balance = request.form.get("balance")

    if not all([accno, name, mobile, email, balance]):
        flash("All fields are required!", "error")
        return redirect("/admin/dashboard")

    balance = float(balance)
    password = name[:3] + "@" + mobile[:4]

    conn = getConnection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO customers(accno,name,mobile,email,password,balance)
        VALUES(%s,%s,%s,%s,%s,%s)
    """, (accno, name, mobile, email, password, balance))
    conn.commit()
    conn.close()

    flash("Customer Created Successfully", "success")
    return redirect("/admin/dashboard")


# ------------------- DELETE CUSTOMER -------------------
@app.route("/admin/deleteCustomer/<int:accno>")
def deleteCustomer(accno):
    if "admin" not in session:
        return redirect("/")

    conn = getConnection()
    cur = conn.cursor()
    cur.execute("DELETE FROM customers WHERE accno=%s", (accno,))
    conn.commit()
    conn.close()

    flash("Customer Deleted", "success")
    return redirect("/admin/dashboard")


# ------------------- GET CUSTOMER DETAILS FOR UPDATE -------------------
@app.route("/admin/getCustomer/<int:accno>")
def getCustomer(accno):
    if "admin" not in session:
        return redirect("/")

    conn = getConnection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM customers WHERE accno=%s", (accno,))
    customer = cur.fetchone()
    conn.close()

    return jsonify(customer)  # Return as JSON for AJAX


# ------------------- UPDATE CUSTOMER -------------------
@app.route("/admin/updateCustomer", methods=["POST"])
def updateCustomer():
    if "admin" not in session:
        return redirect("/")

    accno = request.form["accno"]
    name = request.form["name"]
    mobile = request.form["mobile"]
    email = request.form["email"]
    balance = request.form["balance"]

    conn = getConnection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE customers
        SET name=%s, mobile=%s, email=%s, balance=%s
        WHERE accno=%s
    """, (name, mobile, email, balance, accno))
    conn.commit()
    conn.close()

    flash("Customer Updated Successfully", "success")
    return redirect("/admin/dashboard")


# ------------------- ADMIN LOGOUT -------------------
@app.route("/admin/logout")
def adminLogout():
    session.pop("admin", None)
    flash("Admin Logged Out", "success")
    return redirect("/")


# ------------------- CUSTOMER DASHBOARD -------------------
@app.route("/customer/dashboard")
def customerDashboard():
    if "customer" not in session:
        return redirect("/")

    accno = session["customer"]
    conn = getConnection()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT * FROM customers WHERE accno=%s", (accno,))
    customer = cur.fetchone()

    cur.execute("""
        SELECT * FROM transactions
        WHERE accno=%s
        ORDER BY created_at DESC
        LIMIT 10
    """, (accno,))
    transactions = cur.fetchall()

    conn.close()
    return render_template("customerDashboard.html",
                           customer=customer,
                           transactions=transactions)


# ------------------- CUSTOMER PROFILE -------------------
@app.route("/customer/profile")
def viewProfile():
    accno = session.get("customer")
    conn = getConnection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM customers WHERE accno=%s", (accno,))
    customer = cur.fetchone()
    conn.close()
    return render_template("profile.html", customer=customer)


# ------------------- CUSTOMER TRANSFER -------------------
@app.route("/customer/transfer", methods=["POST"])
def customerTransfer():
    sender = session["customer"]
    receiver = request.form["receiver"]
    amt = float(request.form["amount"])

    conn = getConnection()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT balance FROM customers WHERE accno=%s", (sender,))
    sbal = cur.fetchone()["balance"]

    if sbal < amt:
        flash("Insufficient Balance", "error")
        return redirect("/customer/dashboard")

    cur.execute("SELECT balance FROM customers WHERE accno=%s", (receiver,))
    r = cur.fetchone()

    if not r:
        flash("Receiver not found", "error")
        return redirect("/customer/dashboard")

    cur.execute("UPDATE customers SET balance=balance-%s WHERE accno=%s", (amt, sender))
    cur.execute("UPDATE customers SET balance=balance+%s WHERE accno=%s", (amt, receiver))

    cur.execute("""
        INSERT INTO transactions VALUES
        (NULL,%s,'TRANSFER-DEBIT',%s,%s,NOW())
    """, (sender, amt, sbal-amt))

    cur.execute("""
        INSERT INTO transactions VALUES
        (NULL,%s,'TRANSFER-CREDIT',%s,%s,NOW())
    """, (receiver, amt, r["balance"]+amt))

    conn.commit()
    conn.close()
    return redirect("/customer/dashboard")

# ------------------- CUSTOMER TRANSACTIONS -------------------
@app.route("/customer/transactions")
def customerTransactions():
    accno = session.get("customer")
    conn = getConnection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT * FROM transactions
        WHERE accno=%s
        ORDER BY created_at DESC
        LIMIT 10
    """, (accno,))
    transactions = cur.fetchall()
    conn.close()
    return render_template("transactions.html", transactions=transactions)


# ------------------- CUSTOMER PASSWORD -------------------
@app.route("/customer/updatePassword", methods=["POST"])
def updatePassword():
    accno = session["customer"]
    newpass = request.form["newpass"]

    conn = getConnection()
    cur = conn.cursor()
    cur.execute("UPDATE customers SET password=%s WHERE accno=%s", (newpass, accno))
    conn.commit()
    conn.close()

    flash("Password Updated", "success")
    return redirect("/customer/dashboard")


@app.route("/customer/download-transactions")
def downloadTransactions():
    accno = session["customer"]
    conn = getConnection()
    cur = conn.cursor()

    cur.execute("""
        SELECT created_at,type,amount,balance
        FROM transactions
        WHERE accno=%s
        ORDER BY created_at DESC
        LIMIT 10
    """, (accno,))
    rows = cur.fetchall()
    conn.close()

    content = "Date,Type,Amount,Balance\n"
    for r in rows:
        content += f"{r[0]},{r[1]},{r[2]},{r[3]}\n"

    return Response(
        content,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=transactions.csv"}
    )

@app.route("/admin/viewTransactions", methods=["POST"])
def adminViewTransactions():
    if "admin" not in session:
        return redirect("/")

    accno = request.form.get("accno")
    txn_type = request.form.get("type")

    conn = getConnection()
    cur = conn.cursor(dictionary=True)

    query = "SELECT * FROM transactions WHERE 1=1"
    params = []

    if accno:
        query += " AND accno=%s"
        params.append(accno)

    if txn_type != "ALL":
        if txn_type == "TRANSFER":
            query += " AND type LIKE %s"
            params.append("%TRANSFER%")
        else:
            query += " AND type=%s"
            params.append(txn_type)

    query += " ORDER BY created_at DESC"

    cur.execute(query, tuple(params))
    transactions = cur.fetchall()

    cur.execute("SELECT * FROM customers")
    customers = cur.fetchall()

    conn.close()

    return render_template(
        "adminDashboard.html",
        customers=customers,
        transactions=transactions
    )



# ------------------- CUSTOMER LOGOUT -------------------
@app.route("/customer/logout")
def customerLogout():
    session.pop("customer", None)
    flash("Customer Logged Out", "success")
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)
