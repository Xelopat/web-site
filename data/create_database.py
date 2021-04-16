from datetime import datetime
import sqlalchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from .db_session import SqlAlchemyBase


class User(SqlAlchemyBase, UserMixin):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    about = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    email = sqlalchemy.Column(sqlalchemy.String,
                              index=True, unique=True, nullable=True)
    hashed_password = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    created_date = sqlalchemy.Column(sqlalchemy.DateTime,
                                     default=datetime.now)

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)

    def set_name(self, name):
        self.name = name

    def set_about(self, about):
        self.about = about

    def set_email(self, email):
        self.email = email


class My_spending(SqlAlchemyBase):
    __tablename__ = 'spending'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    id_user = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    eat = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    traveling = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    fun = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    clothes = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    health = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    another = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    month = sqlalchemy.Column(sqlalchemy.String,
                              default="-".join(str(datetime.now().date()).split("-")[:2]))
