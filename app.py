from flask import Flask, render_template, request, redirect
import mysql.connector
from datetime import datetime

app = Flask(__name__)

# MySQL database connection
db = mysql.connector.connect(
    host='localhost',
    user='root',
    password='Arun@1234',
    database='flight_booking_system'
)

# Create cursor object to execute queries
cursor = db.cursor()

# Create database and tables if they don't exist
try:
    query = "create table if not exists users (username varchar(20) primary key, password varchar(20), type varchar(20))"
    cursor.execute(query)
except:
    pass
try:
    query = "create table if not exists flights (flight_id varchar(20) primary key, flight_name varchar(20), source varchar(20), destination varchar(20), departure_time datetime, arrival_time datetime, price int)"
    cursor.execute(query)
except:
    pass
try:
    query = "create table if not exists bookings (flight_id varchar(20), username varchar(20), primary key(flight_id, username))"
    cursor.execute(query)
except:
    pass

# default values
try:
    query = "insert into users values('admin', 'admin', 'admin')"
    cursor.execute(query)
    db.commit()
except:
    pass
try:
    query = "insert into users values('user', 'user', 'customer')"
    cursor.execute(query)
    db.commit()
except:
    pass

# add flights by default for debugging
try:
    query = "insert into flights values('1', 'Indigo', 'Delhi', 'Mumbai', '2023-06-09 01:21:00', '2023-06-10 01:21:00', 4000)"
    cursor.execute(query)
    db.commit()
# except Exception as e:
#   print(e)
except:
    pass
try:
    query = "insert into flights values('2', 'Air India', 'Delhi', 'Mumbai', '2021-05-01 14:00:00', '2021-05-01 16:00:00', 5000)"
    cursor.execute(query)
    db.commit()
except:
    pass
# Home page


@app.route('/')
def index():
    return render_template('index.html')

# Login page


@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    # Check if the username and password are valid in the database
    query = "SELECT * FROM users WHERE username = %s AND password = %s"
    values = (username, password)
    cursor.execute(query, values)
    user = cursor.fetchone()

    if user:
        user_type = user[2]
        if user_type == 'admin':
            return redirect('/admin')
        elif user_type == 'customer':
            # Redirect to customer page')
            return redirect('/customer/' + username)

    return redirect('/')

# Register page


@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']

    # Check if the username is already taken
    query = "SELECT * FROM users WHERE username = %s"
    values = (username,)
    cursor.execute(query, values)
    user = cursor.fetchone()

    if user:
        # Username is already taken
        return redirect('/')

    # Register the user
    query = "INSERT INTO users (username, password, type) VALUES (%s, %s, 'customer')"
    values = (username, password)
    cursor.execute(query, values)
    db.commit()

    return redirect('/')

# Admin page


@app.route('/admin')
def admin():
    # Fetch flights from the database
    query = "SELECT * FROM flights"
    cursor.execute(query)
    flights = cursor.fetchall()

    return render_template('admin.html', flights=flights)

# Add flight


@app.route('/add_flight', methods=['POST'])
def add_flight_route():
    flight_id = request.form['flight_id']
    flight_name = request.form['flight_name']
    source = request.form['source']
    destination = request.form['destination']
    departure_time_str = request.form['departure_time']
    arrival_time_str = request.form['arrival_time']
    price = request.form['price']

    # Convert time strings to datetime objects
    departure_time = datetime.strptime(
        departure_time_str, "%Y-%m-%dT%H:%M").strftime("%Y-%m-%d %H:%M:%S")
    arrival_time = datetime.strptime(
        arrival_time_str, "%Y-%m-%dT%H:%M").strftime("%Y-%m-%d %H:%M:%S")

    # Insert flight details into the database
    query = "INSERT INTO flights (flight_id, flight_name, source, destination, departure_time, arrival_time, price) VALUES (%s, %s, %s, %s, %s, %s, %s)"
    values = (flight_id, flight_name, source, destination,
              departure_time, arrival_time, price)
    cursor.execute(query, values)
    db.commit()

    return redirect('/admin')

# Remove flight


@app.route('/remove_flight', methods=['POST'])
def remove_flight_route():
    flight_id = request.form['flight_id']

    # Delete the flight from the database
    query = "DELETE FROM flights WHERE flight_id = %s"
    values = (flight_id,)
    cursor.execute(query, values)
    db.commit()

    return redirect('/admin')

# Customer page


@app.route('/my_bookings', methods=['POST'])
def my_bookings():
    username = request.form['username']

    # Fetch bookings from the database
    query = "SELECT * FROM bookings as b, flights as f WHERE b.flight_id = f.flight_id AND b.username = %s"
    values = (username,)
    cursor.execute(query, values)
    bookings = cursor.fetchall()

    return render_template('mybooking.html', bookings=bookings, username=username)


@app.route('/customer/<username>')
def customer(username):
    # Fetch flights from the database
    query = "SELECT * FROM flights"
    cursor.execute(query)
    flights = cursor.fetchall()

    return render_template('customer.html', flights=flights, username=username)

# Book flight


@app.route('/logout', methods=['GET'])
def logout():
    return redirect('/')


@app.route('/search_flights', methods=['POST'])
def search_flights():
    source = request.form['source']
    destination = request.form['destination']
    departure_date_str = request.form['departure_date']
    departure_time_str = request.form['departure_time']

    # Convert date and time strings to datetime objects
    departure_date = datetime.strptime(departure_date_str, "%Y-%m-%d").date()
    departure_time = datetime.strptime(departure_time_str, "%H:%M").time()

    # Search for flights matching the criteria
    query = "SELECT * FROM flights WHERE source = %s AND destination = %s AND DATE(departure_time) = %s AND TIME(departure_time) > %s"
    values = (source, destination, departure_date, departure_time)
    cursor.execute(query, values)
    flights = cursor.fetchall()

    return render_template('search_results.html', flights=flights)

# Book flight based on availability
@app.route('/book_flight', methods=['POST'])
def book_flight_route():
    flight_id = request.form['flight_id']
    username = request.form['username']

    # Check if the flight has available seats (assuming 60 as the default seat count)
    query = "SELECT COUNT(*) FROM bookings WHERE flight_id = %s"
    values = (flight_id,)
    cursor.execute(query, values)
    bookings_count = cursor.fetchone()[0]

    if bookings_count >= 60:
        return "No available seats on the selected flight."

    # Check if the user has already booked the flight
    query = "SELECT COUNT(*) FROM bookings WHERE flight_id = %s AND username = %s"
    values = (flight_id, username)
    cursor.execute(query, values)
    booking_exists = cursor.fetchone()[0]

    if booking_exists:
        return "You have already booked this flight."

    # Insert booking details into the database
    query = "INSERT INTO bookings (flight_id, username) VALUES (%s, %s)"
    values = (flight_id, username)
    cursor.execute(query, values)
    db.commit()

    return "Successfully booked flight"



@app.route('/cancel_flight', methods=['POST'])
def cancel_flight_route():
    flight_id = request.form['flight_id']
    username = request.form['username']

    # Insert booking details into the database
    query = "DELETE FROM bookings WHERE flight_id = %s AND username = %s"
    values = (flight_id, username)
    try:
        cursor.execute(query, values)
        db.commit()
    except Exception as e:
        return str(e)
    return "Successfully cancelled flight"


@app.route('/view_bookings')
def view_bookings():
    flight_id = request.args.get('flight_id')
    # Fetch bookings from the database
    query = "SELECT * FROM bookings as b, flights as f WHERE b.flight_id = f.flight_id AND b.flight_id = %s"
    values = (flight_id,)
    cursor.execute(query, values)
    bookings = cursor.fetchall()

    return render_template('viewbooking.html', bookings=bookings)


if __name__ == '__main__':
    app.run(debug=True)
