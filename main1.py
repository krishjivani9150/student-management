from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional
from sqlalchemy import create_engine, Column, Integer, String, Text, Float, JSON
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv
import json,os



app = FastAPI()


# CORS (frontend to backend access)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

# Database setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# SQLAlchemy model
class Student(Base):
    __tablename__ = "student_result"
    id = Column(Integer, primary_key=True, autoincrement=True)
    roll_number = Column(Integer)
    name = Column(String(50))
    age = Column(Integer)
    gender = Column(String(10))
    course = Column(String(20))
    mark = Column(JSON)
    avg = Column(Float)
    grade = Column(String(2))

Base.metadata.create_all(engine)

# Pydantic model
class StudentIn(BaseModel):
    name: str
    age: int
    gender: str
    course: str
    mark: Dict[str, int]
    id: Optional[int] = None  # used for editing

class StudentOut(StudentIn):
    roll_number: int
    avg: float
    grade: str

# Grade calculation
def get_grade(avg):
    if avg >= 90:
        return 'A'
    elif avg >= 75:
        return 'B'
    elif avg >= 60:
        return 'C'
    else:
        return 'D'

# 🔹 Add Student
@app.post("/insert/")
def insert_student(student: StudentIn):
    db = SessionLocal()
    try:
        # Step 1: Insert the new student with temporary roll_number = 0
        marks = student.mark
        avg = sum(marks.values()) / len(marks)
        grade = get_grade(avg)

        temp_student = Student(
            name=student.name,
            age=student.age,
            gender=student.gender,
            course=student.course,
            mark=marks,
            avg=avg,
            grade=grade,
            roll_number=0  # temporary, will be sorted
        )
        db.add(temp_student)
        db.commit()  # Now we have the student with ID
        db.refresh(temp_student)

        # Step 2: Fetch all students in that course and sort them by name
        course_students = (
            db.query(Student)
            .filter_by(course=student.course)
            .order_by(Student.name.asc())
            .all()
        )

        # Step 3: Assign new roll numbers based on sorted order
        for idx, stud in enumerate(course_students, start=1):
            stud.roll_number = idx

        db.commit()

        return {"message": "Student added and roll numbers updated alphabetically"}

    finally:
        db.close()


# 🔹 View All
@app.get("/view/", response_model=List[StudentOut])
def view_all():
    db = SessionLocal()
    try:
        students = db.query(Student).order_by(Student.course, Student.roll_number).all()
        return students
    finally:
        db.close()

# 🔹 Update
@app.put("/update/")
def update_student(course: str, student_id: int, updated: StudentIn):
    db = SessionLocal()
    try:
        # Update student info
        student = db.query(Student).filter_by(course=course, id=student_id).first()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")

        student.name = updated.name
        student.age = updated.age
        student.gender = updated.gender
        student.course = updated.course
        student.mark = updated.mark

        # Recalculate avg and grade
        student.avg = sum(updated.mark.values()) / len(updated.mark)
        student.grade = get_grade(student.avg)

        db.commit()

        # Now reassign roll numbers alphabetically in this course
        course_students = db.query(Student).filter_by(course=updated.course).all()
        course_students.sort(key=lambda s: s.name.lower())

        for idx, stud in enumerate(course_students, start=1):
            stud.roll_number = idx

        db.commit()
        return {"message": "Student updated with alphabetical roll number"}
    finally:
        db.close()


# 🔹 Delete
@app.delete("/delete/")
def delete_student(student_id: int, course: str):
    db = SessionLocal()
    try:
        stud = db.query(Student).filter_by(id=student_id, course=course).first()
        if not stud:
            raise HTTPException(status_code=404, detail="Student not found")
        db.delete(stud)
        db.commit()
        return {"message": "Student deleted"}
    finally:
        db.close()

# 🔹 Filter
@app.get("/students/filter", response_model=List[StudentOut])
def filter_students(course: Optional[str] = None, gender: Optional[str] = None):
    db = SessionLocal()
    try:
        query = db.query(Student)
        if course:
            query = query.filter(Student.course == course)
        if gender:
            query = query.filter(Student.gender == gender)
        return query.order_by(Student.course, Student.roll_number).all()
    finally:
        db.close()


from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi import Request
from fastapi.staticfiles import StaticFiles

templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
def serve_home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Hosting notes:
# ----------------
# To deploy this on Replit or Render:
# 1. Add `requirements.txt` file:
#    fastapi
#    uvicorn
#    sqlalchemy
#    pymysql
#    python-dotenv
# 2. On Replit: add `.replit` with:
#    run = "uvicorn main:app --host=0.0.0.0 --port=8000"
# 3. OR On Render: connect GitHub repo and set start command same as above.
