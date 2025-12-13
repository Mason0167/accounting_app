# app.py
from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS expenses
                 (id INTEGER PRIMARY KEY, item TEXT, amount REAL)''')
    conn.commit()
    conn.close()

@app.route('/', methods=['GET', 'POST'])
def index():
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    if request.method == 'POST':
        item = request.form['item']
        amount = request.form['amount']
        c.execute('INSERT INTO expenses (item, amount) VALUES (?, ?)', (item, amount))
        conn.commit()
        return redirect('/')
    c.execute('SELECT * FROM expenses')
    expenses = c.fetchall()
    conn.close()
    return render_template('index.html', expenses=expenses)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)

