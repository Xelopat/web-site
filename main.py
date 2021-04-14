from flask import Flask, render_template
from werkzeug.security import check_password_hash
from werkzeug.utils import redirect

from data.users import User
from forms.user import RegisterForm, LoginForm

from data import db_session

from data import db_session

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'


# main window
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.name.data
        password = form.password.data
        db_sess = db_session.create_session()
        table = db_sess.query(User).filter(User.email == username).first()
        is_password = False
        if table:
            is_password = check_password_hash(table.hashed_password, password)
        elif db_sess.query(User).filter(User.name == username).first():
            table = db_sess.query(User).filter(User.name == username).first()
            is_password = check_password_hash(table.hashed_password, password)
        else:
            return render_template('login.html', title='Вход',
                                   form=form,
                                   message="Такого пользователя не существует")
        if is_password:
            return redirect('/')
        else:
            return render_template('login.html', title='Вход',
                                   form=form,
                                   message="Неверный пароль")
    return render_template('login.html', title='Вход', form=form)


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
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            email=form.email.data,
            about=form.about.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


db_session.global_init("db/blogs.db")
app.run('localhost', 8080, debug=True)
