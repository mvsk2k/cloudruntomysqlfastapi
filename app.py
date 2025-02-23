from fastapi import FastAPI, HTTPException, Depends, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel
import os
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# FastAPI app instance
app = FastAPI()


"""
# Cloud SQL connection parameters (Use environment variables for security)
DB_USER = os.getenv('DB_USER', 'your_user')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'your_password')
DB_NAME = os.getenv('DB_NAME', 'your_database')
DB_CONNECTION_NAME = os.getenv('DB_CONNECTION_NAME', 'your-project:your-region:your-instance')

# SQLAlchemy configuration (Using Cloud SQL Unix Socket)
DATABASE_URL = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@/{DB_NAME}"
    f"?unix_socket=/cloudsql/{DB_CONNECTION_NAME}"
)

"""

DB_USER = 'root'
DB_PASSWORD = 'siva12345'
DB_NAME = 'supersimple'
DB_HOST = '34.28.238.234'

# SQLAlchemy configuration (Using Public IP)
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"


# Create database engine
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Define Base
Base = declarative_base()

# Ensure EmployeeCreate is Defined Before Use
class EmployeeCreate(BaseModel):
    name: str
    department: str
    salary: int

#Use Pydantic model for request body
class EmployeeUpdate(BaseModel):
    name: str | None = None
    department: str | None = None
    salary: int | None = None


# Define Employee model (Ensure this matches your MySQL table name)
class Employee(Base):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    department = Column(String(100), nullable=False)
    salary = Column(Integer, nullable=False)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create the database tables (if not already created)
Base.metadata.create_all(bind=engine)

# --- CRUD Routes ---

# READ: Get all employees
@app.get("/employees")
def get_employees(db: Session = Depends(get_db)):
    employees = db.query(Employee).all()
    return employees

# READ: Get a single employee by ID
@app.get("/employee/{emp_id}")
def get_employee(emp_id: int, db: Session = Depends(get_db)):
    employee = db.query(Employee).filter(Employee.id == emp_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee

# CREATE: Add a new employee
@app.post("/employee", status_code=201)
#def add_employee(name: str, department: str, salary: int, db: Session = Depends(get_db)):
def add_employee(employee: EmployeeCreate = Body(...), db: Session = Depends(get_db)):  # this line to recognize Json
    #new_employee = Employee(name=name, department=department, salary=salary)
    new_employee = Employee(name=employee.name, department=employee.department, salary=employee.salary)
    db.add(new_employee)
    db.commit()
    db.refresh(new_employee)
    return {"message": "Employee added successfully!", "id": new_employee.id}

# UPDATE: Update an existing employee
@app.put("/employee/{emp_id}")
#def update_employee(emp_id: int, name: str = None, department: str = None, salary: int = None, db: Session = Depends(get_db)):
def update_employee(emp_id: int, employee_update: EmployeeUpdate, db: Session = Depends(get_db)):
    employee = db.query(Employee).filter(Employee.id == emp_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    # Update fields only if new values are provided
    if employee_update.name is not None:
        employee.name = employee_update.name
    if employee_update.department is not None:
        employee.department = employee_update.department
    if employee_update.salary is not None:
        employee.salary = employee_update.salary

    db.commit()
    db.refresh(employee)  # Refresh the object from the DB to reflect the changes
    
    return {"message": "Employee updated successfully!"}

# DELETE: Remove an employee
@app.delete("/employee/{emp_id}")
def delete_employee(emp_id: int, db: Session = Depends(get_db)):
    employee = db.query(Employee).filter(Employee.id == emp_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    db.delete(employee)
    db.commit()
    return {"message": "Employee deleted successfully!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)

