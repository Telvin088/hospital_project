from flask import Flask, render_template, request, redirect, url_for, session, json, jsonify
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash
import os
import logging
from werkzeug.utils import secure_filename
import uuid
import hashlib
from datetime import datetime
from flask_mail import Mail, Message
import pytz
import base64
import requests


app = Flask(__name__, template_folder='templates')
app.secret_key = 'your_secret_key'


app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'rodneymwangi1810@gmail.com'
app.config['MAIL_PASSWORD'] = 'rbos loes riok vhku'

mail = Mail(app)


@app.route('/send-mail')
def send_mail(name, email, illness, date, time):
    msg = Message('Subject of the Email',
                  sender=app.config.get("MAIL_USERNAME"),
                  recipients=[email],
                  body = f"Dear {name} you have successfully booked for the issue {illness}. You have requested to see the doctor on {date} at {time}")
    mail.send(msg)
    return 'Email Sent!'

@app.route('/send-update-mail')
def send_update_mail(name, email, doctor_name, notes, bill, date):
    msg = Message('Subject of the Email',
                  sender=app.config.get("MAIL_USERNAME"),
                  recipients=[email],
                  body = f"Dear {name},\n You visited Dr. {doctor_name} on {date} and the following was recorded: \n\n {notes}\n\n. The bill was Ksh.{bill} was paid via MPESA")
    mail.send(msg)
    return 'Email Sent!'


UPLOAD_FOLDER = os.path.join('website', 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Database connection function


def create_connection():
    connection = None
    try:
        connection = mysql.connector.connect(
            host='localhost',
            database='hospital_auth',
            user='root',
            password=''
        )
    except Error as e:
        print(f"Error: '{e}'")
    return connection


db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="hospital_auth"
)
cursor = db.cursor()


@app.route('/signup', methods=['POST'])
def signup():
    try:
        # Get data from request
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Hash the password
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        # Generate a unique session_id
        session_id = str(uuid.uuid4())

        # Insert user data into database
        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO users (username, email, password, session_id) VALUES (%s, %s, %s, %s)",
            (username, email, hashed_password, session_id)
        )
        connection.commit()

        # Close the connection
        cursor.close()
        connection.close()

        return render_template('login.html')

    except Error as e:
        return jsonify({"message": f"Error: '{e}'"}), 500

    except Exception as e:
        return jsonify({"message": f"An error occurred: '{e}'"}), 500


@app.route('/feedback', methods=['POST'])
def feedback():
    try:
        # Get form data
        username = request.form['username']
        email = request.form['email']
        phone = request.form['phone']
        date = request.form['date']
        message = request.form['message']

        # Establish database connection
        connection = create_connection()
        cursor = connection.cursor()

        # Insert feedback data into the database
        cursor.execute(
            "INSERT INTO feedback (username, email, phone, date, message) VALUES (%s, %s, %s, %s, %s)",
            (username, email, phone, date, message)
        )
        connection.commit()

        cursor.close()
        connection.close()

        return jsonify({"message": "Feedback submitted successfully!"}), 200

    except Error as e:
        return jsonify({"message": f"Error: '{e}'"}), 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            username = request.form['username']
            password = request.form['password']

            hashed_password = hashlib.sha256(password.encode()).hexdigest()

            connection = create_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM users WHERE username = %s AND password = %s",
                (username, hashed_password)
            )
            user = cursor.fetchone()

            cursor.close()
            connection.close()

            if user:
                session['patient_id'] = user['id']
                session['patient_username'] = user['username']
                session['email'] = user['email']
                # session['phone'] = user['phone']

                return redirect(url_for('patient_dash'))
            else:
                return jsonify({"message": "Invalid username or password"}), 401

        except Error as e:
            return jsonify({"message": f"Error: '{e}'"}), 500

    return render_template('login.html')



@app.route('/accounts')
def accounts():
    return render_template('accounts.html')


@app.route('/')
def index():
    return render_template('accounts.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('user_session_id', None)
    return redirect(url_for('index'))


@app.route('/patient_dash')
def patient_dash():
    if 'patient_id' not in session:
        return redirect(url_for('login'))
    
    # Get patient username
    patient_username = session.get("patient_username")

    connection = create_connection()
    cursor = connection.cursor(dictionary=True)  # Use dictionary cursor for easier access

    try:
        # Count total users (patients)
        cursor.execute("SELECT COUNT(*) AS total_users FROM users")
        result = cursor.fetchone()
        total_users = result['total_users']

        # Count total doctors
        cursor.execute("SELECT COUNT(*) AS total_doctors FROM doctors")
        result = cursor.fetchone()
        total_doctors = result['total_doctors']

        # Fetch all doctors
        cursor.execute("SELECT session_id, username, email, field, gender, phone_number, created_at FROM doctors")
        doctors = cursor.fetchall()

        # Fetch all feedback data
        cursor.execute("SELECT * FROM feedback ORDER BY date DESC")
        feedbacks = cursor.fetchall()

        cursor.close()
        connection.close()

        user = {
            'username': session.get('patient_username', ''),
            'email': session.get('email', '')
            # 'phone': session.get('phone', '')
        }

        print(f"User data: {user}")
        
        return render_template('patient_dash.html',
                               total_users=total_users,
                               total_doctors=total_doctors,
                               doctors=doctors,
                               patient_username=session.get('patient_username', ''),
                               user=user,
                               feedbacks=feedbacks)

    except Error as e:
        print(f"Error fetching data: {e}")
        cursor.close()
        connection.close()
        return render_template('error.html', message="Error fetching data. Please try again later.")



@app.template_filter('truncate_words')
def truncate_words(s, num_words):
    words = s.split()
    return ' '.join(words[:num_words]) + ('...' if len(words) > num_words else '')

app.jinja_env.filters['truncate_words'] = truncate_words



@app.route('/doctors_dash')
def doctors_dash():
    try:
        # Ensure only doctors can access this route
        if 'doctor_id' not in session:
            # Redirect to doctors_login if not logged in as a doctor
            return redirect(url_for('doctors_login'))

        # Get doctor username from session
        doctor_username = session.get('doctor_username')

        connection = create_connection()
        cursor = connection.cursor()

        # Count total users (patients)
        cursor.execute("SELECT COUNT(*) AS total_users FROM users")
        result = cursor.fetchone()
        total_users = result[0]

        # Count total doctors
        cursor.execute("SELECT COUNT(*) AS total_doctors FROM doctors")
        result = cursor.fetchone()
        total_doctors = result[0]

        # Fetch all feedback data
        cursor.execute("SELECT * FROM feedback ORDER BY date DESC")
        feedbacks = cursor.fetchall()

        # Fetch all doctors
        cursor.execute(
            "SELECT session_id, username, email, field, gender, phone_number, created_at FROM doctors")
        doctors = cursor.fetchall()

        # Fetch the sum of bills from the updates table
        cursor.execute("SELECT SUM(bill) FROM updates")
        result = cursor.fetchone()
        total_bill = result[0] if result[0] is not None else 0

        cursor.close()
        connection.close()

        return render_template('doctors_dash.html',
                               total_doctors=total_doctors,
                               doctors=doctors,
                               total_users=total_users,
                               doctor_username=doctor_username,
                               total_bill=total_bill,
                               feedbacks=feedbacks)
    except Exception as e:
        print(f"Error: '{e}'")
        return "An error occurred"
  # Pass doctor_username to the template

    except Error as e:
        print(f"Error: '{e}'")  # Debug print
        return jsonify({"message": f"Error: '{e}'"}), 500

    except Exception as e:
        print(f"Exception: '{e}'")  # Debug print
        return jsonify({"message": f"An error occurred: '{e}'"}), 500


@app.route('/doctors_signup', methods=['GET', 'POST'])
def doctors_signup():
    if request.method == 'POST':
        try:
            # Get data from request
            username = request.form['username']
            email = request.form['email']
            field = request.form['field']
            password = request.form['password']
            phone_number = request.form['phone_number']
            gender = request.form['gender']

            # Hash the password
            hashed_password = hashlib.sha256(password.encode()).hexdigest()

            # Generate a unique session_id
            session_id = str(uuid.uuid4())

            # Insert user data into database
            connection = create_connection()
            cursor = connection.cursor()
            cursor.execute(
                "INSERT INTO doctors (username, email, field, password, phone_number, gender, session_id) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (username, email, field, hashed_password,
                 phone_number, gender, session_id)
            )
            connection.commit()

            # Close the connection
            cursor.close()
            connection.close()

            return render_template('doctors_login.html')

        except Error as e:
            return jsonify({"message": f"Error: '{e}'"}), 500

        except Exception as e:
            return jsonify({"message": f"An error occurred: '{e}'"}), 500

    return render_template('doctors_signup.html')


@app.route('/doctors_login', methods=['GET', 'POST'])
def doctors_login():
    if request.method == 'POST':
        try:
            username = request.form['username']
            password = request.form['password']

            hashed_password = hashlib.sha256(password.encode()).hexdigest()

            connection = create_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM doctors WHERE username = %s AND password = %s",
                (username, hashed_password)
            )
            user = cursor.fetchone()

            cursor.close()
            connection.close()

            if user:
                session['doctor_id'] = user['id']
                session['doctor_username'] = user['username']

                return redirect(url_for('doctors_dash'))
            else:
                return jsonify({"message": "Invalid username or password"}), 401

        except Error as e:
            return jsonify({"message": f"Error: '{e}'"}), 500

    return render_template('doctors_login.html')


@app.route('/booking', methods=['GET', 'POST'])
def booking():
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        email = request.form['email']
        illness = request.form['illness']
        date = request.form['date']
        time = request.form['time']
        area = request.form['area']
        city = request.form['city']
        state = request.form['state']
        post_code = request.form['post-code']
        session_id = session.get('patient_id')  # Use the correct session ID

        connection = create_connection()
        cursor = connection.cursor()

        try:
            sql = """
            INSERT INTO bookings (session_id, name, phone, email, illness, date, time, area, city, state, post_code)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (session_id, name, phone, email,
                           illness, date, time, area, city, state, post_code))
            connection.commit()

            send_mail(name, email, illness, date, time)
        except Error as e:
            print(f"Error: '{e}'")
            connection.rollback()
        finally:
            cursor.close()
            connection.close()

        return redirect('/booking')

    session_id = session.get('patient_id')  # Use the correct session ID
    user_data = None
    total_users = 0
    total_doctors = 0

    if session_id:
        connection = create_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            sql = "SELECT username, email FROM users WHERE id = %s"
            cursor.execute(sql, (session_id,))
            user_data = cursor.fetchone()

            cursor.execute("SELECT COUNT(*) AS total_users FROM users")
            result = cursor.fetchone()
            total_users = result['total_users']

            cursor.execute("SELECT COUNT(*) AS total_doctors FROM doctors")
            result = cursor.fetchone()
            total_doctors = result['total_doctors']
        except Error as e:
            print(f"Error: '{e}'")
        finally:
            cursor.close()
            connection.close()

    return render_template('booking.html', user_data=user_data, total_users=total_users, total_doctors=total_doctors)


@app.route('/my_appointments')
def my_appointments():
    session_id = session.get('patient_id')  # Use the correct session ID
    bookings = []
    total_users = 0
    total_doctors = 0
    current_patient_username = ""

    if session_id:
        connection = create_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            sql = "SELECT * FROM bookings WHERE session_id = %s"
            cursor.execute(sql, (session_id,))
            bookings = cursor.fetchall()

            cursor.execute("SELECT COUNT(*) AS total_users FROM users")
            result = cursor.fetchone()
            total_users = result['total_users']

            cursor.execute("SELECT COUNT(*) AS total_doctors FROM doctors")
            result = cursor.fetchone()
            total_doctors = result['total_doctors']
        except Error as e:
            print(f"Error: '{e}'")
        finally:
            cursor.close()
            connection.close()

        current_patient_username = session.get('patient_username')

    return render_template('my_appointments.html', bookings=bookings, total_doctors=total_doctors, total_users=total_users, current_patient_username=current_patient_username)


@app.route('/appointments')
def appointments():
    bookings = []

    connection = create_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        sql = "SELECT * FROM bookings"
        cursor.execute(sql)
        bookings = cursor.fetchall()

        cursor.execute("SELECT COUNT(*) AS total_users FROM users")
        result = cursor.fetchone()
        total_users = result['total_users']

        cursor.execute("SELECT COUNT(*) AS total_doctors FROM doctors")
        result = cursor.fetchone()
        total_doctors = result['total_doctors']

        cursor.execute("SELECT COUNT(*) AS total_appointments FROM bookings")
        result = cursor.fetchone()
        total_appointments = result['total_appointments']
    except Error as e:
        print(f"Error: '{e}'")
    finally:
        cursor.close()
        connection.close()

        # Get current doctor's username from session
        current_doctor_username = session.get('username')

    return render_template('appointments.html', bookings=bookings, total_doctors=total_doctors, total_users=total_users, total_appointments=total_appointments, current_doctor_username=current_doctor_username)


@app.route('/patients')
def patients():
    bookings = []

    # Fetching bookings data
    connection = create_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        # Fetch approved bookings
        sql = "SELECT * FROM bookings WHERE status = 'Approved'"
        cursor.execute(sql)
        bookings = cursor.fetchall()

        # Count total users
        cursor.execute("SELECT COUNT(*) AS total_users FROM users")
        result = cursor.fetchone()
        total_users = result['total_users']

        # Count total doctors
        cursor.execute("SELECT COUNT(*) AS total_doctors FROM doctors")
        result = cursor.fetchone()
        total_doctors = result['total_doctors']

        # Count total appointments
        cursor.execute("SELECT COUNT(*) AS total_appointments FROM bookings")
        result = cursor.fetchone()
        total_appointments = result['total_appointments']

        # Fetch session_id and doctor's name from session
        session_id = session.get('session_id', '')
        doctor_name = session.get('doctor_name', '')

    except Error as e:
        print(f"Error: '{e}'")
    finally:
        cursor.close()
        connection.close()

    return render_template('patients.html', bookings=bookings, total_doctors=total_doctors, total_users=total_users, total_appointments=total_appointments, session_id=session_id, doctor_name=doctor_name)


# Your M-Pesa credentials and endpoint URLs
consumer_key = 'dtIKy3EDiD0NyGmwZ1QjUVjJo1oQWXlZ7D4M62cBtjraPDkf'
consumer_secret = 'kZL8TlKj5Zu25sy1IHgsqyqNzV68pysTVfS5GGGvtvUUu954DyKi6eeT7GUQAzxB'
business_short_code = '174379'
passkey = 'bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919'
# Replace with your callback URL
callback_url = 'https://morning-basin-87523.herokuapp.com/callback_url.php'

# Function to get OAuth access token


def get_access_token():
    access_token_url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
    headers = {'Content-Type': 'application/json'}
    response = requests.get(access_token_url, headers=headers, auth=(
        consumer_key, consumer_secret))
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        raise Exception(f"Failed to get access token: {response.text}")


import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

@app.route('/save_update', methods=['POST'])
def save_update():
    if request.method == 'POST':
        session_id = request.form.get('sessionId')
        date = request.form.get('date')
        doctor_name = request.form.get('doctorName')
        notes = request.form.get('notes')
        bill = request.form.get('bill')
        phone = request.form.get('phone')

        # Save data to updates table
        connection = create_connection()
        if connection:
            cursor = connection.cursor()
            try:
                # Ensure 'static/notes' directory exists
                notes_directory = os.path.join(app.root_path, 'static', 'notes')
                os.makedirs(notes_directory, exist_ok=True)

                # Save notes to a PDF file
                notes_filename = secure_filename(f"{session_id}_notes.pdf")
                notes_path = os.path.join(notes_directory, notes_filename)
                relative_notes_path = os.path.join('static', 'notes', notes_filename)

                # Generate PDF
                c = canvas.Canvas(notes_path, pagesize=letter)
                c.drawString(100, 750, f"Notes for Session ID: {session_id}")
                c.drawString(100, 730, f"Date: {date}")
                c.drawString(100, 710, f"Doctor's Name: {doctor_name}")
                c.drawString(100, 690, f"Notes:")
                c.drawString(100, 670, notes)
                c.save()

                # Store file path in the database
                sql = "INSERT INTO updates (session_id, date, doctor_name, notes, bill, phone, notes_path) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                cursor.execute(sql, (session_id, date, doctor_name, notes, bill, phone, relative_notes_path))
                connection.commit()

                # Fetch email and name from the related booking
                cursor.execute("SELECT name, email, illness, date, time FROM bookings WHERE session_id = %s", (session_id,))
                booking = cursor.fetchone()
                if booking:
                    name, email, illness, date, time = booking
                    send_update_mail(name, email, doctor_name, notes, bill, date)
                
                print("Update saved successfully!")
                cursor.close()
                connection.close()

            except mysql.connector.Error as e:
                print(f"Error: '{e}'")
                connection.rollback()
            finally:
                cursor.close()
                connection.close()

        # Initiate STK push
        try:
            # Set timezone
            nairobi_time = pytz.timezone('Africa/Nairobi')
            timestamp = datetime.now(nairobi_time).strftime('%Y%m%d%H%M%S')

            # Generate password
            password = base64.b64encode(
                (business_short_code + passkey + timestamp).encode('utf-8')).decode('utf-8')

            # Get access token
            access_token = get_access_token()

            # Prepare STK push request data
            stk_push_url = 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
            headers = {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + access_token
            }
            payload = {
                'BusinessShortCode': business_short_code,
                'Password': password,
                'Timestamp': timestamp,
                'TransactionType': 'CustomerPayBillOnline',
                'Amount': bill,
                'PartyA': phone,
                'PartyB': business_short_code,
                'PhoneNumber': phone,
                'CallBackURL': callback_url,
                'AccountReference': '2255',  # Adjust as necessary
                'TransactionDesc': 'Payment for appointment'  # Adjust as necessary
            }

            # Send STK push request
            response = requests.post(
                stk_push_url, json=payload, headers=headers)
            if response.status_code == 200:
                print("STK push request sent successfully!")
            else:
                print(f"Failed to send STK push request: {response.text}")

        except Exception as e:
            print(f"Error initiating STK push: {str(e)}")

        return redirect('/patients')

    return 'Method not allowed', 405



@app.route('/approve_action/<int:booking_id>', methods=['POST'])
def approve_booking(booking_id):
    if request.method == 'POST':
        connection = create_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            # connection = create_connection()
            # with connection.cursor() as cursor:
                # Update the status of the booking with the given booking_id
                sql = "UPDATE bookings SET status = 'Approved' WHERE id = %s"
                cursor.execute(sql, (booking_id,))
                connection.commit()
                # Optionally, you can fetch updated data or redirect to another page
                return redirect(url_for('appointments'))
        except Error as e:
            print(f"Error updating booking status: {e}")
        finally:
            connection.close()

    # Handle other methods or errors gracefully
    # Redirect to appointments page if not POST or error
    return redirect(url_for('appointments'))


# @app.route('/appointments')
@app.route('/notifications')
def notifications():
    combined_data = []

    connection = create_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        # Fetch combined data from bookings and updates tables
        sql = """
        SELECT b.session_id, b.date, b.doctor AS doctor_name, u.notes, u.notes_path, u.bill AS update_bill,
               u.phone AS update_phone, b.name, b.email, b.illness, b.time, b.area, b.city, 
               b.state, b.post_code, b.status
        FROM bookings b
        LEFT JOIN updates u ON b.session_id = u.session_id
        WHERE b.status = 'Approved'
        """
        cursor.execute(sql)
        combined_data = cursor.fetchall()
        # print(combined_data)

    except Error as e:
        print(f"Error: '{e}'")
    finally:
        cursor.close()
        connection.close()

    return render_template('notifications.html', combined_data=combined_data)


@app.route('/reminders')
def reminders():
    user_role = 'doctor'
    return render_template('reminder.html')


@app.route('/patient_reminder')
def patient_reminder():
    session_id = session.get('user_id')

    # Get current doctor's username from session
    current_patient_username = session.get('username')
    return render_template('patient_reminder.html', current_patient_username=current_patient_username)


@app.route('/recents')
def recents():
    combined_data = []

    connection = create_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        # Fetch combined data from bookings and updates tables
        sql = """
        SELECT b.session_id, b.date, b.doctor AS doctor_name, u.notes, u.notes_path, u.bill AS update_bill,
               u.phone AS update_phone, b.name, b.email, b.illness, b.time, b.area, b.city, 
               b.state, b.post_code, b.status
        FROM bookings b
        LEFT JOIN updates u ON b.session_id = u.session_id
        WHERE b.status = 'Approved'
        """
        cursor.execute(sql)
        combined_data = cursor.fetchall()
        # print(combined_data)

    except Error as e:
        print(f"Error: '{e}'")
    finally:
        cursor.close()
        connection.close()

    return render_template('recents.html', combined_data=combined_data)






if __name__ == '__main__':
    app.run(debug=True)
