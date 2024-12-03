from flask import Flask, jsonify, request
import mysql.connector
from config import DATABASE

from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required

app = Flask(__name__)


bcrypt = Bcrypt(app)
app.config['JWT_SECRET_KEY'] = 'your-secret-key'
jwt = JWTManager(app)

# Register user
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    conn = get_db_connection()
    cursor = conn.cursor()
    query = 'INSERT INTO Users (username, password_hash) VALUES (%s, %s)'
    cursor.execute(query, (data['username'], hashed_password))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'message': 'User registered successfully'}), 201

# Login user
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM Users WHERE username = %s', (data['username'],))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if user and bcrypt.check_password_hash(user['password_hash'], data['password']):
        access_token = create_access_token(identity=user['user_id'])
        return jsonify({'access_token': access_token}), 200
    else:
        return jsonify({'message': 'Invalid credentials'}), 401

# Database connection function
def get_db_connection():
    conn = mysql.connector.connect(
        host=DATABASE['host'],
        user=DATABASE['user'],
        password=DATABASE['password'],
        database=DATABASE['database']
    )
    return conn

@app.route('/')
def index():
    return jsonify({'message': 'Connected successfully to Flask!'})

@app.route('/products', methods=['GET'])
def get_all_products():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM Product')
    products = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(products)

@app.route('/products', methods=['POST'])
def add_product():
    try:
        data = request.get_json()
        if not data or 'product_name' not in data:
            return jsonify({'error': 'Invalid input'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        query = '''
            INSERT INTO Product (product_name, tags, quantity, description, location_id)
            VALUES (%s, %s, %s, %s, %s)
        '''
        values = (
            data['product_name'],
            data['tags'],
            data['quantity'],
            data['description'],
            data['location_id']
        )
        cursor.execute(query, values)
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'message': 'Product added successfully'}), 201
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500


@app.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()
    query = '''
        UPDATE Product
        SET product_name = %s, tags = %s, quantity = %s, description = %s, location_id = %s
        WHERE product_id = %s
    '''
    values = (
        data['product_name'],
        data['tags'],
        data['quantity'],
        data['description'],
        data['location_id'],
        product_id
    )
    cursor.execute(query, values)
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'message': 'Product updated successfully'})

@app.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = 'DELETE FROM Product WHERE product_id = %s'
    cursor.execute(query, (product_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'message': 'Product deleted successfully'})



@app.route('/inbound', methods=['POST'])
def add_inbound():
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()
    query = '''
        INSERT INTO Inbound (product_id, supplier_id, quantity_received, received_date)
        VALUES (%s, %s, %s, %s)
    '''
    values = (
        data['product_id'],
        data['supplier_id'],
        data['quantity_received'],
        data['received_date']
    )
    cursor.execute(query, values)
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'message': 'Inbound record added successfully'}), 201

@app.route('/outbound', methods=['POST'])
def add_outbound():
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()
    query = '''
        INSERT INTO Outbound (product_id, customer_id, quantity_sent, sent_date)
        VALUES (%s, %s, %s, %s)
    '''
    values = (
        data['product_id'],
        data['customer_id'],
        data['quantity_sent'],
        data['sent_date']
    )
    cursor.execute(query, values)
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'message': 'Outbound record added successfully'}), 201





if __name__ == '__main__':
    app.run(debug=True)
