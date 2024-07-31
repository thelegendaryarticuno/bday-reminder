from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
from datetime import datetime, timedelta
from config import DATABASE_CONFIG
from flask_mail import Mail, Message
from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables

app = Flask(__name__)
app.secret_key = 'ddad214d0942b07320546c2109c392e5f7ad6898ebce4ede'

def get_db_connection():
    try:
        return mysql.connector.connect(**DATABASE_CONFIG)
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

@app.route('/')
def index():
    conn = get_db_connection()
    if conn is None:
        flash('Database connection failed!', 'error')
        return render_template('index.html', birthday_reminder=[])

    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM birthday_reminder')
    employees = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('index.html', birthday_reminder=employees)

@app.route('/save', methods=['POST'])
def save_employee():
    name = request.form['name']
    employee_id = request.form['employee_id']
    birth_date = request.form['birth_date']
    anniversary_date = request.form.get('anniversary_date', None)
    
    conn = get_db_connection()
    if conn is None:
        flash('Database connection failed!', 'error')
        return redirect(url_for('index'))

    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO birthday_reminder (name, employee_id, birth_date, anniversary_date) VALUES (%s, %s, %s, %s)',
        (name, employee_id, birth_date, anniversary_date)
    )
    conn.commit()
    cursor.close()
    conn.close()
    
    flash('Employee details saved successfully!')
    return redirect(url_for('index'))

@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update_employee(id):
    conn = get_db_connection()
    if conn is None:
        flash('Database connection failed!', 'error')
        return redirect(url_for('index'))

    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM birthday_reminder WHERE id = %s', (id,))
    employee = cursor.fetchone()
    
    if request.method == 'POST':
        name = request.form.get('name')
        birth_date = request.form.get('birth_date')
        anniversary_date = request.form.get('anniversary_date')
        
        cursor.execute(
            'UPDATE birthday_reminder SET name = %s, birth_date = %s, anniversary_date = %s WHERE id = %s',
            (name, birth_date, anniversary_date, id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        flash('Employee updated successfully!')
        return redirect(url_for('index'))
    
    cursor.close()
    conn.close()
    return render_template('update.html', employee=employee)

@app.route('/delete/<int:id>')
def delete_employee(id):
    conn = get_db_connection()
    if conn is None:
        flash('Database connection failed!', 'error')
        return redirect(url_for('index'))

    cursor = conn.cursor()
    cursor.execute('DELETE FROM birthday_reminder WHERE id = %s', (id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash('Employee deleted successfully!')
    return redirect(url_for('index'))

@app.route('/birthdays')
def birthdays():
    today = datetime.today().date()
    week_later = today + timedelta(days=7)
    
    conn = get_db_connection()
    if conn is None:
        flash('Database connection failed!', 'error')
        return render_template('birthdays.html', birthdays=[])

    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        '''SELECT id, name, employee_id, birth_date, anniversary_date
           FROM birthday_reminder
           WHERE (DAYOFYEAR(birth_date) >= DAYOFYEAR(%s) AND DAYOFYEAR(birth_date) <= DAYOFYEAR(%s))
           OR (DAYOFYEAR(%s) > DAYOFYEAR(%s) AND (DAYOFYEAR(birth_date) >= DAYOFYEAR(%s) OR DAYOFYEAR(birth_date) <= DAYOFYEAR(%s)))
           OR (DAYOFYEAR(anniversary_date) >= DAYOFYEAR(%s) AND DAYOFYEAR(anniversary_date) <= DAYOFYEAR(%s))
           OR (DAYOFYEAR(%s) > DAYOFYEAR(%s) AND (DAYOFYEAR(anniversary_date) >= DAYOFYEAR(%s) OR DAYOFYEAR(anniversary_date) <= DAYOFYEAR(%s)))
           ORDER BY birth_date''',
        (today, week_later, week_later, today, today, week_later,
         today, week_later, week_later, today, today, week_later)
    )
    upcoming_events = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('birthdays.html', birthdays=upcoming_events)

# Configuring Flask-Mail
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT'))
app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL') == '1'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')

mail = Mail(app)

@app.route('/send_email', methods=['GET', 'POST'])
def send_email():
    if request.method == 'POST':
        sender_email = request.form['sender_email']
        recipients = request.form['recipients'].split(',')
        subject = request.form['subject']
        body = request.form['body']
        
        msg = Message(subject, sender=sender_email, recipients=recipients)
        msg.body = body
        mail.send(msg)
        
        flash('Email sent successfully!')
        return redirect(url_for('index'))
    return render_template('send_email.html')

if __name__ == '__main__':
    app.run(debug=True)
