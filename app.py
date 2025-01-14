import os
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dependencies import Input, Output
import logging
import threading
from dotenv import load_dotenv
from flask import Flask, redirect, url_for, request, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from passlib.hash import pbkdf2_sha256
from cache_config import cache, initialize_cache, get_visualizations
import plotly.graph_objects as go
from watchdog_handler import start_watchdog
from callbacks import register_callbacks
from colorlog import ColoredFormatter
import signal
import sys
from OpenSSL import SSL
from flask_socketio import SocketIO

# Signal handler to release the port on exit
def signal_handler(sig, frame):
    print("Gracefully stopping the application...")
    sys.exit(0)

# Register signal handler
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Initialize Flask server
server = Flask(__name__)

# Load environment variables from .env file
load_dotenv()

# Configure colorlog
formatter = ColoredFormatter(
    "%(log_color)s%(levelname)s:%(name)s:%(message)s",
    datefmt=None,
    reset=True,
    log_colors={
        'DEBUG': 'cyan',
        'INFO': 'blue',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'red,bg_white',
    }
)

handler = logging.StreamHandler()
handler.setFormatter(formatter)

# Configure logging
logging.basicConfig(level=logging.INFO, handlers=[handler])
logger = logging.getLogger(__name__)

# Suppress Werkzeug logs
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# Fixed Database URI
server.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
server.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
server.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(server)

# Flask-Login configuration
login_manager = LoginManager()
login_manager.init_app(server)
login_manager.login_view = "/login"

# User model for the MySQL database
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    registration_code = db.Column(db.String(50), nullable=True)
    is_active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.now())

    def set_password(self, password):
        self.password_hash = pbkdf2_sha256.hash(password)

    def check_password(self, password):
        return pbkdf2_sha256.verify(password, self.password_hash)

# Load user for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@server.route('/')
def index():
    # If user is authenticated, redirect to dashboard
    if current_user.is_authenticated:
        return redirect('/dashboard')
    else:
        return redirect('/login')


@server.route('/dashboard')
@login_required  # Ensure the user is logged in
def dashboard_redirect():
    # Render the dashboard layout or redirect to main Dash page
    return app.index()  # Directly serve Dash app if logged in

# Flask route for registration with a code
@server.route('/register', methods=['GET', 'POST'])
def register():
    error_message = None

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        registration_code = request.form['code']
        
        # Check if username or email already exists
        if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
            error_message = 'Username or email already exists'

        # Check if email ends with .edu
        elif not email.endswith('.edu'):
            error_message = 'Registration is only allowed for special email addresses'

        # Validate the registration code
        elif registration_code != os.getenv('AUTH_CODE'):
            error_message = 'Invalid registration code'

        # Check if both passwords match
        elif password != confirm_password:
            error_message = 'Passwords do not match'

        if error_message is None:
            # Create new user and save to the database
            new_user = User(username=username, email=email, registration_code=registration_code, is_active=True)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()

            return redirect(url_for('login'))

    return f'''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Register</title>
            <link rel="stylesheet" href="/assets/styles.css">
        </head>
        <body class="auth-body">
            <div class="auth-container">
                <div class="auth-card">
                    <h2 class="auth-h2">Register</h2>
                    <form class="auth-form" method="POST">
                        <input class="auth-input" type="text" name="username" placeholder="Username" required>
                        <input class="auth-input" type="email" name="email" placeholder="Email" required>
                        <input class="auth-input" type="password" name="password" placeholder="Password" required>
                        <input class="auth-input" type="password" name="confirm_password" placeholder="Confirm Password" required>
                        <input class="auth-input" type="text" name="code" placeholder="Registration Code" required>
                        {f'<p style="color:red;">{error_message}</p>' if error_message else ''}
                        <button class="auth-button" type="submit">Register</button>
                    </form>
                </div>
            </div>
        </body>
        </html>
    '''

# Flask route for login
@server.route('/login', methods=['GET', 'POST'])
def login():
    error_message = None

    if request.method == 'POST':
        login_credential = request.form['username_or_email']
        password = request.form['password']

        # Allow login via username or email
        if '@' in login_credential:
            user = User.query.filter_by(email=login_credential).first()
        else:
            user = User.query.filter_by(username=login_credential).first()

        if user and user.check_password(password):
            login_user(user)

            # Redirect to the page the user was trying to access, or default to dashboard
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard_redirect'))

        else:
            error_message = 'Invalid username/email or password'

    return f'''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Login</title>
            <link rel="stylesheet" href="/assets/styles.css">
        </head>
        <body class="auth-body">
            <div class="auth-container">
                <div class="auth-card">
                    <h2 class="auth-h2">Login</h2>
                    <form class="auth-form" method="POST">
                        <input class="auth-input" type="text" name="username_or_email" placeholder="Username or Email" required>
                        <input class="auth-input" type="password" name="password" placeholder="Password" required>
                        {f'<p style="color:red;">{error_message}</p>' if error_message else ''}
                        <button class="auth-button" type="submit">Login</button>
                    </form>
               </div>
            </div>
        </body>
        </html>
    '''

# Flask route for password reset
@server.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    error_message = None

    if request.method == 'POST':
        email = request.form['email']
        old_password = request.form['old_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        user = User.query.filter_by(email=email).first()

        if user is None:
            error_message = 'Invalid email address'
        elif not user.check_password(old_password):
            error_message = 'Old password is incorrect'
        elif new_password != confirm_password:
            error_message = 'New passwords do not match'
        else:
            # Update password and commit to database
            user.set_password(new_password)
            db.session.commit()
            return redirect(url_for('login'))

    return f'''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Reset Password</title>
            <link rel="stylesheet" href="/assets/styles.css">
        </head>
        <body class="auth-body">
            <div class="auth-container">
                <div class="auth-card">
                    <h2 class="auth-h2">Reset Password</h2>
                    <form class="auth-form" method="POST">
                        <input class="auth-input" type="email" name="email" placeholder="Email" required>
                        <input class="auth-input" type="password" name="old_password" placeholder="Old Password" required>
                        <input class="auth-input" type="password" name="new_password" placeholder="New Password" required>
                        <input class="auth-input" type="password" name="confirm_password" placeholder="Confirm New Password" required>
                        {f'<p style="color:red;">{error_message}</p>' if error_message else ''}
                        <button class="auth-button" type="submit">Reset Password</button>
                    </form>
                </div>
            </div>
        </body>
        </html>
    '''
# Flask route for logout
@server.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# IMPORTANT: initialize cache AFTER creating server but BEFORE loading layouts
cache.init_app(server, config={
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR': 'cache-directory',
    'CACHE_DEFAULT_TIMEOUT': 3600
})

with server.app_context():
    initialize_cache()

# Initialize SocketIO
socketio = SocketIO(server, cors_allowed_origins="*")

# Now import layouts after cache is initialized
from layouts import (
    overview_layout,
    one_hour_layout,
    twenty_four_hour_layout,
    seven_days_layout,
)

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], server=server, suppress_callback_exceptions=True)

# Register the callbacks with the Dash app
register_callbacks(app)

app.layout = html.Div(
    [
        dcc.Location(id='url', refresh=False),
        html.Div(id='page-content')
    ]
)

@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')]
)
def display_page(pathname):
    if not current_user.is_authenticated:
        return redirect('/login')
    
    if pathname == '/1_hour_data':
        return one_hour_layout
    elif pathname == '/24_hours_data':
        return twenty_four_hour_layout
    elif pathname == '/7_days_data':
        return seven_days_layout
    else:
        return overview_layout


if __name__ == "__main__":
    logger.info("Starting the application...")

    # Start the watchdog in a separate thread
    directory_to_watch = "/home/iaes/DiodeSensor/FM1/output/"
    watchdog_thread = threading.Thread(target=start_watchdog, args=(directory_to_watch, app.server))
    watchdog_thread.daemon = True
    watchdog_thread.start()

    # Run the Dash app with SSL on 0.0.0.0:80 (Debug)
    logger.info("Initializing the server")
    socketio.run(server, host=os.getenv('IP'), port=443, debug=False, use_reloader=False, ssl_context=('./certs/pem.pem', './certs/key.key'))