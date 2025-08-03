from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from datetime import datetime
import uuid

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this in production

# Database config
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="food_order_system"
    )

# Homepage - Show menu
@app.route('/')
def index():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT items.id, items.name, items.price, items.description, 
               items.rating, items.preparation_time, categories.name as category 
        FROM items 
        JOIN categories ON items.category_id = categories.id 
        WHERE items.is_available = TRUE
        ORDER BY categories.name, items.name
    """)
    items = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template('index.html', items=items)

# Signup Page
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form.get('phone')
        gender = request.form.get('gender')
        address = request.form.get('address')
        city = request.form.get('city')
        state = request.form.get('state')
        pincode = request.form.get('pincode')
        
        db = get_db_connection()
        cursor = db.cursor()
        try:
            cursor.execute("""
                INSERT INTO users (name, email, phone, gender, address, city, state, pincode)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (name, email, phone, gender, address, city, state, pincode))
            db.commit()
            user_id = cursor.lastrowid
            session['user_id'] = user_id
            session['user_name'] = name
            flash('Account created successfully!', 'success')
            return redirect(url_for('index'))
        except mysql.connector.IntegrityError:
            flash('Email already exists!', 'error')
        finally:
            cursor.close()
            db.close()
    return render_template('signup.html')

# Login (simple email-based)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT id, name FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        db.close()
        
        if user:
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            flash('Logged in successfully!', 'success')
            return redirect(url_for('index'))
        else:
            flash('User not found!', 'error')
    return render_template('login.html')

# Logout
@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))

# Add to cart
@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    if 'user_id' not in session:
        flash('Please login first!', 'error')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    item_id = request.form['item_id']
    quantity = int(request.form.get('quantity', 1))
    
    db = get_db_connection()
    cursor = db.cursor()
    
    # Check if item already in cart
    cursor.execute("SELECT id, quantity FROM cart WHERE user_id = %s AND item_id = %s", (user_id, item_id))
    existing = cursor.fetchone()
    
    if existing:
        # Update quantity
        new_quantity = existing[1] + quantity
        cursor.execute("UPDATE cart SET quantity = %s WHERE id = %s", (new_quantity, existing[0]))
    else:
        # Add new item
        cursor.execute("INSERT INTO cart (user_id, item_id, quantity) VALUES (%s, %s, %s)", (user_id, item_id, quantity))
    
    db.commit()
    cursor.close()
    db.close()
    flash('Item added to cart!', 'success')
    return redirect(url_for('index'))

# Update cart quantity
@app.route('/update_cart', methods=['POST'])
def update_cart():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    cart_id = request.form['cart_id']
    quantity = int(request.form['quantity'])
    
    db = get_db_connection()
    cursor = db.cursor()
    
    if quantity > 0:
        cursor.execute("UPDATE cart SET quantity = %s WHERE id = %s AND user_id = %s", 
                      (quantity, cart_id, session['user_id']))
    else:
        cursor.execute("DELETE FROM cart WHERE id = %s AND user_id = %s", 
                      (cart_id, session['user_id']))
    
    db.commit()
    cursor.close()
    db.close()
    return redirect(url_for('view_cart'))

# Remove from cart
@app.route('/remove_from_cart/<int:cart_id>')
def remove_from_cart(cart_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("DELETE FROM cart WHERE id = %s AND user_id = %s", (cart_id, session['user_id']))
    db.commit()
    cursor.close()
    db.close()
    flash('Item removed from cart!', 'success')
    return redirect(url_for('view_cart'))

# View cart
@app.route('/cart')
def view_cart():
    if 'user_id' not in session:
        flash('Please login first!', 'error')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT cart.id as cart_id, items.id as item_id, items.name, items.price, 
               cart.quantity, categories.name as category
        FROM cart 
        JOIN items ON cart.item_id = items.id 
        JOIN categories ON items.category_id = categories.id
        WHERE cart.user_id = %s
    """, (user_id,))
    cart_items = cursor.fetchall()
    cursor.close()
    db.close()
    
    total = sum(item['price'] * item['quantity'] for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, total=total)

# Place Order
@app.route('/place_order', methods=['GET', 'POST'])
def place_order():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        user_id = session['user_id']
        delivery_address = request.form.get('delivery_address')
        special_instructions = request.form.get('special_instructions')
        
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        # Get cart items
        cursor.execute("SELECT * FROM cart WHERE user_id = %s", (user_id,))
        cart = cursor.fetchall()
        if not cart:
            flash('Cart is empty!', 'error')
            return redirect(url_for('view_cart'))
        
        # Calculate total
        cursor.execute("""
            SELECT items.price, items.name, cart.quantity, cart.item_id, categories.name as category
            FROM cart 
            JOIN items ON cart.item_id = items.id 
            JOIN categories ON items.category_id = categories.id
            WHERE cart.user_id = %s
        """, (user_id,))
        items = cursor.fetchall()
        total_amount = sum(i['price'] * i['quantity'] for i in items)
        
        # Create order
        cursor.execute("""
            INSERT INTO orders (user_id, total_amount, delivery_address, special_instructions) 
            VALUES (%s, %s, %s, %s)
        """, (user_id, total_amount, delivery_address, special_instructions))
        order_id = cursor.lastrowid
        
        # Add order items
        for item in items:
            cursor.execute("""
                INSERT INTO order_items (order_id, item_id, quantity, price, item_name, item_category) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (order_id, item['item_id'], item['quantity'], item['price'], item['name'], item['category']))
        
        # Clear cart
        cursor.execute("DELETE FROM cart WHERE user_id = %s", (user_id,))
        db.commit()
        cursor.close()
        db.close()
        
        return redirect(url_for('payment', order_id=order_id))
    
    # GET request - show order form
    return render_template('place_order.html')

# Payment Page
@app.route('/payment/<int:order_id>', methods=['GET', 'POST'])
def payment(order_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        method = request.form['method']
        transaction_id = str(uuid.uuid4())[:12]  # Generate random transaction ID
        
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO payment (order_id, method, status, transaction_id) 
            VALUES (%s, %s, 'Completed', %s)
        """, (order_id, method, transaction_id))
        
        # Update order status
        cursor.execute("UPDATE orders SET order_status = 'Confirmed' WHERE id = %s", (order_id,))
        db.commit()
        cursor.close()
        db.close()
        
        return render_template('order_success.html', order_id=order_id, transaction_id=transaction_id)
    
    # Get order details
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM orders WHERE id = %s AND user_id = %s", (order_id, session['user_id']))
    order = cursor.fetchone()
    cursor.close()
    db.close()
    
    if not order:
        flash('Order not found!', 'error')
        return redirect(url_for('index'))
    
    return render_template('payment.html', order=order)

# Order History
@app.route('/orders')
def order_history():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT orders.*, payment.method as payment_method, payment.status as payment_status
        FROM orders 
        LEFT JOIN payment ON orders.id = payment.order_id
        WHERE orders.user_id = %s 
        ORDER BY orders.order_time DESC
    """, (user_id,))
    orders = cursor.fetchall()
    cursor.close()
    db.close()
    
    return render_template('order_history.html', orders=orders)

# Order Details
@app.route('/order/<int:order_id>')
def order_details(order_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    
    # Get order info
    cursor.execute("SELECT * FROM orders WHERE id = %s AND user_id = %s", (order_id, session['user_id']))
    order = cursor.fetchone()
    
    if not order:
        flash('Order not found!', 'error')
        return redirect(url_for('order_history'))
    
    # Get order items
    cursor.execute("SELECT * FROM order_items WHERE order_id = %s", (order_id,))
    items = cursor.fetchall()
    
    # Get payment info
    cursor.execute("SELECT * FROM payment WHERE order_id = %s", (order_id,))
    payment_info = cursor.fetchone()
    
    cursor.close()
    db.close()
    
    return render_template('order_details.html', order=order, items=items, payment=payment_info)

if __name__ == '__main__':
    app.run(debug=True)