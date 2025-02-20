from flask import Flask, jsonify
import pandas as pd
import sqlite3
import os
import logging
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Database and Excel File
DATABASE = "meal_plan.db"
EXCEL_FILE = "meal_plan.xlsx"
LOG_FILE = "backend_log.txt"

# Configure Logging
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logging.info("🚀 Backend started successfully.")

# Initialize Database
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS meals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        day INTEGER,
        meal_type TEXT,
        primary_meal TEXT,
        primary_recipe TEXT,
        alternate_meal_1 TEXT,
        alternate_recipe_1 TEXT,
        alternate_meal_2 TEXT,
        alternate_recipe_2 TEXT
    )''')
    conn.commit()
    conn.close()
    logging.info("✅ Database initialized.")

# Load Excel Data into Database (Only If Empty)
def load_excel_to_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Check if database already has meals (avoid reloading)
    cursor.execute("SELECT COUNT(*) FROM meals")
    count = cursor.fetchone()[0]
    
    if count > 0:
        logging.info("🔄 Data already exists in the database. Skipping reload.")
        conn.close()
        return

    # Ensure Excel file exists before loading
    if not os.path.exists(EXCEL_FILE):
        logging.error("❌ Excel file not found. Please upload `meal_plan.xlsx` to GitHub.")
        conn.close()
        return

    try:
        df = pd.read_excel(EXCEL_FILE, engine="openpyxl")

        # Check if DataFrame is empty
        if df.empty:
            logging.error("❌ Error: The uploaded Excel file is empty!")
            conn.close()
            return

        # Insert meal data into database
        cursor.execute("DELETE FROM meals")  # Clear old data
        for _, row in df.iterrows():
            meal_data = (
                row.get("Day", None),
                row.get("Meal Type", None),
                row.get("Primary Meal", None),
                row.get("Primary Recipe", None),
                row.get("Alternate Meal 1", None),
                row.get("Alternate Recipe 1", None),
                row.get("Alternate Meal 2", None),
                row.get("Alternate Recipe 2", None),
            )
            cursor.execute('''INSERT INTO meals (day, meal_type, primary_meal, primary_recipe, 
                              alternate_meal_1, alternate_recipe_1, alternate_meal_2, alternate_recipe_2)
                              VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', meal_data)

        conn.commit()
        logging.info("✅ Meal Plan Successfully Loaded from Excel into Database!")

    except Exception as e:
        logging.error(f"❌ Error loading Excel file: {e}")
    
    conn.close()

# Get Meals for a Specific Day
@app.route('/meals/<int:day>', methods=['GET'])
def get_meals(day):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM meals WHERE day=?", (day,))
    meals = cursor.fetchall()
    conn.close()

    if not meals:
        return jsonify({"message": "❌ No meals found for this day!"})

    meal_list = []
    for meal in meals:
        meal_list.append({
            "meal_type": meal[2],
            "primary_meal": meal[3],
            "primary_recipe": meal[4],
            "alternate_meal_1": meal[5],
            "alternate_recipe_1": meal[6],
            "alternate_meal_2": meal[7],
            "alternate_recipe_2": meal[8]
        })

    return jsonify({"meals": meal_list})

# Debug: Check if File Exists
@app.route('/debug/file_exists', methods=['GET'])
def debug_file():
    return jsonify({"file_exists": os.path.exists(EXCEL_FILE), "file_path": EXCEL_FILE})

# Debug: Get All Meals in Database
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

# Run the App
if __name__ == '__main__':
    init_db()
    load_excel_to_db()
    app.run(host="0.0.0.0", port=10000)
