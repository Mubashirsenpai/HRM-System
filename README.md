# On-Premises HR Management System

A comprehensive, self-hosted HR management solution designed for organizations that prefer to keep their HR data on-premises.

## Features

### Core HR Functions
- **Employee Management**: Complete employee lifecycle management from hiring to retirement
- **Department & Position Management**: Organize your workforce structure
- **Leave Management**: Track and approve employee leave requests
- **Attendance Tracking**: Monitor employee attendance and work hours
- **Payroll Processing**: Calculate salaries, deductions, and generate payslips
- **Performance Reviews**: Conduct and track employee performance evaluations

### System Features
- **User Authentication**: Role-based access control (Admin, HR, Manager, Employee)
- **Dashboard**: Real-time overview of HR metrics
- **Reporting**: Generate various HR reports
- **Self-Service Portal**: Employee self-service capabilities
- **Data Export**: Export data in various formats

## Technology Stack

- **Backend**: Python Flask
- **Database**: SQLite (easily upgradeable to PostgreSQL/MySQL)
- **Frontend**: Bootstrap 5, HTML5, CSS3, JavaScript
- **Icons**: Font Awesome

## Installation & Setup

### Prerequisites
- Python 3.7 or higher
- pip (Python package manager)

### Quick Start

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/HRM-System.git
   cd HRM-System
   ```

2. **Create and activate a virtual environment**:
   *   On Windows:
       ```bash
       python -m venv venv
       .\venv\Scripts\activate
       ```
   *   On macOS/Linux:
       ```bash
       python3 -m venv venv
       source venv/bin/activate
       ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the database and run the application**:
   ```bash
   python app.py
   ```
   This command will create the `hrm_system.db` file if it doesn't exist and start the development server.

5. **Access the system**:
   - Open your browser and navigate to: `http://localhost:5000`
   - Default login credentials:
     - Username: `admin`
     - Password: `admin`

### Database Setup
The system uses SQLite by default. To use PostgreSQL or MySQL:
1. Update the `SQLALCHEMY_DATABASE_URI` in `app.py`
2. Install the appropriate database driver
3. Run the application to create tables

## Usage Guide

### Initial Setup
1. Log in with admin credentials
2. Create departments and positions
3. Add employees
4. Configure leave types and policies
5. Set up payroll parameters

### Daily Operations
- **HR Staff**: Manage employee records, process leave requests, handle payroll
- **Managers**: Approve leave requests, conduct performance reviews
- **Employees**: Submit leave requests, view payslips, update personal information

## Directory Structure

```
HRM_system/
├── app.py                 # Main application file
├── models.py              # Database models
├── routes.py              # Application routes
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── templates/            # HTML templates
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   ├── employees.html
│   ├── departments.html
│   ├── leaves.html
│   ├── attendance.html
│   ├── payroll.html
│   └── add_*.html
└── static/               # CSS, JS, images (if needed)
```

## Security Features

- **Password Hashing**: Uses bcrypt for secure password storage
- **Session Management**: Secure session handling
- **Role-Based Access**: Different permission levels for different user types
- **Data Validation**: Input validation and sanitization
- **CSRF Protection**: Built-in CSRF token protection

## Customization

### Adding New Features
1. Extend the models in `models.py`
2. Add routes in `routes.py`
3. Create corresponding templates

### Database Customization
- Modify models as needed
- Run the application to auto-migrate database changes
- For production, use proper migration tools

### Styling
- Modify CSS in templates
- Override Bootstrap variables
- Add custom styles as needed

## Backup & Maintenance

### Regular Backups
- Database file: `hrm_system.db`
- Configuration files
- Templates and static files

### Maintenance Tasks
- Regular database optimization
- Security updates
- Performance monitoring

## Troubleshooting

### Common Issues
1. **Database Connection**: Ensure SQLite file has write permissions
2. **Port Already in Use**: Change port in `app.py`
3. **Missing Dependencies**: Run `pip install -r requirements.txt`

### Support
For issues or questions:
1. Check the logs in the console
2. Verify database connectivity
3. Ensure all dependencies are installed

## License

This is an open-source HR management system. Feel free to modify and distribute according to your needs.

## Future Enhancements

- [ ] Advanced reporting and analytics
- [ ] Email notifications
- [ ] Mobile responsive design
- [ ] API endpoints for integrations
- [ ] Advanced search and filtering
- [ ] Document management system
- [ ] Training and certification tracking
- [ ] Advanced payroll features
- [ ] Performance management system
- [ ] Employee self-service portal enhancements
