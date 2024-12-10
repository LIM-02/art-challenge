from flask import Flask, jsonify, request, render_template, redirect, url_for, session
import mysql.connector
from config import DATABASE
from models import User
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with your actual secret key


# Database connection function
def get_db_connection():
    conn = mysql.connector.connect(**DATABASE)
    return conn


# Authentication decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def manager_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'manager':
            return jsonify({'error': 'Manager access required'}), 403
        return f(*args, **kwargs)
    return decorated_function


# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.get_by_username(username)
        if user and user.password_hash == password:
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            return redirect(url_for('index'))
        else:
            error = 'Invalid username or password'
            return render_template('login.html', error=error)
    return render_template('login.html')


# Logout route
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# Home route
@app.route('/')
@login_required
def index():
    return render_template('index.html', username=session.get('username'), role=session.get('role'))


# Get all products
@app.route('/products', methods=['GET'])
@login_required
def get_all_products():
    limit = request.args.get('limit', 10, type=int)
    offset = request.args.get('offset', 0, type=int)
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM Product LIMIT %s OFFSET %s', (limit, offset))
        products = cursor.fetchall()
        return jsonify(products)
    finally:
        cursor.close()
        conn.close()



# Get a product by SKU
@app.route('/products/<string:sku>', methods=['GET'])
@login_required
def get_product(sku):
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM Product WHERE sku = %s', (sku,))
        product = cursor.fetchone()
        if product:
            return jsonify(product)
        return jsonify({'error': 'Product not found'}), 404
    except mysql.connector.Error as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    finally:
        cursor.close()
        conn.close()


# Add a new product (Manager only)
@app.route('/products', methods=['POST'])
@manager_required
def add_product():
    data = request.json
    required_fields = ['sku', 'product_name', 'category', 'description', 'quantity', 'location', 'supplier']

    # Validate required fields
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({'error': f'Missing or invalid field: {field}'}), 400

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO Product (sku, product_name, category, description, quantity, location, supplier) VALUES (%s, %s, %s, %s, %s, %s, %s)',
            (data['sku'], data['product_name'], data['category'], data['description'], data['quantity'], data['location'], data['supplier'])
        )
        conn.commit()
        return jsonify({'message': 'Product added successfully'}), 201
    except mysql.connector.Error as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    finally:
        cursor.close()
        conn.close()



# Update an existing product (Manager only)
@app.route('/products/<string:sku>', methods=['PUT'])
@manager_required
def update_product(sku):
    data = request.json
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE Product SET product_name = %s, category = %s, description = %s, quantity = %s, location = %s, supplier = %s WHERE sku = %s',
            (data['product_name'], data['category'], data['description'], data['quantity'], data['location'], data['supplier'], sku)
        )
        conn.commit()
        if cursor.rowcount > 0:
            return jsonify({'message': 'Product updated successfully'})
        return jsonify({'error': 'Product not found'}), 404
    finally:
        cursor.close()
        conn.close()


# Delete a product (Manager only)
@app.route('/products/<string:sku>', methods=['DELETE'])
@manager_required
def delete_product(sku):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM Product WHERE sku = %s', (sku,))
        conn.commit()
        if cursor.rowcount > 0:
            return jsonify({'message': 'Product deleted successfully'}), 200
        return jsonify({'error': 'Product not found'}), 404
    finally:
        cursor.close()
        conn.close()


# Fetch Inbound Records
@app.route('/inbound', methods=['GET'])
@login_required
def get_inbound_records():
    limit = request.args.get('limit', 10, type=int)
    offset = request.args.get('offset', 0, type=int)
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM Inbound LIMIT %s OFFSET %s', (limit, offset))
        records = cursor.fetchall()
        return jsonify(records)
    finally:
        cursor.close()
        conn.close()


# Log an Inbound Record
@app.route('/inbound', methods=['POST'])
@login_required
def log_inbound():
    data = request.json
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        # Check if product exists
        cursor.execute('SELECT COUNT(*) FROM Product WHERE sku = %s', (data['product_sku'],))
        if cursor.fetchone()[0] == 0:
            return jsonify({'error': 'Product SKU not found'}), 400

        # Proceed with inbound record logging
        cursor.execute(
            'UPDATE Product SET quantity = quantity + %s WHERE sku = %s',
            (data['quantity_received'], data['product_sku'])
        )
        cursor.execute(
            'INSERT INTO Inbound (reference, product_sku, supplier_id, quantity_received, received_date, location, remarks) VALUES (%s, %s, %s, %s, %s, %s, %s)',
            (data['reference'], data['product_sku'], data['supplier_id'], data['quantity_received'], data['received_date'], data['location'], data['remarks'])
        )
        conn.commit()
        return jsonify({'message': 'Inbound record logged successfully'}), 201
    except mysql.connector.Error as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    finally:
        cursor.close()
        conn.close()



# Fetch Outbound Records
@app.route('/outbound', methods=['GET'])
@login_required
def get_outbound_records():
    limit = request.args.get('limit', 10, type=int)
    offset = request.args.get('offset', 0, type=int)
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM Outbound LIMIT %s OFFSET %s', (limit, offset))
        records = cursor.fetchall()
        return jsonify(records)
    finally:
        cursor.close()
        conn.close()


# Log an Outbound Record
@app.route('/outbound', methods=['POST'])
@login_required
def log_outbound():
    data = request.json
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        # Check product quantity
        cursor.execute('SELECT quantity FROM Product WHERE sku = %s', (data['product_sku'],))
        result = cursor.fetchone()
        if not result or result[0] < data['quantity_sent']:
            return jsonify({'error': 'Insufficient quantity or product not found'}), 400

        # Reduce product quantity
        cursor.execute('UPDATE Product SET quantity = quantity - %s WHERE sku = %s', (data['quantity_sent'], data['product_sku']))

        # Insert into Outbound table
        cursor.execute(
            'INSERT INTO Outbound (reference, product_sku, customer_id, quantity_sent, sent_date, destination, remarks) VALUES (%s, %s, %s, %s, %s, %s, %s)',
            (data['reference'], data['product_sku'], data['customer_id'], data['quantity_sent'], data['sent_date'], data['destination'], data['remarks'])
        )
        conn.commit()
        return jsonify({'message': 'Outbound record logged successfully'}), 201
    finally:
        cursor.close()
        conn.close()


# Test database connection
@app.route('/test-db', methods=['GET'])
def test_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SHOW TABLES;')
        tables = cursor.fetchall()
        return jsonify({'tables': [table[0] for table in tables]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
