from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
from datetime import datetime, timedelta
from config import DATABASE_CONFIG

app = Flask(__name__)
app.secret_key = 'ddad214d0942b07320546c2109c392e5f7ad6898ebce4ede'

def get_db_connection():
    return mysql.connector.connect(**DATABASE_CONFIG)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/save', methods=['POST'])
def save_employee():
    name = request.form['name']
    employee_id = request.form['employee_id']
    birth_date = request.form['birth_date']
    anniversary_date = request.form.get('anniversary_date', None)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO employees (name, employee_id, birth_date, anniversary_date) VALUES (%s, %s, %s, %s)',
        (name, employee_id, birth_date, anniversary_date)
    )
    conn.commit()
    cursor.close()
    conn.close()
    
    flash('Employee details saved successfully!')
    return redirect(url_for('index'))

@app.route('/birthdays')
def birthdays():
    upcoming_birthdays = []
    today = datetime.today().date()
    week_later = today + timedelta(days=7)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT name, employee_id, birth_date FROM employees WHERE DAYOFYEAR(birth_date) BETWEEN DAYOFYEAR(%s) AND DAYOFYEAR(%s) ORDER BY birth_date',
        (today, week_later)
    )
    upcoming_birthdays = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('birthdays.html', birthdays=upcoming_birthdays)

if __name__ == '__main__':
    app.run(debug=True)
