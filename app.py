from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import csv
from io import StringIO
from flask import Response

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bookstore.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    orders = db.relationship('Order', backref='user', lazy=True)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    image_url = db.Column(db.String(200))

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    books = db.relationship('Book', backref='category', lazy=True)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')
    items = db.relationship('OrderItem', backref='order', lazy=True)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    books = Book.query.all()
    categories = Category.query.all()
    return render_template('index.html', books=books, categories=categories)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username')).first()
        if user and check_password_hash(user.password_hash, request.form.get('password')):
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
        
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    # Get statistics for the dashboard
    books = Book.query.all()
    orders = Order.query.all()
    users = User.query.all()
    recent_orders = Order.query.order_by(Order.date.desc()).limit(5).all()
    low_stock_books = Book.query.filter(Book.stock < 10).all()
    
    # Calculate total revenue
    total_revenue = sum(order.total_amount for order in orders)
    
    # Prepare statistics
    stats = {
        'total_books': len(books),
        'total_orders': len(orders),
        'total_users': len(users),
        'total_revenue': total_revenue,
        'last_updated': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    return render_template('admin/dashboard.html',
                         stats=stats,
                         recent_orders=recent_orders,
                         low_stock_books=low_stock_books)

# Admin routes for managing books
@app.route('/admin/books')
@login_required
def admin_books():
    if not current_user.is_admin:
        return redirect(url_for('index'))
    books = Book.query.all()
    return render_template('admin/books.html', books=books)

@app.route('/admin/books/add', methods=['GET', 'POST'])
@login_required
def add_book():
    if not current_user.is_admin:
        return redirect(url_for('index'))
    if request.method == 'POST':
        book = Book(
            title=request.form.get('title'),
            author=request.form.get('author'),
            price=float(request.form.get('price')),
            stock=int(request.form.get('stock')),
            description=request.form.get('description'),
            category_id=int(request.form.get('category_id')),
            image_url=request.form.get('image_url')
        )
        db.session.add(book)
        db.session.commit()
        flash('Book added successfully')
        return redirect(url_for('admin_books'))
    categories = Category.query.all()
    return render_template('admin/add_book.html', categories=categories)

@app.route('/admin/books/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_book(id):
    if not current_user.is_admin:
        return redirect(url_for('index'))
    book = Book.query.get_or_404(id)
    if request.method == 'POST':
        book.title = request.form.get('title')
        book.author = request.form.get('author')
        book.price = float(request.form.get('price'))
        book.stock = int(request.form.get('stock'))
        book.description = request.form.get('description')
        book.category_id = int(request.form.get('category_id'))
        book.image_url = request.form.get('image_url')
        db.session.commit()
        flash('Book updated successfully')
        return redirect(url_for('admin_books'))
    categories = Category.query.all()
    return render_template('admin/edit_book.html', book=book, categories=categories)

@app.route('/admin/books/delete/<int:id>')
@login_required
def delete_book(id):
    if not current_user.is_admin:
        return redirect(url_for('index'))
    book = Book.query.get_or_404(id)
    db.session.delete(book)
    db.session.commit()
    flash('Book deleted successfully')
    return redirect(url_for('admin_books'))

# Admin routes for managing categories
@app.route('/admin/categories')
@login_required
def admin_categories():
    if not current_user.is_admin:
        return redirect(url_for('index'))
    categories = Category.query.all()
    return render_template('admin/categories.html', categories=categories)

@app.route('/admin/categories/add', methods=['GET', 'POST'])
@login_required
def add_category():
    if not current_user.is_admin:
        return redirect(url_for('index'))
    if request.method == 'POST':
        category = Category(name=request.form.get('name'))
        db.session.add(category)
        db.session.commit()
        flash('Category added successfully')
        return redirect(url_for('admin_categories'))
    return render_template('admin/add_category.html')

@app.route('/admin/categories/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_category(id):
    if not current_user.is_admin:
        return redirect(url_for('index'))
    category = Category.query.get_or_404(id)
    if request.method == 'POST':
        category.name = request.form.get('name')
        db.session.commit()
        flash('Category updated successfully')
        return redirect(url_for('admin_categories'))
    return render_template('admin/edit_category.html', category=category)

@app.route('/admin/categories/delete/<int:id>')
@login_required
def delete_category(id):
    if not current_user.is_admin:
        return redirect(url_for('index'))
    category = Category.query.get_or_404(id)
    db.session.delete(category)
    db.session.commit()
    flash('Category deleted successfully')
    return redirect(url_for('admin_categories'))

# Admin routes for managing orders
@app.route('/admin/orders')
@login_required
def admin_orders():
    if not current_user.is_admin:
        return redirect(url_for('index'))
    orders = Order.query.order_by(Order.date.desc()).all()
    return render_template('admin/orders.html', orders=orders)

@app.route('/admin/orders/<int:id>')
@login_required
def view_order(id):
    if not current_user.is_admin:
        return redirect(url_for('index'))
    order = Order.query.get_or_404(id)
    return render_template('admin/view_order.html', order=order)

@app.route('/admin/orders/update_status/<int:id>', methods=['POST'])
@login_required
def update_order_status(id):
    if not current_user.is_admin:
        return redirect(url_for('index'))
    order = Order.query.get_or_404(id)
    order.status = request.form.get('status')
    db.session.commit()
    flash('Order status updated successfully')
    return redirect(url_for('admin_orders'))

# Admin User Management Routes
@app.route('/admin/users')
@login_required
def admin_users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/users/<int:id>')
@login_required
def get_user(id):
    user = User.query.get_or_404(id)
    return jsonify({
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'role': user.role,
        'is_active': user.is_active,
        'orders': [{'id': order.id, 'total_amount': order.total_amount} for order in user.orders]
    })

@app.route('/admin/users/<int:id>/edit', methods=['POST'])
@login_required
def edit_user(id):
    user = User.query.get_or_404(id)
    data = request.form
    
    user.name = data.get('name')
    user.email = data.get('email')
    user.role = data.get('role')
    user.is_active = 'is_active' in data
    
    db.session.commit()
    flash('User updated successfully!', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/users/<int:id>/delete', methods=['POST'])
@login_required
def delete_user(id):
    user = User.query.get_or_404(id)
    
    # Prevent deleting the last admin
    if user.role == 'admin' and User.query.filter_by(role='admin').count() <= 1:
        return jsonify({'success': False, 'message': 'Cannot delete the last admin user'})
    
    # Delete user's orders first
    Order.query.filter_by(user_id=id).delete()
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/admin/users/export')
@login_required
def export_users():
    users = User.query.all()
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Name', 'Email', 'Role', 'Status', 'Orders Count'])
    
    for user in users:
        writer.writerow([
            user.id,
            user.name,
            user.email,
            user.role,
            'Active' if user.is_active else 'Inactive',
            len(user.orders)
        ])
    
    output.seek(0)
    return Response(
        output,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=users.csv'}
    )

@app.route('/admin/orders/export')
@login_required
def export_orders():
    orders = Order.query.all()
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Order ID', 'Customer', 'Date', 'Amount', 'Status'])
    
    for order in orders:
        writer.writerow([
            order.id,
            order.user.username,
            order.date.strftime('%Y-%m-%d %H:%M'),
            f"${order.total_amount:.2f}",
            order.status.title()
        ])
    
    output.seek(0)
    return Response(
        output,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=orders.csv'}
    )

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Create admin user if not exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@bookstore.com',
                password_hash=generate_password_hash('admin123'),
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
            
        # Create some sample categories if none exist
        if not Category.query.first():
            categories = [
                Category(name='Fiction'),
                Category(name='Non-Fiction'),
                Category(name='Science'),
                Category(name='Technology'),
                Category(name='History'),
                Category(name='Biography')
            ]
            for category in categories:
                db.session.add(category)
            db.session.commit()
            
        # Create some sample books if none exist
        if not Book.query.first():
            books = [
                Book(
                    title='The Great Gatsby',
                    author='F. Scott Fitzgerald',
                    price=9.99,
                    stock=15,
                    description='A story of decadence and excess...',
                    category_id=1
                ),
                Book(
                    title='1984',
                    author='George Orwell',
                    price=12.99,
                    stock=20,
                    description='A dystopian social science fiction novel...',
                    category_id=1
                ),
                Book(
                    title='A Brief History of Time',
                    author='Stephen Hawking',
                    price=14.99,
                    stock=10,
                    description='From the Big Bang to Black Holes...',
                    category_id=3
                )
            ]
            for book in books:
                db.session.add(book)
            db.session.commit()
            
    app.run(debug=True) 