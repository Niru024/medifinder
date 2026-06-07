from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import sqlite3
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "medifinder-dev-secret-key")
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "medifinder.db")


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS medicines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        medicine_name TEXT NOT NULL,
        company_name TEXT,
        dosage TEXT,
        store_name TEXT NOT NULL,
        contact TEXT,
        address TEXT,
        stock_status TEXT NOT NULL,
        quantity INTEGER DEFAULT 0,
        updated_at TEXT NOT NULL
    )
    """)

    # Seed default admin if not present
    admin = cur.execute("SELECT * FROM admins WHERE username = ?", ("admin",)).fetchone()
    if admin is None:
        cur.execute(
            "INSERT INTO admins (username, password, created_at) VALUES (?, ?, ?)",
            ("admin", generate_password_hash("admin123"), datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )

    # Seed demo medicines if table is empty
    count = cur.execute("SELECT COUNT(*) AS c FROM medicines").fetchone()["c"]
    if count == 0:
        demo_data = [
            ("Paracetamol", "Cipla", "500 mg", "City Pharmacy", "9876543210", "Pune Station Road", "Available", 120),
            ("Amoxicillin", "Alkem", "250 mg", "HealthCare Medical", "9123456780", "Shivaji Nagar", "Available", 40),
            ("Cetirizine", "Sun Pharma", "10 mg", "Wellness Medico", "9988776655", "Kothrud", "Out of Stock", 0),
            ("Pantoprazole", "Dr. Reddy's", "40 mg", "MediPoint", "9090909090", "Hadapsar", "Available", 25),
        ]
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cur.executemany(
            """INSERT INTO medicines
               (medicine_name, company_name, dosage, store_name, contact, address, stock_status, quantity, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [(m, c, d, s, ct, a, st, q, now) for (m, c, d, s, ct, a, st, q) in demo_data],
        )

    conn.commit()
    conn.close()


@app.before_request
def ensure_db():
    if not os.path.exists(DB_PATH):
        init_db()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/help")
def help_page():
    return render_template("help.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        if not name or not email or not password:
            flash("All fields are required.", "danger")
            return redirect(url_for("register"))

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "danger")
            return redirect(url_for("register"))

        conn = get_db_connection()
        existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            conn.close()
            flash("Email already exists. Please login.", "warning")
            return redirect(url_for("login"))

        conn.execute(
            "INSERT INTO users (name, email, password, created_at) VALUES (?, ?, ?, ?)",
            (name, email, generate_password_hash(password), datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )
        conn.commit()
        conn.close()

        flash("Registration successful. Please login.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["user_email"] = user["email"]
            session["role"] = "user"
            flash("Login successful.", "success")
            return redirect(url_for("dashboard"))

        flash("Invalid email or password.", "danger")
        return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


def login_required(view_func):
    from functools import wraps

    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if session.get("role") != "user":
            flash("Please login first.", "warning")
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)

    return wrapper


def admin_required(view_func):
    from functools import wraps

    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if session.get("role") != "admin":
            flash("Please login as admin first.", "warning")
            return redirect(url_for("admin_login"))
        return view_func(*args, **kwargs)

    return wrapper


@app.route("/dashboard")
@login_required
def dashboard():
    q = request.args.get("q", "").strip()
    medicines = []
    searched = False

    if q:
        searched = True
        conn = get_db_connection()
        medicines = conn.execute(
            """
            SELECT * FROM medicines
            WHERE LOWER(medicine_name) LIKE ?
               OR LOWER(company_name) LIKE ?
            ORDER BY medicine_name ASC
            """,
            (f"%{q.lower()}%", f"%{q.lower()}%"),
        ).fetchall()
        conn.close()

    return render_template("dashboard.html", medicines=medicines, searched=searched, query=q)


@app.route("/search", methods=["POST"])
@login_required
def search():
    q = request.form.get("query", "").strip()
    return redirect(url_for("dashboard", q=q))


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        conn = get_db_connection()
        admin = conn.execute("SELECT * FROM admins WHERE username = ?", (username,)).fetchone()
        conn.close()

        if admin and check_password_hash(admin["password"], password):
            session["admin_id"] = admin["id"]
            session["admin_username"] = admin["username"]
            session["role"] = "admin"
            flash("Admin login successful.", "success")
            return redirect(url_for("admin_dashboard"))

        flash("Invalid admin credentials.", "danger")
        return redirect(url_for("admin_login"))

    return render_template("admin_login.html")


@app.route("/admin/logout")
def admin_logout():
    session.clear()
    flash("Admin logged out.", "info")
    return redirect(url_for("admin_login"))


@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    conn = get_db_connection()
    medicines = conn.execute("SELECT * FROM medicines ORDER BY updated_at DESC").fetchall()
    conn.close()
    return render_template("admin_dashboard.html", medicines=medicines)


@app.route("/admin/add", methods=["GET", "POST"])
@admin_required
def add_medicine():
    if request.method == "POST":
        medicine_name = request.form.get("medicine_name", "").strip()
        company_name = request.form.get("company_name", "").strip()
        dosage = request.form.get("dosage", "").strip()
        store_name = request.form.get("store_name", "").strip()
        contact = request.form.get("contact", "").strip()
        address = request.form.get("address", "").strip()
        stock_status = request.form.get("stock_status", "Available").strip()
        quantity = request.form.get("quantity", "0").strip()

        if not medicine_name or not store_name:
            flash("Medicine name and store name are required.", "danger")
            return redirect(url_for("add_medicine"))

        conn = get_db_connection()
        conn.execute(
            """
            INSERT INTO medicines
            (medicine_name, company_name, dosage, store_name, contact, address, stock_status, quantity, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                medicine_name, company_name, dosage, store_name, contact, address,
                stock_status, int(quantity or 0), datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ),
        )
        conn.commit()
        conn.close()

        flash("Medicine added successfully.", "success")
        return redirect(url_for("admin_dashboard"))

    return render_template("add_medicine.html")


@app.route("/admin/edit/<int:medicine_id>", methods=["GET", "POST"])
@admin_required
def edit_medicine(medicine_id):
    conn = get_db_connection()
    medicine = conn.execute("SELECT * FROM medicines WHERE id = ?", (medicine_id,)).fetchone()

    if not medicine:
        conn.close()
        flash("Medicine not found.", "danger")
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        medicine_name = request.form.get("medicine_name", "").strip()
        company_name = request.form.get("company_name", "").strip()
        dosage = request.form.get("dosage", "").strip()
        store_name = request.form.get("store_name", "").strip()
        contact = request.form.get("contact", "").strip()
        address = request.form.get("address", "").strip()
        stock_status = request.form.get("stock_status", "Available").strip()
        quantity = request.form.get("quantity", "0").strip()

        conn.execute(
            """
            UPDATE medicines
            SET medicine_name=?, company_name=?, dosage=?, store_name=?, contact=?, address=?, stock_status=?, quantity=?, updated_at=?
            WHERE id=?
            """,
            (
                medicine_name, company_name, dosage, store_name, contact, address,
                stock_status, int(quantity or 0), datetime.now().strftime("%Y-%m-%d %H:%M:%S"), medicine_id
            ),
        )
        conn.commit()
        conn.close()

        flash("Medicine updated successfully.", "success")
        return redirect(url_for("admin_dashboard"))

    conn.close()
    return render_template("edit_medicine.html", medicine=medicine)


@app.route("/admin/delete/<int:medicine_id>")
@admin_required
def delete_medicine(medicine_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM medicines WHERE id = ?", (medicine_id,))
    conn.commit()
    conn.close()
    flash("Medicine deleted successfully.", "success")
    return redirect(url_for("admin_dashboard"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
