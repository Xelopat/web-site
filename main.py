import os
import datetime

import matplotlib
import matplotlib.pyplot as plt

from flask import Flask, render_template, request, jsonify
from flask_login import LoginManager, login_required, login_user, current_user, logout_user
from sqlalchemy import create_engine, select, func
from werkzeug.utils import redirect

from data.create_database import User, MySpending
from forms.user import RegisterForm, LoginForm

from data import db_session, translate

db_path = "db/blogs.db"

app = Flask(__name__, template_folder='Templates')
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.init_app(app)
matplotlib.use('Agg')


@login_manager.user_loader
def load_user(user_id):
    # load current user
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@login_manager.user_loader
def get_id(user_id):
    # get id of current user
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


# main window
@app.route('/')
def index():
    if current_user.is_authenticated:
        return render_template('index.html', name=current_user.name)
    else:
        return render_template('index.html', name="")


@app.route('/login/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        # get info from form
        username = form.name.data
        password = form.password.data
        db_sess = db_session.create_session()
        # search user
        user = db_sess.query(User).filter(User.email == username).first()
        # authorise user
        if user:
            is_password = user.check_password(password)
        elif db_sess.query(User).filter(User.name == username).first():
            user = db_sess.query(User).filter(User.name == username).first()
            is_password = user.check_password(password)

        else:
            # no user
            return render_template('login.html', title='????????',
                                   form=form,
                                   message="???????????? ???????????????????????? ???? ????????????????????")
        if is_password:
            login_user(user, remember=form.remember.data)
            return redirect('/')
        else:
            # no password
            return render_template('login.html', title='????????',
                                   form=form,
                                   message="???????????????? ????????????")
    return render_template('login.html', title='????????', form=form)


# logout
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
        # no current passwords
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='??????????????????????',
                                   form=form,
                                   message="???????????? ???? ??????????????????")
        db_sess = db_session.create_session()
        # user already exist
        if db_sess.query(User).filter(User.email == form.email.data).first() or db_sess.query(User).filter(
                User.name == form.name.data).first():
            return render_template('register.html', title='??????????????????????', form=form,
                                   message="?????????? ???????????????????????? ?????? ????????")
        user = User()
        # set information about user
        user.set_name(form.name.data)
        user.set_about(form.about.data)
        user.set_email(form.email.data)
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        login_user(user, remember=True)
        return redirect('/')
    return render_template('register.html', title='??????????????????????', form=form)


# all spending
@app.route('/view_spending', methods=['GET', 'POST'])
@login_required
def view_spending():
    return render_template('spending.html', title='?????? ??????????')


# get picture with information about month
@app.route('/my_spending_month', methods=['GET', 'POST'])
@login_required
def my_spending_month():
    # get info
    date = request.args.to_dict()["date"]
    user_id = str(current_user.id)
    if not os.path.isdir(f"static/user_diagram/{user_id}"):
        os.mkdir(f"static/user_diagram/{user_id}")
    engine = create_engine(f'sqlite:///{db_path}', echo=False)
    conn = engine.connect()
    # get info from db
    t = select([MySpending.about, func.sum(MySpending.cost)]).where(MySpending.user_id == int(user_id),
                                                                    MySpending.month == date).group_by(MySpending.about)
    res = conn.execute(t).fetchall()
    label = []
    cost = []
    # add information
    for row in res:
        label.append(row[0])
        cost.append(row[1])
    # remove zero information
    for i in range(len(cost) - 1, -1, -1):
        if cost[i] == 0 and len(cost) != 0:
            del cost[i]
            del label[i]
    if not cost:
        cost = [1]
        label = [""]
    # create diagram
    plt.close()
    plt.pie(cost, labels=label, autopct='%.0f%%')
    plt.savefig(f'static/user_diagram/{user_id}/{date}.png')
    # get link
    link = f'static/user_diagram/{user_id}/{date}.png'
    return jsonify({"img": link})


# get info about selected day
@app.route('/my_spending_day', methods=['GET', 'POST'])
@login_required
def my_spending_day():
    # get info
    date = request.args.to_dict()["date"]
    user_id = str(current_user.id)
    engine = create_engine(f'sqlite:///{db_path}', echo=False)
    conn = engine.connect()
    # get info from db
    t = select([MySpending.id, MySpending.about, MySpending.info, MySpending.cost]).where(
        MySpending.user_id == int(user_id),
        MySpending.date == date)
    res = conn.execute(t).fetchall()
    spending_id, name, info, cost = [], [], [], []
    # append elements in list
    for i in res:
        spending_id.append(i[0])
        name.append(i[1])
        info.append(i[2])
        cost.append(i[3])
    return jsonify({"id": spending_id, "name": name, "info": info, "cost": cost})


# append info to db
@app.route('/update_spending', methods=['GET', 'POST'])
@login_required
def update_spending():
    if request.method == 'POST':
        # get info
        about = request.form["about"]
        cost = request.form["cost"]
        date = request.form["date"]
        about_info = request.form["about_info"]
        month = "-".join(date.split("-")[:2])
        user_id = current_user.id
        # append spending to db
        session = db_session.create_session()
        spending = MySpending(about=about, cost=cost, month=month, user_id=user_id,
                              date=date, info=about_info)
        session.add(spending)
        session.commit()
    return "complete"


# remove spending from db
@app.route('/remove_spending', methods=['GET', 'POST'])
@login_required
def remove_spending():
    if request.method == 'POST':
        # get id
        remove_id = request.form["id"].split("_")[0]
        # remove info
        session = db_session.create_session()
        remove = session.query(MySpending).filter_by(id=remove_id).one()
        session.delete(remove)
        session.commit()
    return "complete"


# ?????????????? ???? ?????????? ???????????? ?? ????????????
@app.route('/translation', methods=['GET'])
def translation():
    return render_template('translate.html', d=translate.latest())


# ??????????????
@app.route('/save_money', methods=['POST', 'GET'])
def save_money():
    if request.method == 'GET':
        return render_template('save_money.html')
    elif request.method == 'POST':
        # ???????? ????????????
        date_start = request.form['date_start'].split('-')
        date_start = datetime.date(int(date_start[0]), int(date_start[1]), int(date_start[2]))
        # ???????? ??????????????????
        date_finish = request.form['date_finish'].split('-')
        date_finish = datetime.date(int(date_finish[0]), int(date_finish[1]), int(date_finish[2]))
        # ???????????? ?????????? ?????????????????? ?????????? ?? ????????????????
        month_between = int(str(date_finish - date_start).split(',')[0].split()[0]) // 30
        # ???????????????? ???????????????????????? ?????????????????? ????????????
        if month_between < 0:
            return render_template('answer_save_money.html', f='error time')
        elif month_between == 0:
            return render_template('answer_save_money.html', f='error time 1')
        else:
            # ?????????? ?????????????? ???????????????????????? ?????????? ???????????????? ?? ??????????
            try:
                percent_at_month = float(request.form['percent']) / 12
            except Exception:
                return render_template('answer_save_money.html', f='error value')
            # ?????????????? ???????????????????????? ?????????? ???????????????? ?? ??????????
            try:
                c_finish = float(request.form['c_finish'])
            except Exception:
                return render_template('answer_save_money.html', f='error value')
            # ?????? ???????????????????? ????????????????
            try:
                type_s = request.form['type_s']
            except KeyError:
                type_s = '????????????????????????'
            # ?????? ???????????????????? ??????????????????
            if request.form['type_percent'] == '0':
                # ?????????????? ????????????????
                result = c_finish / month_between / (1 + (percent_at_month / 100))
                return render_template('answer_save_money.html', f='its okay 1', result=round(result, 1))
            else:
                # ?? ????????????????????????????
                if type_s == '0':
                    for i in range(month_between):
                        c_finish = c_finish / (1 + (percent_at_month / 100))
                    return render_template('answer_save_money.html', f='its okay 1', result=round(c_finish, 1))
                else:
                    summ = 0
                    for i in range(1, month_between + 1):
                        summ += (1 + (percent_at_month / 100)) ** i
                    return render_template('answer_save_money.html', f='its okay 2', result=round(c_finish / summ, 1))


# ????????????
@app.route('/credit', methods=['POST', 'GET'])
def credit():
    if request.method == 'GET':
        return render_template('credit.html')
    elif request.method == 'POST':
        # ???????? ????????????
        date_start = request.form['date_start'].split('-')
        date_start = datetime.date(int(date_start[0]), int(date_start[1]), int(date_start[2]))
        # ???????? ??????????????????
        date_finish = request.form['date_finish'].split('-')
        date_finish = datetime.date(int(date_finish[0]), int(date_finish[1]), int(date_finish[2]))
        # ???????????? ?????????? ?????????????????? ?????????? ?? ????????????????
        month_between = int(str(date_finish - date_start).split(',')[0].split()[0]) // 30
        # ???????????????? ???????????????????????? ?????????????????? ????????????
        if month_between < 0:
            return render_template('answer_credit.html', f='error 1')
        elif month_between == 0:
            return render_template('answer_credit.html', f='error 2')
        else:
            # ?????????? ?????????????? ???? ?????????? ???????????????? ?? ??????
            try:
                percent_at_month = float(request.form['percent']) / 12
            except Exception:
                return render_template('answer_credit.html', f='error value')
            # ???? ?????????? ?????????? ???? ???????????? ????????????
            try:
                summ = float(request.form['summ'])
            except Exception:
                return render_template('answer_credit.html', f='error value')
            # ?????????? ?????????? ???? ???????????? ???????????????? ?? ?????????? (????????????????)
            try:
                can = float(request.form['can'])
            except Exception:
                return render_template('answer_credit.html', f='error value')
            # ?????? ??????????????
            result = summ
            for i in range(month_between):
                summa = summ / (month_between - i) + (summ * percent_at_month / 100)
                summ -= summ / (month_between - i)
                result += (summ * percent_at_month)
                if summa > can:
                    return render_template('answer_credit.html', f='error')
            return render_template('answer_credit.html', f='ok', res=round(result, 1))


db_session.global_init(db_path)
port = int(os.environ.get("PORT", 5000))
app.run(host='0.0.0.0', port=port)
