@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'message': 'No file uploaded'}), 400

    file = request.files['file']

    if not file.filename.endswith('.xlsx'):
        return jsonify({'message': 'Invalid file format. Please upload an .xlsx file'}), 400

    try:
        df = pd.read_excel(file, engine='openpyxl')  # Ensure openpyxl is used

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM meals")  # Clear old data

        for _, row in df.iterrows():
            cursor.execute('''
                INSERT INTO meals (day, meal_type, primary_meal, primary_recipe, 
                                  alternate_meal, alternate_recipe, third_meal_option, third_meal_recipe)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                row['Day'],
                row['Meal Type'],
                row['Primary Meal'],
                row['Primary Recipe'],
                row['Alternate Meal'],
                row['Alternate Recipe'],
                row['Third Meal Option'],
                row['Third Meal Recipe']
            ))

        conn.commit()
        conn.close()

        return jsonify({'message': 'Upload successful'}), 200
    except Exception as e:
        print(f"❌ Upload Error: {e}")  # Print error to logs
        return jsonify({'message': f'Error processing file: {str(e)}'}), 500
