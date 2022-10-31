
import psycopg2

't.me/EnglishAntonina_bot'
from config import host, user, password, db_name
password_usr = '1234_test_ogurec_2'
nick_name = 'Ogurec_test_2'
user_name = 'Nickita_test_2'
user_surname = 'Char_test_2'
text = """
Поставьте подходящий предлог.

1. It has been raining … (for/since/until) last Friday.
2. I didn’t see you … (in/at/on) home.
3. Where are you … (from/in/at)? – Russia. 
4. Wait … (of/by/for) me. 
I will come back … (in/over/with) an hour.
5. We often travel … (in/to/at) 
6. Lucy has worked as a waitress … (for/since/during) four years.
7. He couldn’t fall asleep … (since/for/until) 3 in the morning.
8. Was she named … (after/to/by) her grandmother.
9. They are interested … (by/in/with) philosophy.
10. I am not fond … (in/with/of) cats.
11. You should turn left … (at/on/in) the corner.
"""

task_name = 'Поставьте подходящий предлог.'
anwsers = """
0 since 
0 at 
0 from 
0 for 
0 to 
0 for 
0 until 
0 after 
0 in 
0 of 
0 at 
"""
task_from = 'Vocabulary in use'

try:
    # connect to exist database
    connection = psycopg2.connect(
        host=host,
        user=user,
        password=password,
        database=db_name
    )
    connection.autocommit = True

    # the cursor for perfoming database operations
    # cursor = connection.cursor()

    # delete a table
    # with connection.cursor() as cursor:
    #     cursor.execute(
    #         """DROP TABLE users;"""
    #     )

    #     print("[INFO] Table was deleted")

    # create a new table
#     with connection.cursor() as cursor:
#         cursor.execute(
#             """
#                 CREATE TABLE task_times(
#                    id serial PRIMARY KEY,
#                    task_text varchar NOT NULL,
#                    task_name varchar(64),
#                    anwsers varchar NOT NULL,
#                    task_from varchar(256)
# );"""
#         )
#
#         connection.commit()
#         print("[INFO] Table created successfully")
# #
#


    # insert data into a table
    with connection.cursor() as cursor:
        cursor.execute(
            """INSERT INTO task_prepositions (task_text, task_name, anwsers, task_from) VALUES
                (%s, %s, %s, %s );""",
            (text, task_name, anwsers, task_from))
        print("[INFO] Data was succefully inserted")

    # get data from a table
    # with connection.cursor() as cursor:
    #     # cursor.execute(
    #     #     """SELECT password FROM users WHERE password = crypt(%s, password);""",
    #     #     (password_usr,)
    #     # )
    #     cursor.execute(
    #         """SELECT id FROM taskes ;"""
    #
    #     )
    #
    #     print(cursor.fetchall())



    # delete a table
    # with connection.cursor() as cursor:
    #     cursor.execute(
    #         """DROP TABLE time_random_task;"""
    #     )
    #
    #     print("[INFO] Table was deleted")

except Exception as _ex:
    print("[INFO] Error while working with PostgreSQL", _ex)
finally:
    if connection:
        # cursor.close()
        connection.close()
        print("[INFO] PostgreSQL connection closed")







#     создание таблиц
# CREATE TABLE users
# (
#  	id serial PRIMARY KEY,
# 	nick_name varchar(64) NOT NULL UNIQUE,
# 	user_name varchar(64) NOT NULL,
# 	user_surname varchar(64) NOT NULL,
# 	password text NOT NULL
# );
#
# CREATE TABLE user_dictionary
# (
# 	id serial PRIMARY KEY,
# 	word varchar(64) NOT NULL,
# 	word_translate varchar(64) NOT NULL,
# 	fk_user_dictionary_users int REFERENCES users(id)
# );
#
# CREATE TABLE task
# (
# 	id serial PRIMARY KEY,
# 	template_of_task_1	varchar(255) NOT NULL,
# 	fk_task_usres int REFERENCES users(id)
# );


##########################################################
# CREATE TABLE random_task
# (
# 	id serial PRIMARY KEY,
# 	result varchar(30),
# 	task varchar(100) NOT NULL,
# 	errors varchar(255),
# 	date_do_task DATE,
# 	fk_random_task_user int REFERENCES users(id)
# );
#
# CREATE TABLE time_random_task
# (
# 	id serial PRIMARY KEY,
# 	result varchar(30),
# 	task varchar(100) NOT NULL,
# 	errors varchar(255),
# 	date_do_task DATE,
# 	fk_random_task_user int REFERENCES users(id)
# );
#
# CREATE TABLE taskes
# (
# 	task varchar(300),
# 	answer varchar(100),
# 	unit_name varchar(50)
# );
###############################################################
#     with connection.cursor() as cursor:
#         cursor.execute(
#             """
#                 CREATE TABLE task_grammatika (
#                   id serial PRIMARY KEY,
#                   task_text varchar NOT NULL,
#                   task_name varchar(64),
#                   anwsers varchar NOT NULL,
#                   task_from varchar(256)
# );"""
#         )
#
#         connection.commit()
#         print("[INFO] Table created successfully")
#
#
#     with connection.cursor() as cursor:
#         cursor.execute(
#             """
#                 CREATE TABLE task_grammatika_result(
#                   id serial PRIMARY KEY,
#                   task varchar NOT NULL,
#                   errors varchar,
#                   date_do_task date,
#                   fk_random_task_user int REFERENCES users(id),
#                   number_of_tasks integer ,
#                   number_of_right_answer integer
# );"""
#         )
#
#         connection.commit()
#         print("[INFO] Table created successfully")


#     with connection.cursor() as cursor:
#         cursor.execute(
#             """
#                 CREATE TABLE task_prepositions(
#                    id serial PRIMARY KEY,
#                    task_text varchar NOT NULL,
#                    task_name varchar(64),
#                    anwsers varchar NOT NULL,
#                    task_from varchar(256)
# );"""
#         )
#
#         connection.commit()
#         print("[INFO] Table created successfully")