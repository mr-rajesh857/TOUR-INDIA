from flask import Flask, render_template, request, redirect, url_for, flash,session , jsonify
from flask_pymongo import PyMongo
import datetime
from werkzeug.security import generate_password_hash, check_password_hash 
import smtplib
from flask_mail import Mail, Message
import razorpay
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import random
import string
import pickle
import pandas as pd
import google.generativeai as genai
# from ml_model.model import predict_places

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for flash messages
genai.configure(api_key="YOUR_GEMINI_API_KEY")

# MongoDB connection
app.config["MONGO_URI"] = "mongodb://localhost:27017/travelDB"  # Replace with your MongoDB URI if different
mongo = PyMongo(app)

# Define collections within the MongoDB database
# hotel_collection = mongo.db.hotel
user_collection = mongo.db.users
booking_collection = mongo.db.bookings
car_collection = mongo.db.cars
email_verify_collection = mongo.db.email_verify


# Configure Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # For Gmail
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'YOUR EMAIL-ID'
app.config['MAIL_PASSWORD'] = 'YOUR EMAIL-ID SECRECT KEY'  
app.config['MAIL_DEFAULT_SENDER'] = 'rajeshkumarpanda235@gmail.com'

mail = Mail(app)

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

@app.route("/change_password")
def change_password_page():
    return render_template("password_change.html")

@app.route('/forgot_password', methods=['GET'])
def forgot_password_page():
    return render_template("forgot_password.html")

@app.route("/car-bike_Rental")
def car_bike_Rental():
    return render_template("car-bike_Rental.html")


# # Load the model
# model = pickle.load(open('tourism_model.pkl', 'rb'))
# vectorizer = pickle.load(open('vectorizer.pkl', 'rb'))
# # Load the dataset
# df = pd.read_csv('tourism1.csv')


# @app.route('/recommendation')
# def recommendation():
#     return render_template('recommendation.html')

# @app.route('/recommend', methods=['POST'])
# def recommend():
#     state = request.form['state'].strip().lower()
#     city = request.form['city'].strip().lower()

#     # Filter after converting both user input and dataframe columns to lowercase
#     result = df[(df['State'].str.lower() == state) & (df['City'].str.lower() == city)][['Place', 'Place_desc']].head(10)

#     if not result.empty:
#         places = result.values.tolist()
#     else:
#         places = []

#     return render_template('result1.html', state=state.title(), city=city.title(), places=places)

@app.route('/recommendation')
def recommendation():
    return render_template('recommendation.html')

@app.route('/recommend', methods=['POST'])
def recommend():
    state = request.form['state'].strip().title()
    city = request.form['city'].strip().title()

    prompt = (
        f"Recommend 5 tourist places in {city}, {state}, India. "
        f"For each place, provide a short description in the format: "
        f"Place Name: Short Description."
    )

    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(prompt)
        recommendations = response.text.strip()

       
        places = []
        for line in recommendations.split('\n'):
            line = line.strip()
            if not line:
                continue
            if '.' in line[:4]:  
                line = line.split('.', 1)[1].strip()
            if ':' in line:
                place_name, desc = line.split(':', 1)
                places.append([place_name.strip(), desc.strip()])

    except Exception as e:
        places = []
        recommendations = f"Error occurred: {e}"

    return render_template('result1.html', state=state, city=city, places=places)

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
        # Send a welcome email
        try:
            send_welcome_email(user['name'], email)
        except Exception as e:
            flash("Login successful, but email could not be sent.", "warning")
            print(f"Error sending email: {e}")
        return redirect(url_for('index'))
    else:
        flash("Invalid email or password!", "error")
        return redirect(url_for('login'))

def send_welcome_email(name, email):
    message = Message(
        subject="Welcome to Travel Website!",
        recipients=[email],
    )
    # HTML content for the email
    message.html = f"""
    <h1>Welcome, {name}!</h1>
    <p>Thank you for logging in to our website. We're thrilled to have you on board!</p>
    <p>Explore our <a href="{url_for('tours', _external=True)}">tours</a>, book a hotel, or check out our car rentals.</p>
    <p>Have questions? <a href="{url_for('contact', _external=True)}">Contact us</a>.</p>
    <br>
    <p>Best regards,<br>Travel Website Team</p>
    """
    mail.send(message)


   


@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        # Get email from the form
        email = request.form['email']

        # Find user by email
        user = user_collection.find_one({"email": email})
        
        if user:
            # Generate a random password
            new_password = generate_random_password()

            # Hash the new password
            hashed_password = generate_password_hash(new_password)

            # Update the password in the database
            user_collection.update_one({"email": email}, {"$set": {"password": hashed_password}})

            # Send the new password to the user's email
            try:
                send_new_password_email(user['name'], email, new_password)
                message = "A new password has been sent to your email."
                return render_template('forgot_password.html', message=message)
            except Exception as e:
                error = f"Error sending email: {str(e)}"
                return render_template('forgot_password.html', error=error)
        else:
            error = "Email not found."
            return render_template('forgot_password.html', error=error)

    return render_template('forgot_password.html')

def generate_random_password(length=8):
    """Generate a random password."""
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for i in range(length))

def send_new_password_email(name, email, new_password):
    """Send the new password to the user's email."""
    message = Message(
        subject="Your New Password",
        recipients=[email],
    )
    message.html = f"""
    <h1>Hello, {name}!</h1>
    <p>Your new password is: <strong>{new_password}</strong></p>
    <p>Please use this password to log in to your account. You may change it after logging in.</p>
    <br>
    <p>Best regards,<br>Travel Website Team</p>
    """
    mail.send(message)



@app.route("/change_password", methods=["POST"])
def change_password():
    email = request.form.get('email')
    current_password = request.form.get('currentPassword')
    new_password = request.form.get('newPassword')
    confirm_password = request.form.get('confirmPassword')

    # Check if any of the fields are empty
    if not email or not current_password or not new_password or not confirm_password:
        flash("All fields are required!", "error")
        return redirect(url_for('change_password_page'))

    # Check if the new password and confirmation match
    if new_password != confirm_password:
        flash("New passwords do not match!", "error")
        return redirect(url_for('change_password_page'))

    # Find the user in the database
    user = user_collection.find_one({"email": email})
    if user and check_password_hash(user["password"], current_password):
        # Hash the new password
        hashed_new_password = generate_password_hash(new_password)

        # Update the password in the database
        user_collection.update_one({"email": email}, {"$set": {"password": hashed_new_password}})

        # Send confirmation email
        send_confirmation_email(email)

        flash("Password changed successfully! A confirmation email has been sent.", "success")
        return redirect(url_for('index'))
    else:
        flash("Invalid email or current password!", "error")
        return redirect(url_for('change_password_page'))

def send_confirmation_email(user_email):
    msg = Message('Password Change Confirmation',
                  recipients=[user_email])
    msg.body = 'Your password has been changed successfully. If you did not request this change, please contact support immediately.'
    mail.send(msg)





def book_vehicle():
    data = request.json
    email = data.get("email")
    vehicle = data.get("vehicle")
    vehicle_name = data.get("vehicle_name")
    price_per_hour = data.get("price_per_hour")
    pickup_time = datetime.strptime(data.get("pickup_time"), "%Y-%m-%dT%H:%M")
    return_time = datetime.strptime(data.get("return_time"), "%Y-%m-%dT%H:%M")
    
    total_hours = (return_time - pickup_time).total_seconds() / 3600
    total_price = round(total_hours * price_per_hour, 2)
    
    booking_data = {
        "email": email,
        "vehicle": vehicle,
        "vehicle_name": vehicle_name,
        "price_per_hour": price_per_hour,
        "pickup_time": pickup_time,
        "return_time": return_time,
        "total_price": total_price,
        "payment_status": "Pending"
    }
    mongo.db.bookings.insert_one(booking_data)
    
    return jsonify({"message": "Booking created", "total_price": total_price})

@app.route('/payment', methods=['POST'])
def process_payment():
    data = request.json
    email = data.get("email")
    total_price = data.get("total_price")

    try:
        return render_template("payment.html", email=email, total_price=total_price, razorpay_key="YOUR RAZORPAY SECRECT KEY")

    except Exception as e:
        print("Error:", str(e))
        return jsonify({"error": "Failed to load payment page", "details": str(e)}), 500

@app.route('/vehicles', methods=['GET'])
def get_vehicles():
    vehicles = list(mongo.db.vehicles.find({}, {"_id": 0}))
    return jsonify(vehicles)

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
