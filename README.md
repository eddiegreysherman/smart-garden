# Flask Starter Application

## Features
- User Registration and Authentication
- SQLite Database
- Bootstrap 5 Styling
- Secure Password Hashing
- Flask-Login Integration

## Setup
1. Clone the repository
2. Create a virtual environment
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```
3. Install dependencies
   ```
   pip install -r requirements.txt
   ```
4. Set up environment variables
   ```
   cp .env.example .env
   ```
5. Initialize the database
   ```
   flask db upgrade
   ```
6. Run the application
   ```
   flask run
   ```

## Security Features
- Password hashing
- CSRF protection
- Secure cookie settings
- Input validation
- User registration checks
