from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, URLField
from wtforms.validators import DataRequired, URL
import os

app = Flask(__name__)

# --- CONFIGURATION (CHANGE THESE!) ---
# IMPORTANT: Change this to a random long string for security
app.config['SECRET_KEY'] = 'change-this-to-a-very-secret-key-987654321'

# ADMIN CREDENTIALS (CHANGE THESE!)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "password123" 
# --------------------------------------

# Database setup (SQLite)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Login Manager setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# --- DATABASE MODELS ---

# User model for Admin login (Simple hardcoded user for this example)
class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    if user_id == ADMIN_USERNAME:
        return User(user_id)
    return None

# Link model to store your social media links
class Link(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False) # e.g., "Instagram"
    url = db.Column(db.String(500), nullable=False)   # e.g., "https://instagram.com/..."
    # Optional: icon class for FontAwesome (e.g., 'fab fa-instagram')
    icon_class = db.Column(db.String(50), nullable=True) 

# --- FORMS (for Admin view) ---
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class LinkForm(FlaskForm):
    title = StringField('Link Title (e.g., Instagram)', validators=[DataRequired()])
    url = URLField('URL (e.g., https://...)', validators=[DataRequired(), URL()])
    icon_class = StringField('FontAwesome Icon Class (Optional, e.g., fab fa-instagram)')
    submit = SubmitField('Save Link')


# --- ROUTES ---

# 1. THE PUBLIC PAGE (Your Linktree style page)
@app.route('/')
def index():
    # Get all links stored in the database
    links = Link.query.all()
    return render_template('index.html', links=links)


# 2. ADMIN ROUTES

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        # Simple check against hardcoded credentials
        if form.username.data == ADMIN_USERNAME and form.password.data == ADMIN_PASSWORD:
            user = User(ADMIN_USERNAME)
            login_user(user)
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username or password')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin_dashboard():
    links = Link.query.all()
    form = LinkForm()
    if form.validate_on_submit():
        new_link = Link(title=form.title.data, url=form.url.data, icon_class=form.icon_class.data)
        db.session.add(new_link)
        db.session.commit()
        flash('Link added successfully!')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_dashboard.html', links=links, form=form)

@app.route('/admin/delete/<int:link_id>')
@login_required
def delete_link(link_id):
    link_to_delete = Link.query.get_or_404(link_id)
    db.session.delete(link_to_delete)
    db.session.commit()
    flash('Link deleted.')
    return redirect(url_for('admin_dashboard'))

# Create database if it doesn't exist
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
