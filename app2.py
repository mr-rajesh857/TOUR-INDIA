from flask import Flask, render_template, request, redirect, url_for, flash,session , jsonify
from flask_pymongo import PyMongo
import datetime
from werkzeug.security import generate_password_hash, check_password_hash 
import smtplib
from flask_mail import Mail, Message
from functools import wraps
import random
import string

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


# Configure Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # For Gmail
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'rajeshkumarpanda235@gmail.com'
app.config['MAIL_PASSWORD'] = 'pmje ybac glnn wygd'  
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

# login and signup form 
# ================================

@app.route("/register", methods=["POST"])
def register():
    # if 'user' in session:  # If the user is already logged in
    #     return redirect(url_for('home')) 
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')

    if not name or not email or not password:
        flash("All fields are required!", "error")
        return redirect(url_for('login'))

    if user_collection.find_one({"email": email}):
        flash("Email is already registered!", "error")
        return redirect(url_for('login'))
    
    if email in user_collection  and user_collection [email] == password:
            session['user'] = email  # Store user email in the session
            return redirect(url_for('home'))  # Redirect to home or rental page after login
    else:
            return "Invalid credentials", 401

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


@app.route('/search', methods=['GET', 'POST'])
def bike_rental():
    if request.method == 'POST':
        bike_name = request.form.get('bike')
        check_in = request.form.get('check_in')
        check_out = request.form.get('check_out')
        user_email = request.form.get('email')

        # Validate if user exists in the database
        user = user_collection.find_one({"email": user_email})
        if not user:
            flash("You need to log in first!", "error")
            return redirect(url_for('login'))  # Redirect to login page

        # Validate required fields
        if not bike_name or not check_in or not check_out:
            flash("All fields are required!", "error")
            return redirect(url_for('index'))

        # Convert check-in and check-out dates to datetime objects
        try:
            check_in_date = datetime.datetime.strptime(check_in, '%m/%d/%Y %I:%M %p')
            check_out_date = datetime.datetime.strptime(check_out, '%m/%d/%Y %I:%M %p')
        except ValueError:
            flash("Invalid date format! Please use MM/DD/YYYY HH:MM AM/PM.", "error")
            return redirect(url_for('index'))

        # Ensure check-out date is after check-in date
        if check_out_date <= check_in_date:
            flash("Check-out date must be after check-in date.", "error")
            return redirect(url_for('index'))

        # Insert data into the bookings collection
        try:
            rental_data = {
                "email": user_email,
                "bike_name": bike_name,
                "check_in": check_in_date,
                "check_out": check_out_date
            }
            booking_collection.insert_one(rental_data)
            flash("Bike rental successful!", "success")
            print("✅ Data inserted successfully:", rental_data)
            return redirect(url_for('thanku'))  # Redirect to confirmation page
        except Exception as e:
            print("❌ Error inserting data:", e)
            flash(f"Database Error: {str(e)}", "error")
            return redirect(url_for('index'))

    return render_template('index.html')  # Renders the form

@app.route('/car_search', methods=['GET', 'POST'])
def car_rental():
    if request.method == 'POST':
        car_model = request.form.get('model')
        pickup_date = request.form.get('pickup_date')
        return_date = request.form.get('return_date')
        user_email = request.form.get('email')  # Get the email from the form

        # Check if the email exists in user_collection
        user = user_collection.find_one({"email": user_email})

        if not user:  # If the email does not exist in the user collection
            flash("You need to log in first!", "error")
            return redirect(url_for('login'))  # Redirect to login page

        # Check if any field is empty (car_model, pickup_date, return_date)
        if not car_model or not pickup_date or not return_date:
            flash("All fields are required!", "error")
            return redirect(url_for('index'))  # Redirect back to the form if missing fields

        # Convert pickup_date and return_date to date format if needed, or do other validations here
        try:
            # pickup_date_parsed = datetime.datetime.strptime(pickup_date, '%m/%d/%Y')
            # return_date_parsed = datetime.datetime.strptime(return_date, '%m/%d/%Y')
            pickup_date_parsed = datetime.datetime.strptime(pickup_date, '%m/%d/%Y %I:%M %p')
            return_date_parsed = datetime.datetime.strptime(return_date, '%m/%d/%Y %I:%M %p')
        except ValueError:
            flash("Invalid date format! Please use MM/DD/YYYY HH:MM AM/PM.", "error")
            return redirect(url_for('index'))  # Redirect back if dates are invalid

        # If all fields are valid, proceed with rental and store the data in the car collection
        rental_data = {
            "email": user_email,
            "car_model": car_model,
            "pickup_date": pickup_date_parsed,
            "return_date": return_date_parsed
        }
        car_collection.insert_one(rental_data)

        flash("Car rental successful!", "success")
        return redirect(url_for('thanku'))  # Redirect to a confirmation page

    return render_template('index.html')  # Render the car rental page for GET request

@app.route('/search', methods=['GET', 'POST'])
def bike_rental():
    if request.method == 'POST':
        bike_name = request.form.get('Bike')
        check_in = request.form.get('check_in')
        check_out = request.form.get('check_out')
        user_email = request.form.get('email')  # Get the email from the form

        # Check if the email exists in user_collection
        user = user_collection.find_one({"email": user_email})

        if not user:  # If the email does not exist in the user collection
            flash("You need to log in first!", "error")
            return redirect(url_for('login'))  # Redirect to login page

        # If the email exists, proceed with rental and store the data in the booking collection
        rental_data = {
            "email": user_email,
            "bike_name": bike_name,
            "check_in": check_in,
            "check_out": check_out
        }
        booking_collection.insert_one(rental_data)

        flash("Bike rental successful!", "success")
        return redirect(url_for('thanku'))  # Redirect to a confirmation page

    return render_template('index.html')  # Render the bike rental page for GET request


@app.route('/car_search', methods=['GET', 'POST'])
def car_rental():
    if request.method == 'POST':
        car_model = request.form.get('model')
        pickup_date = request.form.get('pickup_date')
        return_date = request.form.get('return_date')
        user_email = request.form.get('email')  # Get the email from the form

        # Check if the email exists in user_collection
        user = user_collection.find_one({"email": user_email})

        if not user:  # If the email does not exist in the user collection
            flash("You need to log in first!", "error")
            return redirect(url_for('login'))  # Redirect to login page

        # If the email exists, proceed with rental and store the data in the car collection
        rental_data = {
            "email": user_email,
            "car_model": car_model,
            "pickup_date": pickup_date,
            "return_date": return_date
        }
        car_collection.insert_one(rental_data)

        flash("Car rental successful!", "success")
        return redirect(url_for('thanku'))  # Redirect to a confirmation page

    return render_template('index.html')  # Render the car rental page for GET request

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
