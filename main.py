from datetime import datetime

from flask import Flask, render_template, request
from flask_login import LoginManager, login_required, login_user, current_user, logout_user
from werkzeug.utils import redirect

from data.create_database import User, My_spending
from forms.user import RegisterForm, LoginForm

from data import db_session

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@login_manager.user_loader
def get_id(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


# main window
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/admin/')
@login_required
def admin():
    return render_template('admin.html')


@app.route('/login/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.name.data
        password = form.password.data
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == username).first()
        if user:
            is_password = user.check_password(password)
        elif db_sess.query(User).filter(User.name == username).first():
            user = db_sess.query(User).filter(User.name == username).first()
            is_password = user.check_password(password)

        else:
            return render_template('login.html', title='Вход',
                                   form=form,
                                   message="Такого пользователя не существует")
        if is_password:
            login_user(user, remember=form.remember.data)
            return redirect('/')
        else:
            return render_template('login.html', title='Вход',
                                   form=form,
                                   message="Неверный пароль")
    return render_template('login.html', title='Вход', form=form)


@app.route('/logout/')
@login_required
def logout():
    logout_user()
    return redirect('/login')


# registration window
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация', form=form,
                                   message="Такой пользователь уже есть")
        user = User()
        user.set_name(form.name.data)
        user.set_about(form.about.data)
        user.set_email(form.email.data)
        user.set_password(form.password.data)

        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/view_spending', methods=['GET', 'POST'])
@login_required
def view_spending():
    temp = {'temp': "hhh"}
    if request.method == 'POST':
        eat = request.form["eat"]
        traveling = request.form["traveling"]
        fun = request.form["fun"]
        clothes = request.form["clothes"]
        health = request.form["health"]
        another = request.form["another"]
        session = db_session.create_session()
        if (session.query(My_spending).filter(My_spending.id == current_user.id,
                                              My_spending.month == "-".join(str(datetime.now().date()).split("-")[
                                                                            :2])).first()):

            session.query(My_spending).filter(My_spending.id == current_user.id,
                                              My_spending.month == "-".join(str(datetime.now().date()).
                                                                            split("-")[:2])). \
                update(
                {My_spending.eat: eat + My_spending.eat, My_spending.traveling: traveling + My_spending.traveling,
                 My_spending.fun: fun + My_spending.fun,
                 My_spending.clothes: clothes + My_spending.clothes, My_spending.health: health + My_spending.health,
                 My_spending.another: another + My_spending.another},
                synchronize_session=False)
        else:
            spending = My_spending(eat=eat, traveling=traveling, fun=fun, clothes=clothes, health=health,
                                   another=another, id_user=current_user.id)
            session.add(spending)
        session.commit()
        return redirect('/view_spending')
    return render_template('spending.html', title='Мои траты', temp=temp)


db_session.global_init("db/blogs.db")
app.run('localhost', 8080, debug=True)
