import os
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dependencies import Input, Output
import logging
from dotenv import load_dotenv
from flask import Flask, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from passlib.hash import pbkdf2_sha256
from cache_config import cache, initialize_cache, get_visualizations
from layouts import (
    overview_layout,
    top10_layout,
    traffic_analysis_layout,
    activity_patterns_layout,
    protocol_analysis_layout,
    data_flow_layout
)
from watchdog_handler import start_watchdog
from callbacks import register_callbacks
from colorlog import ColoredFormatter
import signal
import sys

# Signal handler to release the port on exit
def signal_handler(sig, frame):
    print("Gracefully stopping the application...")
    sys.exit(0)

# Register signal handler
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Initialize the Flask server
server = Flask(__name__)

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

# Load environment variables from .env file
load_dotenv()

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
    if not current_user.is_authenticated:
        return redirect(url_for('login'))  # Redirect to the login page if not logged in
    else:
        return redirect('/dashboard')  # Redirect to Dash app if logged in

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

        if '@' in login_credential:
            user = User.query.filter_by(email=login_credential).first()
        else:
            user = User.query.filter_by(username=login_credential).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect('/')  # Redirect to the main app page after login
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

# Dash app setup
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], server=server, suppress_callback_exceptions=True)
cache.init_app(app.server)

# Initialize the cache with fresh data on startup
with server.app_context():
    initialize_cache()

# Dash layout and routing
# Dash layout and routing
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
@login_required  # This protects the Dash app pages
def display_page(pathname):
    if pathname == '/top10s':
        return top10_layout
    elif pathname == '/traffic-analysis':
        return traffic_analysis_layout
    elif pathname == '/activity-patterns':
        return activity_patterns_layout
    elif pathname == '/protocol-analysis':
        return protocol_analysis_layout
    elif pathname == '/data-flow':
        return data_flow_layout
    else:
        return overview_layout

# Register callbacks
register_callbacks(app)

if __name__ == "__main__":
    logger.info("Starting the application...")
    output_file = "/home/iaes/iaesDash/source/jsondata/fm1/output/data.json"
    directory_to_watch = os.path.dirname(output_file)
    
    # Start the watchdog in a separate thread
    import threading
    watchdog_thread = threading.Thread(target=start_watchdog, args=(directory_to_watch, app.server, output_file))
    watchdog_thread.daemon = True
    watchdog_thread.start()
    
    logger.info("Initializing the server")
    app.run_server(host="0.0.0.0", port=8051, debug=True, use_reloader=False)