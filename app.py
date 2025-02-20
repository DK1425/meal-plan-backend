from flask import Flask, request, jsonify
import pandas as pd
import sqlite3
import os
import logging
from flask_cors import CORS

# Initialize Flask App
app = Flask(__name__)
CORS(app)

# Database & File Configurations
DATABASE = "meal_plan.db"
EXCEL_FILE = "meal_plan.xlsx"
LOG_FILE = "backend_log.txt"

# Set up Logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

logging.info("🚀 Backend Started Successfully")

# Initialize Database
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Create meals table if it doesn't exist
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

    # Create completed days table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS completed_days (
            day INTEGER PRIMARY KEY
        )
    ''')

    conn.commit()
    conn.close()
    logging.info("✅ Database Initialized Successfully")

# Load Excel Data into Database
def load_excel_to_db():
    if not os.path.exists(EXCEL_FILE):
        logging.error("❌ Excel file not found! Please upload `meal_plan.xlsx` to GitHub or via UI.")
        return

    try:
        df = pd.read_excel(EXCEL_FILE, engine="openpyxl")

        if df.empty:
            logging.error("❌ Error: The uploaded Excel file is empty!")
            return

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        # Clear old data before inserting new meals
        cursor.execute("DELETE FROM meals")
        conn.commit()

        logging.info("🔄 Inserting meal data into the database...")

        # Insert meal data
        for _, row in df.iterrows():
            meal_data = (
                row.get("Day", None),
                row.get("Meal Type", None),
                row.get("Primary Meal", None),
                row.get("Primary Recipe", None),
                row.get("Alternate Meal", None),
                row.get("Alternate Recipe", None),
                row.get("Third Meal Option", None),
                row.get("Third Meal Recipe", None),
            )

            cursor.execute(
                '''
                INSERT INTO meals (day, meal_type, primary_meal, primary_recipe, 
                                   alternate_meal, alternate_recipe, third_meal_option, third_meal_recipe) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                meal_data,
            )

            logging.info(f"✅ Inserted: {meal_data}")

        conn.commit()
        conn.close()
        logging.info("✅ Meal Plan Successfully Loaded into Database!")

    except Exception as e:
        logging.error(f"❌ Error loading Excel file: {e}")

# API to Upload Excel File
@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        logging.error("❌ No file uploaded.")
        return jsonify({"message": "No file uploaded"}), 400

    file = request.files["file"]

    if not file.filename.endswith(".xlsx"):
        logging.error("❌ Invalid file format. Only .xlsx allowed.")
        return jsonify({"message": "Invalid file format. Please upload an .xlsx file"}), 400

    try:
        file.save(EXCEL_FILE)
        logging.info(f"📂 File uploaded and saved as {EXCEL_FILE}")
        load_excel_to_db()
        return jsonify({"message": "Upload successful"}), 200

    except Exception as e:
        logging.error(f"❌ Upload Error: {e}")
        return jsonify({"message": f"Error processing file: {str(e)}"}), 500

# API to Get Meals for a Specific Day
@app.route("/meals/<int:day>", methods=["GET"])
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
        meal_list.append(
            {
                "meal_type": meal[2],
                "primary_meal": meal[3],
                "primary_recipe": meal[4],
                "alternate_meal": meal[5],
                "third_meal_option": meal[7],
                "image_url": f"https://source.unsplash.com/100x100/?food&sig={meal[0]}",  # Generates random meal images
            }
        )

    logging.info(f"📅 Fetching meals for Day {day}: {meal_list}")
    return jsonify({"meals": meal_list, "completed": is_completed})

# API to Get Completed Days
@app.route("/completed_days", methods=["GET"])
def get_completed_days():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT day FROM completed_days")
    days = [row[0] for row in cursor.fetchall()]
    conn.close()
    logging.info(f"✅ Completed Days: {days}")
    return jsonify(days)

# API to Check if Data Exists
@app.route("/has_data", methods=["GET"])
def check_data():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM meals")
    count = cursor.fetchone()[0]
    conn.close()
    return jsonify({"has_data": count > 0})

# Debug API: Check All Stored Meals
@app.route("/debug/meals", methods=["GET"])
def debug_meals():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM meals")
    meals = cursor.fetchall()
    conn.close()

    if not meals:
        return jsonify({"message": "❌ No meals found in the database!"})

    return jsonify({"meals": meals})

if __name__ == "__main__":
    init_db()
    logging.info("🔄 Force-loading meal_plan.xlsx into the database on startup...")
    load_excel_to_db()
    app.run(host="0.0.0.0", port=10000)
