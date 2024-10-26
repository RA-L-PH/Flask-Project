# models.py
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)  # Change from username to email
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(100), nullable=False)  # Field for name
    
    # Additional fields
    student_id = db.Column(db.String(20), nullable=True)  # Only for students
    course = db.Column(db.String(100), nullable=True)     # Only for students
    department = db.Column(db.String(100), nullable=True) # Only for staff
    position = db.Column(db.String(100), nullable=True)   # Only for staff




class LeaveApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Foreign key to User
    staff_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Foreign key to Staff
    reason = db.Column(db.String(200), nullable=False)
    start_date = db.Column(db.String(50), nullable=False)
    end_date = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default="Pending")
