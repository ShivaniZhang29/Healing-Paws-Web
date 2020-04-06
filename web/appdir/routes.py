from appdir import app, db
from flask import render_template, flash, redirect, url_for, session, request, jsonify
from appdir.config import Config
from appdir.forms import LoginForm, RegisterForm, ReviewForm, QuestionForm, AppointmentForm
from appdir.models import User, Question, Answer, Appointment
from werkzeug.security import generate_password_hash, check_password_hash

from appdir.models import *


@app.route("/")
@app.route("/index")
def index():
    user = None
    if session.get("USERNAME") != None:
        user = User.query.filter(User.username == session.get("USERNAME")).first()
    return render_template('index.html', title='Home Page', user=user)

@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        passw_hash = generate_password_hash(form.password.data)
        user = User(username=form.username.data, email=form.email.data, dob=form.dob.data, password_hash=passw_hash, phone=form.phone.data, address=form.address.data, is_customer=form.account_type.data=='C')
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('register.html', title='Register a new user', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user_in_db = User.query.filter(User.username == form.username.data).first()
        if not user_in_db:
            flash('No user found with username: {}'.format(form.username.data))
            return redirect(url_for('login'))
        if (check_password_hash(user_in_db.password_hash, form.password.data)):
            session["USERNAME"] = user_in_db.username #登录成功后添加状态
            return redirect(url_for('index'))
        flash('Incorrect Password')
        return redirect(url_for('login'))
    return render_template('login.html', title='Login', form=form)

@app.route('/logout')
def logout():
    session.pop("USERNAME", None)
    return redirect(url_for('login'))

@app.route("/reset")
def reset():
    db.drop_all()
    db.create_all()
    return '重建所有表'

@app.route('/reviewquestions',methods=['GET','POST'])
def reviewquestions():
    form = ReviewForm()
    if form.validate_on_submit():
        prev_questions = Question.query.filter(Question.title.like('%'+form.keyword.data+'%')).all()
        return render_template('reviewquestions.html',title="Questions Review",prev_questions=prev_questions,form=form)
    else:
        prev_questions = Question.query.filter()
    return render_template('reviewquestions.html',title="Questions Review",prev_questions=prev_questions,form=form)

@app.route('/addquestion',methods=['GET','POST'])
def addquestion():
    form = QuestionForm()
    if not session.get("USERNAME") is None:
        username = session.get("USERNAME")
        user_in_db = User.query.filter(User.username == username).first()
        if form.validate_on_submit():
            question_db = Question(title = form.title.data, body = form.body.data, anonymity = form.anonymity.data, user_id=user_in_db.id)
            db.session.add(question_db) 
            db.session.commit()
            return redirect(url_for('reviewquestions'))
        else:
            return render_template('addquestion.html',title="Add a Question", user = user_in_db, form=form)
    else:
        flash("User needs to either login or signup first")
        return redirect(url_for('login'))
    return render_template('addquestion.html',title="Add a Question", form=form)
        
@app.route('/answerquestion', methods=['GET','POST'])
def answerquestion():
    index = int(request.form['index'])
    questions = Question.query.filter()
    question_db = questions[index]

    form = AnswerForm
    if not session.get("USERNAME") is None:
        username = session.get("USERNAME")
        user_in_db = User.query.filter(User.username == username).first()
        if form.validate_on_submit():
            answer_db = Answer(body = form.body.data, question_id = question_db.id, user=user_in_db)
            db.session.add(answer_db) 
            db.session.commit()
            return redirect(url_for('reviewquestions'))
        else:
            prev_answers = Answer.query.filter(Answer.question_id == question_db.id).all()
    return render_template('answerquestion.html',title="Answer Question",prev_answers=prev_answers,question = question_db, form=form)

        

@app.route('/handleappointment/<appointment_id>')
def handleappointment(appointment_id):
    if not session.get("USERNAME") is None:
        username = session.get("USERNAME")
        user_in_db = User.query.filter(User.username == username).first()
        if user_in_db.is_customer:
            return "请以员工身份登录"
        appointment = Appointment.query.filter(Appointment.id == appointment_id).first()
        pet = Pet.query.filter(Pet.id == appointment.pet_id).first()
        customer = User.query.filter(User.id == pet.owner_id).first()
        employee = User.query.filter(User.id == appointment.employee_id).first()
        preferred_doctor = Doctor.query.filter(Doctor.id == appointment.preferred_doctor_id).first()
        assigned_doctor = Doctor.query.filter(Doctor.id == appointment.assigned_doctor_id).first()
        return render_template('handleappointment.html', title="Handle Appointment",
                               appointment=appointment, pet=pet, customer=customer, employee=employee,
                               preferred_doctor=preferred_doctor, assigned_doctor=assigned_doctor, user=user_in_db)
    else:
        flash("User needs to either login or signup first")
        return redirect(url_for('login'))

@app.route('/change_pet_status',methods=["POST"])
def change_pet_status():    
    appointment_id = request.args.get("appointment_id")
    pet_status = request.args.get("pet_status")
    appointment = Appointment.query.filter(Appointment.id == appointment_id).first()
    appointment.pet_status = pet_status
    return jsonify({"code":200})

@app.route('/make_appointment', methods=['POST','GET'])
def make_appointment():
    form = AppointmentForm()
    if not session.get("USERNAME") is None:
        username = session.get("USERNAME")
        user_in_db = User.query.filter(User.username == username).first()
        if not user_in_db.is_customer:
            return "请以顾客身份登录"
        elif form.validate_on_submit(): # 第二次，已填写
            return redirect('index')
        else: # 第一次，还未填写
            pets = Pet.query.filter(Pet.owner_id == user_in_db.id).all()
            form.pet.choices = [(pet.id, pet.name) for pet in pets]
            return render_template('make_appointment.html',title="Make a new appointment", user=user_in_db, form=form)
    else:
        flash("User needs to either login or signup first")
        return redirect(url_for('login'))
