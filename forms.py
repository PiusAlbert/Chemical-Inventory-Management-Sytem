from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DateField, FloatField, FileField, PasswordField,SelectField, IntegerField
from wtforms.validators import DataRequired, URL


# Create a form to register new users
class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    name = StringField("Name", validators=[DataRequired()])
    submit = SubmitField("Sign Me Up!")

#Create a form to login existing users
class LoginForm(FlaskForm):
  email = StringField("Email", validators=[DataRequired()])
  password = PasswordField("Password", validators=[DataRequired()])
  submit = SubmitField("Let Me In!")


class AddStockForm(FlaskForm):
    product_id = SelectField("Select Product", coerce=int, validators=[DataRequired()])
    manufacture_date = DateField("Manufacture Date", validators=[DataRequired()])
    expiry_date = DateField("Expiry Date", validators=[DataRequired()])

    quantity_kg = FloatField("Total Quantity Received (Kg/L)", validators=[DataRequired()])
    drums = IntegerField("Drums (45kg, 200kg, 225kg)", default=0)
    bags = IntegerField("Bags (20kg, 25kg, 50kg)", default=0)
    jerrycans = IntegerField("Jerrycans (20kg, 25kg, 30kg)", default=0)

    msds_file = FileField("Upload MSDS (PDF)")
    coa_file = FileField("Upload COA (PDF)")

    submit = SubmitField("Add Stock")


class ProductMasterForm(FlaskForm):
    name = StringField("Product Name", validators=[DataRequired()])
    product_type = SelectField("Product Type", choices=[
        ("Disinfectant", "Disinfectant"),
        ("Coagulant", "Coagulant"),
        ("pH Adjuster", "pH Adjuster"),
        ("Flocculant", "Flocculant"),
        ("Corrosion Inhibitor", "Corrosion Inhibitor"),
        ("Oxygen Scavenger", "Oxygen Scavenger"),
        ("Oxidizer", "Oxidizer"),
        ("Floc Builder", "Floc Builder"),
        ("Adsorbent", "Adsorbent"),
    ], validators=[DataRequired()])
    origin_country = StringField("Country of Origin", validators=[DataRequired()])
    manufacturer_name = StringField("Manufacturer Name", validators=[DataRequired()])
    manufacturer_address = StringField("Manufacturer Address", validators=[DataRequired()])
    submit = SubmitField("Register Product")
