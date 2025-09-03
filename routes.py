"""
Application routes for the HR Management System
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, send_file, make_response
from datetime import datetime, timedelta
from database import db
from models import *
import os
import csv
import re
import html
from functools import wraps
# import pandas as pd  # Commented out due to compatibility issues
import io

# Create a blueprint for all routes
bp = Blueprint('main', __name__)

# --- New Routes for Authentication ---
from flask_login import login_user, logout_user, login_required, current_user

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login route to authenticate users"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully.', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.dashboard'))
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('login.html')

@bp.route('/logout')
@login_required
def logout():
    """Logout route to clear the session"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.login'))
# --- End of New Routes ---


@bp.route('/')
@login_required
def dashboard():
    """Main dashboard with system overview"""
    total_employees = Employee.query.count()
    total_departments = Department.query.count()
    total_branches = Branch.query.count()
    pending_leaves = Leave.query.filter_by(status='pending').count()
    
    # Get recent attendance count for today
    today_date = datetime.now().date()
    recent_attendance = Attendance.query.filter(Attendance.date == today_date).count()

    # Fetch recent activities from different models
    recent_employees = Employee.query.order_by(Employee.appointment_date.desc()).limit(3).all()
    recent_leaves = Leave.query.order_by(Leave.created_at.desc()).limit(3).all()
    recent_departments = Department.query.order_by(Department.created_at.desc()).limit(3).all()
    recent_branches = Branch.query.order_by(Branch.created_at.desc()).limit(3).all()
    
    # Combine and sort all recent activities by their creation/hire date
    all_recent_activities = []
    
    for emp in recent_employees:
        all_recent_activities.append({
            'type': 'employee_hired',
            # Convert date object to datetime object for consistent sorting
            'timestamp': datetime.combine(emp.appointment_date, datetime.min.time()) if emp.appointment_date else datetime.now(),
            'id': emp.id,
            'name': f"{emp.first_name} {emp.last_name}"
        })
        
    for leave in recent_leaves:
        all_recent_activities.append({
            'type': 'leave_request',
            'timestamp': leave.created_at,
            'id': leave.id,
            'employee_name': f"{leave.employee.first_name} {leave.employee.last_name}" if leave.employee else 'N/A',
            'status': leave.status
        })
        
    for dept in recent_departments:
        all_recent_activities.append({
            'type': 'new_department',
            'timestamp': dept.created_at,
            'id': dept.id,
            'name': dept.name
        })
        
    for branch in recent_branches:
        all_recent_activities.append({
            'type': 'new_branch',
            'timestamp': branch.created_at,
            'id': branch.id,
            'name': branch.name
        })
    
    all_recent_activities.sort(key=lambda x: x['timestamp'], reverse=True)

    return render_template('dashboard.html', 
                            total_employees=total_employees,
                            total_departments=total_departments,
                            total_branches=total_branches,
                            pending_leaves=pending_leaves,
                            recent_attendance=recent_attendance,
                            all_recent_activities=all_recent_activities)

# --- Employee Management Routes ---
@bp.route('/employees', methods=['GET', 'POST'])
@login_required
def employees():
    """Display all employees and handle search with pagination"""
    search_query = None
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    # Validate per_page to prevent abuse
    if per_page not in [10, 25, 50]:
        per_page = 10

    def sanitize_input(user_input):
        # Remove any non-alphanumeric characters except spaces, @, ., -, _
        if user_input is None:
            return None
        sanitized = re.sub(r'[^\w\s@.\-]', '', user_input)
        # Escape HTML to prevent XSS
        sanitized = html.escape(sanitized)
        return sanitized

    if request.method == 'POST':
        search_query = request.form.get('search')
        search_query = sanitize_input(search_query)
        if search_query:
            # Search by employee_id, first_name, last_name, or email (case-insensitive)
            query = Employee.query.filter(
                (Employee.employee_id.ilike(f'%{search_query}%')) |
                (Employee.first_name.ilike(f'%{search_query}%')) |
                (Employee.last_name.ilike(f'%{search_query}%')) |
                (Employee.email.ilike(f'%{search_query}%'))
            )
        else:
            query = Employee.query
    else:
        query = Employee.query

    # Apply pagination
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    employees = pagination.items

    return render_template('employees.html',
                         employees=employees,
                         search_query=search_query,
                         pagination=pagination,
                         per_page=per_page)

@bp.route('/employees/add', methods=['GET', 'POST'])
@login_required
def add_employee():
    """Add a new employee"""
    departments = Department.query.all()
    positions = Position.query.all()
    branches = Branch.query.all()
    if request.method == 'POST':
        try:
            # Personal Information
            employee_id = request.form.get('employee_id')
            first_name = request.form.get('first_name')
            middle_name = request.form.get('middle_name')
            last_name = request.form.get('last_name')
            email = request.form.get('email')  # Personal email
            corporate_email = request.form.get('corporate_email')
            phone = request.form.get('phone')
            address = request.form.get('address')
            marital_status = request.form.get('marital_status')
            date_of_birth_str = request.form.get('date_of_birth')
            emergency_contact = request.form.get('emergency_contact')
            
            # Employment Information
            username = request.form.get('username')
            qualification = request.form.get('qualification')
            job_title = request.form.get('job_title')
            department_id = request.form.get('department_id')
            position_id = request.form.get('position_id')
            branch_id = request.form.get('branch_id')
            appointment_date_str = request.form.get('appointment_date')
            salary = request.form.get('salary')
            employment_type = request.form.get('employment_type')
            
            # Validate required fields
            required_fields = {
                'employee_id': employee_id,
                'first_name': first_name,
                'last_name': last_name,
                'department_id': department_id,
                'position_id': position_id,
                'appointment_date': appointment_date_str,
                'salary': salary
            }
            
            missing_fields = [field for field, value in required_fields.items() if not value]
            if missing_fields:
                flash(f'Required fields are missing: {", ".join(missing_fields)}', 'danger')
                return redirect(url_for('main.add_employee'))
            
            # Check if employee_id already exists
            existing_employee = Employee.query.filter_by(employee_id=employee_id).first()
            if existing_employee:
                flash(f'Employee with ID {employee_id} already exists.', 'danger')
                return redirect(url_for('main.add_employee'))
            
            # Check if email already exists (if provided)
            if email:
                existing_email = Employee.query.filter_by(email=email).first()
                if existing_email:
                    flash(f'Employee with email {email} already exists.', 'danger')
                    return redirect(url_for('main.add_employee'))
            
            # Check if corporate_email already exists (if provided)
            if corporate_email:
                existing_corp_email = Employee.query.filter_by(corporate_email=corporate_email).first()
                if existing_corp_email:
                    flash(f'Employee with corporate email {corporate_email} already exists.', 'danger')
                    return redirect(url_for('main.add_employee'))
            
            # Check if username already exists (if provided)
            if username:
                existing_username = Employee.query.filter_by(username=username).first()
                if existing_username:
                    flash(f'Employee with username {username} already exists.', 'danger')
                    return redirect(url_for('main.add_employee'))
            
            # Validate foreign keys
            department = Department.query.get(department_id)
            if not department:
                flash(f'Department with ID {department_id} not found.', 'danger')
                return redirect(url_for('main.add_employee'))
            
            position = Position.query.get(position_id)
            if not position:
                flash(f'Position with ID {position_id} not found.', 'danger')
                return redirect(url_for('main.add_employee'))
            
            if branch_id:
                branch = Branch.query.get(branch_id)
                if not branch:
                    flash(f'Branch with ID {branch_id} not found.', 'danger')
                    return redirect(url_for('main.add_employee'))
            
            # Parse dates
            try:
                appointment_date = datetime.strptime(appointment_date_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid appointment date format. Please use YYYY-MM-DD format.', 'danger')
                return redirect(url_for('main.add_employee'))
            
            date_of_birth = None
            if date_of_birth_str:
                try:
                    date_of_birth = datetime.strptime(date_of_birth_str, '%Y-%m-%d').date()
                except ValueError:
                    flash('Invalid date of birth format. Please use YYYY-MM-DD format.', 'danger')
                    return redirect(url_for('main.add_employee'))
            
            # Validate salary
            try:
                salary_float = float(salary)
                if salary_float <= 0:
                    flash('Salary must be a positive number.', 'danger')
                    return redirect(url_for('main.add_employee'))
            except ValueError:
                flash('Invalid salary format. Please enter a valid number.', 'danger')
                return redirect(url_for('main.add_employee'))
            
            # Handle image upload
            image_path = None
            if 'image' in request.files:
                image = request.files['image']
                if image.filename != '':
                    try:
                        # Create images directory if it doesn't exist
                        images_dir = os.path.join('static', 'images')
                        os.makedirs(images_dir, exist_ok=True)

                        # Validate file extension
                        allowed_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp'}
                        ext = os.path.splitext(image.filename)[1].lower()
                        if ext not in allowed_extensions:
                            flash('Invalid image format. Please upload PNG, JPG, JPEG, GIF, or BMP files.', 'danger')
                            return redirect(url_for('main.add_employee'))

                        # Save the image with a unique filename to avoid conflicts
                        import uuid
                        unique_filename = f"{uuid.uuid4().hex}{ext}"
                        image_path_full = os.path.join(images_dir, unique_filename)
                        image.save(image_path_full)
                        # Store the relative path in the database (relative to static folder)
                        image_path = os.path.join('images', unique_filename)
                    except Exception as e:
                        flash(f'Error uploading image: {str(e)}', 'danger')
                        return redirect(url_for('main.add_employee'))
            
            # Create new employee
            new_employee = Employee(
                employee_id=employee_id,
                first_name=first_name,
                middle_name=middle_name,
                last_name=last_name,
                username=username,
                email=email,
                corporate_email=corporate_email,
                phone=phone,
                qualification=qualification,
                job_title=job_title,
                department_id=int(department_id),
                position_id=int(position_id),
                branch_id=int(branch_id) if branch_id else None,
                appointment_date=appointment_date,
                salary=salary_float,
                address=address,
                marital_status=marital_status,
                date_of_birth=date_of_birth,
                image_path=image_path,
                emergency_contact=emergency_contact,
                employment_type=employment_type
            )
            
            db.session.add(new_employee)
            db.session.commit()
            
            flash('Employee added successfully!', 'success')
            return redirect(url_for('main.employees'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding employee: {str(e)}', 'danger')
            print(f"Error adding employee: {str(e)}")  # For debugging

    # Return the form for GET requests
    return render_template('add_employee.html', departments=departments, positions=positions, branches=branches)


@bp.route('/employees/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_employee(id):
    """Edit an existing employee"""
    employee = Employee.query.get_or_404(id)
    departments = Department.query.all()
    positions = Position.query.all()
    branches = Branch.query.all()
    if request.method == 'POST':
        try:
            # Personal Information
            employee.employee_id = request.form.get('employee_id')
            employee.first_name = request.form.get('first_name')
            employee.middle_name = request.form.get('middle_name')
            employee.last_name = request.form.get('last_name')
            employee.email = request.form.get('email')
            employee.corporate_email = request.form.get('corporate_email')
            employee.phone = request.form.get('phone')
            employee.address = request.form.get('address')
            employee.marital_status = request.form.get('marital_status')

            # Employment Information
            employee.username = request.form.get('username')
            employee.qualification = request.form.get('qualification')
            employee.job_title = request.form.get('job_title')
            employee.department_id = request.form.get('department_id')
            employee.position_id = request.form.get('position_id')
            employee.branch_id = request.form.get('branch_id') if request.form.get('branch_id') else None
            employee.appointment_date = datetime.strptime(request.form.get('appointment_date'), '%Y-%m-%d').date()
            employee.salary = float(request.form.get('salary'))
            employee.emergency_contact = request.form.get('emergency_contact')
            employee.employment_type = request.form.get('employment_type')

            # Handle date of birth
            date_of_birth_str = request.form.get('date_of_birth')
            if date_of_birth_str:
                employee.date_of_birth = datetime.strptime(date_of_birth_str, '%Y-%m-%d').date()
            else:
                employee.date_of_birth = None

            # Handle image upload
            if 'image' in request.files:
                image = request.files['image']
                if image.filename != '':
                    try:
                        # Create images directory if it doesn't exist
                        images_dir = os.path.join('static', 'images')
                        os.makedirs(images_dir, exist_ok=True)

                        # Validate file extension
                        allowed_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp'}
                        ext = os.path.splitext(image.filename)[1].lower()
                        if ext not in allowed_extensions:
                            flash('Invalid image format. Please upload PNG, JPG, JPEG, GIF, or BMP files.', 'danger')
                            return redirect(url_for('main.edit_employee', id=id))

                        # Save the image with a unique filename to avoid conflicts
                        import uuid
                        unique_filename = f"{uuid.uuid4().hex}{ext}"
                        image_path_full = os.path.join(images_dir, unique_filename)
                        image.save(image_path_full)
                        # Store the relative path in the database (relative to static folder)
                        employee.image_path = os.path.join('images', unique_filename)
                    except Exception as e:
                        flash(f'Error uploading image: {str(e)}', 'danger')
                        return redirect(url_for('main.edit_employee', id=id))

            db.session.commit()
            flash('Employee updated successfully!', 'success')
            return redirect(url_for('main.employees'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating employee: {e}', 'danger')

    return render_template('edit_employee.html', employee=employee, departments=departments, positions=positions, branches=branches)

from flask import send_file
from fpdf import FPDF

@bp.route('/employees/view/<int:id>', methods=['GET'])
@login_required
def view_employee(id):
    """View details of a single employee"""
    employee = Employee.query.get_or_404(id)
    return render_template('view_employee.html', employee=employee)

@bp.route('/employees/pdf/<int:id>')
def employee_pdf(id):
    """Generate and serve employee details as PDF"""
    try:
        employee = Employee.query.get_or_404(id)

        # Create PDF with custom page size
        pdf = FPDF('P', 'mm', 'A4')
        pdf.add_page()

        # Set margins
        pdf.set_margins(20, 20, 20)

        # Header Section
        pdf.set_font("Arial", 'B', 20)
        pdf.set_text_color(0, 51, 102)  # Dark blue
        pdf.cell(0, 15, "HR Management System", 0, 1, 'C')
        pdf.ln(5)

        # Employee Name and ID
        pdf.set_font("Arial", 'B', 18)
        pdf.set_text_color(0, 0, 0)  # Black
        full_name = f"{employee.first_name} {employee.middle_name if employee.middle_name else ''} {employee.last_name}".strip()
        pdf.cell(0, 12, full_name, 0, 1, 'C')
        pdf.set_font("Arial", '', 12)
        pdf.cell(0, 8, f"Employee ID: {employee.employee_id}", 0, 1, 'C')
        pdf.ln(10)

        # Profile Picture Section
        if employee.image_path:
            from PIL import Image, ImageDraw
            import tempfile

            # Normalize path separators for cross-platform compatibility
            normalized_path = employee.image_path.replace('\\', '/')
            image_path = os.path.join('static', normalized_path)
            if os.path.exists(image_path):
                # Open the image with Pillow
                with Image.open(image_path).convert("RGBA") as im:
                    # Resize image to smaller size for faster processing
                    max_size = (200, 200)
                    im.thumbnail(max_size, Image.LANCZOS)

                    # Create same size alpha layer with circle
                    bigsize = (im.size[0] * 3, im.size[1] * 3)
                    mask = Image.new('L', bigsize, 0)
                    draw = ImageDraw.Draw(mask)
                    draw.ellipse((0, 0) + bigsize, fill=255)
                    # Replace deprecated ANTIALIAS with LANCZOS for Pillow >= 10.0.0
                    mask = mask.resize(im.size, Image.LANCZOS)
                    im.putalpha(mask)

                    # Save to a temporary file
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmpfile:
                        temp_path = tmpfile.name
                        im.save(temp_path, format="PNG")

                    # Center the image in PDF
                    x_pos = 75
                    y_pos = pdf.get_y()
                    width = 60
                    height = 60

                    # Draw the circular image
                    pdf.image(temp_path, x=x_pos, y=y_pos, w=width, h=height)

                    pdf.ln(height + 15)  # Space for image

                    # Remove temporary file
                    os.remove(temp_path)
            else:
                pdf.ln(10)
        else:
            pdf.ln(10)

        # Personal Information Section
        pdf.set_font("Arial", 'B', 14)
        pdf.set_text_color(0, 51, 102)
        pdf.cell(0, 10, "Personal Information", 0, 1, 'L')
        pdf.ln(2)

        # Draw line under section header
        pdf.set_draw_color(0, 51, 102)
        pdf.line(20, pdf.get_y(), 190, pdf.get_y())
        pdf.ln(5)

        pdf.set_font("Arial", '', 11)
        pdf.set_text_color(0, 0, 0)

        # Left column
        pdf.cell(90, 8, f"Full Name: {full_name}", 0, 0)
        pdf.cell(90, 8, f"Date of Birth: {employee.date_of_birth.strftime('%B %d, %Y') if employee.date_of_birth else 'N/A'}", 0, 1)

        pdf.cell(90, 8, f"Personal Email: {employee.email if employee.email else 'N/A'}", 0, 0)
        pdf.cell(90, 8, f"Marital Status: {employee.marital_status if employee.marital_status else 'N/A'}", 0, 1)

        pdf.cell(90, 8, f"Phone: {employee.phone if employee.phone else 'N/A'}", 0, 0)
        pdf.cell(90, 8, f"Emergency Contact: {employee.emergency_contact if employee.emergency_contact else 'N/A'}", 0, 1)

        if employee.address:
            pdf.cell(0, 8, f"Address: {employee.address}", 0, 1)

        pdf.ln(10)

        # Employment Information Section
        pdf.set_font("Arial", 'B', 14)
        pdf.set_text_color(0, 51, 102)
        pdf.cell(0, 10, "Employment Information", 0, 1, 'L')
        pdf.ln(2)

        # Draw line under section header
        pdf.line(20, pdf.get_y(), 190, pdf.get_y())
        pdf.ln(5)

        pdf.set_font("Arial", '', 11)
        pdf.set_text_color(0, 0, 0)

        pdf.cell(90, 8, f"Department: {employee.department.name if employee.department else 'N/A'}", 0, 0)
        pdf.cell(90, 8, f"Position: {employee.position.title if employee.position else 'N/A'}", 0, 1)

        pdf.cell(90, 8, f"Job Title: {employee.job_title if employee.job_title else 'N/A'}", 0, 0)
        pdf.cell(90, 8, f"Employment Type: {employee.employment_type.capitalize() if employee.employment_type else 'N/A'}", 0, 1)

        pdf.cell(90, 8, f"Appointment Date: {employee.appointment_date.strftime('%B %d, %Y') if employee.appointment_date else 'N/A'}", 0, 0)
        pdf.cell(90, 8, f"Salary: GHS {employee.salary:,.2f}", 0, 1)

        pdf.cell(90, 8, f"Corporate Email: {employee.corporate_email if employee.corporate_email else 'N/A'}", 0, 0)
        pdf.cell(90, 8, f"Username: {employee.username if employee.username else 'N/A'}", 0, 1)

        if employee.qualification:
            pdf.cell(0, 8, f"Qualification: {employee.qualification}", 0, 1)

        if employee.branch:
            pdf.cell(0, 8, f"Branch: {employee.branch.name}", 0, 1)

        pdf.ln(10)

        # Additional Information Section
        pdf.set_font("Arial", 'B', 14)
        pdf.set_text_color(0, 51, 102)
        pdf.cell(0, 10, "Additional Information", 0, 1, 'L')
        pdf.ln(2)

        # Draw line under section header
        pdf.line(20, pdf.get_y(), 190, pdf.get_y())
        pdf.ln(5)

        pdf.set_font("Arial", '', 11)
        pdf.set_text_color(0, 0, 0)

        pdf.cell(90, 8, f"Created At: {employee.created_at.strftime('%B %d, %Y %H:%M')}", 0, 1)

        # Footer
        pdf.ln(20)
        pdf.set_font("Arial", 'I', 8)
        pdf.set_text_color(128, 128, 128)
        pdf.cell(0, 5, "Generated by HR Management System", 0, 1, 'C')
        pdf.cell(0, 5, f"Generated on: {datetime.now().strftime('%B %d, %Y %H:%M')}", 0, 1, 'C')

        # Create response
        response = make_response(pdf.output(dest='S').encode('latin1'))
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=employee_{employee.employee_id}_profile.pdf'

        return response

    except Exception as e:
        flash(f'Error generating PDF: {e}', 'danger')
        return redirect(url_for('main.view_employee', id=id))

@bp.route('/employees/delete/<int:id>', methods=['POST', 'GET'])
@login_required
def delete_employee(id):
    """Delete an employee"""
    employee = Employee.query.get_or_404(id)
    if request.method == 'POST':
        try:
            db.session.delete(employee)
            db.session.commit()
            flash('Employee deleted successfully!', 'success')
            return redirect(url_for('main.employees'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error deleting employee: {e}', 'danger')
    
    # Render a confirmation page for GET requests
    return render_template('confirm_delete_employee.html', employee=employee)
    
# --- Bulk Employee Upload Routes ---
@bp.route('/employees/sample_csv')
@login_required
def sample_csv():
    """Provide a sample CSV template for bulk employee upload"""
    # Create a sample CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    # Include all the fields that are used in the add employee form
    writer.writerow([
        'employee_id', 'first_name', 'last_name', 'email', 'phone',
        'appointment_date', 'department_id', 'position_id', 'salary',
        'middle_name', 'corporate_email', 'address', 'marital_status',
        'date_of_birth', 'emergency_contact', 'username', 'qualification',
        'job_title', 'branch_id', 'employment_type'
    ])
    writer.writerow([
        'EMP001', 'John', 'Doe', 'john.doe@example.com', '123-456-7890',
        '2023-01-15', '1', '1', '50000.00',
        'Michael', 'john.doe@company.com', '123 Main St, City', 'Single',
        '1990-05-15', 'Jane Doe - 555-1234', 'johndoe', 'Bachelor of Science',
        'Software Engineer', '1', 'full_time'
    ])
    
    # Create response
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename=sample_employees.csv'
    return response

@bp.route('/employees/sample_excel')
@login_required
def sample_excel():
    """Provide a sample Excel template for bulk employee upload"""
    # Create a simple CSV alternative since Excel support is disabled
    # due to pandas/numpy compatibility issues
    flash('Excel template generation is temporarily disabled due to compatibility issues. Please use the CSV template instead.', 'warning')
    return redirect(url_for('main.sample_csv'))

@bp.route('/employees/bulk_upload', methods=['GET', 'POST'])
@login_required
def bulk_upload_employees():
    """Handle bulk upload of employees from CSV or Excel files"""
    if request.method == 'POST':
        try:
            # Check if file was uploaded
            if 'file' not in request.files:
                flash('No file selected.', 'danger')
                return redirect(request.url)
            
            file = request.files['file']
            if file.filename == '':
                flash('No file selected.', 'danger')
                return redirect(request.url)
            
            # Check file extension
            if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
                flash('Invalid file format. Please upload a CSV or Excel file.', 'danger')
                return redirect(request.url)
            
            # Process the file based on its extension
            if file.filename.endswith('.csv'):
                # Process CSV file
                stream = io.StringIO(file.stream.read().decode('utf-8'))
                reader = csv.DictReader(stream)
                employees_data = list(reader)
            else:
                # Process Excel file - disabled due to pandas/numpy compatibility issues
                flash('Excel file processing is temporarily disabled. Please use CSV files for bulk upload.', 'danger')
                return redirect(url_for('main.bulk_upload_employees'))
            
            # Process each employee record
            success_count = 0
            error_count = 0
            errors = []
            
            for i, row in enumerate(employees_data):
                try:
                    # Validate required fields
                    required_fields = ['employee_id', 'first_name', 'last_name', 'email', 'phone', 'appointment_date', 'department_id', 'position_id', 'salary']
                    missing_fields = [field for field in required_fields if not row.get(field)]
                    if missing_fields:
                        errors.append(f"Row {i+1}: Missing required fields: {', '.join(missing_fields)}")
                        error_count += 1
                        continue
                    
                    # Check if employee already exists
                    if Employee.query.filter_by(employee_id=row['employee_id']).first():
                        errors.append(f"Row {i+1}: Employee with ID {row['employee_id']} already exists")
                        error_count += 1
                        continue
                    
                    # Validate department and position IDs
                    department = Department.query.get(row['department_id'])
                    position = Position.query.get(row['position_id'])
                    if not department:
                        errors.append(f"Row {i+1}: Department with ID {row['department_id']} not found")
                        error_count += 1
                        continue
                    if not position:
                        errors.append(f"Row {i+1}: Position with ID {row['position_id']} not found")
                        error_count += 1
                        continue
                    
                    # Validate appointment date
                    try:
                        appointment_date = datetime.strptime(row['appointment_date'], '%Y-%m-%d').date()
                    except ValueError:
                        errors.append(f"Row {i+1}: Invalid appointment date format. Use YYYY-MM-DD")
                        error_count += 1
                        continue
                    
                    # Validate salary
                    try:
                        salary = float(row['salary'])
                    except ValueError:
                        errors.append(f"Row {i+1}: Invalid salary format")
                        error_count += 1
                        continue
                    
                    # Parse optional fields
                    middle_name = row.get('middle_name')
                    corporate_email = row.get('corporate_email')
                    address = row.get('address')
                    marital_status = row.get('marital_status')
                    date_of_birth_str = row.get('date_of_birth')
                    emergency_contact = row.get('emergency_contact')
                    username = row.get('username')
                    qualification = row.get('qualification')
                    job_title = row.get('job_title')
                    branch_id_str = row.get('branch_id')
                    employment_type = row.get('employment_type')

                    date_of_birth = None
                    if date_of_birth_str:
                        try:
                            date_of_birth = datetime.strptime(date_of_birth_str, '%Y-%m-%d').date()
                        except ValueError:
                            errors.append(f"Row {i+1}: Invalid date_of_birth format. Use YYYY-MM-DD")
                            error_count += 1
                            continue

                    branch_id = int(branch_id_str) if branch_id_str else None

                    # Create new employee
                    new_employee = Employee(
                        employee_id=row['employee_id'],
                        first_name=row['first_name'],
                        middle_name=middle_name,
                        last_name=row['last_name'],
                        username=username,
                        email=row['email'],
                        corporate_email=corporate_email,
                        phone=row['phone'],
                        qualification=qualification,
                        job_title=job_title,
                        department_id=int(row['department_id']),
                        position_id=int(row['position_id']),
                        branch_id=branch_id,
                        appointment_date=appointment_date,
                        address=address,
                        marital_status=marital_status,
                        date_of_birth=date_of_birth,
                        image_path=None,
                        emergency_contact=emergency_contact,
                        salary=salary,
                        employment_type=employment_type
                    )
                    
                    db.session.add(new_employee)
                    success_count += 1
                    
                except Exception as e:
                    errors.append(f"Row {i+1}: {str(e)}")
                    error_count += 1
            
            # Commit all changes
            db.session.commit()
            
            # Flash messages
            if success_count > 0:
                flash(f'Successfully uploaded {success_count} employees.', 'success')
            if error_count > 0:
                flash(f'Failed to upload {error_count} employees. Check the errors below.', 'danger')
                for error in errors:
                    flash(error, 'danger')
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error processing file: {str(e)}', 'danger')
        
        return redirect(url_for('main.employees'))
    
    return render_template('bulk_upload_employees.html')


# --- Branch Management Routes ---
@bp.route('/branches')
@login_required
def branches():
    """Display all branches"""
    branches = Branch.query.all()
    return render_template('branches.html', branches=branches)

@bp.route('/branches/add', methods=['GET', 'POST'])
@login_required
def add_branch():
    """Add a new branch"""
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            location = request.form.get('location')
            description = request.form.get('description')
            new_branch = Branch(name=name, location=location, description=description)
            db.session.add(new_branch)
            db.session.commit()
            flash('Branch added successfully!', 'success')
            return redirect(url_for('main.branches'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding branch: {e}', 'danger')
    return render_template('add_branch.html')

@bp.route('/branches/view/<int:id>')
@login_required
def view_branch(id):
    """View details of a single branch"""
    branch = Branch.query.get_or_404(id)
    return render_template('view_branch.html', branch=branch)

@bp.route('/branches/edit/<int:id>', methods=['GET', 'POST'])
def edit_branch(id):
    """Edit an existing branch"""
    branch = Branch.query.get_or_404(id)
    if request.method == 'POST':
        try:
            branch.name = request.form.get('name')
            branch.location = request.form.get('location')
            branch.description = request.form.get('description')
            db.session.commit()
            flash('Branch updated successfully!', 'success')
            return redirect(url_for('main.branches'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating branch: {e}', 'danger')
    return render_template('edit_branch.html', branch=branch)

@bp.route('/branches/delete/<int:id>', methods=['POST', 'GET'])
def delete_branch(id):
    """Delete a branch"""
    branch = Branch.query.get_or_404(id)
    if request.method == 'POST':
        try:
            db.session.delete(branch)
            db.session.commit()
            flash('Branch deleted successfully!', 'success')
            return redirect(url_for('main.branches'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error deleting branch: {e}', 'danger')
    return render_template('confirm_delete_branch.html', branch=branch)

# --- Department Management Routes ---
@bp.route('/departments')
def departments():
    """Display all departments"""
    departments = Department.query.all()
    return render_template('departments.html', departments=departments)

@bp.route('/departments/add', methods=['GET', 'POST'])
def add_department():
    """Add a new department"""
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            description = request.form.get('description')
            new_department = Department(name=name, description=description)
            db.session.add(new_department)
            db.session.commit()
            flash('Department added successfully!', 'success')
            return redirect(url_for('main.departments'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding department: {e}', 'danger')
    return render_template('add_department.html')

@bp.route('/departments/edit/<int:id>', methods=['GET', 'POST'])
def edit_department(id):
    """Edit an existing department"""
    department = Department.query.get_or_404(id)
    if request.method == 'POST':
        try:
            department.name = request.form.get('name')
            department.description = request.form.get('description')
            db.session.commit()
            flash('Department updated successfully!', 'success')
            return redirect(url_for('main.departments'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating department: {e}', 'danger')
    return render_template('edit_department.html', department=department)

@bp.route('/departments/delete/<int:id>', methods=['POST', 'GET'])
def delete_department(id):
    """Delete a department"""
    department = Department.query.get_or_404(id)
    if request.method == 'POST':
        try:
            db.session.delete(department)
            db.session.commit()
            flash('Department deleted successfully!', 'success')
            return redirect(url_for('main.departments'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error deleting department: {e}', 'danger')
    return render_template('confirm_delete_department.html', department=department)


@bp.route('/departments/view/<int:department_id>')
def view_department(department_id):
    """View details of a single department"""
    department = Department.query.get_or_404(department_id)
    return render_template('view_department.html', department=department)


# --- Position Management Routes ---
@bp.route('/positions')
def positions():
    """Display all positions"""
    positions = Position.query.all()
    return render_template('positions.html', positions=positions)

@bp.route('/positions/view/<int:id>')
def view_position(id):
    """View details of a single position"""
    position = Position.query.get_or_404(id)
    return render_template('view_position.html', position=position)

@bp.route('/positions/add', methods=['GET', 'POST'])
def add_position():
    """Add a new position"""
    departments = Department.query.all()
    if request.method == 'POST':
        try:
            title = request.form.get('title')
            description = request.form.get('description')
            department_id = request.form.get('department_id')
            salary_range_min = request.form.get('salary_range_min')
            salary_range_max = request.form.get('salary_range_max')
            
            new_position = Position(
                title=title,
                description=description,
                department_id=department_id if department_id else None,
                salary_range_min=float(salary_range_min) if salary_range_min else None,
                salary_range_max=float(salary_range_max) if salary_range_max else None
            )
            db.session.add(new_position)
            db.session.commit()
            flash('Position added successfully!', 'success')
            return redirect(url_for('main.positions'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding position: {e}', 'danger')
    return render_template('add_position.html', departments=departments)

@bp.route('/positions/edit/<int:id>', methods=['GET', 'POST'])
def edit_position(id):
    """Edit an existing position"""
    position = Position.query.get_or_404(id)
    departments = Department.query.all()
    if request.method == 'POST':
        try:
            position.title = request.form.get('title')
            position.description = request.form.get('description')
            position.department_id = request.form.get('department_id') if request.form.get('department_id') else None
            position.salary_range_min = float(request.form.get('salary_range_min')) if request.form.get('salary_range_min') else None
            position.salary_range_max = float(request.form.get('salary_range_max')) if request.form.get('salary_range_max') else None
            db.session.commit()
            flash('Position updated successfully!', 'success')
            return redirect(url_for('main.positions'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating position: {e}', 'danger')
    return render_template('edit_position.html', position=position, departments=departments)

@bp.route('/positions/delete/<int:id>', methods=['POST', 'GET'])
def delete_position(id):
    """Delete a position"""
    position = Position.query.get_or_404(id)
    if request.method == 'POST':
        try:
            db.session.delete(position)
            db.session.commit()
            flash('Position deleted successfully!', 'success')
            return redirect(url_for('main.positions'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error deleting position: {e}', 'danger')
    return render_template('confirm_delete_position.html', position=position)


# --- Leave Management Routes ---
@bp.route('/leave')
def leave():
    """Display all leave requests"""
    leave_requests = Leave.query.all()
    # The variable name in the template is `leaves`, so we should
    # pass the data with that key.
    return render_template('leaves.html', leaves=leave_requests)

@bp.route('/leave/add', methods=['GET', 'POST'])
def add_leave():
    """Add a new leave request"""
    employees = Employee.query.all()
    if request.method == 'POST':
        try:
            employee_id = request.form.get('employee_id')
            start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
            end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date()
            reason = request.form.get('reason')

            new_leave = Leave(
                employee_id=employee_id,
                start_date=start_date,
                end_date=end_date,
                reason=reason,
                status='pending'
            )
            db.session.add(new_leave)
            db.session.commit()
            flash('Leave request submitted successfully!', 'success')
            return redirect(url_for('main.leave'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error submitting leave request: {e}', 'danger')
    return render_template('add_leave.html', employees=employees)

@bp.route('/leave/edit/<int:leave_id>', methods=['GET', 'POST'])
def edit_leave(leave_id):
    """Edit an existing leave request"""
    leave_request = Leave.query.get_or_404(leave_id)
    employees = Employee.query.all()
    if request.method == 'POST':
        try:
            leave_request.employee_id = request.form.get('employee_id')
            leave_request.start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
            leave_request.end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date()
            leave_request.reason = request.form.get('reason')
            leave_request.status = request.form.get('status')
            db.session.commit()
            flash('Leave request updated successfully!', 'success')
            return redirect(url_for('main.leave'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating leave request: {e}', 'danger')
    return render_template('edit_leave.html', leave_request=leave_request, employees=employees)

@bp.route('/leave/delete/<int:leave_id>', methods=['POST', 'GET'])
def delete_leave(leave_id):
    """Delete a leave request"""
    leave_request = Leave.query.get_or_404(leave_id)
    if request.method == 'POST':
        try:
            db.session.delete(leave_request)
            db.session.commit()
            flash('Leave request deleted successfully!', 'success')
            return redirect(url_for('main.leave'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error deleting leave request: {e}', 'danger')
    return render_template('confirm_delete_leave.html', leave_request=leave_request)

@bp.route('/leave/view/<int:leave_id>')
def view_leave(leave_id):
    """View details of a single leave request"""
    leave_request = Leave.query.get_or_404(leave_id)
    return render_template('view_leave.html', leave_request=leave_request)

# --- Public Leave Request Routes (No Login Required) ---
@bp.route('/public/leave/request', methods=['GET', 'POST'])
def public_leave_request():
    """Public page for employees to submit leave requests"""
    if request.method == 'POST':
        try:
            # Collect employee information
            employee_id = request.form.get('employee_id')
            first_name = request.form.get('first_name')
            last_name = request.form.get('last_name')
            email = request.form.get('email')
            phone = request.form.get('phone')
            department = request.form.get('department')

            # Collect leave information
            start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
            end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date()
            reason = request.form.get('reason')
            additional_notes = request.form.get('additional_notes')

            # Find employee by employee_id if provided
            employee = None
            if employee_id:
                employee = Employee.query.filter_by(employee_id=employee_id).first()

            # If employee exists, use their ID, otherwise create a temporary leave request
            if employee:
                new_leave = Leave(
                    employee_id=employee.id,
                    start_date=start_date,
                    end_date=end_date,
                    reason=reason,
                    status='pending'
                )
            else:
                # For public requests without matching employee, we'll store additional info
                # We'll need to modify the Leave model to handle this
                new_leave = Leave(
                    employee_id=None,  # Will be assigned later by HR
                    start_date=start_date,
                    end_date=end_date,
                    reason=reason,
                    status='pending'
                )
                # Store additional information in the reason field or create a new field
                extended_reason = f"{reason}\n\nEmployee Details:\nName: {first_name} {last_name}\nEmail: {email}\nPhone: {phone}\nDepartment: {department}"
                if additional_notes:
                    extended_reason += f"\nAdditional Notes: {additional_notes}"
                new_leave.reason = extended_reason

            db.session.add(new_leave)
            db.session.commit()

            # Store request ID in session for status checking
            session['last_leave_request_id'] = new_leave.id

            flash('Your leave request has been submitted successfully! Please note down this reference for future inquiries.', 'success')
            return redirect(url_for('main.public_leave_status'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error submitting leave request: {str(e)}', 'danger')

    return render_template('public_leave_request.html')

@bp.route('/public/leave/status', methods=['GET', 'POST'])
def public_leave_status():
    """Public page for employees to check their leave request status"""
    leave_request = None
    if request.method == 'POST':
        request_id = request.form.get('request_id')
        email = request.form.get('email')

        if request_id:
            try:
                leave_request = Leave.query.get(int(request_id))
                # Basic email verification (in production, you'd want more secure verification)
                if leave_request and email in leave_request.reason:
                    pass  # Valid request
                else:
                    flash('Request not found or email does not match.', 'warning')
                    leave_request = None
            except ValueError:
                flash('Invalid request ID format.', 'danger')
        else:
            flash('Please provide a request ID.', 'warning')

    # Show last submitted request if available
    if 'last_leave_request_id' in session and not leave_request:
        try:
            leave_request = Leave.query.get(session['last_leave_request_id'])
        except:
            pass

    return render_template('public_leave_status.html', leave_request=leave_request)


# --- Attendance Management Routes ---
@bp.route('/attendance')
def attendance():
    """Display all attendance records"""
    attendance_records = Attendance.query.all()
    return render_template('attendance.html', attendance_records=attendance_records)

@bp.route('/attendance/add', methods=['GET', 'POST'])
def add_attendance():
    """Add a new attendance record"""
    employees = Employee.query.all()
    if request.method == 'POST':
        try:
            employee_id = request.form.get('employee_id')
            date_str = request.form.get('date')
            check_in_str = request.form.get('check_in')
            check_out_str = request.form.get('check_out')
            status = request.form.get('status')

            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            check_in = datetime.strptime(f"{date_str} {check_in_str}", '%Y-%m-%d %H:%M') if check_in_str else None
            check_out = datetime.strptime(f"{date_str} {check_out_str}", '%Y-%m-%d %H:%M') if check_out_str else None

            new_attendance = Attendance(
                employee_id=employee_id,
                date=date,
                check_in=check_in,
                check_out=check_out,
                status=status
            )
            db.session.add(new_attendance)
            db.session.commit()
            flash('Attendance record added successfully!', 'success')
            return redirect(url_for('main.attendance'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding attendance record: {e}', 'danger')
    return render_template('add_attendance.html', employees=employees)

@bp.route('/attendance/edit/<int:id>', methods=['GET', 'POST'])
def edit_attendance(id):
    """Edit an existing attendance record"""
    attendance = Attendance.query.get_or_404(id)
    employees = Employee.query.all()
    if request.method == 'POST':
        try:
            attendance.employee_id = request.form.get('employee_id')
            attendance.date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
            attendance.check_in = datetime.strptime(f"{attendance.date} {request.form.get('check_in')}", '%Y-%m-%d %H:%M') if request.form.get('check_in') else None
            attendance.check_out = datetime.strptime(f"{attendance.date} {request.form.get('check_out')}", '%Y-%m-%d %H:%M') if request.form.get('check_out') else None
            attendance.status = request.form.get('status')
            db.session.commit()
            flash('Attendance record updated successfully!', 'success')
            return redirect(url_for('main.attendance'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating attendance record: {e}', 'danger')
    return render_template('edit_attendance.html', attendance=attendance, employees=employees)

@bp.route('/attendance/delete/<int:id>', methods=['POST', 'GET'])
def delete_attendance(id):
    """Delete an attendance record"""
    attendance = Attendance.query.get_or_404(id)
    if request.method == 'POST':
        try:
            db.session.delete(attendance)
            db.session.commit()
            flash('Attendance record deleted successfully!', 'success')
            return redirect(url_for('main.attendance'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error deleting attendance record: {e}', 'danger')
    return render_template('confirm_delete_attendance.html', attendance=attendance)


# --- Payroll Management Routes ---
@bp.route('/payroll')
def payroll():
    """Display all payroll records and employees for the generation modal"""
    payroll_records = Payroll.query.all()
    employees = Employee.query.all()
    return render_template('payroll.html', payroll_records=payroll_records, employees=employees)


@bp.route('/payroll/generate', methods=['POST'])
def generate_payroll():
    """Generate a new payroll record based on a time period"""
    try:
        employee_id = request.form.get('employee_id')
        pay_period_start_str = request.form.get('pay_period_start')
        pay_period_end_str = request.form.get('pay_period_end')

        employee = Employee.query.get(employee_id)
        if not employee:
            flash('Employee not found.', 'danger')
            return redirect(url_for('main.payroll'))

        pay_period_start = datetime.strptime(pay_period_start_str, '%Y-%m-%d').date()
        pay_period_end = datetime.strptime(pay_period_end_str, '%Y-%m-%d').date()

        # Calculate the number of days in the pay period
        days_in_period = (pay_period_end - pay_period_start).days + 1

        # Simple payroll calculation: assuming salary is annual
        # and a work year has 260 days (52 weeks * 5 days)
        daily_salary = employee.salary / 260.0
        gross_pay = daily_salary * days_in_period
        
        # Simple tax deduction assumption (e.g., 20%)
        deductions = gross_pay * 0.20
        net_pay = gross_pay - deductions

        new_payroll = Payroll(
            employee_id=employee_id,
            pay_date=datetime.now().date(),
            pay_period_start=pay_period_start,
            pay_period_end=pay_period_end,
            gross_salary=gross_pay, # Use gross_salary to match model attribute
            overtime_pay=0.0, # Placeholder
            bonus=0.0, # Placeholder for bonus
            deductions=deductions,
            net_salary=net_pay
        )

        db.session.add(new_payroll)
        db.session.commit()
        
        flash('Payroll generated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error generating payroll: {e}', 'danger')

    return redirect(url_for('main.payroll'))

@bp.route('/payroll/edit/<int:id>', methods=['GET', 'POST'])
def edit_payroll(id):
    """Edit an existing payroll record"""
    payroll = Payroll.query.get_or_404(id)
    employees = Employee.query.all()
    if request.method == 'POST':
        try:
            payroll.employee_id = request.form.get('employee_id')
            payroll.pay_date = datetime.strptime(request.form.get('pay_date'), '%Y-%m-%d').date()
            payroll.gross_salary = float(request.form.get('gross_salary'))
            payroll.deductions = float(request.form.get('deductions'))
            payroll.net_salary = float(request.form.get('net_salary'))
            db.session.commit()
            flash('Payroll record updated successfully!', 'success')
            return redirect(url_for('main.payroll'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating payroll record: {e}', 'danger')
    return render_template('edit_payroll.html', payroll=payroll, employees=employees)

@bp.route('/payroll/delete/<int:id>', methods=['POST', 'GET'])
def delete_payroll(id):
    """Delete a payroll record"""
    payroll = Payroll.query.get_or_404(id)
    if request.method == 'POST':
        try:
            db.session.delete(payroll)
            db.session.commit()
            flash('Payroll record deleted successfully!', 'success')
            return redirect(url_for('main.payroll'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error deleting payroll record: {e}', 'danger')
    return render_template('confirm_delete_payroll.html', payroll=payroll)

@bp.route('/payroll/view/<int:id>')
def view_payroll(id):
    """View details of a single payroll record"""
    payroll = Payroll.query.get_or_404(id)
    return render_template('view_payroll.html', payroll=payroll)


# --- API Endpoints ---
@bp.route('/api/employees')
def api_employees():
    """Get employees list as JSON"""
    employees = Employee.query.all()
    return jsonify([
        {
            'id': e.id,
            'employee_id': e.employee_id,
            'name': f"{e.first_name} {e.last_name}",
            'department': e.department.name if e.department else 'N/A',
            'position': e.position.title if e.position else 'N/A',
            'hire_date': e.hire_date.strftime('%Y-%m-%d'),
            'salary': e.salary,
            'phone': e.phone
        } for e in employees
    ])

@bp.route('/api/departments')
def api_departments():
    """Get departments list as JSON"""
    departments = Department.query.all()
    return jsonify([
        {
            'id': d.id,
            'name': d.name,
            'description': d.description,
            'employee_count': len(d.department_employees)
        } for d in departments
    ])

@bp.route('/api/positions')
def api_positions():
    """Get positions list as JSON"""
    positions = Position.query.all()
    return jsonify([
        {
            'id': p.id,
            'title': p.title,
            'description': p.description,
            'department': p.department.name if p.department else 'N/A',
            'salary_range_min': p.salary_range_min,
            'salary_range_max': p.salary_range_max,
            'employee_count': len(p.position_employees)
        } for p in positions
    ])

@bp.route('/api/attendance')
def api_attendance():
    """Get attendance records as JSON"""
    attendance_records = Attendance.query.all()
    return jsonify([
        {
            'id': a.id,
            'employee_name': f"{a.employee.first_name} {a.employee.last_name}" if a.employee else 'N/A',
            'date': a.date.strftime('%Y-%m-%d'),
            'check_in': a.check_in.strftime('%Y-%m-%d %H:%M') if a.check_in else 'N/A',
            'check_out': a.check_out.strftime('%Y-%m-%d %H:%M') if a.check_out else 'N/A',
            'status': a.status
        } for a in attendance_records
    ])

@bp.route('/api/leave')
def api_leave():
    """Get leave requests as JSON"""
    leave_requests = Leave.query.all()
    return jsonify([
        {
            'id': l.id,
            'employee_name': f"{l.employee.first_name} {l.employee.last_name}" if l.employee else 'N/A',
            'start_date': l.start_date.strftime('%Y-%m-%d'),
            'end_date': l.end_date.strftime('%Y-%m-%d'),
            'reason': l.reason,
            'status': l.status
        } for l in leave_requests
    ])

@bp.route('/api/payroll')
def api_payroll():
    """Get payroll records as JSON"""
    payroll_records = Payroll.query.all()
    return jsonify([
        {
            'id': p.id,
            'employee_name': f"{p.employee.first_name} {p.employee.last_name}" if p.employee else 'N/A',
 'pay_date': p.pay_date.strftime('%Y-%m-%d'),
 'pay_period_start': p.pay_period_start.strftime('%Y-%m-%d'),
 'pay_period_end': p.pay_period_end.strftime('%Y-%m-%d'),
 'gross_salary': p.gross_salary, # Changed key to gross_salary
            'deductions': p.deductions,
            'net_salary': p.net_salary
        } for p in payroll_records
    ])

