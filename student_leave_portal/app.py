from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, LeaveApplication  # Assuming you have a models.py file with db and User defined
from functools import wraps
import requests


script_url = "https://script.google.com/macros/s/AKfycbyaR4uBFwC9JDyG40ZOJkvE028dFcue0E0cpteRJxxRqyvJFXokv9v9sIwjhrZg3IGhLw/exec"

app = Flask(__name__)
app.secret_key = 'FlaskApIApP'  # Replace with your actual secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///leave.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize db with app after configuring the app
db.init_app(app)

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']  # Change from username to email
        password = request.form['password']
        name = request.form['name']  # Get the name from the form
        role = request.form['role']
        
        # Additional details based on role
        student_id = request.form.get('student_id') if role == 'Student' else None
        course = request.form.get('course') if role == 'Student' else None
        department = request.form.get('department') if role == 'Staff' else None
        position = request.form.get('position') if role == 'Staff' else None

        # Check if the email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already exists. Please choose a different one.')
            return render_template('signup.html')
        
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        user = User(
            email=email,  # Set the email for the new user
            password=hashed_password,
            role=role,
            name=name,  # Set the name for the new user
            student_id=student_id,
            course=course,
            department=department,
            position=position
        )
        db.session.add(user)
        db.session.commit()
        flash('Account created successfully! Please log in.')
        return redirect(url_for('login'))
    
    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # Query the user by email
        user = User.query.filter_by(email=email).first()
        
        # Check if the user exists and the password is correct
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['role'] = user.role
            session['user_name'] = user.name  # Store user name in session
            
            # Redirect based on role
            if user.role == 'Student':
                return redirect(url_for('apply_leave'))
            elif user.role == 'Staff':
                return redirect(url_for('manage_leaves'))
            else:
                flash('Role not recognized. Please contact support.', 'danger')
                return redirect(url_for('login'))

        flash('Invalid email or password.', 'danger')
        return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    # Clear the session
    session.clear()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('login'))  # Redirect to the login page

@app.route('/')
@login_required
def index():
    user_role = session.get('role')

    if user_role == 'Staff':
        return redirect(url_for('manage_leaves'))
    elif user_role == 'Student':
        return redirect(url_for('apply_leave'))
    else:
        return "Unauthorized", 403

@app.route('/apply_leave', methods=['GET', 'POST'])
@login_required
def apply_leave():
    # Get staff members for selection in form
    staff_members = User.query.filter_by(role='Staff').all()

    if request.method == 'POST':
        user_id = session.get('user_id')
        student_name = session.get('user_name')
        reason = request.form['reason']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        staff_id = request.form['staff_id']

        # Save new leave application
        new_application = LeaveApplication(
            user_id=user_id,
            reason=reason,
            start_date=start_date,
            end_date=end_date,
            staff_id=staff_id
        )

        db.session.add(new_application)
        db.session.commit()

        # Notify staff member about the new leave request
        staff_member = User.query.get(staff_id)
        staff_email = staff_member.email if staff_member else None

        if staff_email:
            payload = {
                'staffEmail': staff_email,
                'studentName': student_name,
                'reason': reason,
                'startDate': start_date,
                'endDate': end_date
            }

            response = requests.post(script_url, json=payload)
            if response.status_code != 200:
                print("Error sending email:", response.text)

        return redirect(url_for('view_leaves'))

    return render_template('apply_leave.html', staff_members=staff_members)



@app.route('/view_leaves')
@login_required
def view_leaves():
    user_id = session.get('user_id')
    leave_applications = LeaveApplication.query.filter_by(user_id=user_id).all()

    # Create a list to hold leave applications with staff names
    leave_data = []
    for leave in leave_applications:
        staff_member = User.query.get(leave.staff_id)
        leave_data.append({
            'reason': leave.reason,
            'start_date': leave.start_date,
            'end_date': leave.end_date,
            'status': leave.status,
            'staff_name': staff_member.name if staff_member else 'Unknown'
        })

    return render_template('view_leaves.html', leave_applications=leave_data)


@app.route('/manage_leaves', methods=['GET', 'POST'])
@login_required
def manage_leaves():
    # Ensure the user is a staff member
    if session.get('role') != 'Staff':
        return redirect(url_for('index'))

    staff_id = session.get('user_id')
    leave_applications = LeaveApplication.query.filter_by(staff_id=staff_id).all()

    if request.method == 'POST':
        leave_id = request.form['leave_id']
        action = request.form['action']  # "approve" or "deny"
        
        leave_application = LeaveApplication.query.get(leave_id)
        if leave_application:
            # Update the leave status based on the action
            leave_application.status = 'Approved' if action == 'approve' else 'Denied'
            db.session.commit()

            # Retrieve the student's details from the `User` model
            student = User.query.get(leave_application.user_id)
            if student:
                student_email = student.email
                student_name = student.name
                status_message = "approved" if action == 'approve' else "denied"

                # Prepare the payload for the Apps Script
                payload = {
                    'studentEmail': student_email,
                    'studentName': student_name,
                    'status': status_message,
                    'reason': leave_application.reason,
                    'startDate': leave_application.start_date,
                    'endDate': leave_application.end_date
                }

                # Send notification to the student about the leave request status
                response = requests.post(script_url, json=payload)
                if response.status_code != 200:
                    print("Error sending email:", response.text)

        return redirect(url_for('manage_leaves'))

    return render_template('manage_leaves.html', leave_applications=leave_applications)



if __name__ == '__main__':
    # Create database tables within the application context
    with app.app_context():
        db.create_all()
    app.run(debug=True)