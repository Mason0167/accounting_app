from flask import Flask, render_template, request, redirect, url_for, flash, get_flashed_messages
import sqlite3
from datetime import datetime

app = Flask(__name__)
DB_FILE = 'expenses.db'
app.secret_key = 'your_secret_key_here'

# 初始化資料庫
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # trips table
    c.execute('''
        CREATE TABLE IF NOT EXISTS trips (
            id INTEGER PRIMARY KEY,
            trip_name TEXT UNIQUE,
            start_date TEXT,
            end_date TEXT
        )
    ''')    
            
    # paymentMethods table
    c.execute('''
        CREATE TABLE IF NOT EXISTS paymentMethods (
            id INTEGER PRIMARY KEY,
            method_name TEXT UNIQUE
        )
    ''')
    
    # insert paymentMethods
    default_paymentMethods = [
        (1, 'cash'),
        (2, 'card')
    ]
    
    for method in default_paymentMethods:
        c.execute('INSERT OR IGNORE INTO paymentMethods (id, method_name) VALUES (?, ?)', method)

    # categories table
    c.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY,
            cat_name TEXT UNIQUE,
            order_index INTEGER
        )
    ''')
    
    # insert categories
    default_categories = [
        (1, 'meals', 1),
        (2, 'activities', 2),
        (3, 'transportation', 3),
        (4, 'accommodation', 4),
        (4, 'others', 4)
    ]
    
    for cat in default_categories:
        c.execute('INSERT OR IGNORE INTO categories (id, cat_name, order_index) VALUES (?, ?, ?)', cat)
    
    # expenses table
    c.execute('''CREATE TABLE IF NOT EXISTS expenses (
                 id INTEGER PRIMARY KEY, 
                 method_id INTEGER, 
                 category_id INTEGER,
                 trip_id INTEGER,
                 item TEXT, 
                 amount REAL, 
                 FOREIGN KEY(method_id) REFERENCES paymentMethods(id),
                 FOREIGN KEY(category_id) REFERENCES categories(id),
                 FOREIGN KEY(trip_id) REFERENCES trips(id)
                )
            ''')
            
    conn.commit()
    conn.close()

# Index
@app.route('/')
def index():
    return render_template('index.html')

# tripSelection
@app.route('/tripSelection', methods=['GET', 'POST'])
def tripSelection():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # To store any error/info messages for the modal
    modal_message = None  
    
    if request.method == 'POST':
        trip_name = request.form['trip_name'].strip().lower()
        display_trip_name = request.form['trip_name'].strip()
        start_date = request.form['start_date']
        end_date = request.form['end_date']

        # 1. Validate empty trip name
        if not trip_name:
            modal_message = "Trip name cannot be empty!"
            
        elif not start_date:
            modal_message = "Start date cannot be empty!"
            
        elif not end_date:
            modal_message = "End date cannot be empty!"

        else:
            # 2. Validate dates
            try:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                
                if start_dt > end_dt:
                    modal_message = "End date must be after start date!"
            except ValueError:
                modal_message = "Invalid date format!"

        # 3. Insert trip if no error
        if not modal_message:
            try:
                c.execute(
                    'INSERT INTO trips (trip_name, start_date, end_date) VALUES (?, ?, ?)',
                    (trip_name, start_date, end_date)
                )
                conn.commit()
            except sqlite3.IntegrityError:
                modal_message = f'Trip name "{display_trip_name}" already exists!'

    # Fetch trips for display
    c.execute('SELECT * FROM trips ORDER BY start_date')
    trips_list = c.fetchall()
    conn.close()
    
    if modal_message:
        # send back trips list + entered values
        return render_template(
            "tripSelection.html",
            trips=trips_list,
            modal_message=modal_message,
            entered_trip_name=display_trip_name,
            entered_start_date=start_date,
            entered_end_date=end_date
        )
    
    return render_template(
        'tripSelection.html',
        trips=trips_list,
        modal_message=modal_message
    )
    
# newExpense
@app.route('/newExpense/<int:trip_id>', methods=['GET', 'POST'])
def newExpense(trip_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # To get trip_name in trips table
    c.execute('SELECT trip_name FROM trips WHERE id=?', (trip_id,))
    trip_name = c.fetchone()[0]
    
    # To get order_index in categories table
    c.execute('SELECT order_index FROM categories WHERE id=?', (order_index,))
    order_index = c.fetchone()[0]

    if request.method == 'POST':
        
        item = request.form['item'].strip().lower()
        amount = request.form['amount'].strip()
        
        # Validate "item" input
        if not item:  # empty string, None, or only spaces
            return redirect(url_for('newExpense', trip_id=trip_id))
        
        # Validate "amount" input
        try:
            amount = round(float(amount_str), 2)  # 兩位小數
        except ValueError:
            return redirect(url_for('newExpense', trip_id=trip_id))
        
        # Ensure insert successfully or not
        try:
            c.execute('INSERT OR IGNORE INTO expenses (trip_id, item, amount) VALUES (?, ?, ?)',
                  (trip_id, item, amount))
            conn.commit()
            
        except sqlite3.IntegrityError:
            return redirect(url_for('newExpense', trip_id=trip_id))
        
    conn.close()
    return render_template('newExpense.html', trip_name=trip_name, trip_id=trip_id)

# viewExpense
@app.route('/viewExpense')
def viewExpense():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    trips = []
    grouped_expenses = {}
    
    try:
        # Select all trips for dropdown
        c.execute('SELECT id, trip_name FROM trips')
        trips = c.fetchall()

        # Get selected trip_id
        trip_id = request.args.get('trip_id')
        if trip_id:
            try:
                trip_id = int(trip_id)
            except ValueError:
                # Invalid trip_id from URL, ignore and show all expenses
                trip_id = None

        # Fetch expenses only for selected trip
        if trip_id:
            c.execute('SELECT * FROM expenses WHERE trip_id = ? ORDER BY category', (trip_id,))
        
        all_expenses = c.fetchall()

        # Group expenses by category
        for e in all_expenses:
            category = e[4]
            if category not in grouped_expenses:
                grouped_expenses[category] = []
            grouped_expenses[category].append(e)

    except sqlite3.DatabaseError:
        # In case of DB error, just show empty lists
        trips = []
        grouped_expenses = {}
        
    finally:
        conn.close()

    return render_template(
        'viewExpense.html',
        grouped_expenses=grouped_expenses,
        trips=trips,
        selected_trip=trip_id
    )

    
# deleteTrip
@app.route('/deleteTrip/<int:trip_id>', methods=['POST'])
def deleteTrip(trip_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Delete trip and its related expenses (if you have a foreign key)
    c.execute('DELETE FROM trips WHERE id = ?', (trip_id,))
    conn.commit()
    conn.close()

    return redirect(url_for('tripSelection'))
    
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
