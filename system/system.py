from telebot.custom_filters import SimpleCustomFilter
from database import connection

def user_lang(user_id: int):
    conn = connection()
    cur = conn.cursor()
    cur.execute('SELECT lang FROM students WHERE user_id = %s', (user_id,))
    lang = cur.fetchone()
    try:return lang[0]
    except:return 'undifined'

def get_message_channels() -> list:
    import json
    conn = connection()
    cur = conn.cursor()
    cur.execute('SELECT channels FROM bot_setting')
    ujson = json.loads(cur.fetchone()[0])
    avalibale_channels = [key for key, val in ujson.items() if ujson[key]['send_message']]
    return avalibale_channels


def creator_id():
    conn = connection()
    cur = conn.cursor()
    cur.execute('SELECT user_id, status FROM students')
    for i, s in cur.fetchall():
        if s == 'creator':
            return i
            
def get_admins():
    import json
    conn = connection()
    cur = conn.cursor()
    cur.execute("SELECT admins from bot_setting")
    try:
        admins = json.loads(cur.fetchone()[0])
    except:
        admins = {}
    return admins


def get_user_p(user_id):
    conn = connection()
    cur = conn.cursor()
    cur.execute("SELECT name, account_link, gender, status FROM students WHERE user_id = %s", (user_id,))
    name, ac_l, gen, stat = cur.fetchone()
    if not gen:
        gen = ""
    return name, ac_l, gen, stat


class IsDeeplinkFilter(SimpleCustomFilter):
    key = 'is_deeplink'

    def check(self, message):
        from telebot.util import is_command
        return len(message.text.split()) > 1 and is_command(message.text.split()[0])


class FromUserFlter(SimpleCustomFilter):
    key = 'from_user'

    def check(self, msg):
        return msg.forward_from is not None


class IsAdminfilter(SimpleCustomFilter):
    key = 'is_admin_or_creator'

    def check(self, message):
        conn = connection()
        cur = conn.cursor()
        cur.execute('SELECT status FROM students WHERE user_id = %s', (message.chat.id, ))
        admin = cur.fetchone()[0]
        if admin == 'admin' or admin == 'creator':
            return True
        else:
            return False


class IsNumberFilter(SimpleCustomFilter):
    key = 'is_number'

    def check(self, message):
        try:
            eval(message.text)
        except:
            return False
        else:
            return True


class NotBannedFilter(SimpleCustomFilter):
    key = 'not_banned'

    def check(self, message):
        conn = connection()
        cur = conn.cursor()
        cur.execute("SELECT status FROM students WHERE user_id = %s", (message.from_user.id, ))
        user = cur.fetchone()
        if user:
            return user[0] != 'banned'
        else:
            return True


class UserJoinedChannelsFilter(SimpleCustomFilter):
    from telebot import TeleBot
    key = 'joined'

    def __init__(self, bot:TeleBot):
        self.bot = bot

    def check(self, message):
        import json
        joined = True
        conn = connection()
        cur = conn.cursor()
        cur.execute("select channels from bot_setting")
        channels = cur.fetchone()[0]

        for channel, val in channels.items():
            if val.get('force_join'):
                try:
                    user = self.bot.get_chat_member(channel, message.from_user.id)
                    if user.status in ['creator', 'administrator', 'member']:
                        joined = True
                    else:
                        joined = False
                except Exception as e:
                    if 'user not found' in e.args[0]:
                        continue

        if joined:
            return True

        else:
            return False
