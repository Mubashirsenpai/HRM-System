"""
Database models for the HR Management System
"""

from database import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='admin')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

    def __repr__(self):
        return f"<User {self.username}>"

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(50), unique=True, nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    middle_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=True) # personal email
    corporate_email = db.Column(db.String(120), unique=True, nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    qualification = db.Column(db.String(100), nullable=True)
    job_title = db.Column(db.String(100), nullable=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('branch.id'), nullable=True)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=True)
    position_id = db.Column(db.Integer, db.ForeignKey('position.id'), nullable=True)
    appointment_date = db.Column(db.Date, nullable=False)
    address = db.Column(db.String(255), nullable=True)
    marital_status = db.Column(db.String(20), nullable=True)  # Options: Married, Single, Others
    date_of_birth = db.Column(db.Date, nullable=True)
    image_path = db.Column(db.String(255), nullable=True)  # Path for the uploaded image
    emergency_contact = db.Column(db.String(50), nullable=True)
    salary = db.Column(db.Float, nullable=False)
    employment_type = db.Column(db.String(50), nullable=True)  # Added employment_type field
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    branch = db.relationship('Branch', back_populates='employees', lazy=True)
    department = db.relationship('Department', back_populates='department_employees', lazy=True)
    position = db.relationship('Position', back_populates='position_employees', lazy=True)
    attendance = db.relationship('Attendance', backref='employee', lazy=True, cascade='all, delete-orphan')
    leaves = db.relationship('Leave', backref='employee', lazy=True, cascade='all, delete-orphan')
    payroll = db.relationship('Payroll', backref='employee', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Employee {self.employee_id}>"
    
class Branch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    location = db.Column(db.String(255), nullable=True)
    description = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    employees = db.relationship('Employee', back_populates='branch', lazy=True)
    
    def __repr__(self):
        return f"<Branch {self.name}>"

class Department(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    department_employees = db.relationship('Employee', back_populates='department', lazy=True)
    
    def __repr__(self):
        return f"<Department {self.name}>"

class Position(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=True)
    salary_range_min = db.Column(db.Float, nullable=True)
    salary_range_max = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    department = db.relationship('Department', backref='positions', lazy=True)
    position_employees = db.relationship('Employee', back_populates='position', lazy=True)

    def __repr__(self):
        return f"<Position {self.title}>"

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    check_in = db.Column(db.DateTime, nullable=True)
    check_out = db.Column(db.DateTime, nullable=True)
    work_hours = db.Column(db.Float, nullable=True)
    overtime_hours = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(20), nullable=True) # e.g., 'present', 'late', 'absent'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Attendance {self.employee_id} on {self.date}>"

class Leave(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.String(50), nullable=False)  # Changed to String with choices
    status = db.Column(db.String(20), nullable=False, default='pending') # e.g., 'pending', 'approved', 'rejected'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Predefined leave reason choices
    LEAVE_REASONS = [
        ('Annual Leave', 'Annual Leave'),
        ('Maternity', 'Maternity'),
        ('Paternity', 'Paternity'),
        ('Sick', 'Sick'),
        ('Casual Leave', 'Casual Leave'),
        ('Others', 'Others')
    ]

    def __repr__(self):
        return f"<Leave {self.employee_id} from {self.start_date} to {self.end_date}>"

class Payroll(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    pay_period_start = db.Column(db.Date, nullable=False)
    pay_period_end = db.Column(db.Date, nullable=False)
    pay_date = db.Column(db.Date, nullable=False)
    gross_salary = db.Column(db.Float, nullable=True) # Made nullable to accommodate initial creation without full calculation
    overtime_pay = db.Column(db.Float, nullable=True)
    bonus = db.Column(db.Float, nullable=True)
    deductions = db.Column(db.Float, nullable=True)
    net_salary = db.Column(db.Float, nullable=True) # Made nullable
    status = db.Column(db.String(20), nullable=True) # e.g., 'processed', 'pending'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Payroll {self.employee_id} for {self.pay_date}>"
