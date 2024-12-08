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




# Get a product by ID
@app.route('/products/<int:product_id>', methods=['GET'])
@login_required
def get_product(product_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM Product WHERE product_id = %s', (product_id,))
        product = cursor.fetchone()
        if product:
            return jsonify(product)
        return jsonify({'error': 'Product not found'}), 404
    finally:
        cursor.close()
        conn.close()

# Add a new product (Manager only)
@app.route('/products', methods=['POST'])
@manager_required
def add_product():
    data = request.json
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO Product (product_name, tags, description, quantity) VALUES (%s, %s, %s, %s)',
            (data['product_name'], data['tags'], data['description'], data['quantity'])
        )
        conn.commit()
        return jsonify({'message': 'Product added successfully'}), 201
    finally:
        cursor.close()
        conn.close()

# Update an existing product (Manager only)
@app.route('/products/<int:product_id>', methods=['PUT'])
@manager_required
def update_product(product_id):
    data = request.json
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE Product SET product_name = %s, tags = %s, description = %s, quantity = %s WHERE product_id = %s',
            (data['product_name'], data['tags'], data['description'], data['quantity'], product_id)
        )
        conn.commit()
        if cursor.rowcount > 0:
            return jsonify({'message': 'Product updated successfully'})
        return jsonify({'error': 'Product not found'}), 404
    finally:
        cursor.close()
        conn.close()

# Delete a product (Manager only)
@app.route('/products/<int:product_id>', methods=['DELETE'])
@manager_required
def delete_product(product_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM Product WHERE product_id = %s', (product_id,))
        conn.commit()
        if cursor.rowcount > 0:
            return jsonify({'message': 'Product deleted successfully'}), 200
        return jsonify({'error': 'Product not found'}), 404
    finally:
        cursor.close()
        conn.close()


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


# Log an inbound record
@app.route('/inbound', methods=['POST'])
@login_required
def log_inbound():
    data = request.json
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        print("Inbound data received:", data)  # Debug: Log incoming data
        
        # Check if the product exists in the inventory
        cursor.execute('SELECT COUNT(*) FROM Product WHERE product_id = %s', (data['product_id'],))
        exists = cursor.fetchone()[0]
        print("Product exists in inventory:", exists)  # Debug: Log existence check

        if exists:
            # Update product quantity
            cursor.execute(
                'UPDATE Product SET quantity = quantity + %s WHERE product_id = %s',
                (data['quantity_received'], data['product_id'])
            )
            print("Product quantity updated.")  # Debug: Log update
        else:
            # Add new product if it doesn't exist
            cursor.execute(
                'INSERT INTO Product (product_id, product_name, tags, quantity, description) VALUES (%s, %s, %s, %s, %s)',
                (data['product_id'], data.get('product_name', ''), data.get('tags', ''), data['quantity_received'], data.get('description', ''))
            )
            print("New product added to inventory.")  # Debug: Log new product insertion

        # Add to Inbound table
        cursor.execute(
            'INSERT INTO Inbound (product_id, supplier_id, quantity_received, received_date) VALUES (%s, %s, %s, %s)',
            (data['product_id'], data['supplier_id'], data['quantity_received'], data['received_date'])
        )
        conn.commit()
        print("Inbound record added.")  # Debug: Log inbound record insertion
        return jsonify({'message': 'Inbound record added and inventory updated successfully'}), 201
    except Exception as e:
        conn.rollback()
        print("Error:", e)  # Debug: Log errors
        return jsonify({'error': str(e)}), 400
    finally:
        cursor.close()
        conn.close()


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

# Log an outbound record
@app.route('/outbound', methods=['POST'])
@login_required
def log_outbound():
    data = request.json  # Get JSON data from the client
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        # Step 1: Check if the product exists
        cursor.execute('SELECT quantity FROM Product WHERE product_id = %s', (data['product_id'],))
        result = cursor.fetchone()
        if not result:
            return jsonify({'error': 'Product not found'}), 404

        # Step 2: Ensure quantity values are integers for proper comparison
        current_quantity = int(result[0])  # Convert to integer
        quantity_sent = int(data['quantity_sent'])  # Convert to integer

        # Step 3: Check if there is sufficient quantity
        if current_quantity < quantity_sent:
            return jsonify({'error': 'Insufficient quantity in inventory'}), 400

        # Step 4: Reduce the quantity in the inventory
        new_quantity = current_quantity - quantity_sent
        cursor.execute(
            'UPDATE Product SET quantity = %s WHERE product_id = %s',
            (new_quantity, data['product_id'])
        )

        # Step 5: (Optional) Remove the product if the quantity reaches zero
        if new_quantity == 0:
            cursor.execute('DELETE FROM Product WHERE product_id = %s', (data['product_id'],))

        # Step 6: Record the outbound operation in the Outbound table
        cursor.execute(
            'INSERT INTO Outbound (product_id, customer_id, quantity_sent, sent_date) VALUES (%s, %s, %s, %s)',
            (data['product_id'], data['customer_id'], quantity_sent, data['sent_date'])
        )

        # Commit the transaction
        conn.commit()

        return jsonify({'message': 'Outbound record logged successfully'}), 201
    except Exception as e:
        conn.rollback()  # Roll back in case of error
        return jsonify({'error': str(e)}), 400
    finally:
        cursor.close()
        conn.close()



# test connection to database
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
