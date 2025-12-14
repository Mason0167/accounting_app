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
    
    # 旅遊表
# 建立 trips table，如果還沒建立
    c.execute('''
        CREATE TABLE IF NOT EXISTS trips (
            id INTEGER PRIMARY KEY,
            trip_name TEXT UNIQUE,
            start_date TEXT,
            end_date TEXT
        )
    ''')    
    
    # 支出表
    c.execute('''CREATE TABLE IF NOT EXISTS expenses
                 (id INTEGER PRIMARY KEY, trip_id INTEGER, item TEXT, amount REAL, category TEXT,
                  FOREIGN KEY(trip_id) REFERENCES trips(id))''')
                  
    conn.commit()
    conn.close()

# 首頁
@app.route('/')
def index():
    return render_template('index.html')

# 選擇旅遊頁
@app.route('/tripSelection', methods=['GET', 'POST'])
def tripSelection():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    if request.method == 'POST':
        trip_name = request.form['trip_name']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        
       # 日期驗證
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            flash("Invalid date format!")
            return redirect(url_for('tripSelection'))

        if start_dt > end_dt:
            flash("End date must be after or equal to start date!")
            return redirect(url_for('tripSelection'))
        
        try:
            c.execute('INSERT OR IGNORE INTO trips (trip_name, start_date, end_date) VALUES (?, ?, ?)', 
                 (trip_name, start_date, end_date))
            conn.commit()
            flash(f"Trip '{trip_name}' added successfully!")
            
        except sqlite3.IntegrityError:
            flash(f"Trip name '{trip_name}' already exists!")
            return redirect(url_for('tripSelection'))
        
        return redirect(url_for('tripSelection'))
        
    c.execute('SELECT * FROM trips ORDER BY start_date')
    trips_list = c.fetchall()
    
    conn.close()
    return render_template('tripSelection.html', trips=trips_list)

# 新增支出頁面
@app.route('/newExpense/<int:trip_id>', methods=['GET', 'POST'])
def newExpense(trip_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # 取得旅遊名稱
    c.execute('SELECT trip_name FROM trips WHERE id=?', (trip_id,))
    trip_name = c.fetchone()[0]

    if request.method == 'POST':
        item = request.form['item']
        amount = request.form['amount']
        category = request.form['category']
        c.execute('INSERT INTO expenses (trip_id, item, amount, category) VALUES (?, ?, ?, ?)',
                  (trip_id, item, amount, category))
        conn.commit()
    conn.close()
    return render_template('newExpense.html', trip_name=trip_name, trip_id=trip_id)

# 顯示所有支出
@app.route('/viewExpense')
def viewExpense():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # 取得所有 trips（給下拉選單用）
    c.execute('SELECT id, trip_name FROM trips')
    trips = c.fetchall()
    
    # 取得選擇的 trip_id
    trip_id = request.args.get('trip_id')
    
    if trip_id:
        c.execute(
            'SELECT * FROM expenses WHERE trip_id = ? ORDER BY category',
            (trip_id,)
        )

    
    expenses = c.fetchall()
    conn.close()
    return render_template(
        'viewExpense.html',
        expenses=expenses,
        trips=trips,
        selected_trip=trip_id
    )
    
# Delete Page
@app.route('/deleteTrip/<int:trip_id>', methods=['POST'])
def deleteTrip(trip_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Delete trip and its related expenses (if you have a foreign key)
    c.execute('DELETE FROM trips WHERE id = ?', (trip_id,))
    conn.commit()
    conn.close()

    flash("Trip deleted successfully!")
    return redirect(url_for('tripSelection'))
    
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
