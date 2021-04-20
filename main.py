import os
import matplotlib
import matplotlib.pyplot as plt

from flask import Flask, render_template, request, jsonify
from flask_login import LoginManager, login_required, login_user, current_user, logout_user
from sqlalchemy import create_engine, select, func
from werkzeug.utils import redirect

from data.create_database import User, MySpending
from forms.user import RegisterForm, LoginForm

from data import db_session

db_path = "db/blogs.db"

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


@app.route('/my_spending_month', methods=['GET', 'POST'])
@login_required
def my_spending_month():
    date = request.args.to_dict()["date"]
    user_id = str(current_user.id)
    if not os.path.isdir(f"static/user_diagram/{user_id}"):
        os.mkdir(f"static/user_diagram/{user_id}")
    engine = create_engine(f'sqlite:///{db_path}', echo=False)
    conn = engine.connect()
    t = select([MySpending.about, func.sum(MySpending.cost)]).where(MySpending.user_id == int(user_id),
                                                          MySpending.month == date).group_by(MySpending.about)
    res = conn.execute(t).fetchall()
    label = []
    cost = []
    for row in res:
        label.append(row[0])
        cost.append(row[1])

    for i in range(len(cost) - 1, -1, -1):
        if cost[i] == 0:
            del cost[i]
            del label[i]
    if not cost:
        cost = [1]
        label = [""]
    plt.close()
    plt.pie(cost, labels=label, autopct='%.0f%%')
    plt.savefig(f'static/user_diagram/{user_id}/{date}.png')
    link = f'static/user_diagram/{user_id}/{date}.png'
    return jsonify({"img": link})


@app.route('/my_spending_day', methods=['GET', 'POST'])
@login_required
def my_spending_day():
    date = request.args.to_dict()["date"]
    user_id = str(current_user.id)
    if not os.path.isdir(f"static/user_diagram/{user_id}"):
        os.mkdir(f"static/user_diagram/{user_id}")
    engine = create_engine(f'sqlite:///{db_path}', echo=False)
    conn = engine.connect()
    t = select([MySpending.id, MySpending.about, MySpending.info, MySpending.cost]).where(
        MySpending.user_id == int(user_id),
        MySpending.date == date)
    res = conn.execute(t).fetchall()
    spending_id, name, info, cost = [], [], [], []
    for i in res:
        spending_id.append(i[0])
        name.append(i[1])
        info.append(i[2])
        cost.append(i[3])
    return jsonify({"id": spending_id, "name": name, "info": info, "cost": cost})


@app.route('/update_spending', methods=['GET', 'POST'])
@login_required
def update_spending():
    if request.method == 'POST':
        about = request.form["about"]
        cost = request.form["cost"]
        date = request.form["date"]
        about_info = request.form["about_info"]
        month = "-".join(date.split("-")[:2])
        user_id = current_user.id
        session = db_session.create_session()
        spending = MySpending(about=about, cost=cost, month=month, user_id=user_id,
                              date=date, info=about_info)
        session.add(spending)
        session.commit()
    return "complete"


@app.route('/remove_spending', methods=['GET', 'POST'])
@login_required
def remove_spending():
    if request.method == 'POST':
        remove_id = request.form["id"].split("_")[0]
        session = db_session.create_session()
        remove = session.query(MySpending).filter_by(id=remove_id).one()
        session.delete(remove)
        session.commit()
    return "complete"


db_session.global_init(db_path)
app.run('localhost', 8080, debug=False)
