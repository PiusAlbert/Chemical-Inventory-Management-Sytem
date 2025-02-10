from datetime import date,timedelta
from fpdf import FPDF  # For PDF generation
import pandas as pd  # For Excel export
from functools import wraps
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, abort, send_file,send_from_directory
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, declarative_base, Mapped, mapped_column
from sqlalchemy import Integer, String, Float, Date, Column, ForeignKey
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from forms import RegisterForm, LoginForm, AddStockForm,ProductMasterForm
from config import Config
import os

app = Flask(__name__)
app.config.from_object(Config)



# Initialize extensions
ckeditor = CKEditor(app)
bootstrapp = Bootstrap5(app)
Base = declarative_base()
db = SQLAlchemy(app)
migrate = Migrate(app, db)  # Enables database migrations
login_manager = LoginManager()
login_manager.init_app(app)

# User loader function
@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)

def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "admin":
            return abort(403)  # Forbidden
        return f(*args, **kwargs)
    return decorated_function

# User Model
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(20), default="user")  # "admin" or "user"

    sales = relationship("Sales", back_populates="user")  # Relationship with Sales


class ProductMaster(db.Model):
    """Stores unique product names & details and links to inventory and sales."""
    __tablename__ = 'product_master'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)
    product_type = Column(String(255), nullable=False)  # e.g., Disinfectant, pH Adjuster
    origin_country = Column(String(100), nullable=False)
    manufacturer_name = Column(String(255), nullable=False)
    manufacturer_address = Column(String(255), nullable=False)

    # Relationship with Inventory (One product can have multiple inventory entries)
    inventories = relationship("Inventory", back_populates="product_master")

    # Relationship with Sales (A product can have multiple sales)
    sales = relationship("Sales", back_populates="product_master")


class Inventory(db.Model):
    """Handles product stock tracking and connects to ProductMaster and Sales."""
    __tablename__ = 'inventory'

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Link to ProductMaster
    product_id = Column(Integer, ForeignKey('product_master.id'), nullable=False)

    # Product Details (Retrieved from ProductMaster)
    product_name = Column(String(255), nullable=False)  # Redundant but useful for queries
    product_type = Column(String(255), nullable=False) 

    # Stock & Packaging
    quantity_kg = Column(Float, default=0)  # Available stock in KG/Liters
    drums = Column(Integer, default=0)  # 200kg, 225kg Drums
    bags = Column(Integer, default=0)  # 20kg, 25kg, 50kg Bags
    jerrycans = Column(Integer, default=0)  # 20kg, 25kg, 30kg Jerrycans

    # Expiry & Pricing
    manufacture_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=False) 
    
    # File Uploads (MSDS & COA)
    msds_path = Column(String(255))  # Material Safety Data Sheet
    coa_path = Column(String(255))   # Certificate of Analysis

    # Relationships
    product_master = relationship("ProductMaster", back_populates="inventories")
    sales = relationship("Sales", back_populates="inventory")
            
class Sales(db.Model):
    """Tracks sales transactions and updates stock levels automatically."""
    __tablename__ = 'sales'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Link to ProductMaster
    product_id = Column(Integer, ForeignKey('product_master.id'), nullable=False)
    
    # Link to Inventory (Specific stock being sold)
    inventory_id = Column(Integer, ForeignKey('inventory.id'), nullable=False)
    
    # Link to User (Who made the sale)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    client_name = Column(String(255), nullable=False)
    quantity_sold = Column(Float, nullable=False)  # Quantity sold in KG/Liters
    selling_price = Column(Float, nullable=False)
    sale_date = Column(Date, default=date.today, nullable=False)

    # Relationships
    product_master = relationship("ProductMaster", back_populates="sales")
    inventory = relationship("Inventory", back_populates="sales")
    user = relationship("User", back_populates="sales")


# Routes
@app.route('/')
def home():
    return redirect(url_for('login'))


@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        existing_user = db.session.execute(db.select(User).where(User.email == form.email.data)).scalar()
        if existing_user:
            flash("Email already exists, please log in.", "danger")
            return redirect(url_for('login'))
        
        hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256', salt_length=8)
        role = "admin" if db.session.query(User).count() == 0 else "user"  # First user is admin
        
        new_user = User(email=form.email.data, name=form.name.data, password=hashed_password, role=role)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        flash("Registration successful!", "success")
        return redirect(url_for('dashboard'))
    return render_template("register.html", form=form, background_image=url_for('static', filename='assets/img/register-bg.jpg'))


@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.execute(db.select(User).where(User.email == form.email.data)).scalar()
        if not user or not check_password_hash(user.password, form.password.data):
            flash("Invalid email or password. Try again.", "danger")
            return redirect(url_for('login'))
        login_user(user)
        flash("Login successful!", "success")
        return redirect(url_for('dashboard'))
    return render_template("login.html", form=form,background_image=url_for('static', filename='assets/img/login-bg.png'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.", "info")
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Count total registered products
    product_count = ProductMaster.query.count()

    # Count total sales transactions
    sales_count = Sales.query.count()

    # Count low stock products (Example: Below 100kg considered low stock)
    low_stock_count = Inventory.query.filter(Inventory.quantity_kg < 100).count()

    # Fetch inventory to display product names correctly
    inventories = db.session.query(
        Inventory.product_name,
        Inventory.product_type,
        Inventory.quantity_kg
    )

    return render_template(
        "dashboard.html",
        product_count=product_count,
        sales_count=sales_count,
        low_stock_count=low_stock_count,
        inventories=inventories,
        today=date.today(), background_image=url_for('static', filename='assets/img/dashboard-bg.jpg')
    )




@app.route('/register-product', methods=["GET", "POST"])
def register_product():
    form = ProductMasterForm()
    
    if form.validate_on_submit():
        new_product = ProductMaster(
            name=form.name.data,
            product_type=form.product_type.data,
            origin_country=form.origin_country.data,
            manufacturer_name=form.manufacturer_name.data,
            manufacturer_address=form.manufacturer_address.data
        )
        db.session.add(new_product)
        db.session.commit()
        flash("Product Registered Successfully!", "success")
        return redirect(url_for("register_product"))

    return render_template("register_product.html", form=form, background_image=url_for('static', filename='img/polydadmac-img.png'))

UPLOAD_FOLDER = "uploads/"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Ensure upload directory exist.

@app.route('/add-stock', methods=["GET", "POST"])
def add_stock():
    form = AddStockForm()
    form.product_id.choices = [(p.id, p.name) for p in ProductMaster.query.all()]  # Ensure choices are correct.

    if form.validate_on_submit():
        manufacture_date = form.manufacture_date.data
        expiry_date = form.expiry_date.data

        # Get product details from ProductMaster
        product = ProductMaster.query.get(form.product_id.data)
        if not product:
            flash("Selected product does not exist!", "danger")
            return redirect(url_for("add_stock"))

        # Handle File Uploads
        msds_filename = None
        coa_filename = None
        if form.msds_file.data:
            msds_filename = secure_filename(form.msds_file.data.filename)
            form.msds_file.data.save(os.path.join(app.config["UPLOAD_FOLDER"], msds_filename))

        if form.coa_file.data:
            coa_filename = secure_filename(form.coa_file.data.filename)
            form.coa_file.data.save(os.path.join(app.config["UPLOAD_FOLDER"], coa_filename))

        # Check if inventory exists
        inventory = Inventory.query.filter_by(product_id=form.product_id.data).first()
        if inventory:
            # Update existing inventory
            inventory.quantity_kg += form.quantity_kg.data
            inventory.drums += form.drums.data
            inventory.bags += form.bags.data
            inventory.jerrycans += form.jerrycans.data
            inventory.manufacture_date = manufacture_date
            inventory.expiry_date = expiry_date
            if msds_filename:
                inventory.msds_path = msds_filename
            if coa_filename:
                inventory.coa_path = coa_filename
        else:
            # Create new inventory entry
            inventory = Inventory(
                product_id=product.id,
                product_name=product.name,  # ✅ Correctly fetch product name
                product_type=product.product_type,  # ✅ Fetch product type
                quantity_kg=form.quantity_kg.data,
                drums=form.drums.data,
                bags=form.bags.data,
                jerrycans=form.jerrycans.data,
                manufacture_date=manufacture_date,
                expiry_date=expiry_date,
                msds_path=msds_filename,
                coa_path=coa_filename
            )
            db.session.add(inventory)

        db.session.commit()
        flash("Stock updated successfully!", "success")
        return redirect(url_for("add_stock"))

    return render_template("add_stock.html", form=form, background_image=url_for('static', filename='assets/img/add_stock-bg.jpg'))


@app.route('/view-stock')
def view_stock():
    inventories = Inventory.query.all()
    return render_template("view_stock.html", inventories=inventories, today=date.today(), background_image=url_for('static', filename='assets/img/view_stock-bg.jpeg'))

@app.route('/api/stock-levels', methods=['GET'])
def get_stock_levels():
    inventories = Inventory.query.all()
    stock_data = [{
        "id": inv.id,
        "type": inv.product_type,
        "stock": inv.quantity_kg
    } for inv in inventories]

    return jsonify(stock_data)


@app.route('/view-products')
def view_products():
    products = ProductMaster.query.all()
    return render_template("view_products.html", products=products, background_image=url_for('static', filename='assets/img/registered_products-bg.jpg'))

@app.route('/sales', methods=["GET", "POST"])
@login_required
def manage_sales():
    if request.method == "POST":
        inventory_id = request.form.get("inventory_id")
        client_name = request.form.get("client_name")
        quantity_sold = float(request.form.get("quantity_sold"))
        selling_price = float(request.form.get("selling_price"))

        inventory = Inventory.query.get(inventory_id)

        if not inventory or inventory.quantity_kg < quantity_sold:
            flash("Insufficient stock available!", "danger")
            return redirect(url_for("manage_sales"))

        # Deduct sold quantity from stock
        inventory.quantity_kg -= quantity_sold

        new_sale = Sales(
            inventory_id=inventory_id,
            user_id=current_user.id,
            client_name=client_name,
            quantity_sold=quantity_sold,
            selling_price=selling_price,
            sale_date=date.today()
        )

        db.session.add(new_sale)
        db.session.commit()
        flash("Sale recorded successfully!", "success")

        return redirect(url_for("manage_sales"))

    sales = Sales.query.all()
    inventories = Inventory.query.all()
    return render_template("sales.html", sales=sales, inventories=inventories)


@app.route('/stock-report', methods=["GET", "POST"])
def stock_report():
    selected_date = request.form.get("report_date", date.today())
    stock_data = Inventory.query.filter(Inventory.expiry_date >= selected_date).all()
    return render_template("stock_report.html", stock_data=stock_data, selected_date=selected_date)

@app.route('/stock-report/pdf')
def download_stock_report_pdf():
    """Generates and downloads the stock report as a PDF."""
    stock_data = Inventory.query.all()

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", style='B', size=16)
    pdf.cell(200, 10, "Stock Report", ln=True, align='C')

    pdf.set_font("Arial", size=12)
    pdf.ln(10)  # Line break

    # Table Header
    pdf.cell(40, 10, "Product", border=1)
    pdf.cell(30, 10, "Stock (Kg/L)", border=1)
    pdf.cell(20, 10, "Drums", border=1)
    pdf.cell(20, 10, "Bags", border=1)
    pdf.cell(20, 10, "Jerrycans", border=1)
    pdf.cell(40, 10, "Expiry Date", border=1)
    pdf.ln()

    # Table Rows
    for stock in stock_data:
        pdf.cell(40, 10, stock.product_name, border=1)
        pdf.cell(30, 10, str(stock.quantity_kg), border=1)
        pdf.cell(20, 10, str(stock.drums), border=1)
        pdf.cell(20, 10, str(stock.bags), border=1)
        pdf.cell(20, 10, str(stock.jerrycans), border=1)
        pdf.cell(40, 10, str(stock.expiry_date), border=1)
        pdf.ln()

    pdf_file = "stock_report.pdf"
    pdf.output(pdf_file)

    return send_file(pdf_file, as_attachment=True)

@app.route('/stock-report/excel')
def download_stock_report_excel():
    """Generates and downloads the stock report as an Excel file."""
    stock_data = Inventory.query.all()

    data = {
        "Product": [stock.product_name for stock in stock_data],
        "Stock (Kg/L)": [stock.quantity_kg for stock in stock_data],
        "Drums": [stock.drums for stock in stock_data],
        "Bags": [stock.bags for stock in stock_data],
        "Jerrycans": [stock.jerrycans for stock in stock_data],
        "Expiry Date": [stock.expiry_date for stock in stock_data],
    }

    df = pd.DataFrame(data)
    excel_file = "stock_report.xlsx"
    df.to_excel(excel_file, index=False)

    return send_file(excel_file, as_attachment=True)

@app.route('/download/<filename>')
def download_file(filename):
    """Allow users to download MSDS or COA files."""
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    
    if os.path.exists(file_path):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=True)
    else:
        abort(404)  # File not found error


# Create database tables
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
