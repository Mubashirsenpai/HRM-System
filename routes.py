"""
Application routes for the HR Management System
"""

from flask import render_template, request, redirect, url_for, flash, jsonify, session, send_file, make_response
from datetime import datetime, timedelta
from app import app
from database import db
from models import *
import os
import csv
import pandas as pd
import io

# --- New Routes for Authentication ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Placeholder login route"""
    # For now, we will just redirect to the dashboard.
    # In a real application, you would handle user authentication here.
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    """Logout route to clear the session"""
    # In a real application, you might use flask-login to handle this.
    # Here, we'll just clear the session and redirect to login or dashboard.
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('dashboard'))
# --- End of New Routes ---


@app.route('/')
def dashboard():
    """Main dashboard with system overview"""
    total_employees = Employee.query.count()
    total_departments = Department.query.count()
    pending_leaves = Leave.query.filter_by(status='pending').count()
    
    # Get recent attendance count for today
    today_date = datetime.now().date()
    recent_attendance = Attendance.query.filter(Attendance.date == today_date).count()

    # Fetch recent activities from different models
    recent_employees = Employee.query.order_by(Employee.hire_date.desc()).limit(3).all()
    recent_leaves = Leave.query.order_by(Leave.created_at.desc()).limit(3).all()
    recent_departments = Department.query.order_by(Department.created_at.desc()).limit(3).all()
    
    # Combine and sort all recent activities by their creation/hire date
    all_recent_activities = []
    
    for emp in recent_employees:
        all_recent_activities.append({
            'type': 'employee_hired',
            # Convert date object to datetime object for consistent sorting
            'timestamp': datetime.combine(emp.hire_date, datetime.min.time()),
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
    
    all_recent_activities.sort(key=lambda x: x['timestamp'], reverse=True)

    return render_template('dashboard.html', 
                            total_employees=total_employees,
                            total_departments=total_departments,
                            pending_leaves=pending_leaves,
                            recent_attendance=recent_attendance,
                            all_recent_activities=all_recent_activities)

# --- Employee Management Routes ---
@app.route('/employees')
def employees():
    """Display all employees"""
    employees = Employee.query.all()
    return render_template('employees.html', employees=employees)

@app.route('/employees/add', methods=['GET', 'POST'])
def add_employee():
    """Add a new employee"""
    departments = Department.query.all()
    positions = Position.query.all()
    if request.method == 'POST':
        try:
            employee_id = request.form.get('employee_id')
            first_name = request.form.get('first_name')
            last_name = request.form.get('last_name')
            email = request.form.get('email')
            department_id = request.form.get('department_id')
            position_id = request.form.get('position_id')
            hire_date_str = request.form.get('hire_date')
            salary = request.form.get('salary')

            if not all([employee_id, first_name, last_name, email, phone, department_id, position_id, hire_date_str, salary]):
                flash('All fields are required.', 'danger')
                return redirect(url_for('add_employee'))
            
            hire_date = datetime.strptime(hire_date_str, '%Y-%m-%d').date()
            phone = request.form.get('phone')
            
            new_employee = Employee(
                employee_id=employee_id,
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                department_id=department_id,
                position_id=position_id,
                hire_date=hire_date,
                salary=float(salary)
            )
            
            db.session.add(new_employee)
            db.session.commit()
            
            flash('Employee added successfully!', 'success')
            return redirect(url_for('employees'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding employee: {e}', 'danger')

    return render_template('add_employee.html', departments=departments, positions=positions)

@app.route('/employees/edit/<int:id>', methods=['GET', 'POST'])
def edit_employee(id):
    """Edit an existing employee"""
    employee = Employee.query.get_or_404(id)
    departments = Department.query.all()
    positions = Position.query.all()
    if request.method == 'POST':
        try:
            employee.employee_id = request.form.get('employee_id')
            employee.first_name = request.form.get('first_name')
            employee.last_name = request.form.get('last_name')
            employee.email = request.form.get('email')
            employee.department_id = request.form.get('department_id')
            employee.position_id = request.form.get('position_id')
            employee.phone = request.form.get('phone')
            employee.hire_date = datetime.strptime(request.form.get('hire_date'), '%Y-%m-%d').date()
            employee.salary = float(request.form.get('salary'))
            db.session.commit()
            flash('Employee updated successfully!', 'success')
            return redirect(url_for('employees'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating employee: {e}', 'danger')

    return render_template('edit_employee.html', employee=employee, departments=departments, positions=positions)

@app.route('/employees/delete/<int:id>', methods=['POST', 'GET'])
def delete_employee(id):
    """Delete an employee"""
    employee = Employee.query.get_or_404(id)
    if request.method == 'POST':
        try:
            db.session.delete(employee)
            db.session.commit()
            flash('Employee deleted successfully!', 'success')
            return redirect(url_for('employees'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error deleting employee: {e}', 'danger')
    
    # Render a confirmation page for GET requests
        return render_template('confirm_delete_employee.html', employee=employee)
    
# --- Bulk Employee Upload Routes ---
@app.route('/employees/sample_csv')
def sample_csv():
    """Provide a sample CSV template for bulk employee upload"""
    # Create a sample CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['employee_id', 'first_name', 'last_name', 'email', 'phone', 'hire_date', 'department_id', 'position_id', 'salary'])
    writer.writerow(['EMP001', 'John', 'Doe', 'john.doe@example.com', '123-456-7890', '2023-01-15', '1', '1', '50000.00'])
    
    # Create response
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename=sample_employees.csv'
    return response

@app.route('/employees/sample_excel')
def sample_excel():
    """Provide a sample Excel template for bulk employee upload"""
    # Create a sample DataFrame
    data = {
        'employee_id': ['EMP001'],
        'first_name': ['John'],
        'last_name': ['Doe'],
        'email': ['john.doe@example.com'],
        'phone': ['123-456-7890'],
        'hire_date': ['2023-01-15'],
        'department_id': ['1'],
        'position_id': ['1'],
        'salary': ['50000.00']
    }
    df = pd.DataFrame(data)
    
    # Create Excel file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Employees')
    output.seek(0)
    
    # Create response
    response = make_response(output.read())
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    response.headers['Content-Disposition'] = 'attachment; filename=sample_employees.xlsx'
    return response

@app.route('/employees/bulk_upload', methods=['GET', 'POST'])
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
                # Process Excel file
                df = pd.read_excel(file)
                employees_data = df.to_dict('records')
            
            # Process each employee record
            success_count = 0
            error_count = 0
            errors = []
            
            for i, row in enumerate(employees_data):
                try:
                    # Validate required fields
                    required_fields = ['employee_id', 'first_name', 'last_name', 'email', 'phone', 'hire_date', 'department_id', 'position_id', 'salary']
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
                    
                    # Validate hire date
                    try:
                        hire_date = datetime.strptime(row['hire_date'], '%Y-%m-%d').date()
                    except ValueError:
                        errors.append(f"Row {i+1}: Invalid hire date format. Use YYYY-MM-DD")
                        error_count += 1
                        continue
                    
                    # Validate salary
                    try:
                        salary = float(row['salary'])
                    except ValueError:
                        errors.append(f"Row {i+1}: Invalid salary format")
                        error_count += 1
                        continue
                    
                    # Create new employee
                    new_employee = Employee(
                        employee_id=row['employee_id'],
                        first_name=row['first_name'],
                        last_name=row['last_name'],
                        email=row['email'],
                        phone=row['phone'],
                        department_id=int(row['department_id']),
                        position_id=int(row['position_id']),
                        hire_date=hire_date,
                        salary=salary
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
        
        return redirect(url_for('employees'))
    
    return render_template('bulk_upload_employees.html')


# --- Department Management Routes ---
@app.route('/departments')
def departments():
    """Display all departments"""
    departments = Department.query.all()
    return render_template('departments.html', departments=departments)

@app.route('/departments/add', methods=['GET', 'POST'])
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
            return redirect(url_for('departments'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding department: {e}', 'danger')
    return render_template('add_department.html')

@app.route('/departments/edit/<int:id>', methods=['GET', 'POST'])
def edit_department(id):
    """Edit an existing department"""
    department = Department.query.get_or_404(id)
    if request.method == 'POST':
        try:
            department.name = request.form.get('name')
            department.description = request.form.get('description')
            db.session.commit()
            flash('Department updated successfully!', 'success')
            return redirect(url_for('departments'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating department: {e}', 'danger')
    return render_template('edit_department.html', department=department)

@app.route('/departments/delete/<int:id>', methods=['POST', 'GET'])
def delete_department(id):
    """Delete a department"""
    department = Department.query.get_or_404(id)
    if request.method == 'POST':
        try:
            db.session.delete(department)
            db.session.commit()
            flash('Department deleted successfully!', 'success')
            return redirect(url_for('departments'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error deleting department: {e}', 'danger')
    return render_template('confirm_delete_department.html', department=department)


@app.route('/departments/view/<int:department_id>')
def view_department(department_id):
    """View details of a single department"""
    department = Department.query.get_or_404(department_id)
    return render_template('view_department.html', department=department)


# --- Position Management Routes ---
@app.route('/positions')
def positions():
    """Display all positions"""
    positions = Position.query.all()
    return render_template('positions.html', positions=positions)

@app.route('/positions/view/<int:id>')
def view_position(id):
    """View details of a single position"""
    position = Position.query.get_or_404(id)
    return render_template('view_position.html', position=position)

@app.route('/positions/add', methods=['GET', 'POST'])
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
            return redirect(url_for('positions'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding position: {e}', 'danger')
    return render_template('add_position.html', departments=departments)

@app.route('/positions/edit/<int:id>', methods=['GET', 'POST'])
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
            return redirect(url_for('positions'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating position: {e}', 'danger')
    return render_template('edit_position.html', position=position, departments=departments)

@app.route('/positions/delete/<int:id>', methods=['POST', 'GET'])
def delete_position(id):
    """Delete a position"""
    position = Position.query.get_or_404(id)
    if request.method == 'POST':
        try:
            db.session.delete(position)
            db.session.commit()
            flash('Position deleted successfully!', 'success')
            return redirect(url_for('positions'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error deleting position: {e}', 'danger')
    return render_template('confirm_delete_position.html', position=position)


# --- Leave Management Routes ---
@app.route('/leave')
def leave():
    """Display all leave requests"""
    leave_requests = Leave.query.all()
    # The variable name in the template is `leaves`, so we should
    # pass the data with that key.
    return render_template('leaves.html', leaves=leave_requests)

@app.route('/leave/add', methods=['GET', 'POST'])
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
            return redirect(url_for('leave'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error submitting leave request: {e}', 'danger')
    return render_template('add_leave.html', employees=employees)

@app.route('/leave/edit/<int:leave_id>', methods=['GET', 'POST'])
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
            return redirect(url_for('leave'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating leave request: {e}', 'danger')
    return render_template('edit_leave.html', leave_request=leave_request, employees=employees)

@app.route('/leave/delete/<int:leave_id>', methods=['POST', 'GET'])
def delete_leave(leave_id):
    """Delete a leave request"""
    leave_request = Leave.query.get_or_404(leave_id)
    if request.method == 'POST':
        try:
            db.session.delete(leave_request)
            db.session.commit()
            flash('Leave request deleted successfully!', 'success')
            return redirect(url_for('leave'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error deleting leave request: {e}', 'danger')
    return render_template('confirm_delete_leave.html', leave_request=leave_request)

@app.route('/leave/view/<int:leave_id>')
def view_leave(leave_id):
    """View details of a single leave request"""
    leave_request = Leave.query.get_or_404(leave_id)
    return render_template('view_leave.html', leave_request=leave_request)


# --- Attendance Management Routes ---
@app.route('/attendance')
def attendance():
    """Display all attendance records"""
    attendance_records = Attendance.query.all()
    return render_template('attendance.html', attendance_records=attendance_records)

@app.route('/attendance/add', methods=['GET', 'POST'])
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
            return redirect(url_for('attendance'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding attendance record: {e}', 'danger')
    return render_template('add_attendance.html', employees=employees)

@app.route('/attendance/edit/<int:id>', methods=['GET', 'POST'])
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
            return redirect(url_for('attendance'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating attendance record: {e}', 'danger')
    return render_template('edit_attendance.html', attendance=attendance, employees=employees)

@app.route('/attendance/delete/<int:id>', methods=['POST', 'GET'])
def delete_attendance(id):
    """Delete an attendance record"""
    attendance = Attendance.query.get_or_404(id)
    if request.method == 'POST':
        try:
            db.session.delete(attendance)
            db.session.commit()
            flash('Attendance record deleted successfully!', 'success')
            return redirect(url_for('attendance'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error deleting attendance record: {e}', 'danger')
    return render_template('confirm_delete_attendance.html', attendance=attendance)


# --- Payroll Management Routes ---
@app.route('/payroll')
def payroll():
    """Display all payroll records and employees for the generation modal"""
    payroll_records = Payroll.query.all()
    employees = Employee.query.all()
    return render_template('payroll.html', payroll_records=payroll_records, employees=employees)


@app.route('/payroll/generate', methods=['POST'])
def generate_payroll():
    """Generate a new payroll record based on a time period"""
    try:
        employee_id = request.form.get('employee_id')
        pay_period_start_str = request.form.get('pay_period_start')
        pay_period_end_str = request.form.get('pay_period_end')

        employee = Employee.query.get(employee_id)
        if not employee:
            flash('Employee not found.', 'danger')
            return redirect(url_for('payroll'))

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

    return redirect(url_for('payroll'))

@app.route('/payroll/edit/<int:id>', methods=['GET', 'POST'])
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
            return redirect(url_for('payroll'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating payroll record: {e}', 'danger')
    return render_template('edit_payroll.html', payroll=payroll, employees=employees)

@app.route('/payroll/delete/<int:id>', methods=['POST', 'GET'])
def delete_payroll(id):
    """Delete a payroll record"""
    payroll = Payroll.query.get_or_404(id)
    if request.method == 'POST':
        try:
            db.session.delete(payroll)
            db.session.commit()
            flash('Payroll record deleted successfully!', 'success')
            return redirect(url_for('payroll'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error deleting payroll record: {e}', 'danger')
    return render_template('confirm_delete_payroll.html', payroll=payroll)


# --- API Endpoints ---
@app.route('/api/employees')
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

@app.route('/api/departments')
def api_departments():
    """Get departments list as JSON"""
    departments = Department.query.all()
    return jsonify([
        {
            'id': d.id,
            'name': d.name,
            'description': d.description,
            'employee_count': len(d.employees)
        } for d in departments
    ])

@app.route('/api/positions')
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
            'employee_count': len(p.employees)
        } for p in positions
    ])

@app.route('/api/attendance')
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

@app.route('/api/leave')
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

@app.route('/api/payroll')
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

