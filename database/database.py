from psycopg2 import connect
import os


def connection():
    conn = connect(host=os.getenv('host'), password=os.getenv('pwd'),
                   database=os.getenv('db'), port=int(os.getenv('port')), user=os.getenv('user'))

    conn.autocommit = True
    return conn


class PrivateDatabase:
    def __init__(self):
        conn = connection()
        cur = conn.cursor()
        cur.execute("select msg_id from books")
        bi = cur.fetchone()
        sub = ['math', 'physics', 'chemistry', 'biology', 'civics', 'geography', 'ict',  'hpe',  'history', 'english', 'amharic']
        if bi is None:
            for grade in range(7, 13):
                for s in sub:
                    for i in ['student', 'teacher', 'reference']:
                        cur.execute('insert into books(grade, type, subject, balance, msg_id) values(%s, %s, %s, %s, %s)', 
                        (grade, i, s, 0, 0))
                        conn.commit()

    @classmethod
    def update_query(cls, query, *args):
        conn = connection()
        cur = conn.cursor()
        if not args:
            cur.execute(query)
        else:
            cur.execute(query, args)
        conn.commit()

    @classmethod
    def select_query(cls, query, *args):
        conn = connection()
        cur = conn.cursor()
        if not args:
            cur.execute(query)
        else:
            cur.execute(query, args)

        return cur

    @classmethod
    def user_is_not_exist(cls, user_id) -> bool:
        conn = connection()
        cur = conn.cursor()
        cur.execute("SELECT user_id FROM students")
        if user_id not in [i for j in cur.fetchall() for i in j]:
            return True
        else:
            return False

    @classmethod
    def save_data(cls, name, user_id, date, acc_lick, status):
        link = f"i{user_id}"
        list = [name, user_id, date, link, acc_lick, status]
        cls.update_query('''    
            INSERT INTO students(
            name, 
            user_id,
            joined_date,
            invitation_link, 
            account_link, 
            status)
            VALUES (%s,%s,%s,%s,%s,%s)
            ''', *list)

    def update_lang(self, lang, user_id):
        self.update_query("""UPDATE students SET lang = %s WHERE user_id = %s""", lang, user_id)

    def update_name(self, user_id, name):
        self.update_query("UPDATE students SET name = %s WHERE user_id = %s", name, user_id)
        
    def update_username(self, user_id, username):
        self.update_query("UPDATE students SET username = %s WHERE user_id = %s", username, user_id)

    def update_gender(self, user_id, gender):
        self.update_query("UPDATE students SET gender = %s  WHERE user_id = %s", gender, user_id)
    
    def update_phone(self, user_id, phone):
        self.update_query("UPDATE students SET phone_number = %s  WHERE user_id = %s", phone,user_id)

    def update_bio(self, user_id, bio):
        self.update_query('UPDATE students SET bio = %s WHERE user_id = %s', bio, user_id)

    def save_question(self, user_id, text, typ, subj,  q_link, b_link, caption=""):
        from time import time
        if caption is None: caption = ''
        self.update_query("""INSERT INTO Questions(asker_id, question, time, type_q, status, subject, question_link, 
        browse_link, browse, caption) VALUES(%s , %s, %s, %s, %s, %s, %s, %s, 0, %s)""",
                     user_id, text, time(), typ, 'preview', subj, q_link, b_link, caption)

    def update_bot_balance(self, balance):
        self.update_query("UPDATE bot_setting SET bbalance = %s", balance)

    def update_balance(self, user_id, balance):
        self.update_query("UPDATE students SET balance = balance + %s WHERE user_id = %s", balance, user_id)
        
    def update_invite(self, inviter_id, invited_id):
        self.update_query("INSERT INTO invites VALUES(%s, %s)", inviter_id, invited_id)
        self.update_query("UPDATE students SET invites = invites + 1 WHERE user_id =  %s", inviter_id)

        cur = self.select_query("SELECT bbalance from bot_setting")
        bl = cur.fetchone()[0]
        self.update_balance(inviter_id, bl)

    def ban_user(self, user_id):
        self.update_query("UPDATE students SET status = 'banned' WHERE user_id = %s", user_id)

    def unban_user(self, user_id):
        self.update_query("UPDATE students SET status = 'member' WHERE user_id = %s", user_id)

    def insert_answer(self, user_id, q_id, ans, typ, a_link, caption, reply_to=0):
        from time import time
        
        self.update_query(
            "INSERT INTO Answers(user_id, question_id, answer, type_ans, time, answer_link, status, caption, reply_to) "
            "VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                user_id, q_id, ans, typ, time(), a_link, 'preview', caption, reply_to
            )

    def withdraw(self, user_id, amount):
        self.update_query('update students set balance = balance - %s where user_id = %s', amount, user_id)
        self.update_query('update students set withdraw = withdraw +  %s where user_id = %s', amount, user_id)
