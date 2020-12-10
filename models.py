import os
import psycopg2
from peewee import (
    FloatField, ForeignKeyField, IntegerField, Model,
    PostgresqlDatabase, TextField
)

# DATABASE_URL = os.environ['DATABASE_URL']
# conn = psycopg2.connect(DATABASE_URL, sslmode='require')

DATABASE = os.environ.get('DATABASE')
USER = os.environ.get('USER')
PORT = os.environ.get('PORT')
HOST = os.environ.get('HOST')
PASSWORD = os.environ.get('PASSWORD')

print("[DEBUG]: {}:{}".format(HOST,PORT))

database = PostgresqlDatabase(
    DATABASE,
    user=USER,
    password=PASSWORD,
    host=HOST,
    port=PORT,
)

print(database)


class UnknownField(object):
    def __init__(self, *_, **__):
        pass


class BaseModel(Model):
    class Meta:
        database = database


class Categories(BaseModel):
    name = TextField()

    class Meta:
        table_name = 'categories'


class Companies(BaseModel):
    name = TextField()

    class Meta:
        table_name = 'companies'


class Movies(BaseModel):
    budget = IntegerField(null=True)
    homepage = TextField(null=True)
    overview = TextField(null=True)
    popularity = TextField(null=True)
    title = TextField()
    vote_average = FloatField()
    vote_count = IntegerField()

    class Meta:
        table_name = 'movies'


class Users(BaseModel):
    name = TextField()
    username = TextField(unique=True)
    password = TextField()
    email = TextField(unique=True)

    class Meta:
        table_name = 'users'


class MoviesCategory(BaseModel):
    category_id = ForeignKeyField(Categories)
    movie_id = ForeignKeyField(Movies)

    class Meta:
        table_name = 'movies_category'


class MoviesCompany(BaseModel):
    company_id = ForeignKeyField(Companies)
    movie_id = ForeignKeyField(Movies)

    class Meta:
        table_name = 'movies_company'


class Reviews(BaseModel):
    review = TextField()
    score = IntegerField()
    user_id = ForeignKeyField(Users)
    movie_id = ForeignKeyField(Movies)

    class Meta:
        table_name = 'reviews'


TABLES = [
    Categories, Companies, Movies, Users,
    MoviesCategory, Reviews, MoviesCompany
]

with database.connection_context():
    database.create_tables(TABLES, safe=True)
    database.commit()
