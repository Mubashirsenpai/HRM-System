import pytest
from app import app as create_app
from database import db as _db
from models import Employee, Department, Payroll

@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
    })

    with app.app_context():
        _db.create_all()
        # Setup initial data
        dept = Department(name="HR", description="Human Resources")
        _db.session.add(dept)
        _db.session.commit()
        emp = Employee(employee_id="EMP001", first_name="John", last_name="Doe", email="john@example.com",
                       phone="1234567890", department_id=dept.id, position_id=None, appointment_date="2023-01-01", salary=50000)
        _db.session.add(emp)
        _db.session.commit()
        payroll = Payroll(employee_id=emp.id, pay_date="2023-04-01", pay_period_start="2023-03-01",
                          pay_period_end="2023-03-31", gross_salary=4000, overtime_pay=0, bonus=0,
                          deductions=800, net_salary=3200, status="paid")
        _db.session.add(payroll)
        _db.session.commit()

    yield app

    with app.app_context():
        _db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_employees_page(client):
    response = client.get('/employees')
    assert response.status_code == 200
    assert b"Employee Management" in response.data

def test_view_employee(client):
    response = client.get('/employees/view/1')
    assert response.status_code == 200
    assert b"John Doe" in response.data

def test_payroll_page(client):
    response = client.get('/payroll')
    assert response.status_code == 200
    assert b"Payroll Management" in response.data

def test_view_payroll(client):
    response = client.get('/payroll/view/1')
    assert response.status_code == 200
    assert b"Payroll Details" in response.data

def test_department_delete_confirmation(client):
    response = client.get('/departments/delete/1')
    assert response.status_code == 200
    assert b"Confirm Deletion" in response.data

def test_department_list(client):
    response = client.get('/departments')
    assert response.status_code == 200
    assert b"Department Management" in response.data
