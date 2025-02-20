from flask import Flask, jsonify
import pandas as pd
import sqlite3
import os
import logging
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Database and Excel file settings
DATABASE = "meal_plan.db"
EXCEL_FILE = "meal_plan.xlsx"  # This will be manually replaced in GitHub

LOG_FILE = "backend_log.txt"

# Set up logging
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ✅ Initialize the database (Runs ONLY ONCE)
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS meals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            day INTEGER,
            week INTEGER,
            meal_type TEXT,
            primary_meal TEXT,
            primary_recipe TEXT,
            alternate_meal_1 TEXT,
            alternate_recipe_1 TEXT,
            alternate_meal_2 TEXT,
            alternate_recipe_2 TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS completed_days (
            day INTEGER PRIMARY KEY
        )
    ''')
    conn.commit()
    conn.close()
    logging.info("✅ Database initialized successfully.")

# ✅ Load meal data from GitHub meal_plan.xlsx ONLY ONCE
def load_excel_to_db():
    if not os.path.exists(EXCEL_FILE):
        logging.error("❌ Excel file not found. Upload `meal_plan.xlsx` to GitHub manually.")
        return
    
    try:
        df = pd.read_excel(EXCEL_FILE, engine="openpyxl")

        # Ensure the file is not empty
        if df.empty:
            logging.error("❌ Error: The uploaded Excel file is empty!")
            return

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        # Check if database is already populated
        cursor.execute("SELECT COUNT(*) FROM meals")
        if cursor.fetchone()[0] > 0:
            logging.info("✅ Meal data already loaded, skipping reload.")
            conn.close()
            return  # Skip reloading if data already exists

        # ✅ Insert meal data from Excel into the database
        logging.info("🔄 Inserting meal data into the database...")
        for _, row in df.iterrows():
            cursor.execute('''
                INSERT INTO meals (day, week, meal_type, primary_meal, primary_recipe,
                                  alternate_meal_1, alternate_recipe_1, alternate_meal_2, alternate_recipe_2)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                row.get("Day", None),
                row.get("Week", None),
                row.get("Meal Type", None),
                row.get("Primary Meal", None),
                row.get("Primary Recipe", None),
                row.get("Alternate Meal 1", None),
                row.get("Alternate Recipe 1", None),
                row.get("Alternate Meal 2", None),
                row.get("Alternate Recipe 2", None)
            ))

        conn.commit()
        conn.close()
        logging.info("✅ Meal Plan Successfully Loaded into Database!")

    except Exception as e:
        logging.error(f"❌ Error loading Excel file: {e}")

# ✅ Get meals for a specific day & week
@app.route('/meals/<int:week>/<int:day>', methods=['GET'])
def get_meals(week, day):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM meals WHERE week=? AND day=?", (week, day))
    meals = cursor.fetchall()
    
    cursor.execute("SELECT * FROM completed_days WHERE day=?", (day,))
    is_completed = cursor.fetchone() is not None
    conn.close()

    meal_list = []
    for meal in meals:
        meal_list.append({
            "meal_type": meal[3],
            "primary_meal": meal[4],
            "primary_recipe": meal[5],
            "alternate_meal_1": meal[6],
            "alternate_recipe_1": meal[7],
            "alternate_meal_2": meal[8],
            "alternate_recipe_2": meal[9],
            "image_url": f"https://source.unsplash.com/100x100/?food&sig={meal[0]}"
        })

    return jsonify({"meals": meal_list, "completed": is_completed})

# ✅ Get list of completed days
@app.route('/completed_days', methods=['GET'])
def get_completed_days():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT day FROM completed_days")
    days = [row[0] for row in cursor.fetchall()]
    conn.close()
    return jsonify(days)

# ✅ Check if data exists in the database
@app.route('/has_data', methods=['GET'])
def check_data():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM meals")
    count = cursor.fetchone()[0]
    conn.close()
    return jsonify({'has_data': count > 0})

# ✅ Debug: Preview meal data
@app.route('/debug/meals', methods=['GET'])
def debug_meals():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM meals")
    meals = cursor.fetchall()
    conn.close()

    if not meals:
        return jsonify({"message": "❌ No meals found in the database!"})

    return jsonify({"meals": meals})

# ✅ Debug: Check if meal_plan.xlsx exists
@app.route('/debug/file_exists', methods=['GET'])
def debug_file():
    return jsonify({
        "file_exists": os.path.exists(EXCEL_FILE),
        "file_path": EXCEL_FILE
    })

# ✅ Force loading meals on first startup only
if __name__ == '__main__':
    init_db()
    load_excel_to_db()  # Load data ONCE
    app.run(host="0.0.0.0", port=10000)
