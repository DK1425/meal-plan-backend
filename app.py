from flask import Flask, request, jsonify
import pandas as pd
import sqlite3
import os
import logging
import subprocess
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DATABASE = "meal_plan.db"
EXCEL_FILE = "meal_plan.xlsx"  # This file should be in your repo
LOG_FILE = "backend_log.txt"  # Log file for debugging

# Set up logging
logging.basicConfig(filename=LOG_FILE, level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

logging.info("🚀 Backend Started")

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
    logging.info("✅ Database initialized successfully.")

# Load Excel Data into Database
def load_excel_to_db():
    if not os.path.exists(EXCEL_FILE):
        logging.error("❌ Excel file not found. Please upload `meal_plan.xlsx` to GitHub.")
        return

    try:
        df = pd.read_excel(EXCEL_FILE, engine="openpyxl")

        if df.empty:
            logging.error("❌ Error: The uploaded Excel file is empty!")
            return

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM meals")  # Clear old data
        conn.commit()

        logging.info("🔄 Inserting meal data into the database...")

        for _, row in df.iterrows():
            meal_data = (
                row.get('Day', None),
                row.get('Meal Type', None),
                row.get('Primary Meal', None),
                row.get('Primary Recipe', None),
                row.get('Alternate Meal', None),
                row.get('Alternate Recipe', None),
                row.get('Third Meal Option', None),
                row.get('Third Meal Recipe', None)
            )
            cursor.execute('''
                INSERT INTO meals (day, meal_type, primary_meal, primary_recipe,
                                   alternate_meal, alternate_recipe, third_meal_option, third_meal_recipe)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', meal_data)

            logging.info(f"✅ Inserted: {meal_data}")

        conn.commit()
        conn.close()
        logging.info("✅ Meal Plan Successfully Loaded from Excel into Database!")

    except Exception as e:
        logging.error(f"❌ Error loading Excel file: {e}")

# Debug API: Check if the Excel file exists
@app.route('/debug/file_exists', methods=['GET'])
def debug_file_exists():
    exists = os.path.exists(EXCEL_FILE)
    return jsonify({"file_exists": exists, "file_path": EXCEL_FILE})

# Debug API: Preview Excel file contents
@app.route('/debug/preview_excel', methods=['GET'])
def debug_preview_excel():
    if not os.path.exists(EXCEL_FILE):
        return jsonify({"error": "Excel file not found!"})

    try:
        df = pd.read_excel(EXCEL_FILE, engine="openpyxl")
        return jsonify({"preview": df.head(5).to_dict()})
    except Exception as e:
        return jsonify({"error": str(e)})

# Upload Excel File via API
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        logging.error("❌ No file uploaded.")
        return jsonify({'message': 'No file uploaded'}), 400

    file = request.files['file']

    if not file.filename.endswith('.xlsx'):
        logging.error("❌ Invalid file format. Only .xlsx allowed.")
        return jsonify({'message': 'Invalid file format. Please upload an .xlsx file'}), 400

    try:
        file.save(EXCEL_FILE)  # Save the uploaded file
        logging.info("📂 File uploaded successfully. Reloading database...")
        load_excel_to_db()  # Reload the data
        return jsonify({'message': 'Upload successful'}), 200
    except Exception as e:
        logging.error(f"❌ Upload Error: {e}")
        return jsonify({'message': f'Error processing file: {str(e)}'}), 500

# Get Meals for a Specific Day
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
            "third_meal_option": meal[7],
            "image_url": f"https://source.unsplash.com/100x100/?food&sig={meal[0]}"  
        })

    logging.info(f"📅 Fetching meals for Day {day}: {meal_list}")
    return jsonify({"meals": meal_list, "completed": is_completed})

# Get Completed Days
@app.route('/completed_days', methods=['GET'])
def get_completed_days():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT day FROM completed_days")
    days = [row[0] for row in cursor.fetchall()]
    conn.close()
    logging.info(f"✅ Completed Days: {days}")
    return jsonify(days)

# Check if Data Exists
@app.route('/has_data', methods=['GET'])
def check_data():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM meals")
    count = cursor.fetchone()[0]
    conn.close()
    return jsonify({'has_data': count > 0})

if __name__ == '__main__':
    init_db()
    print("🔄 Forcing Excel file reload on startup...")
    load_excel_to_db()  # Force reload on startup
    app.run(host="0.0.0.0", port=10000)

@app.route('/debug/installed_packages', methods=['GET'])
def installed_packages():
    try:
        output = subprocess.check_output(['pip', 'freeze']).decode('utf-8')
        return jsonify({"installed_packages": output.split("\n")})
    except Exception as e:
        return jsonify({"error": str(e)})
