from flask import Flask, render_template, request, redirect, url_for, flash,session
from flask_pymongo import PyMongo
import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for flash messages

# MongoDB connection
app.config["MONGO_URI"] = "mongodb://localhost:27017/travelDB"  # Replace with your MongoDB URI if different
mongo = PyMongo(app)

# Define collections within the MongoDB database
# hotel_collection = mongo.db.hotel
user_collection = mongo.db.users
booking_collection = mongo.db.bookings
car_collection = mongo.db.cars
email_verify_collection = mongo.db.email_verify

@app.route("/")
def index():
    message = request.args.get('message')  # Get the message from the query parameter
    return render_template("index.html", message=message)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/tours")
def tours():
    return render_template("tours.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/favorites")
def favorites():
    return render_template("favorites.html")

@app.route("/budget")
def budget():
    return render_template("budget.html")
@app.route("/thanku")
def thanku():
    return render_template("thanku.html")

@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/travel")
def travel():
    return render_template("travel.html")


# login and signup form 
# ================================

@app.route("/register", methods=["POST"])
def register():
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')

    if not name or not email or not password:
        flash("All fields are required!", "error")
        return redirect(url_for('login'))

    if user_collection.find_one({"email": email}):
        flash("Email is already registered!", "error")
        return redirect(url_for('login'))

    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
    user_collection.insert_one({"name": name, "email": email, "password": hashed_password})

    flash("Account created successfully! Please log in.", "success")
    return redirect(url_for('login'))

@app.route("/signin", methods=["POST"])
def signin():
    email = request.form.get('email')
    password = request.form.get('password')

    if not email or not password:
        flash("All fields are required!", "error")
        return redirect(url_for('login'))

    user = user_collection.find_one({"email": email})
    if user and check_password_hash(user["password"], password):
        session['user_id'] = str(user['_id'])
        session['username'] = user['name']
        flash("Logged in successfully!", "success")
        return redirect(url_for('index'))
    else:
        flash("Invalid email or password!", "error")
        return redirect(url_for('login'))


#hotel form:-
# ======================

@app.route("/search", methods=["POST"])
def search():
    hotel_name = request.form.get('hotel_name')
    check_in = request.form.get('check_in')
    check_out = request.form.get('check_out')
    guests = request.form.get('guests')

    # Check for missing form data
    # if not hotel_name or not check_in or not check_out or not guests:
    #     flash("All fields are required!")
    #     return redirect(url_for('index'))

    try:
        # Parse the dates
        check_in_date = datetime.datetime.strptime(check_in, '%m/%d/%Y')
        check_out_date = datetime.datetime.strptime(check_out, '%m/%d/%Y')

        # Create a document to insert into the MongoDB collection
        booking_data = {
            "hotel_name": hotel_name,
            "check_in": check_in_date,
            "check_out": check_out_date,
            "guests": int(guests)
        }

        # Insert the document into the collection
        booking_collection.insert_one(booking_data)

        message = f"Your booking at {hotel_name} is confirmed from {check_in} to {check_out} for {guests} guest(s)."
        return redirect(url_for('thanku',message=message))
    except ValueError:
        flash("Invalid date format! Please use MM/DD/YYYY.")
        return redirect(url_for('index'))
    

#car form:-
# =====================
@app.route("/car_search", methods=["POST"])
def car_search():
    model = request.form.get('model')
    pickup_date = request.form.get('pickup_date')
    return_date = request.form.get('return_date')
    options = request.form.get('options')

    # Check for missing form data
    # if not model or not pickup_date or not return_date or not options:
    #     flash("All fields are required!")
    #     return redirect(url_for('index'))

    try:
        # Parse the dates
        pickup_date_parsed = datetime.datetime.strptime(pickup_date, '%m/%d/%Y %I:%M %p')
        return_date_parsed = datetime.datetime.strptime(return_date, '%m/%d/%Y %I:%M %p')

        # Create a document to insert into the MongoDB collection
        car_data = {
            "model": model,
            "pickup_date": pickup_date_parsed,
            "return_date": return_date_parsed,
            "options": options
        }

        # Insert the document into the collection
        car_collection.insert_one(car_data)

        return redirect(url_for('thanku'))
    except ValueError:
        flash("Invalid date format! Please use MM/DD/YYYY HH:MM AM/PM.")
        return redirect(url_for('index'))
    
#email form (footer):-
# =============================

@app.route("/subscribe", methods=["POST"])
def subscribe():
    email = request.form.get('newsletter')
    
    if not email:
        flash("Please enter a valid email address.", "error")
        return redirect(url_for('index'))

    if email_verify_collection.find_one({"email": email}):
        flash("This email is already subscribed.", "error")
        return redirect(url_for('index'))

    email_verify_collection.insert_one({"email": email, "date": datetime.datetime.utcnow()})
    flash("You have been subscribed to the newsletter!", "success")
    return redirect(url_for('thanku'))


if __name__ == "__main__":
    app.run(debug=True,port=4400)
