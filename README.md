# Bookstore Management System

A professional web-based bookstore management system built with Flask, featuring both customer and admin interfaces. The system allows customers to browse books, place orders, and manage their accounts, while administrators can manage books, categories, orders, and users.

## Features

### Customer Features
- User registration and authentication
- Browse books by category
- Search for books
- Add books to shopping cart
- Place orders
- View order history
- Update profile information

### Admin Features
- Secure admin dashboard
- Manage books (add, edit, delete)
- Manage categories
- Process orders
- View sales statistics
- Manage user accounts
- Track inventory

## Technologies Used
- Python 3.x
- Flask
- SQLAlchemy
- Flask-Login
- Bootstrap 5
- Font Awesome Icons

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/bookstore-management-system.git
cd bookstore-management-system
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

4. Initialize the database:
```bash
flask db init
flask db migrate
flask db upgrade
```

5. Run the application:
```bash
python app.py
```

The application will be available at `http://localhost:5000`

## Default Admin Account
- Username: admin
- Password: admin123

## Project Structure
```
bookstore-management-system/
├── app.py
├── requirements.txt
├── README.md
├── instance/
│   └── bookstore.db
└── templates/
    ├── base.html
    ├── index.html
    ├── login.html
    ├── register.html
    └── admin/
        ├── dashboard.html
        ├── books.html
        ├── categories.html
        ├── orders.html
        └── view_order.html
```

## Security Features
- Password hashing
- User authentication
- Admin-only access to management features
- CSRF protection
- Secure session management

## Contributing
1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments
- Bootstrap for the UI components
- Font Awesome for the icons
- Flask team for the amazing framework 