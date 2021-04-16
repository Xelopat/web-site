import os
import matplotlib
import matplotlib.pyplot as plt

from flask import Flask, render_template, request, jsonify
from flask_login import LoginManager, login_required, login_user, current_user, logout_user
from sqlalchemy import create_engine, text, select
from werkzeug.utils import redirect

from data.create_database import User, MySpending
from forms.user import RegisterForm, LoginForm

from data import db_session

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.init_app(app)
matplotlib.use('Agg')


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
    return render_template('spending.html', title='Мои траты')


@app.route('/my_spending', methods=['GET', 'POST'])
@login_required
def my_spending():
    date = request.args.to_dict()["date"]
    user_id = str(current_user.id)
    if not os.path.isdir(f"static/user_diagram/{user_id}"):
        os.mkdir(f"static/user_diagram/{user_id}")
    engine = create_engine('sqlite:///db/blogs.db', echo=False)
    conn = engine.connect()
    t = select([MySpending.about, MySpending.cost]).where(MySpending.user_id == int(user_id), MySpending.month == date)
    res = conn.execute(t).fetchall()
    label = []
    cost = []
    for row in res:
        label.append(row[0])
        cost.append(row[1])
    if not cost:
        cost = [1]
        label = [""]
    plt.close()
    plt.pie(cost, labels=label, autopct='%.0f%%')
    plt.savefig(f'static/user_diagram/{user_id}/{date}.png')
    link = f'static/user_diagram/{user_id}/{date}.png'
    return jsonify({"img": link})


@app.route('/update_spending', methods=['GET', 'POST'])
@login_required
def update_spending():
    if request.method == 'POST':
        about = request.form["about"]
        cost = request.form["cost"]
        date = request.form["date"]
        month = "-".join(date.split("-")[:2])
        user_id = current_user.id
        session = db_session.create_session()
        info = session.query(MySpending).filter(MySpending.user_id == user_id,
                                                MySpending.month == month,
                                                MySpending.about == about)
        if info.first():
            info.update({MySpending.cost: MySpending.cost + int(cost)}, synchronize_session=False)
        else:
            spending = MySpending(about=about, cost=cost, month=month, user_id=user_id,
                                  date=date)
            session.add(spending)
        session.commit()
        return "complete"


db_session.global_init("db/blogs.db")
app.run('localhost', 8080, debug=True)
