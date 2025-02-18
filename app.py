from flask import Flask, request, jsonify
import pandas as pd
import sqlite3
from flask_cors import CORS
import datetime

app = Flask(__name__)
CORS(app)

DATABASE = "meal_plan.db"

# Initialize Database
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS meals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            day INTEGER,
            meal_type TEXT,
            primary_meal TEXT,
            primary_recipe TEXT,
            alternate_meal TEXT,
            alternate_recipe TEXT,
            third_meal_option TEXT,
            third_meal_recipe TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS completed_days (
            day INTEGER PRIMARY KEY
        )
    ''')

    conn.commit()
    conn.close()

init_db()

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'message': 'No file uploaded'}), 400
    
    file = request.files['file']
    df = pd.read_excel(file)

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM meals")  # Clear existing data

    for _, row in df.iterrows():
        cursor.execute('''
            INSERT INTO meals (day, meal_type, primary_meal, primary_recipe, 
                              alternate_meal, alternate_recipe, third_meal_option, third_meal_recipe)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (row['Day'], row['Meal Type'], row['Primary Meal'], row['Primary Recipe'],
              row['Alternate Meal'], row['Alternate Recipe'], row['Third Meal Option'], row['Third Meal Recipe']))

    conn.commit()
    conn.close()

    return jsonify({'message': 'Upload successful'}), 200

@app.route('/meals/<int:day>', methods=['GET'])
def get_meals(day):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM meals WHERE day=?", (day,))
    meals = cursor.fetchall()
    
    cursor.execute("SELECT * FROM completed_days WHERE day=?", (day,))
    is_completed = cursor.fetchone() is not None

    conn.close()

    meal_list = []
    for meal in meals:
        meal_list.append({
            "meal_type": meal[2],
            "primary_meal": meal[3],
            "primary_recipe": meal[4],
            "alternate_meal": meal[5],
            "third_meal_option": meal[7]
        })

    return jsonify({"meals": meal_list, "completed": is_completed})

@app.route('/complete/<int:day>', methods=['POST'])
def mark_day_done(day):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO completed_days (day) VALUES (?)", (day,))
    conn.commit()
    conn.close()
    return jsonify({'message': f'Day {day} marked as done!'}), 200

@app.route('/completed_days', methods=['GET'])
def get_completed_days():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT day FROM completed_days")
    days = [row[0] for row in cursor.fetchall()]
    conn.close()
    return jsonify(days)

@app.route('/has_data', methods=['GET'])
def check_data():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM meals")
    count = cursor.fetchone()[0]
    conn.close()
    return jsonify({'has_data': count > 0})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)
