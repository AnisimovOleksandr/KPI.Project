import os
import psycopg2
from flask import Flask, render_template, request, redirect, url_for, g, session, flash
from config import Config

server = Flask(__name__)
server.config.from_object(Config)

def get_user_by_login(login):
    connection = psycopg2.connect(server.config['SQLALCHEMY_DATABASE_URI'])
    connection.autocommit = True

    cursor = connection.cursor()
    cursor.execute("""SELECT * FROM users WHERE users.user_login = %(u_login)s""", {'u_login': login})
    result = cursor.fetchall()
    connection.close()

    users = []
    for uid, login, password, email, fname, lname, role in result:
        user = {
            "id": uid,
            "login": login,
            "password": password,
            "email": email,
            "fname": fname,
            "lname": lname,
            "role": role
        }
        users.append(user)

    return users

def get_user_by_id(id):
    connection = psycopg2.connect(server.config['SQLALCHEMY_DATABASE_URI'])
    connection.autocommit = True

    cursor = connection.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = {0}'.format(id))
    result = cursor.fetchall()
    connection.close()

    users = []
    for uid, login, password, email, fname, lname, role in result:
        user = {
            "id": uid,
            "login": login,
            "password": password,
            "email": email,
            "fname": fname,
            "lname": lname,
            "role": role
        }
        users.append(user)

    return users

def get_student_by_id(id):
    connection = psycopg2.connect(server.config['SQLALCHEMY_DATABASE_URI'])
    connection.autocommit = True

    cursor = connection.cursor()
    cursor.execute('SELECT * FROM students WHERE student_id = {0}'.format(id))
    result = cursor.fetchall()
    connection.close()

    students = []
    for sid, curator, group in result:
        student = {
            "id": sid,
            "curator": curator,
            "group": group
        }
        students.append(student)

    return students

def get_teacher_by_id(id):
    connection = psycopg2.connect(server.config['SQLALCHEMY_DATABASE_URI'])
    connection.autocommit = True

    cursor = connection.cursor()
    cursor.execute('SELECT * FROM teachers WHERE teacher_id = {0}'.format(id))
    result = cursor.fetchall()
    connection.close()

    teachers = []
    for sid, title, degree in result:
        teacher = {
            "id": sid,
            "title": title,
            "degree": degree
        }
        teachers.append(teacher)

    return teachers

@server.route('/')
def index():
    return redirect(url_for('admin'))
        
@server.route('/admin')
def admin():
    connection = psycopg2.connect(server.config['SQLALCHEMY_DATABASE_URI'])
    connection.autocommit = True

    cursor = connection.cursor()
    cursor.execute("SELECT * FROM users")
    users_lst = cursor.fetchall()
    connection.close()

    return render_template('admin.html', users = users_lst)

@server.route('/adduser', methods=['POST'])
def adduser():
    connection = psycopg2.connect(server.config['SQLALCHEMY_DATABASE_URI'])
    connection.autocommit = True

    login = request.form['login']
    password = request.form['password']
    email = request.form['email']
    fname = request.form['fname']
    lname = request.form['lname']
    
    role = request.form['role']
    curator = request.form['curator']
    group = request.form['group']
    degree = request.form['degree']
    title = request.form['title']

    if (login == '' or
        password == '' or
        email == '' or 
        fname == '' or 
        lname == ''):
        flash('Заповніть усі поля, позначені *!')
    elif len(login) < 6:
        flash('Логін занадто короткий (потрібно мінімум 6 символів)!')
    elif len(password) < 6:
        flash('Пароль занадто короткий (потрібно мінімум 6 символів)!')
    else:
        users = get_user_by_login(login)

        if users != []:
            flash('Користувача з таким логіном вже зареєстровано')
        else:
            cursor = connection.cursor()
            cursor.execute("INSERT INTO users (user_login, user_password, user_email, user_fname, user_lname, user_role ) VALUES (%s, %s, %s, %s, %s, %s)", 
                          (login, password, email, fname, lname, role))
            
            users_after_insert = get_user_by_login(login)

            if role == 'student':
                cursor.execute("INSERT INTO students (student_id, student_curator, student_group) VALUES (%s, %s, %s)", 
                              (users_after_insert[0]['id'], curator, group))
            elif role == 'teacher':
                cursor.execute("INSERT INTO teachers (teacher_id, teacher_title, teacher_degree) VALUES (%s, %s, %s)", 
                              (users_after_insert[0]['id'], degree, title))

            flash('Користувача успішно додано')

    connection.close()
    return redirect(url_for('admin')) 

@server.route('/delete/<string:id>', methods=['POST', 'GET'])
def delete(id):
    connection = psycopg2.connect(server.config['SQLALCHEMY_DATABASE_URI'])
    connection.autocommit = True

    user = get_user_by_id(id)[0]
    if user['role'] == 'admin':
        flash('Адміністратора не може бути видалено')
    else:
        cursor = connection.cursor()
        cursor.execute('DELETE FROM users WHERE user_id = {0}'.format(id))

        if user['role'] == 'student':
            cursor.execute('DELETE FROM students WHERE student_id = {0}'.format(id))
        elif user['role'] == 'teacher':
            cursor.execute('DELETE FROM teachers WHERE teacher_id = {0}'.format(id))

        flash('Користувача успішно видалено')
    
    connection.close()
    return redirect(url_for('admin'))

@server.route('/edit/<id>', methods=['POST', 'GET'])
def edit(id):
    users_lst = get_user_by_id(id)

    students_lst = []
    teachers_lst = []

    if users_lst[0]['role'] == 'student':
        students_lst = get_student_by_id(id)
        return render_template('edit_student.html', users = users_lst, students = students_lst)
    if users_lst[0]['role'] == 'teacher':
        teachers_lst = get_teacher_by_id(id)
        return render_template('edit_teacher.html', users = users_lst, teachers = teachers_lst)
    
    flash('Щось пішло не так...')
    return redirect(url_for('admin'))
    
@server.route('/update/<id>', methods=['POST'])
def update(id):
    fname = request.form['fname']
    lname = request.form['lname']
    email = request.form['email']
    role = request.form['role']

    connection = psycopg2.connect(server.config['SQLALCHEMY_DATABASE_URI'])
    connection.autocommit = True

    cursor = connection.cursor()
    cursor.execute("""UPDATE users SET user_fname = %s, user_lname = %s, user_email = %s WHERE user_id = %s""",
                  (fname, lname, email, id))
    
    if role == 'student':
        curator = request.form['curator']
        group = request.form['group']

        cursor.execute("""UPDATE students SET student_curator = %s, student_group = %s WHERE student_id = %s""",
                      (curator, group, id))
    elif role == 'teacher':
        title = request.form['title']
        degree = request.form['degree']

        cursor.execute("""UPDATE teachers SET teacher_title = %s, teacher_degree = %s WHERE teacher_id = %s""",
                      (title, degree, id))
    
    connection.close()
    return redirect(url_for('admin'))

if __name__ == '__main__':
    server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))