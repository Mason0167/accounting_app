from flask import Flask, render_template, request, redirect, url_for, flash, get_flashed_messages, send_file
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
DB_FILE = 'expenses.db'
app.secret_key = 'your_secret_key_here'

# 初始化資料庫
def init_db():
    with sqlite3.connect(DB_FILE) as conn:
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
            (1, 'card'),
            (2, 'cash')
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
            ('meals', 1),
            ('activities', 2),
            ('transportation', 3),
            ('accommodation', 4),
            ('others', 5)
        ]

        for cat_name, order_index in default_categories:
            c.execute(
                'INSERT OR IGNORE INTO categories (cat_name, order_index) VALUES (?, ?)',
                (cat_name, order_index)
            )

        # currencies table
        c.execute('''CREATE TABLE IF NOT EXISTS currencies (
                     id INTEGER PRIMARY KEY, 
                     code TEXT UNIQUE, 
                     currency_name TEXT,
                     symbol TEXT,
                     is_base INTEGER DEFAULT 0
                    )
                ''')
                
        default_currencies = [
            ('NTD', 'New Taiwanese Dollar', '$'),
            ('JPY', 'Japanese Yen', '¥'),
            ('KRW', 'Korean Won', '₩'),
            ('VND', 'Vietnamese Dong', '₫'),
            ('USD', 'US Dollar', '$'),
            ('EUR', 'Euro', '€'),
            ('GBP', 'British Pound', '£')
        ]

        for code, currency_name, symbol in default_currencies:
            c.execute(
                'INSERT OR IGNORE INTO currencies (code, currency_name, symbol) VALUES (?, ?, ?)',
                (code, currency_name, symbol)
            )
            
        # Exchange_rates table
        c.execute('''
            CREATE TABLE IF NOT EXISTS exchange_rates (
                id INTEGER PRIMARY KEY,
                currency_id INTEGER UNIQUE,
                rate_to_base REAL NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(currency_id) REFERENCES currencies(id)
            )
        ''')

        default_exchange_rates = [
            ('NTD', 1.0),
            ('JPY', 0.2004),
            ('KRW', 0.02114),
            ('VND', 0.001187),
            ('USD', 31.215),
            ('EUR', 36.617),
            ('GBP', 41.761)
        ]

        for code, rate in default_exchange_rates:
            c.execute('SELECT id FROM currencies WHERE code = ?', (code,))
            row = c.fetchone()
            if row:
                currency_id = row[0]
                updated_at = datetime.now().isoformat()
                c.execute('INSERT OR IGNORE INTO exchange_rates (currency_id, rate_to_base, updated_at)VALUES (?, ?, ?)', 
                    (currency_id, rate, updated_at)
                )
        
        # expenses table
        c.execute('''CREATE TABLE IF NOT EXISTS expenses (
                     id INTEGER PRIMARY KEY, 
                     currency_id INTEGER,
                     method_id INTEGER, 
                     category_id INTEGER,
                     trip_id INTEGER,
                     item TEXT, 
                     amount REAL, 
                     FOREIGN KEY(currency_id) REFERENCES currensies(id),
                     FOREIGN KEY(method_id) REFERENCES paymentMethods(id),
                     FOREIGN KEY(category_id) REFERENCES categories(id),
                     FOREIGN KEY(trip_id) REFERENCES trips(id)
                    )
                ''')
                
        conn.commit()

# Index
@app.route('/')
def index():
    return render_template('index.html')

# tripSelection
@app.route('/tripSelection', methods=['GET', 'POST'])
def tripSelection():
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
    
        # Fetch trips for display
        c.execute('SELECT * FROM trips ORDER BY start_date')
        trips_list = c.fetchall()

        modal_message = None
        trip_name = ''
        display_trip_name = ''
        start_date = ''
        end_date = ''
        
        if request.method == 'POST':
            trip_name = request.form.get('trip_name', '').strip()
            display_trip_name = request.form.get('trip_name', '').strip()
            start_date = request.form.get('start_date', '').strip()
            end_date = request.form.get('end_date', '').strip()

            # Validation
            if not trip_name:
                modal_message = "Trip name cannot be empty!"
            elif not start_date:
                modal_message = "Start date cannot be empty!"
            elif not end_date:
                modal_message = "End date cannot be empty!"
            else:
                try:
                    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                    end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                    if start_dt > end_dt:
                        modal_message = "End date must be after or equal to start date!"
                except ValueError:
                    modal_message = "Invalid date format!"

            # Insert trip if no error
            if not modal_message:
                try:
                    c.execute(
                        'INSERT INTO trips (trip_name, start_date, end_date) VALUES (?, ?, ?)',
                        (trip_name, start_date, end_date)
                    )
                    conn.commit()
                    flash(f'"{display_trip_name}" added successfully!', 'success')
                    return redirect(url_for('tripSelection'))  # PRG pattern
                    
                except sqlite3.IntegrityError:
                    modal_message = f'"{display_trip_name}" already exists!'

        # Refresh trips after potential insertion
        c.execute('SELECT * FROM trips ORDER BY start_date')
        trips_list = c.fetchall()

        # Calculate total expenses in base currency for each trip
        trips_with_total = []
        for trip in trips_list:
            trip_id = trip[0]
            c.execute('''
                SELECT SUM(e.amount * r.rate_to_base) 
                FROM expenses e
                JOIN exchange_rates r ON e.currency_id = r.currency_id
                WHERE e.trip_id = ?
            ''', (trip_id,))
            
            row = c.fetchone()
            total_in_base = row[0] if row[0] is not None else 0
            
            trips_with_total.append({
                'id': trip_id,
                'trip_name': trip[1],
                'start_date': trip[2],
                'end_date': trip[3],
                'total_in_base': total_in_base
            })

        return render_template(
            'tripSelection.html',
            trips=trips_with_total,
            modal_message=modal_message,
            entered_trip_name=trip_name,
            entered_start_date=start_date,
            entered_end_date=end_date
        )

    
# newExpense
@app.route('/newExpense/<int:trip_id>', methods=['GET', 'POST'])
def newExpense(trip_id):
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()

        # To get trip_name in trips table
        c.execute('SELECT trip_name FROM trips WHERE id=?', (trip_id,))
        row = c.fetchone()
        trip_name = row[0] if row else None
    
        # To get categories table
        c.execute('SELECT * FROM categories')
        categories_list = c.fetchall()
    
        # To get paymentMethods table
        c.execute('SELECT * FROM paymentMethods')
        paymentMethods_list = c.fetchall()
    
        # To get currencies table
        c.execute('SELECT * FROM currencies')
        currencies_list = c.fetchall()
    
        modal_message = None
        category = ''
        payment_method = ''
        item = ''
        amount_str = ''
        currency = ''
    
        if request.method == 'POST':
        
            category = request.form.get('category', '').strip()
            payment_method = request.form.get('payment_method', '').strip()
            item = request.form.get('item', '').strip().lower()
            amount_str = request.form.get('amount', '').strip()
            currency = request.form.get('currency', '').strip()
        
            # Validation
            if not category:
                modal_message = "Category cannot be empty!"
            elif not payment_method:
                modal_message = "Please select a payment method!"
            elif not item:
                modal_message = "Item cannot be empty!"
            elif not amount_str:
                modal_message = "Amount cannot be empty!"
            elif not currency:
                modal_message = "Please select a currency!"
            else:
                # Validate "amount" input
                try:
                    amount = round(float(amount_str), 2)  # 兩位小數
                    if amount <= 0:
                        modal_message = "Amount must be greater than 0!"
                except ValueError:
                    modal_message = "Invalid amount!"
        
            if not modal_message:
            
                # Get category ID
                c.execute('SELECT id FROM categories WHERE cat_name = ?', (category,))
                category_row = c.fetchone()
                if not category_row:
                    modal_message = "Invalid category selected!"
                else:
                    category_id = category_row[0]

                # Get payment method ID
                c.execute('SELECT id FROM paymentMethods WHERE method_name = ?', (payment_method,))
                payment_row = c.fetchone()
                if not payment_row:
                    modal_message = "Invalid payment method selected!"
                else:
                    payment_id = payment_row[0]

                # Get currency ID
                c.execute('SELECT id FROM currencies WHERE code = ?', (currency,))
                currency_row = c.fetchone()
                if not currency_row:
                    modal_message = "Invalid currency selected!"
                else:
                    currency_id = currency_row[0]
            
                # Ensure insert successfully or not
                try:
                    c.execute('''
                        INSERT INTO expenses (trip_id, category_id, method_id, item, amount, currency_id)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (trip_id, category_id, payment_id, item, amount, currency_id))
                
                    conn.commit()
                    flash("Expense added successfully!", "error")
                    return redirect(url_for('newExpense', trip_id=trip_id))
            
                except sqlite3.IntegrityError:
                    modal_message = "Oh no! Something went wrong!"

    
        all_expenses = []
        # Fetch expenses only for selected trip
        if trip_id:
            c.execute('''
                SELECT e.id, c.cat_name, e.item, e.amount, cu.code, cu.symbol
                FROM expenses e
                JOIN categories c ON e.category_id = c.id
                JOIN currencies cu ON e.currency_id = cu.id
                WHERE trip_id = ? 
                ORDER BY c.order_index
            ''', (trip_id,))
            rows = c.fetchall()

            for e in rows:
                all_expenses.append({
                'id': e[0],
                'category': e[1],
                'item': e[2],
                'amount': e[3],
                'code': e[4],
                'symbol': e[5]
                })
    
        grouped_expenses = {}
    
        for e in all_expenses:
            cat = e['category']
            grouped_expenses.setdefault(cat, []).append(e)
            
        
    
    return render_template(
        'newExpense.html', 
        grouped_expenses=grouped_expenses,
        modal_message=modal_message,
        trip_name=trip_name, 
        categories_list=categories_list,
        paymentMethods_list=paymentMethods_list,
        currencies_list=currencies_list,
        entered_category=category,
        entered_paymentMethod=payment_method,
        entered_item=item,
        entered_amount_str=amount_str,
        entered_currency=currency
    )
    

# viewExpense
@app.route('/viewExpense')
def viewExpense():
    # Initialize variables
    trips = []
    trip = None
    expenses = []
    grouped_expenses = {}
    total_in_base = 0
    modal_message = ""

    # Safely get trip_id from query string
    trip_id = request.args.get('trip_id', type=int)

    # Open DB connection
    try:
        with sqlite3.connect(DB_FILE) as conn:
            c = conn.cursor()

            # Fetch all trips for dropdown (always)
            try:
                c.execute('SELECT id, trip_name FROM trips ORDER BY start_date')
                trips = [{'id': r[0], 'trip_name': r[1]} for r in c.fetchall()]
            except sqlite3.DatabaseError:
                modal_message = "Failed to fetch trips."

            # If a valid trip is selected, fetch trip info and expenses
            if trip_id:
                try:
                    # Fetch selected trip info
                    c.execute('SELECT id, trip_name, start_date, end_date FROM trips WHERE id = ?', (trip_id,))
                    row = c.fetchone()
                    if row:
                        trip = {
                            'id': row[0],
                            'trip_name': row[1],
                            'start_date': row[2],
                            'end_date': row[3]
                        }
                    else:
                        modal_message = "Selected trip not found."
                        trip_id = None  # prevent further queries

                    if trip:
                        # Calculate total in base currency
                        c.execute('''
                            SELECT SUM(e.amount * r.rate_to_base)
                            FROM expenses e
                            JOIN exchange_rates r ON e.currency_id = r.currency_id
                            WHERE e.trip_id = ?
                        ''', (trip_id,))
                        total_in_base = c.fetchone()[0] or 0

                        # Fetch expenses for the trip
                        c.execute('''
                            SELECT e.id, c.cat_name, e.item, e.amount, cu.code, cu.symbol
                            FROM expenses e
                            JOIN categories c ON e.category_id = c.id
                            JOIN currencies cu ON e.currency_id = cu.id
                            WHERE e.trip_id = ?
                            ORDER BY c.order_index
                        ''', (trip_id,))
                        rows = c.fetchall()

                        for e in rows:
                            expense = {
                                'id': e[0],
                                'category': e[1],
                                'item': e[2],
                                'amount': e[3],
                                'code': e[4],
                                'symbol': e[5]
                            }
                            expenses.append(expense)
                            grouped_expenses.setdefault(e[1], []).append(expense)

                except sqlite3.DatabaseError:
                    modal_message = "Failed to fetch selected trip details or expenses."

    except sqlite3.DatabaseError:
        modal_message = "Database connection failed."

    # Render template
    return render_template(
        'viewExpense.html',
        trips=trips,
        selected_trip=trip_id,
        trip=trip,
        grouped_expenses=grouped_expenses,
        expenses=expenses,
        total_in_base=total_in_base,
        modal_message=modal_message
    )


#editTrip
@app.route('/editTrip/<int:trip_id>', methods=['GET', 'POST'])
def editTrip(trip_id):
    modal_message = None
    
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        
        c.execute('''
                    SELECT trip_name, start_date, end_date FROM trips WHERE id = ? 
                    ORDER BY start_date
                ''', (trip_id,))
        trip = c.fetchone()
                
        if not trip:
            flash("Trip not found!", "error")
            return redirect(url_for('tripSelection'))
                   
        trip_name, start_date, end_date = trip
            
        if request.method == 'POST':
            new_name = request.form.get('trip_name', '').strip()
            new_start = request.form.get('start_date', '').strip()
            new_end = request.form.get('end_date', '').strip()
            
            if not new_name:
                modal_message = "Trip name cannot be empty!"
            elif not new_start or not new_end:
                modal_message = "Dates cannot be empty!"
            else:
                try:
                    if datetime.strptime(new_start, '%Y-%m-%d') > datetime.strptime(new_end, '%Y-%m-%d'):
                        modal_message = "End date must be after start date!"
                except:
                    modal_message = "Invalid date format!"
        
            if not modal_message:
                c.execute('''
                    UPDATE trips
                    SET trip_name = ?, start_date = ?, end_date = ?
                    WHERE id = ?
                ''', (new_name, new_start, new_end, trip_id))
                conn.commit()
                flash("Trip updated successfully", "error")
                return redirect(url_for('tripSelection'))
            
    return render_template(
        'editTrip.html', 
        modal_message=modal_message,
        trip_id=trip_id,
        trip_name=trip_name,
        start_date=start_date,
        end_date=end_date
    )   
    
# deleteTrip
@app.route('/deleteTrip/<int:trip_id>', methods=['POST'])
def deleteTrip(trip_id):
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        
        # Delete trip and its related expenses (if you have a foreign key)
        c.execute('DELETE FROM trips WHERE id = ?', (trip_id,))
        conn.commit()

    return redirect(url_for('tripSelection'))
    
    
# deleteExpense
@app.route('/deleteExpense/<int:expense_id>', methods=['POST'])
def deleteExpense(expense_id):
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        
        # Delete expense
        c.execute('DELETE FROM expenses WHERE id = ?', (expense_id,))
        conn.commit()

    return redirect(request.referrer or url_for('tripSelection'))
    
    
@app.route('/downloadBackup')
def downloadBackup():
    db_path = DB_FILE

    if not os.path.exists(db_path):
        abort(404)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f'expense_backup_{timestamp}.db'

    return send_file(
        db_path,
        as_attachment=True,
        download_name=backup_name,
        mimetype='application/octet-stream'
    )
    
    
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
