import random
import logging
import re
import generator
import pandas as pd
from text import *
from buttons import *
from database import *
import schedule
from time import time
import threading
from flask import Flask, request
from system import *
from time_convertor import time_parse as tp
from telebot.custom_filters import *
from telebot.apihelper import ApiTelegramException
from telebot.handler_backends import StatesGroup
from telebot import (
    TeleBot,
    types,
    util,
    apihelper
    )
import os
import json

apihelper.ENABLE_MIDDLEWARE = True
app = Flask(__name__)
db = PrivateDatabase()

ADMIN_ID = 5213764043
CHANNEL_ID = -1001646258900

TOKEN = os.getenv('TOKEN')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
bot = TeleBot(TOKEN)

DEEPLINK = 'https://telegram.me/'+bot.get_me().username+'?start='
SHARE = ''
markups = {}
MAX_PHOTO_SIZE = 5120
MAX_VOICE_SIZE = 2048
MAX_VIDEO_SIZE = 10240


class AskQuestion(StatesGroup):
    question = 'question'
    subject = 'subject'
    submit = 'submit'
    edit_question = 'edit_question'


class Answer(StatesGroup):
    answer = 'on_answer_reply'


class Feedback(StatesGroup):
    get_comment = 'get_feedback'


class BotSetting(StatesGroup):
    admin = 'admin'
    channel = 'channel'
    balance = 'balance'


class OnMessage(StatesGroup):
    get_msg = 'get_msg'
    add_btn = 'add_btn'
    reply = 'reply'
    to_user = 'to_user'


@bot.channel_post_handler(commands=['id'])
def on_channel(msg):
    print(msg)
    bot.edit_message_text(f"<code>{msg.chat.id}</code>", msg.chat.id, msg.message_id, parse_mode='html')

@bot.middleware_handler(['message'])
def get_update(instance, msg: types.Message):
    state = bot.get_state(msg.chat.id)


@bot.message_handler(commands=['start'], chat_types=['private'], is_deeplink=False, not_banned=True)
def start_message(msg: types.Message):
    state = bot.get_state(msg.chat.id)
    if state != 'no-state':
        bot.delete_state(msg.chat.id)
    """
    A function used to handle `/start` command.
    This function will do three (3) taks:-
        - Check weather user is already sarted the bot (saved in database)
        - Save into database if not user  started the bot previusly.
        - Send message with `KeyboardButton` (options) to user that let user comunicate with bot.
    :param msg:
    :return: Message
    """

    user_id = msg.chat.id
    ui = db.select_query('SELECT admins FROM bot_setting').fetchone()
    if ui:
        kwargs = json.loads(ui[0])
    else:
        kwargs = {}
    if db.user_is_not_exist(user_id):
        if user_id == ADMIN_ID:
            status = 'creator'
        else: status = 'member'

        db.save_data('Student', user_id, time(), generator.account_link(), status)
    lang = user_lang(user_id)
    if lang == 'en':
        bot.send_message(msg.chat.id, "_Select one Option_", reply_markup=main_buttons('en', user_id, **kwargs),
                         parse_mode="Markdown")
    elif lang == 'am':
        bot.send_message(msg.chat.id, "_አንዱን ምርጫ ይምረጡ_", reply_markup=main_buttons('am', user_id, **kwargs),
                         parse_mode="Markdown")
    else:
        bot.send_message(msg.chat.id, "_Select Language / ቋንቋ ይምረጡ_", reply_markup=language_btn(),
                         parse_mode="Markdown")


@bot.message_handler(commands=['start'], is_deeplink=True, chat_types=["private"], not_banned=True)
def start_(msg: types.Message):
    """
    Function used to handle useful `deepliks`.
    - Deeplink` is a message like "/start hello" or
    "https://t.me/bot_username?start=hello"
    :param msg:
    :return:
    """
    text = msg.text.split()[1]
    al = db.select_query("SELECT account_link FROM students").fetchall()
    account_link = [link for links in al for link in links]
    bl = db.select_query("SELECT browse_link FROM Questions").fetchall()
    browse_link = [ui for ux in bl for ui in ux]
    il = db.select_query("SELECT invitation_link FROM students").fetchall()
    invitation_link = [link for links in il for link in links]
    que = db.select_query("SELECT question_link FROM Questions").fetchall()
    questions = [q for qu in que for q in qu]
    clink = db.select_query("SELECT link from admin_post").fetchall()
    comment_link = [ln for link in clink for ln in link]
    if text == 'start':
        start_message(msg)

    elif text in account_link:
        if user_lang(msg.chat.id) == 'undifined':
            start_message(msg)

        else:
            show_account_info(msg, text)

    elif text in browse_link:
        if user_lang(msg.chat.id) == 'undifined':
            start_message(msg)
        else:
            cur = db.select_query("SELECT question_id FROM Questions WHERE browse_link = %s", text)
            ids = cur.fetchone()[0]
            target = threading.Thread(target=browse, args=(msg, ids))
            target.start()

    elif text in invitation_link:
        cur = db.select_query("SELECT user_id FROM students WHERE invitation_link = %s", text)
        user_via_link(msg, cur.fetchone()[0])

    elif text in questions:
        if user_lang(msg.chat.id) == 'undifined':
            start_message(msg)

        else:
            cur = db.select_query("SELECT question_id  FROM Questions WHERE question_link = %s", text)
            q_id = cur.fetchone()[0]
            lang = user_lang(msg.from_user.id)
            bot.send_message(msg.from_user.id, "<code>Send your answer through text,voice or media(photo,video)</code>",
                             reply_markup=cancel(lang), parse_mode="html")
            bot.set_state(msg.from_user.id, Answer.answer)
            json_format = {
                'question_id': q_id,
                'answer_id': None,
                'is_reply': None,
                'user_msg_id': None
            }
            with bot.retrieve_data(msg.chat.id) as data:
                data['json'] = json_format

    elif text in comment_link:
        if user_lang(msg.chat.id) == 'undifined':
            start_message(msg)
        else:
            send_comment_browse(msg, text)
    else:
        start_message(msg)


@bot.message_handler(commands=['user'], chat_types=['private'], chat_id=[creator_id()])
def free_user(msg: types.Message):
    """
    #Branch of backed
    #This method is useful to manage users' status;
    #For example if they banned to make unbanned

    """
    text = msg.text.split()
    if len(text) == 2:
        try:
            user_id = bot.get_chat(text[1]).id
            query = '''SELECT name, joined_date, gender, username, bio, status FROM students 
                WHERE user_id  = %s'''
            user = db.select_query(query, user_id).fetchone()
            name, jd, gend, us, bio, stat = user
            if stat == 'banned':
                banned = True
            else:
                banned = False
            if not gend:
                gend = ""
            get = bot.get_chat(user_id)
            bot.send_message(msg.chat.id, f"👤 <b>Name:</b> {name} {gend}\n" 
                                          f"🧧 <b>Username:</b> {us}\n"
                                          f"💬 <b>Bio:</b> {bio}\n" 
                                          f"❇ <b>status:</b> {stat}\n" 
                                          f"🆔 <a href='tg://user?id={get.id}'>{get.id}</a>",
                             parse_mode="HTML", reply_markup=on_user_(user_id, banned, admin_id=creator_id()))

        except ApiTelegramException as e:
            bot.send_message(msg.chat.id, f"User not found...\n\n{e}")


@bot.message_handler(commands=['ban'], is_deeplink=True, chat_types=['private'], is_admin_or_creator=True)
def ban_user_cmd(msg: types.Message):
    user_id = msg.text.split()[1]
    ustatus = db.select_query('select status from students where user_id = %s', user_id).fetchone()
    status = db.select_query('select status from students where user_id = %s', msg.chat.id).fetchone()[0]
    admins = get_admins()

    if ustatus is not None:
        if (admins.get(user_id, {}).get('ban_user')) or (status == 'creator' and ustatus[0] != 'creator') \
                and ustatus[0] != 'banned':
            db.update_query("update students set status = 'banned' where user_id = %s", user_id)
            user = bot.get_chat(int(user_id))
            try:
                del admins[user_id]
            except: pass
            text = f'''<b>✅ User <a href='tg://user?id={user.id}'>{user.id}</a> has been banned.</b>"
            '''
            bot.send_message(msg.chat.id, text, parse_mode='html')
        elif ustatus[0] == 'banned':
            user = bot.get_chat(int(user_id))
            text = f'''<b>✅ User <a href='tg://user?id={user.id}'>{user.id}</a> has already banned.</b>
                    '''
            bot.send_message(msg.chat.id, text, parse_mode='html')

    else:
        try:
            user = bot.get_chat(int(user_id))
            text = f'''<b>❌ Sorry user <a href='tg://user?id={user.id}'>{user.id}</a> is not a member of this bot.</b>"
                        '''
            bot.send_message(msg.chat.id, text, parse_mode='html')
        except:
            bot.send_message(msg.chat.id, "Invalid User id")


@bot.message_handler(commands=['unban'], is_deeplink=True, chat_types=['private'], is_admin_or_creator=True)
def unban_user(msg: types.Message):
    user_id = msg.text.split()[1]
    ustatus = db.select_query('select status from students where user_id = %s', user_id).fetchone()
    status = db.select_query('select status from students where user_id = %s', msg.chat.id).fetchone()[0]
    admins = get_admins()

    if ustatus is not None:
        if (admins.get(user_id, {}).get('ban_user') and ustatus[0] == 'banned') or \
                (status == 'creator' and ustatus[0] == 'banned'):
            db.update_query("update students set status = 'member' where user_id = %s", user_id)
            user = bot.get_chat(int(user_id))
            text = f'''<b>✅ User <a href='tg://user?id={user.id}'>{user.id}</a> has been unbanned.</b>"
            '''
            bot.send_message(msg.chat.id, text, parse_mode='html')
    else:
        try:
            user = bot.get_chat(int(user_id))
            text = f'''<b>❌ User <a href='tg://user?id={user.id}'>{user.id}</a> is not banned.</b>"
                    '''
            bot.send_message(msg.chat.id, text, parse_mode='html')
        except:
            pass


@bot.callback_query_handler(func=lambda call: call.data in ['am', 'en'], not_banned=True)
def update_user_language(call: types.CallbackQuery):
    user_id = call.message.chat.id
    if call.data == 'am':
        db.update_lang(call.data, user_id)
        bot.answer_callback_query(call.id, "ቋንቋዎ ወደ አማርኛ ተቀይሯል ።")
        bot.delete_message(user_id, call.message.id)
        bot.send_message(user_id, "_አንዱን ምርጫ ይምረጡ_", reply_markup=main_buttons('am', user_id), parse_mode="Markdown")
    else:
        db.update_lang(call.data, user_id)
        bot.answer_callback_query(call.id, "Language updated to english.")
        bot.delete_message(user_id, call.message.id)
        bot.send_message(user_id, "_Select one option_", reply_markup=main_buttons('en', user_id),
                         parse_mode="Markdown")


@bot.message_handler(state="*", text=["❌ ሰርዝ", "❌ Cancel"], joined=True, not_banned=True)
def cancel_feedback(msg):
    user_id = msg.chat.id
    if bot.get_state(user_id):
        start_message(msg)
        bot.delete_state(user_id)


@bot.message_handler(commands=['lang'], chat_types=['private'], joined=True, not_banned=True)
def lang_command(msg):
    bot.send_message(msg.chat.id, "_Select Language / ቋንቋ ይምረጡ_", reply_markup=language_btn(), parse_mode="Markdown")


@bot.message_handler(func=lambda msg: msg.text in en_btns, chat_types=['private'], joined=True, not_banned=True)
def english_button(msg):
    conn = connection()
    cur = conn.cursor()
    """
    A function used to handle all english `KeyboardButton` that the bot sent to the user previusly.
    :param msg:
    :return:
    """
    user_id = msg.chat.id
    lang = user_lang(user_id)
    if not lang == 'en':
        return
    query = "SELECT name, joined_date, gender,username,bio,lang FROM students WHERE user_id = %s"
    cur.execute(query, (user_id,))
    name, joined_date, gender, username, bio, lang = cur.fetchone()
    if not gender:
        gender = ''

    if msg.text == "📚 Books":
        bot.send_message(user_id, "<i>Select book type</i>", parse_mode='HTMl', reply_markup=types_book_am())

    elif msg.text == "👨‍👩‍👦‍👦 Invite":
        query = """
    SELECT invitation_link, invites, balance, withdraw, bbalance FROM students,  bot_setting WHERE user_id = %s"""
        link, invites, balance, withdr, bbl = db.select_query(query, user_id).fetchone()
        bot.send_message(user_id, BalanceText['en'].format(balance, withdr, invites, bbl, DEEPLINK + link),
                         parse_mode="HTML", reply_markup=withdraw('en', DEEPLINK + link))

    elif msg.text == "⚙️ Settings":
        question = db.select_query("SELECT count(asker_id) FROM questions WHERE asker_id = %s", user_id).fetchone()[0]
        bot.send_message(user_id, SettingText.format(name, gender, username, bio, question, tp(time(), joined_date)),
                         parse_mode="HTML", reply_markup=user_setting(lang))

    elif msg.text == "🙋‍♂ My Questions":
        target = threading.Thread(target=show_questions, args=(user_id, 'en'))
        target.start()
        target.join()

    elif msg.text == "🗣 Ask Question":
        bot.send_message(user_id, "<code>Send your question through text or media(vedio,voice,photo)</code>",
                         parse_mode="HTML", reply_markup=cancel(lang))
        bot.set_state(user_id, AskQuestion.question)

    elif msg.text == "💬 Feedback":
        bot.send_message(user_id, "Send us your feedback", reply_markup=cancel('en'))
        bot.set_state(user_id, Feedback.get_comment)
        Feedback.on_state = True


@bot.message_handler(func=lambda msg: msg.text in am_btns, chat_types=['private'], joined=True, not_banned=True)
def amharic_button(msg: types.Message):
    conn = connection()
    cur = conn.cursor()
    user_id = msg.chat.id
    lang = user_lang(user_id)
    if not lang == 'am':
        return
    query = "SELECT name,joined_date, gender, username, bio FROM students  WHERE user_id=%s"
    cur.execute(query, (user_id,))
    name, joined_date, gender, username, bio = cur.fetchone()

    if not gender:
        gender = ""

    if msg.text == "📚መጽሐፍት":
        bot.send_message(msg.chat.id, "_የመጽሃፍ አይነት ይምረጡ_", parse_mode="Markdown", reply_markup=types_book_am())

    elif msg.text == "👨‍👩‍👦‍👦 ጋብዝ":
        query = """
              SELECT invitation_link, invites, balance, bbalance, withdraw FROM students, bot_setting WHERE user_id = %s
        """

        link, invites, balance, bbl, withdr = db.select_query(query, user_id).fetchone()
        bot.send_message(user_id, BalanceText['am'].format(balance, withdr, invites, bbl, DEEPLINK+link),
                         parse_mode="HTML", reply_markup=withdraw('am', DEEPLINK+link))

    elif msg.text == "🙋‍♂ የኔ ጥያቄዎች":
        target = threading.Thread(target=show_questions, args=(user_id, 'am'))
        target.start()
        target.join()

    elif msg.text == "⚙️ ቅንብሮች":
        question = db.select_query("SELECT count(asker_id) FROM questions WHERE asker_id = %s", user_id).fetchone()[0]
        bot.send_message(user_id, SettingText.format(name, gender, username, bio, question, tp(time(), joined_date)),
                         parse_mode="HTML", reply_markup=user_setting(lang))

    elif msg.text == "🗣 ጥያቄ ጠይቅ":
        bot.send_message(user_id, "<code>ጥያቄዎትን በጽሁፍ ፣ በድምጽ ወይም በምስል (video, photo) ይላኩ።</code>",
                         reply_markup=cancel(lang), parse_mode="html")
        bot.set_state(user_id, AskQuestion.question)

    elif msg.text == "💬 አስታየት":
        bot.send_message(user_id, "<code>ያሎትን ሃሳብ ወይም አስታየት ይላኩ።</code>",
                         reply_markup=cancel(lang), parse_mode="html")
        bot.set_state(user_id, Feedback.get_comment)



@bot.message_handler(state=AskQuestion.question, content_types=util.content_type_media,
                     joined=True, not_banned=True)
def ask_question(msg):
    user_id = msg.chat.id
    lang = user_lang(user_id)
    with bot.retrieve_data(user_id) as Question:
        if not msg.text:
            if msg.content_type not in  ['sticker', 'animation']:
                file_id = getattr(msg, msg.content_type).file_id if not msg.photo else msg.photo[-1].file_id

            else:
                bot.send_message(user_id,
                                 "<code>Allowed content is text, voice, photo, audio please use only this to ask"
                                 " questions! </code>", parse_mode='html')
                return

        else:
            file_id = None

        '''
        if not msg.text and not msg.caption:
            bot.send_message(user_id, f"Sorry the {msg.content_type} has not a caption. please send with a caption!")
            bot.set_state(user_id, AskQuestion.question)
            return
        '''

        Question['message'] = {'type': msg.content_type, 'data': msg.text or file_id, 'caption': msg.caption or ''}

    if lang == 'en':
        text = "select subject of your question"
    else:
        text = "የጥያቄዎን የትምህርት አይነት ይምርጡ"
    bot.send_message(user_id, text, reply_markup=subject_btn(lang))
    bot.set_state(user_id, AskQuestion.subject)


@bot.message_handler(state=AskQuestion.subject, joined=True, not_banned=True)
def response_question(msg):
    conn = connection()
    user_id = msg.from_user.id
    subject = msg.text
    lang = user_lang(user_id)
    cur = conn.cursor()
    if subject == "🇬🇧 English":
        subje = '#English'

    elif subject == "🇪🇹 አማርኛ":
        subje = "#Amharic"

    elif subject == "⚽️ HPE":
        subje = "#HPE"
    else:
        subject = msg.text[1:].strip()
        subje = "#" + subject
    with bot.retrieve_data(user_id) as Question:
        Question['subject'] = subje
    cur.execute('select name,account_link,gender from students where user_id = %s', (user_id,))
    name, acc, gend = cur.fetchone()

    if not gend:
        gend = ''

    if msg.text in subj:
        with bot.retrieve_data(user_id) as Data:
            Data = Data['message']
            data = Data['data']
            typ = Data['type']
            caption = Data['caption']
            if caption is None: caption = ''
            db.save_question(user_id, data, typ, subje, generator.question_link(), generator.browse_link(), caption)

            cur.execute("SELECT MAX(question_id) FROM Questions")
            q_id = cur.fetchone()[0]
            if typ == 'text':
                bot.send_message(user_id,
                                 f"{subje}\n\n<b>{data}</b>\n\nBy: <a href='{DEEPLINK + acc}'>{name}</a> {gend}",
                                 reply_markup=Panel(q_id), parse_mode="html")

                start_message(msg)
                bot.delete_state(msg.chat.id)
                return
            system = getattr(bot, f'send_{typ}')

            system(user_id, data,
                   caption=f"{subje}\n\n<b>{caption}</b>\n\nBy: <a href='{DEEPLINK + acc}'>{name}</a>"
                           f" {gend}",
                   parse_mode="html", reply_markup=Panel(q_id))

        start_message(msg)
        bot.delete_state(msg.chat.id)
    else:
        bot.send_message(msg.chat.id, "Please use only bellow button!", reply_markup=subject_btn(lang))


@bot.callback_query_handler(func=lambda call: call.data == 'ask_question', joined=True, not_banned=True)
def askquestion(call):
    user_id = call.from_user.id
    bot.delete_message(user_id, call.message.id)
    lang = user_lang(user_id)
    if lang == 'am':
        bot.send_message(user_id, "<code>ጥያቄዎትን በጽሁፍ ፣ በድምጽ ወይም በምስል (Video,Photo) ይላኩ።</code>",
                         reply_markup=cancel(lang), parse_mode="html")
        bot.set_state(user_id, AskQuestion.question)
    elif lang == 'en':
        bot.send_message(user_id, "<code>Send your question through text or media(vedio,voice,photo)</code>",
                         parse_mode="HTML", reply_markup=cancel(lang))
        bot.set_state(user_id, AskQuestion.question)


@bot.callback_query_handler(func=lambda call: call.data.startswith('report'))
def report_answer(call: types.CallbackQuery):
    bot.answer_callback_query(call.id, "report sent!")
    user_id = int(call.data.split(":")[1])
    if user_id == creator_id():
        return
    name, acc, gen, stat = get_user_p(user_id)
    if stat == 'banned':
        banned = True
    else:
        banned = False
    bot.send_message(creator_id(), "#report_answer")
    bot.copy_message(creator_id(), call.message.chat.id, call.message.message_id,
                     reply_markup=on_user_(user_id, banned, creator_id()))


@bot.message_handler(state=Feedback.get_comment, content_types=util.content_type_media, joined=True, not_banned=True)
def user_feedback(msg):
    connec = connection()
    user_id = msg.chat.id
    cur = connec.cursor()
    lang = user_lang(user_id)
    if msg.text:
        cur.execute("select name, account_link, gender from students where user_id = %s", (user_id,))
        name, link, gend = cur.fetchone()
        if not gend:
            gend = ''
        bot.send_message(user_id, "Thank you for your comment!" if lang == 'en' else "ስለ አስታየቶ ከልብ እናመሰግናለን ።")
        start_message(msg)
        md = "markdown"
        bot.send_message(creator_id(), f"""#Feedback !\n\n*{msg.text}*\n\nfrom: [{name}]({DEEPLINK + link}) {gend}
""", reply_markup=on_user_(user_id, banned=False, admin_id=creator_id()), parse_mode=md, disable_notification=False)

        admin: dict = json.loads(db.select_query("SELECT admins FROM bot_setting").fetchone()[0])
        for key, val in admin.items():
            if val.get('feedback'):
                try:
                    bot.send_message(int(key), f"""#Feedback !\n\n*{msg.text}*\nFrom: [{name}]({DEEPLINK + link}) {gend}
                    """, reply_markup=on_user_(user_id, banned=False, admin_id=int(key),
                                               msg_id=msg.message_id, **admin),
                                     parse_mode="Markdown", disable_notification=False)
                except ApiTelegramException:
                    continue
        Feedback.on_state = False
    else:
        bot.send_message(user_id, "Text is required!")


@bot.callback_query_handler(func=lambda call: re.search('^(send_|edit_|del_)', call.data), joined=True, not_banned=True)
def submit_question(call: types.CallbackQuery):
    conn = connection()
    user_id = call.from_user.id
    cur = conn.cursor()
    lang = user_lang(user_id)
    text = call.data.split("_")[0]
    q_id = call.data.split("_")[1]
    if text == 'send':
        bot.answer_callback_query(call.id, "Your question will be approved by admin!", show_alert=True)
        cur.execute("UPDATE Questions SET status = 'pending' WHERE question_id = %s", (q_id,))
        conn.commit()
        msg = call.message
        bot.edit_message_reply_markup(call.from_user.id, msg.message_id, reply_markup=on_user_question('pending', q_id))
        bot.delete_state(call.from_user.id)

    elif text == 'edit':
        cur.execute("DELETE FROM Questions WHERE question_id = %s", (q_id,))
        conn.commit()
        bot.edit_message_reply_markup(call.from_user.id, call.message.message_id, reply_markup=None)
        bot.send_message(user_id, "Send new your question.", reply_markup=cancel(lang))
        bot.set_state(user_id, AskQuestion.question)

    else:
        bot.answer_callback_query(call.id, "Question has been deleted!")
        cur.execute("DELETE FROM Questions WHERE question_id = %s", (q_id,))
        conn.commit()
        bot.delete_message(user_id, call.message.id)
        bot.delete_state(user_id)


@bot.callback_query_handler(func=lambda call: call.data.startswith("q:"))
def on_questions_status(call: types.CallbackQuery):
    q_id = call.data.split(":")[2]
    text = call.data.split(":")[1]
    conn = connection()
    cur = conn.cursor()
    user_id = call.from_user.id
    cur.execute("SELECT status, asker_id FROM Questions WHERE question_id = %s", (q_id,))
    status, q_u_id = cur.fetchone()

    if user_id != q_u_id:
        bot.answer_callback_query(call.id, "Error")
        bot.delete_message(user_id, call.message.message_id)
        return

    if text == 'cancel':
        if status == 'pending':
            bot.answer_callback_query(call.id, "question was canceld!")
            cur.execute("UPDATE Questions SET status = 'canceld' WHERE question_id = %s", (q_id,))
            conn.commit()
            bot.edit_message_reply_markup(call.from_user.id, call.message.message_id,
                                          reply_markup=on_user_question('canceld', q_id))

        elif status == 'canceld':
            bot.answer_callback_query(call.id, "This questions is already canceld!", show_alert=True)
            bot.edit_message_reply_markup(call.from_user.id, call.message.message_id,
                                          reply_markup=on_user_question('canceld', q_id))

        elif status == 'approved':
            bot.answer_callback_query(call.id, "This question is already approved!", show_alert=True)
            bot.delete_message(call.from_user.id, call.message.message_id)

        else:
            bot.answer_callback_query(call.id, "something went wrong :(")

    else:

        if status == 'canceld':
            bot.answer_callback_query(call.id, "question submited!")
            cur.execute("UPDATE Questions SET status = 'pending' WHERE question_id = %s", (q_id,))
            conn.commit()
            bot.edit_message_reply_markup(call.from_user.id, call.message.message_id,
                                          reply_markup=on_user_question('pending', q_id))

        elif status == 'pending':
            bot.answer_callback_query(call.id, "This questions is already submited!", show_alert=True)
            bot.edit_message_reply_markup(call.from_user.id, call.message.message_id,
                                          reply_markup=on_user_question('pending', q_id))

        elif status == 'approved':
            bot.answer_callback_query(call.id, "This question is already approved!", show_alert=True)
            bot.delete_message(call.from_user.id, call.message.message_id)

        else:
            bot.answer_callback_query(call.id, "something went wrong :(")


@bot.callback_query_handler(func=lambda call: re.search('^answer', call.data), joined=True, not_banned=True)
def answer_questions(call: types.CallbackQuery):
    bot.answer_callback_query(call.id)
    msg = call.message
    q_id = int(call.data.split('_')[1])
    lang = user_lang(msg.chat.id)
    bot.send_message(msg.chat.id, "<code>Send your answer through text,voice or media(photo, video)</code>",
                     reply_markup=cancel(lang), parse_mode="html")
    bot.set_state(msg.chat.id, Answer.answer)
    json_format = {
        'question_id': q_id,
        'answer_id': None,
        'is_reply': None,
        'user_msg_id': None
    }
    with bot.retrieve_data(msg.chat.id) as data:
        data['json'] = json_format


@bot.message_handler(state=Answer.answer, content_types=util.content_type_media,
                     joined=True, not_banned=True, chat_types=['private'])
def on_preview_answer(msg: types.Message):
    user_id = msg.from_user.id
    connec = connection()
    cur = connec.cursor()
    with bot.retrieve_data(user_id) as data:
        json_format = data['json']

    text = msg.text
    photo = msg.photo
    caption = msg.caption or ''
    typ = msg.content_type
    q_id = json_format['question_id']
    asker_id = db.select_query("SELECT asker_id FROM questions WHERE question_id = %s", q_id).fetchone()[0]

    if json_format['is_reply']:
        reply_to = json_format['is_reply']['to_id']
    else:
        reply_to = 0

    if text:
        file = msg.text
        if asker_id == user_id:
           file = text = "#asker\n\n" + text

    else:
        file = getattr(msg, msg.content_type).file_id if photo else msg.photo[-1].file_id
        if asker_id == user_id:
            file = caption = "#asker\n\n" + caption
    db.insert_answer(user_id, q_id, file, typ, generator.question_link(), caption, reply_to)
    cur.execute("SELECT MAX(answer_id) FROM Answers")
    a_ = cur.fetchone()[0]
    cur.execute("SELECT name, gender, account_link, Answers.time FROM students, Answers WHERE students.user_id = "
                " Answers.user_id AND students.user_id = %s AND Answers.answer_id = %s", (user_id, a_))
    name, gender, link, time_ = cur.fetchone()
    _time = tp(time(), time_)
    if not gender:
        gender = ""
    parse_time = f"<i>{_time} ago</i>" if _time != "Just now" else "<i>Just now</i>"

    if text:

        bot.send_message(user_id, f"<b>{text}</b>\n\nBy: <a href='{DEEPLINK + link}'>{name}</a> {gender}\n{parse_time}",
                         parse_mode="html", reply_markup=answer_btn(q_id, a_))
        file = text

    else:
        if not msg.content_type == 'sticker':
            if asker_id == user_id:
                caption = "#asker\n\n" + caption

            send_document = getattr(bot, f'send_{msg.content_type}')
            file = getattr(msg, msg.content_type).file_id if photo else msg.photo[-1].file_id
            send_document(user_id, file, caption=f"<b>{caption}</b>\nBy: <a href='{DEEPLINK + link}'>{name}</a> {gender}"
                                                 f"\n{parse_time}".strip(),
                           parse_mode="html", reply_markup=answer_btn(q_id, a_))
        else:
            bot.send_message(user_id, "Allowed content is text, voice, photo, audio, gif please use only this to answer"
                                      " questions! ")
            return

    bot.set_state(user_id, 'no-state')
    with bot.retrieve_data(user_id) as data:
        data['no_state'] = msg.message_id + 1
    start_message(msg)


@bot.callback_query_handler(func=lambda call: re.search("^(Send|Edit|Del)Answer", call.data),
                            joined=True, not_banned=True)
def send_answer(call: types.CallbackQuery):
    user_id = call.message.chat.id
    conn = connection()
    cur = conn.cursor()
    umsg_id = call.message.message_id
    q_id = int(call.data.split("_")[1])
    ans_id = int(call.data.split("_")[2])
    with bot.retrieve_data(user_id) as data:
        json_format = data['json']
    if not json_format.get('is_reply'):
        cur.execute("SELECT asker_id FROM Questions WHERE question_id = %s", (q_id,))
        user = cur.fetchone()[0]
        msg_idx = None
        reply_msg_id = None

    else:
        user = int(json_format['is_reply']['to_reply'])
        reply_msg_id = int(json_format['is_reply']['reply_msg_id'])
        msg_idx = int(json_format['is_reply']['msg_id'])

    if call.data == f"SendAnswer_{q_id}_{ans_id}":
        db.update_query('update Answers set time = %s where answer_id = %s', time(), ans_id)
        db.update_query("update Answers set status = 'posted' where answer_id = %s", ans_id)

        try:

            channels = json.loads(db.select_query("select channels from bot_setting").fetchone()[0])

            for key, val in channels.items():
                if val.get('approve'):
                    ch_u = bot.get_chat(key).username
                    break
            else:
                bot.send_message(user_id, "You can not answer this question!")
                return

            umsg = bot.copy_message(user_id, user_id, umsg_id, parse_mode='html',
                                    reply_markup=on_answer(user_id, q_id, ans_id, umsg_id),
                                    reply_to_message_id=reply_msg_id)

            bot.edit_message_reply_markup(user_id, umsg.message_id,
                                          reply_markup=on_answer(user_id, q_id, ans_id, umsg.message_id))
            bot.delete_message(user_id, umsg_id)
            db.update_query('UPDATE Answers set msg_id = %s WHERE answer_id = %s ', umsg.message_id, ans_id)
            db.update_query('update Questions set browse = browse + 1 where question_id = %s', q_id)
            msg_id, br = db.select_query('select message_id, browse from Questions where question_id = %s',
                                         q_id).fetchone()
            btn = types.InlineKeyboardMarkup()
            ql, bl = db.select_query('select question_link, browse_link from Questions where question_id = %s',
                                     q_id).fetchone()
            btn.add(
                types.InlineKeyboardButton("Answer", url=DEEPLINK + ql),
                types.InlineKeyboardButton(f"Browse ({br})", url=DEEPLINK + bl)
            )
            try:
                bot.edit_message_reply_markup(f"@{ch_u}", int(msg_id), reply_markup=btn)
            except ApiTelegramException:
                pass

            username = 'https://t.me/{0}/{1}'.format(ch_u, msg_id)
            if not json_format['is_reply']:
                if not user == user_id:
                    bot.send_message(user, f"🔂 You have one new answer for [your question]({username})",
                                     parse_mode='markdown', disable_web_page_preview=True)
                    bot.copy_message(user, user_id, umsg.message_id, parse_mode='html',
                                     reply_markup=on_answer(user_id, q_id, ans_id, umsg.message_id))
            else:
                if user != user_id:
                    bot.copy_message(user, user_id, umsg.message_id, parse_mode='html',
                                     reply_markup=on_answer(user_id, q_id, ans_id, umsg.message_id),
                                     reply_to_message_id=msg_idx)
        except ApiTelegramException:
            pass
        finally:
            bot.delete_state(user_id)
    elif call.data == f"EditAnswer_{q_id}_{ans_id}":
        cur.execute("DELETE FROM Answers WHERE answer_id = %s", (ans_id,))
        conn.commit()
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)
        bot.send_message(call.from_user.id, "Send new your answer", reply_markup=cancel(user_lang(call.message.chat.id))
                         )
        bot.set_state(call.from_user.id, Answer.answer)
        return

    else:
        bot.delete_message(call.message.chat.id, call.message.message_id)
        db.update_query("DELETE FROM Answers WHERE answer_id = %s", ans_id)
        bot.delete_state(call.from_user.id)


@bot.callback_query_handler(func=lambda call: re.match(r'^reply', call.data))
def reply_to_answer(call: types.CallbackQuery):
    bot.answer_callback_query(call.id)
    ui, q_id, a_id, msg_id = call.data.split(':')[1:]
    on_json = {'to_reply': ui, 'reply_msg_id': call.message.message_id, 'to_id': a_id, 'msg_id': msg_id}

    json_format = {'question_id': q_id,
                   "answer_id": a_id,
                   'is_reply': on_json,
                   }
    bot.send_message(call.message.chat.id, "<code>Send your reply through text, voice or Media (Photo, Video)</code>",
                     parse_mode='html', reply_markup=cancel(user_lang(call.message.chat.id)))
    bot.set_state(call.message.chat.id, Answer.answer)
    with bot.retrieve_data(call.message.chat.id) as data:
        data['json'] = json_format


@bot.message_handler(not_banned=False, chat_types=['private'])
def for_banned_user(msg: Union[types.Message, types.CallbackQuery]):
    remove = types.ReplyKeyboardRemove()
    bot.send_message(msg.chat.id, "💢 You are currently banned from using the bot.\nContact @natiprado for more.",
                     reply_markup=remove)


@bot.message_handler(joined=False, chat_types=['private'])
def join_channel_message(msg: Union[types.Message, types.CallbackQuery]):
    """
    This function will raise if user not joined channel.
    :param msg:
    :return:
    """
    user_id = msg.from_user.id
    channels = json.loads(db.select_query('select channels from bot_setting').fetchone()[0])
    username, usernames = '', ''
    for channel, value in channels.items():
        if value['force_join']:
            try:
                if not bot.get_chat_member(channel, user_id).is_member:
                    username += "@" + bot.get_chat(channel).username + "\n"
                    usernames += "▫️ @" + bot.get_chat(channel).username + "\n"
            except Exception as e:
                if 'user not found' in e.args[0]:
                    continue
    channel_list = {bot.get_chat(chat_id).title: chat_id for chat_id in username.split('\n') if chat_id != ''}
    lists = [types.InlineKeyboardButton(name, url=f't.me/{url}') for name, url in channel_list.items()]
    btn = types.InlineKeyboardMarkup(row_width=2)
    btn.add(*lists)
    bot.send_message(user_id, f"✳ Dear user first you need to join our channel(s)!\n\n{usernames}",
                     reply_markup=btn)


@bot.callback_query_handler(func=lambda call: True, not_banned=False)
def call_banned(call: types.CallbackQuery):
    bot.answer_callback_query(call.id)
    bot.delete_message(call.from_user.id)
    if call.message.chat.type == 'private':
        for_banned_user(call.message)


@bot.callback_query_handler(func=lambda call: True, joined=False)
def call_not_joined(call: types.CallbackQuery):
    bot.answer_callback_query(call.id)
    bot.delete_message(call.from_user.id)
    if call.message.chat.type == 'private':
        join_channel_message(call.message)


@bot.callback_query_handler(func=lambda call: re.match(r"^user", call.data))
def get_user(call: types.CallbackQuery):
    bot.answer_callback_query(call.id)
    admin_id = call.message.chat.id
    text = call.data.split(":")[1]
    user_id = int(call.data.split(':')[2])
    try:
        admins = json.loads(db.select_query("SELECT admins FROM bot_setting").fetchone()[0])
    except (TypeError, AttributeError):
        admins = {}
    kwargs = admins
    if text == 'ban':
        if int(user_id) == creator_id():
            return
        bot.answer_callback_query(call.id, "Banned!")
        db.ban_user(user_id)
        channels = json.loads(db.select_query("SELECT channels FROM bot_setting").fetchone()[0])
        for channel in channels:
            bot.ban_chat_member(channel, user_id)
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id,
                                      reply_markup=on_user_(user_id, True, call.message.chat.id, **kwargs))

    elif text == 'show':
        bot.answer_callback_query(call.id)
        query = "SELECT name, joined_date, gender, username, bio, status FROM students WHERE user_id  = %s"
        name, jd, gend, us, bio, stat = db.select_query(query, user_id).fetchone()
        if not gend:
            gend = ""
        get = bot.get_chat(user_id)
        bot.send_message(call.message.chat.id, f"<b>Name:</b> {name} {gend}\n"
                                               f"<b>Username:</b> {us}\n<b>Bio:</b> {bio}\n"
                                               f"<b>status:</b> {stat}\n"
                                               f"mention: <a href='tg://user?id={user_id}'>{name}</a>\n"
                                               f"real <a href='tg://user?id={get.id}'>{get.id}</a>",
                                               parse_mode="HTML")
    elif text == 'unban':
        if int(user_id) == creator_id():
            return
        bot.answer_callback_query(call.id, "Unbanned!")
        db.unban_user(user_id)
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id,
                                      reply_markup=on_user_(user_id, False, call.message.chat.id, **kwargs))
        channels = json.loads(db.select_query("SELECT channels FROM bot_setting").fetchone()[0])
        for channel in channels:
            bot.unban_chat_member(channel, user_id)
    elif text == "reply":
        admin_id = call.message.chat.id
        bot.send_message(call.message.chat.id, "Hy admin send any message you want to reply",
                         reply_markup=cancel(user_lang(admin_id)))
        bot.set_state(admin_id, OnMessage.reply)
        with bot.retrieve_data(call.message.chat.id) as data:
            data['to'] = user_id

    elif text == 'chat':
        bot.send_message(call.message.chat.id, "Send your message", reply_markup=cancel(user_lang(admin_id)))
        bot.set_state(call.message.chat.id, OnMessage.to_user)
        with bot.retrieve_data(call.message.chat.id) as data:
            data['to_message'] = user_id


@bot.callback_query_handler(func=lambda call: re.match(r'^usend', call.data))
def send_message(call: types.CallbackQuery):
    user_id = int(call.data.split(":")[1])
    bot.answer_callback_query(call.id, "Sent")
    name, acc, gen, stat = get_user_p(user_id)
    if stat == 'banned':
        banned = True
    else:
        banned = False
    try:
        kwargs = get_admins()
        bot.copy_message(user_id, call.message.chat.id, call.message.message_id, 
                         reply_markup=user_profile_info(call.message.chat.id, banned, user_id, **kwargs))
    except ApiTelegramException:
        logging.exception("msg cannot be sent")
    finally:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)


def bot_stng_msg(user_id):
    bot.send_message(user_id, f"<b>🤖 Bot Setting</b>\n\nFrom this menu you can manage your bot setting.",
                     reply_markup=bot_setting_btn(), parse_mode='html')


@bot.message_handler(text=["📝 Send Message", "🤖 Bot Setting", "📊 Statics", "🧩 Questions"],
                     is_admin_or_creator=True, chat_types=['private'])
def admins_button(msg: types.Message):
    try:
        permision = json.loads(db.select_query("SELECT admins FROM bot_setting").fetchone()[0])
    except (TypeError, AttributeError):
        permision = {}
    admins: dict = permision
    text = msg.text
    user_id = msg.from_user.id

    if text == "📝 Send Message":
        if user_id == creator_id() or admins[str(user_id)].get('send_message'):
            bot.send_message(user_id, """✳️Enter New Message.\n
You can also «Forward» text from another chat or channel.
            """, reply_markup=cancel('en'))
            bot.set_state(user_id, OnMessage.get_msg)

    elif text == "🤖 Bot Setting":
        if user_id == creator_id() or admins[str(user_id)].get('manage_setting'):
            bot_stng_msg(user_id)

    elif text == "🧩 Questions":
        if user_id == creator_id() or admins[str(user_id)].get('approve_questions'):
            sent = False
            query = """SELECT students.name, students.gender, students.account_link, 
                        Questions.question, Questions.caption,
                        Questions.subject, Questions.type_q, Questions.question_id FROM students 
                        JOIN Questions ON students.user_id = Questions.asker_id
                        WHERE Questions.status = 'pending' LIMIT 25"""

            for user in db.select_query(query).fetchall():
                name, gender, link, question, caption, subject, type_qustion, question_id = user
                if not gender:
                    gender = ''
                if type_qustion == "text":
                    bot.send_message(user_id, f"{subject}\n\n<b>{question}</b>\n\n"
                                              f"By: <a href='{DEEPLINK+link}'>{name}</a>{gender}",
                                              reply_markup=question_btn(question_id), parse_mode="html")

                else:
                    send_document = getattr(bot, f"send_{type_qustion}")
                    send_document(user_id, question, caption=f"{subject}\n\n<b>{caption}</b>\n\n"
                                                             f"By: <a href='{DEEPLINK + link}'>{name}</a>{gender}",
                                                             reply_markup=question_btn(question_id), parse_mode="html")
                sent = True

            if not sent:
                bot.send_message(user_id, "There is no question")

    else:
        if user_id == creator_id() or admins[str(user_id)].get('can_see'):
            count = db.select_query("SELECT count(user_id) FROM students").fetchone()[0]
            users = db.select_query("""SELECT name, account_link, gender FROM students 
                                       ORDER BY joined_date DESC LIMIT 10""").fetchall()
            ls = []
            for n, a, g in users:
                if not g:
                    g = ''
                ls.append(f"<a href='{DEEPLINK+a}'>{n}</a> {g}")
            data_ = pd.Series(ls, index=[i for i in range(1, count+1)])
            txt = [f"<i>#{i+1}.</i> {names}" for i, names in enumerate(data_)]
            data = '\n'.join(txt)
            bot.send_message(user_id, f'{data}\n\nShowed {len(ls)} out of {count}', parse_mode='html',
                             reply_markup=members_button(count, 1))


@bot.callback_query_handler(lambda call: re.search(r'members', call.data))
def on_members(call: types.CallbackQuery):
    bot.answer_callback_query(call.id)
    user_id, msg_id = call.message.chat.id, call.message.message_id
    pos = int(call.data.split('_')[1])
    try:
        count = db.select_query("SELECT count(user_id) FROM students").fetchone()[0]
        users = db.select_query("""SELECT name, account_link, gender FROM students WHERE id BETWEEN
        %s AND %s""", pos*10-9, pos*10).fetchall()
        ls = []
        left = count % 10
        if not left:
            total = pos * 10
        elif left:
            total = ((pos * 10) - count) + pos*10 if pos * 10 > 10 else ((count-(pos*10)))+pos*10
        else:
            total = count
        for n, a, g in users:
            if not g:
                g = ''
            ls.append(f"<a href='{DEEPLINK+a}'>{n}</a> {g}")
        data_ = pd.Series(ls, index=[i for i in range(pos*10-9, pos*10)])
        txt = [f"<i>#{i + (pos*10-9)}.</i> {names}" for i, names in enumerate(data_)]
        data = '\n'.join(txt)
        bot.edit_message_text(f"{data}\n\nShowed {total}: Total {count}", user_id, msg_id,
                              reply_markup=members_button(count, pos))
    except ApiTelegramException:
        bot.answer_callback_query(call.id, "Please press another button!")


@bot.message_handler(state='no-state')
def no_state(message: types.Message):
    with bot.retrieve_data(message.chat.id) as data:
        msg_id = data['no_state']
        bot.send_message(message.chat.id, '<code>First finish your proccess here</code>', 'html',
                         reply_to_message_id=msg_id)


@bot.message_handler(state=OnMessage.get_msg, content_types=util.content_type_media)
def on_get_message(msg: types.Message):
    btn = types.InlineKeyboardMarkup()
    btn.add(
        types.InlineKeyboardButton("👥 Users", callback_data='to_users'),
        types.InlineKeyboardButton("📣 Channel", callback_data='to_channel')
    )
    bot.copy_message(msg.chat.id, msg.chat.id, msg.message_id, parse_mode='HTML', reply_markup=btn)
    start_message(msg)
    bot.delete_state(msg.chat.id)

class Comment(StatesGroup):
    get_comment = 'get_comment'


@bot.callback_query_handler(lambda call: call.data.startswith('comment'))
def comment_on_post(call: types.CallbackQuery):
    bot.answer_callback_query(call.id)
    post_id = int(call.data.split("_")[1])
    bot.send_message(call.message.chat.id, "<code>Send your comment through text</code>", parse_mode='html',
                     reply_markup=cancel(user_lang(call.message.chat.id)))
    bot.set_state(call.message.chat.id, Comment.get_comment)
    with bot.retrieve_data(call.message.chat.id) as data:
        data['post_id'] = post_id


@bot.message_handler(state=Comment.get_comment, content_types=util.content_type_media)
def on_get_comment_post(msg: types.Message):
    with bot.retrieve_data(msg.chat.id) as data:
        post_id = data['post_id']
        reply_to = data.get('reply_to_comment')

    if reply_to is None:
        reply_to = 0

    if not msg.content_type == 'text':
        bot.send_message(msg.chat.id, "Text is required!", reply_markup=cancel(user_lang(msg.chat.id)))

    else:
        admin_id = db.select_query("SELECT from_admin FROM admin_post").fetchone()[0]
        if msg.chat.id == admin_id or msg.chat.id == creator_id():
            txt = f"#admin\n\n{msg.text}"
        else:
            txt = msg.text

        db.update_query("INSERT INTO comments(to_post, user_id, reply_to, comment, link, status, time) "
                        "VALUES(%s, %s, %s, %s, %s, 'pending', %s)",
                        post_id, msg.chat.id, reply_to, txt, generator.comment_hash_link(), time())
        comment_id = db.select_query("SELECT max(id) FROM comments").fetchone()[0]

        name, acc, gender = db.select_query("SELECT name, account_link, gender FROM students WHERE user_id"
                                            " = %s", msg.chat.id).fetchone()
        if not gender:
            gender = ""
        bot.send_message(msg.chat.id, f"<b>{txt}</b>\n\nBy: <a href='{DEEPLINK+acc}'>{name}</a> {gender}",
                         reply_markup=on_comment(post_id, comment_id), parse_mode='html')

        bot.set_state(msg.chat.id, 'no-state')
        with bot.retrieve_data(msg.chat.id) as data:
            data['no_state'] = msg.message_id + 1
        start_message(msg)


@bot.callback_query_handler(lambda call: call.data.startswith('ucomments'))
def send_user_comment(call: types.CallbackQuery):
    post_id = int(call.data.split('_')[1])
    user_id = call.message.chat.id
    comment_id = int(call.data.split('_')[2])
    _msg_id = call.message.message_id
    with bot.retrieve_data(user_id) as data:
        reply_to = data.get('reply_to_comment')
        msg_id = data.get('comment_msg_id')
        user_msg_id = data.get('user_msg_id')

    msg = bot.copy_message(user_id, user_id, call.message.message_id, parse_mode='html',
                           reply_markup=oncomment(user_id, post_id, comment_id, _msg_id + 1),
                           reply_to_message_id=msg_id
                           )
    bot.edit_message_reply_markup(user_id, msg.message_id,
                                  reply_markup=oncomment(user_id, post_id, comment_id, msg.message_id))
    if reply_to is not None:
        to_reply_id = db.select_query("SELECT user_id FROM comments WHERE id = %s", reply_to).fetchone()[0]
        if not to_reply_id == user_id:
            try:
                bot.copy_message(to_reply_id, user_id, call.message.message_id, reply_to_message_id=user_msg_id,
                                 parse_mode='html',
                                 reply_markup=oncomment(user_id, post_id, comment_id, msg.message_id))
            except ApiTelegramException:
                pass
    else:
        admin_id = db.select_query("SELECT from_admin FROM admin_post WHERE id = %s", post_id).fetchone()[0]
        if not admin_id == user_id:
            bot.send_message(admin_id, "1 comment")
            bot.copy_message(admin_id, user_id, call.message.message_id, parse_mode='html',
                             reply_markup=oncomment(user_id, post_id, comment_id, msg.message_id))

    db.update_query("UPDATE comments SET status = 'posted' WHERE id = %s", comment_id)
    db.update_query("UPDATE comments SET msg_id = %s WHERE id = %s", msg.message_id, comment_id)
    db.update_query("UPDATE admin_post SET browse = browse + 1 WHERE id = %s", post_id)
    channel = db.select_query("SELECT to_channel FROM admin_post WHERE id = %s", post_id).fetchone()[0]
    post_msg_id = db.select_query('SELECT msg_id FROM admin_post WHERE id = %s', post_id).fetchone()[0]
    browse_ = db.select_query("SELECT browse FROM admin_post WHERE id = %s", post_id).fetchone()[0]
    link = db.select_query("SELECT link FROM admin_post WHERE id = %s", post_id).fetchone()[0]
    btn = types.InlineKeyboardMarkup()
    btn.add(*[types.InlineKeyboardButton(f"🗯 Comment ({browse_})", url=f'{DEEPLINK+link}')])
    bot.delete_message(user_id, call.message.message_id)

    try:
        bot.edit_message_reply_markup(channel, post_msg_id, reply_markup=btn)
    except Exception as e:
        logging.exception(e)
    bot.delete_state(user_id)


@bot.callback_query_handler(lambda call: call.data.startswith('ucommente'))
def edit_user_comment(call: types.CallbackQuery):
    comment_id = int(call.data.split("_")[2])
    db.update_query("DELETE FROM comments WHERE id = %s", comment_id)
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)
    bot.send_message(call.message.chat.id, "Send new your comment", reply_markup=cancel(call.message.chat.id))
    bot.set_state(call.message.chat.id, Comment.get_comment)


@bot.callback_query_handler(lambda call: call.data.startswith('creply'))
def on_comment_reply(call: types.CallbackQuery):
    bot.answer_callback_query(call.id)
    comment_id = int(call.data.split(":")[3])
    post_id = int(call.data.split(":")[2])
    msg_id = int(call.data.split(':')[4])
    bot.send_message(call.message.chat.id, "<code>Send your reply through text</code>", parse_mode='html',
                     reply_markup=cancel(user_lang(call.message.chat.id)))
    bot.set_state(call.message.chat.id, Comment.get_comment)
    with bot.retrieve_data(call.message.chat.id) as data:
        data['post_id'] = post_id
        data['reply_to_comment'] = comment_id
        data['comment_msg_id'] = call.message.message_id
        data['user_msg_id'] = msg_id


@bot.callback_query_handler(lambda call: call.data.startswith('ucommentd'))
def delete_user_comment(call: types.CallbackQuery):
    bot.answer_callback_query(call.id, 'Your comment has been deleted!')
    comment_id = int(call.data.split("_")[2])
    db.update_query("DELETE FROM comments WHERE id = %s", comment_id)
    bot.delete_state(call.from_user.id)
    bot.delete_message(call.from_user.id, call.message.message_id)


@bot.callback_query_handler(lambda call: call.data.startswith('creply'))
def reply_to_comment(call: types.CallbackQuery):
    post_id = call.data.split(":")[2]
    comment_id = call.data.split(":")[3]
    msg_id = call.data.split(":")[3]

    bot.send_message(call.message.chat.id, "<code>Send your reply through text</code>", parse_mode='html',
                     reply_markup=cancel(user_lang(call.message.chat.id)))
    bot.set_state(call.message.chat.id, Comment.get_comment)
    with bot.retrieve_data(call.message.chat.id) as data:
        data['reply_to_comment'] = int(comment_id)
        data['comment_msg_id'] = int(call.message.message_id)
        data['user_msg_id'] = int(msg_id)
        data['post_id'] = int(post_id)


@bot.callback_query_handler(lambda call: call.data.startswith('creport'))
def report_comment(call: types.CallbackQuery):
    bot.answer_callback_query(call.id, "report sent!")
    user_id = int(call.data.split(":")[1])
    if user_id == creator_id():
        return
    name, gend, acc, status = get_user_p(user_id)
    bot.send_message(creator_id(), "#report_comment")
    if status == 'banned':
        banned = True
    else:
        banned = False
    bot.copy_message(creator_id(), call.message.chat.id, call.message.message_id,
                     parse_mode='html', reply_markup=on_user_(user_id, banned, creator_id()))


@bot.callback_query_handler(lambda call: call.data in ['to_users', 'to_channel'])
def chose(call: types.CallbackQuery):
    pos = 'users' if call.data == 'to_users' else 'channel'
    btn = types.InlineKeyboardMarkup()
    if pos != 'users':
        btn.row_width = 1
    btn.add(
        types.InlineKeyboardButton("➕ Add", callback_data=f'sm:add:{pos}:no') if pos == 'users' else
        types.InlineKeyboardButton("❌ Attach Comment", callback_data=f'sm:com:{pos}:no'),
        types.InlineKeyboardButton("☑ Done", callback_data=f'sm:done:{pos}:no')
    )

    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=btn)


@bot.callback_query_handler(func=lambda call: re.match('^sm', call.data))
def on_got_message(call: types.CallbackQuery):
    bot.answer_callback_query(call.id)
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)
    data = call.data.split(':')[1]

    to = call.data.split(":")[2] if data == "done" else None
    with_ = call.data.split(":")[3]
    if data == 'add':
        bot.send_message(call.message.chat.id, "Send your button link this:\ntext -> www.text.com")
        bot.set_state(call.message.chat.id, OnMessage.add_btn)
        with bot.retrieve_data(call.message.chat.id) as data:
            data['msg_id'] = call.message.message_id
    
    elif data == 'done':
        if to == 'users':
            send_to_users(call)
        else:
            channels_id = json.loads(db.select_query('SELECT channels FROM bot_setting').fetchone()[0])
            allowed_channels = [key for key, val in channels_id.items() if channels_id[key].get('send_message')]
            if with_ == 'yes':
                btn = types.InlineKeyboardMarkup(row_width=2)
                channels = [types.InlineKeyboardButton(f"{bot.get_chat(chat_id).title}",
                                                       callback_data=f'post_on:{chat_id}')
                            for chat_id in allowed_channels]
                btn.add(*channels)
                bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=btn)
            else:
                send_to_channel(call, False, allowed_channels)
        bot.delete_state(call.message.chat.id)
    elif data == 'com':
        if with_ == 'no':
            pos = 'yes'
        else:
            pos = 'no'
        btn = types.InlineKeyboardMarkup(row_width=1)
        btn.add(
            types.InlineKeyboardButton("❌ Attach Comment" if pos == 'no' else "✅ Attach Comment",
                                       callback_data=f'sm:com:channel:{pos}'),
            types.InlineKeyboardButton("☑ Done", callback_data=f'sm:done:channel:{pos}')
        )
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=btn)


@bot.message_handler(state=OnMessage.add_btn)
def on_send_btn(msg: types.Message):
    text = msg.text
    match = re.findall(r".+\s*->\s*[a-zA-Z.@]+", text)
    if match:
        btns = {k.split('->')[0]: k.split('->')[1] for k in match}
        for k, v in btns.items():
            markups[k] = {'url': v.lstrip()}
        try:
            del markups["➕ Add"], markups["☑ Done"]
        except (IndexError, KeyError):
            pass
        markups["➕ Add"] = {'callback_data': f'sm:add:users:no'}
        markups["☑ Done"] = {'callback_data': f'sm:done:users:no'}
        try:
            with bot.retrieve_data(msg.chat.id) as data:
                msg_id = data['msg_id']
            bot.copy_message(msg.chat.id, msg.chat.id, msg_id, parse_mode='html',
                             reply_markup=util.quick_markup(markups))
        except Exception as e:
            bot.reply_to(msg, e.args[0])
            bot.reply_to(msg, "Invalid Url link ...")
    else:
        bot.reply_to(msg, "Error typing...")
    bot.delete_state(msg.chat.id)


@bot.callback_query_handler(lambda call: call.data.startswith('post_on'))
def post_one_channel(call: types.CallbackQuery):
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)
    bot.answer_callback_query(call.id, "Posted!")
    channel_id = int(call.data.split(':')[1])
    send_to_channel(call, True, channel_id)


@bot.message_handler(state=OnMessage.reply, content_types=util.content_type_media)
def reply_to_user_message(msg: types.Message):
    with bot.retrieve_data(msg.chat.id) as data:
        user_id = data['to']
    bot.send_message(msg.chat.id, "sent!")
    bot.copy_message(user_id, msg.chat.id, msg.message_id, parse_mode='html')
    start_message(msg)
    bot.delete_state(msg.chat.id)


@bot.message_handler(state=OnMessage.to_user)
def send_message_to_users(msg: types.Message):
    with bot.retrieve_data(msg.chat.id) as data:
        user_id = data['to_message']
    name, acc, gen, stat = get_user_p(msg.chat.id)
    btn = types.InlineKeyboardMarkup()
    btn.add(types.InlineKeyboardButton("✅ Send", callback_data=f'usend:{user_id}'))
    bot.send_message(msg.chat.id, f"<b>{msg.text}</b>\n\n<a href='{DEEPLINK+name}'>{name}</a>", parse_mode="html",
                     reply_markup=btn)
    start_message(msg)


@bot.callback_query_handler(func=lambda call: re.match(r"^uq", call.data))
def approve_or_decline(call: types.CallbackQuery):
    conn = connection()
    text = call.data.split("_")[1]
    q_id = call.data.split("_")[2]
    cur = conn.cursor()
    try:
        channel = json.loads(db.select_query("SELECT channels FROM bot_setting").fetchone()[0])
    except (TypeError, AttributeError):
        channel = {}
    ch: dict = channel
    ch_u, ch_i = None, None
    cur.execute("SELECT asker_id FROM Questions  WHERE question_id = %s", (q_id,))
    user_id = cur.fetchone()[0]
    for key, val in ch.items():
        if val.get('approve'):
            ch_u = bot.get_chat(key).username
            ch_i = key
            break
    if not ch_u:
        bot.answer_callback_query(call.id, "No channel is satted for approve question!", show_alert=True)
        return
    cur.execute('SELECT status FROM Questions WHERE question_id = %s', (q_id,))
    status = cur.fetchone()[0]
    if text == "approve":
        if (status == 'approved') or (status == "declined"):
            if status == 'approved':
                cur.execute('SELECT message_id FROM Questions WHERE question_id = %s', (q_id,))
                msg_id = cur.fetchone()[0]
                show = types.InlineKeyboardMarkup()
                show.add(types.InlineKeyboardButton("👀 Show me", url=f"t.me/{ch_u}" + '/' + str(msg_id)))
                bot.answer_callback_query(call.id, "This question is already approved!")
                bot.edit_message_reply_markup(call.from_user.id, call.message.message_id, reply_markup=show)
            else:
                bot.answer_callback_query(call.id, "This question is already declined!")
                bot.edit_message_reply_markup(call.from_user.id, call.message.message_id, reply_markup=None)
            return

        cur.execute("SELECT question_link, browse_link, browse FROM Questions WHERE question_id = %s", (q_id,))
        ql, bl, b = cur.fetchone()
        btn = types.InlineKeyboardMarkup()
        btn.add(
            types.InlineKeyboardButton("Answer", url=DEEPLINK+ql),
            types.InlineKeyboardButton(f"Browse ({b})", url=DEEPLINK+bl)
        )
        msg = bot.copy_message(ch_i, call.message.chat.id, call.message.message_id, parse_mode='markdown',
                               reply_markup=btn)
        
        cur.execute("UPDATE Questions SET status = 'approved', message_id = %s"
                    " WHERE question_id = %s", (msg.message_id, q_id))
        conn.commit()
        ch_u = 'https://t.me/'+ch_u
        show = types.InlineKeyboardMarkup()
        show.add(types.InlineKeyboardButton("👀 Show me", url=ch_u+'/'+str(msg.message_id)))
        d = types.InlineKeyboardMarkup()
        d.add(types.InlineKeyboardButton('🗑 Delete', callback_data=f'uq_delete_{q_id}'))
        bot.answer_callback_query(call.id, "Approved!")
        bot.send_message(user_id, "Your question is approved!", reply_markup=show)
        bot.edit_message_reply_markup(call.from_user.id, call.message.message_id, reply_markup=d)
        bot.answer_callback_query(call.id, "Question is approved")

    elif text == 'decline':
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)
        msg = bot.send_message(call.message.chat.id, "Send the reason")
        bot.register_next_step_handler(msg, get_reason, q_id, user_id)

    elif text == 'delete':
        cur.execute("SELECT message_id FROM Questions WHERE question_id = %s", (q_id,))
        msg_id = cur.fetchone()[0]
        try:
            bot.answer_callback_query(call.id, "Deleted")
            bot.delete_message(ch_i, msg_id)
        except Exception as e:
            bot.send_message(user_id, e.args[0])
        finally:
            bot.delete_message(user_id, call.message.message_id)


def get_reason(msg, q_id, user_id):
    reason = msg.text
    db.update_query("UPDATE Questions SET status = 'declined' WHERE question_id = %s", q_id)
    bot.send_message(user_id, reason)
    bot.send_message(msg.chat.id, "reason sent")
    bot.clear_step_handler_by_chat_id(msg.chat.id)
    msg.text = "🧩 Questions"
    admins_button(msg)


@bot.callback_query_handler(func=lambda call: call.data in ['edus', 'edut', 'edutref'], joined=True, not_banned=True)
def answer_books(call):
    bot.answer_callback_query(call.id)
    lang = user_lang(call.from_user.id)

    if call.data == call.data:
        if lang == 'am':
            text = "የክፍል ደረጃዎን ይምረጡ"
        else:
            text = "Select Your Grade"
        bot.edit_message_text(text, call.from_user.id, call.message.id, reply_markup=grade(lang, call.data))


@bot.callback_query_handler(func=lambda call: call.data == 'backgrade', joined=True, not_banned=True)
def back_grade(call):
    bot.answer_callback_query(call.id)
    user_id = call.from_user.id
    lang = user_lang(user_id)
    if lang == 'en':
        back = "<i>Select book type</i>"
    else:
        back = "<i>የመጽሃፍ አይነት ይምረጡ</i>"
    bot.edit_message_text(back, call.from_user.id, call.message.message_id,
                          parse_mode='HTMl', reply_markup=types_book_am())


@bot.callback_query_handler(func=lambda call: re.match(r"^grade", call.data))
def get_books(call: types.CallbackQuery):
    bot.answer_callback_query(call.id)
    gr = call.data.split("_")[1]
    typ = call.data.split("_")[2]
    if typ == "edus":
        typ = "student"
    elif typ == "edut":
        typ = "teacher"
    else:
        typ = 'reference'
    text, btn = info_book(call, gr, typ)
    bot.edit_message_text(text, call.from_user.id, call.message.message_id, reply_markup=btn, parse_mode='html')


def info_book(call, gr, typ):
    connex = connection()
    cur = connex.cursor()
    cur.execute("SELECT subject, balance, msg_id FROM books WHERE grade = %s AND type = %s", (gr, typ))
    catch = cur.fetchall()
    if catch is not None:
        result = ""
        for i, v, m in catch:
            i = i.title()
            if m != 0:
                if v == 0:
                    result += i+"<i>: Free ✅</i>\n"
                elif v >= 1:
                    result += f"<i>{i}: {v} Birr</i>\n"
            else:
                result += f'<i>{i}: Not found</i>\n'
    else:
        result = """All book Coomingsoon !!"""
    lang = user_lang(call.from_user.id)
    if call.data == call.data:
        if lang == "am":
            text = '<b>🧾 መጽሃፍ ይምረጡ</b>'
        else:
            text = "<b>🧾 Chose book</b>"
        text += '\n\n'+result
        lang = user_lang(call.message.chat.id)
        return text, books_btn(lang, typ, gr)


@bot.callback_query_handler(func=lambda call: re.match(r"book", call.data))
def on_get_books(call: types.CallbackQuery):
    subject = call.data.split(":")[1]
    conn = connection()
    cur = conn.cursor()
    lang = user_lang(call.message.chat.id)
    if subject not in ['back', 'main']:
        bot.answer_callback_query(call.id)
        bk = call.data.split(":")[2]
        gr = call.data.split(":")[3]
        cur.execute("SELECT msg_id, balance, subject FROM books WHERE grade = %s AND type = %s AND subject = %s",
                    (gr, bk, subject))
        u = cur.fetchone()
        exist = None if u in [None, (None,)] else u
        
        if call.message.chat.id == creator_id():
            msg_id, bl, sub = exist
            cur.execute('select id from books where type = %s AND subject = %s AND grade = %s', (bk, subject, gr))
            bi = cur.fetchone()[0]
            if bi is None:
                return
            btn = on_book_click(bi, msg_id)
            if msg_id:
                text = f"""
                Subject: {sub}\nBalance: {bl}
                """
            else:
                text = f"Subject : {sub}"
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=btn,
                                  parse_mode='html')
        
        msg_id, bl, sub = exist
        if msg_id:
            try:
                cur = db.select_query("SELECT balance FROM students WHERE user_id = %s", call.from_user.id)
                ub = cur.fetchone()[0]
                if not call.message.chat.id == creator_id():
                    if not bl:
                        bot.answer_callback_query(call.id)
                        bot.copy_message(call.message.chat.id, CHANNEL_ID, msg_id)
                    
                    elif ub >= bl:
                        bot.answer_callback_query(call.id)
                        db.update_query("update students set balance  = balance - %s where user_id = %s", bl,)
                        bot.copy_message(call.message.chat.id, CHANNEL_ID, msg_id)
                        
                    else:
                        bot.answer_callback_query(call.id, "Your balance is insuficient", show_alert=True)

                else:
                    bot.answer_callback_query(call.id)
                    bot.copy_message(call.message.chat.id, CHANNEL_ID, msg_id)
            except Exception as e:
                bot.answer_callback_query(call.id, e.args[0], show_alert=True)
        else:
            bot.answer_callback_query(call.id, "This book is not available", show_alert=True)

    elif subject == 'back':
        bk = call.data.split(":")[2]
        if call.data == call.data:
            if lang == 'am':
                text = "የክፍል ደረጃዎን ይምረጡ"
            else:
                text = "Select Your Grade"
            bot.edit_message_text(text, call.from_user.id, call.message.id, reply_markup=grade(lang, bk))
    else:
        if lang == 'am':
            text = "_የመጽሃፍ አይነት ይምረጡ_"
        else:
            text = "_Select book type_"
        bot.edit_message_text(text, call.from_user.id, call.message.message_id,
                              parse_mode="Markdown", reply_markup=types_book_am())


class OnBook(StatesGroup):
    bal = 'book_balace'
    add = 'add_book'


@bot.callback_query_handler(func=lambda call: re.match(r"ubook", call.data))
def on_book_setting(call: types.CallbackQuery):
    conn = connection()
    cur = conn.cursor()
    bot.answer_callback_query(call.id)
    bk, cmd, bi = call.data.split(":")
    cur.execute('select grade from books where id = %s ', (bi,))
    gr = cur.fetchone()[0]
    cur.execute('select subject, type from books where id = %s', (bi,))
    sub, ty = cur.fetchone()
    if cmd == 'dl':
        cur.execute("update books set msg_id = '0' where id = %s", (bi,))
        conn.commit()
        text, btn = info_book(call, gr, ty)
        bot.edit_message_text(text, call.from_user.id, call.message.message_id, reply_markup=btn)        
    
    elif cmd == 'back':
        text, btn = info_book(call, gr, ty)
        bot.edit_message_text(text, call.from_user.id, call.message.message_id, reply_markup=btn, parse_mode='html')
    
    elif cmd == 'add':
        bot.edit_message_reply_markup(call.from_user.id, call.message.message_id)
        bot.send_message(call.message.chat.id, "Forward the book")
        bot.set_state(call.message.chat.id, OnBook.add)
        with bot.retrieve_data(call.message.chat.id) as data:
            data['book_id'] = bi
    
    elif cmd == 'bl':
        bot.edit_message_reply_markup(call.from_user.id, call.message.message_id)
        bot.send_message(call.message.chat.id, "Enter Balance")
        bot.set_state(call.message.chat.id, OnBook.bal)
        with bot.retrieve_data(call.message.chat.id) as data:
            data['book_id'] = bi


@bot.message_handler(state=OnBook.add, content_types=['document'], is_forwarded=True)
def add_book(msg: types.Message):
    conn = connection()
    cur = conn.cursor()
    msg_id = msg.forward_from_message_id
    with bot.retrieve_data(msg.chat.id) as data:
        kw = data['book_id']
    cur.execute("UPDATE books set msg_id = %s WHERE id = %s", (msg_id, kw))
    conn.commit()
    bot.send_message(msg.chat.id, "Book Added ")
    cur.execute('select type, subject, grade, balance from books where id = %s', (kw,))
    ty, sub, gr, bl = cur.fetchone()
    btn = on_book_click(kw, msg_id)
    text = f"""
        Subject: {sub}\nBalance: {bl}
        """
    bot.send_message(msg.chat.id, text, reply_markup=btn)
    bot.delete_state(msg.chat.id)


@bot.message_handler(state=OnBook.bal, is_digit=True)
def set_book_balance(msg: types.Message):
    balance = msg.text
    conn = connection()
    cur = conn.cursor()
    with bot.retrieve_data(msg.chat.id) as data:
        kw = data['book_id']
    cur.execute("UPDATE books set balance = %s WHERE id = %s", (balance, kw))
    conn.commit()
    bot.send_message(msg.chat.id, "Book Added ")
    cur.execute('select type, subject, grade, balance from books where id = %s', (kw,))
    ty, sub, gr, bl = cur.fetchone()
    btn = on_book_click(kw, True)
    text = f"""
        Subject: {sub}\nBalance: {bl}
        """
    bot.send_message(msg.chat.id, text, reply_markup=btn)
    bot.delete_state(msg.chat.id)


@bot.callback_query_handler(func=lambda call: call.data == 'withdr', joined=True, not_banned=True)
def withdraw_money(call):
    bot.answer_callback_query(call.id)
    user_id = call.from_user.id
    lang = user_lang(user_id)
    if lang == 'am':
        text = "ምን ያህል ብር ማዉጣት ይፈልጋሉ ?"
    else:
        text = "How many Birr do you want to withdraw?"
    bot.edit_message_text(text, user_id, call.message.message_id, reply_markup=amounts(lang))
 

@bot.message_handler(content_types=['contact'], joined=True, not_banned=True)
def register_phone(msg):
    phone_number = msg.contact.phone_number
    user_id = msg.chat.id
    phone = db.select_query("SELECT phone_number FROM students WHERE user_id = %s", user_id).fetchone()[0]

    if phone is not None:
        return
    db.update_phone(user_id, phone_number)
    lang = user_lang(user_id)
    if lang == 'am':
        text = "ምን ያህል ብር ማዉጣት ይፈልጋሉ ?"
    else:
        text = "How many Birr do you want to withdraw?"
    bot.send_message(user_id, text, reply_markup=amounts(lang))


@bot.callback_query_handler(func=lambda call: re.search('birr$|^backwithdr$', call.data), joined=True, not_banned=True)
def cashout_or_ignore(call):
    connex = connection()
    user_id = call.from_user.id
    cur = connex.cursor()
    cur.execute('select balance,lang,withdraw, phone_number from students where user_id = %s', (user_id,))
    balance, lang, withdr, phone = cur.fetchone()
    money = call.data.split('-')[0]
    money = ''.join(money)
    if call.data.endswith('birr'):
        
        if balance >= int(money):
            if phone is None:
                bot.send_message(user_id, "Share us your phone", reply_markup=en_phone())
                bot.delete_message(user_id, call.message.message_id)
                return

            db.withdraw(user_id, money)
            
            if lang == 'en':
                bot.answer_callback_query(call.id, "We will send your withdrawal money in 24 hours.")
            elif lang == 'am':
                bot.answer_callback_query(call.id, "ወጪ ያረጉትን ገንዘብ በ 24 ሰአት ጊዜ ውስጥ እንልክሎታለን ።")

            start_message(call.message)
            cur.execute("""
SELECT name,user_id,phone_number, account_link,
lang, gender, balance FROM students WHERE user_id = %s""", (user_id,))
            name, ui, phone_number, acc_link, lang, gender, balance = cur.fetchone()
            if not gender:
                gender = ''
            bot.send_message(creator_id(), f"""#Withdraw\n
<a href='{DEEPLINK+acc_link}'>{name}</a> {gender}
<b>ID</b> : <code>{ui}</code>
<b>Asked Balance</b> : {money}
<b>Current Balance</b>: {balance} 
<b>Phone Number</b>: <code>{phone}</code>""", parse_mode="HTML", reply_markup=cashout_btn(ui))
        else:
            if lang == 'en':
                bot.answer_callback_query(call.id, "Your balance is insufficent", show_alert=True)
            elif lang == 'am':
                bot.answer_callback_query(call.id, "ይቅርታ ያሎት ቀሪ ሂሳብ አነስተኛ ነው", show_alert=True)
    else:
        cur.execute('select invitation_link,invites,balance, withdraw, bbalance from students, '
                    'bot_setting where user_id = %s', (user_id,))
        link, invites, balance, withdr, bbl = cur.fetchone()
        bot.edit_message_text(BalanceText[lang].format(balance, withdr, invites, bbl, DEEPLINK+link), user_id,
                              call.message.message_id, parse_mode="HTML", reply_markup=withdraw(lang, DEEPLINK+link))


@bot.callback_query_handler(lambda call: call.data.startswith('cout'))
def on_cash_out(call: types.CallbackQuery):
    bot.answer_callback_query(call.id)
    user_id = call.data.split(":")[1]
    user_id = int(user_id)
    msg_id = call.message.message_id
    msg = bot.send_message(call.message.chat.id, "Send confirmation photo.")
    bot.register_next_step_handler(msg, done_cash_out, user_id, msg_id)


def done_cash_out(msg: types.Message, user_id, msg_id):
    if not msg.content_type == 'photo':
        return
    for users in [msg.chat.id, user_id]:
        bot.send_photo(users, msg.photo[-1].file_id, caption=msg.caption if msg.caption is not None else "",
                       parse_mode="html")
    bot.clear_step_handler_by_chat_id(msg.chat.id)
    bot.copy_message(msg.chat.id, msg.chat.id, msg_id, parse_mode='html')
    bot.reply_to(msg, "Money transfer done!")
    bot.delete_message(msg.chat.id, msg_id)


@bot.callback_query_handler(func=lambda call: call.data == 'bt', joined=True, not_banned=True)
def on_transfer_birr(call):
    user_id = call.from_user.id
    bot.answer_callback_query(call.id)
    lang = user_lang(user_id)
    if lang == 'en':
        text = bot.send_message(user_id, "Send reciever's ID", reply_markup=cancel('en'))
    else:
        text = bot.send_message(user_id, "የተቀባዩን መለያ ቁጥር ያስገቡ", reply_markup=cancel('am'))
    bot.register_next_step_handler(text, tr_money)


def tr_money(msg):
    user_id = msg.chat.id
    lang = user_lang(user_id)
    if msg.text.isdigit():
        r_id = msg.text
        all_btn = types.InlineKeyboardMarkup(row_width=3)
        _5 = types.InlineKeyboardButton("5 Birr", callback_data=f'tr-5_{r_id}')
        _10 = types.InlineKeyboardButton("10 Birr", callback_data=f'tr-10_{r_id}')
        _15 = types.InlineKeyboardButton("15 Birr", callback_data=f'tr-15_{r_id}')
        _20 = types.InlineKeyboardButton("20 Birr", callback_data=f'tr-20_{r_id}')
        _25 = types.InlineKeyboardButton("25 Birr", callback_data=f'tr-25_{r_id}')
        _50 = types.InlineKeyboardButton("50 Birr", callback_data=f'tr-50_{r_id}')
        _75 = types.InlineKeyboardButton("75 Birr", callback_data=f'tr-75_{r_id}')
        _100 = types.InlineKeyboardButton("100 Birr", callback_data=f'tr-100_{r_id}')
        all_btn.add(_5, _10, _15, _20, _25, _50, _75, _100)
        if lang == 'en':
            bot.send_message(user_id, "*How many birr do you want to Transfer?*",
                             reply_markup=all_btn, parse_mode="Markdown")
        elif lang == 'am':
            bot.send_message(user_id, "*ምን ያህል ብር ማስተላለፍ ይፈልጋሉ?*", reply_markup=all_btn, parse_mode="Markdown")
        start_message(msg)

    else:
        start_message(msg)
    bot.clear_step_handler_by_chat_id(msg.chat.id)
    bot.delete_state(msg.chat.id)


@bot.callback_query_handler(func=lambda call: re.search('^tr', call.data), joined=True, not_banned=True)
def transfer_birr_to_user(call):
    """
    function used to transfer birr; attached with line 1355
    :param call:
    :return:
    """
    conn = connection()
    cur = conn.cursor()
    user_id = call.from_user.id
    r_id = call.data.split('_')[1]
    r_id = int(r_id)
    if db.user_is_not_exist(r_id):
        bot.answer_callback_query(call.id, "User not found", show_alert=True)
        return
    cur.execute('select balance from students where user_id = %s', (user_id,))
    balance = cur.fetchone()[0]
    user_b = call.data.split('-')[1]
    user_b = ''.join(user_b).split('_')[0]
    user_b = int(user_b)

    if call.data == call.data:
        try:
            if balance >= user_b or user_id == creator_id():
                cur.execute('select lang from students where user_id = %s', (user_id,))
                lang = cur.fetchone()[0]
                if lang is not None:
                    try:
                        cur.execute('UPDATE students SET balance = balance + %s WHERE user_id = %s', (user_b, r_id,))
                        cur.execute('UPDATE students SET balance = balance - %s WHERE user_id = %s', (user_b, user_id,))
                        conn.commit()
                        bot.answer_callback_query(call.id, "Transfer done!")
                        try:
                            bot.delete_message(user_id, call.message.id)
                        except Exception as e:
                            logging.exception(e)
                        user = bot.get_chat(user_id)
                        bot.send_message(user_id, "Transfer done!")
                        bot.send_message(r_id, f"❇ You have recieved {user_b} Birr from {user.first_name}")
                    except Exception as e:
                        logging.exception(e)
            else:
                bot.answer_callback_query(call.id, 'Sorry balance is insuficient.', show_alert=True)

        except Exception:
            bot.send_message(user_id, "_No User found with {}_".format(r_id), parse_mode="Markdown")
            start_message(call.message)
        return


@bot.callback_query_handler(func=lambda call: call.data == 'bonus', joined=True, not_banned=True)
def on_recieve_bonus(call):
    data = {}
    conn = connection()
    user_id = call.from_user.id
    randb = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.9]
    amount = random.choice(randb)
    cur = conn.cursor()
    if not os.path.exists("bonus.text"):
        with open('bonus.text', 'w') as file:
            data[user_id] = {'amount': amount, 'time': time()}
            cur.execute("update students set balance = balance + %s where user_id = %s", (amount, user_id,))
            conn.commit()
            json.dump(data, file, indent=2)
            bot.answer_callback_query(call.id)
            bot.send_message(user_id, "You have recieved {} Birr bonus!".format(amount))

    else:
        with open('bonus.text') as f:
            data = json.loads(f.read())
            if not str(user_id) in data:
                data[user_id] = {'amount': amount, 'time': time()}
                cur.execute("update students set balance = balance + %s where user_id = %s", (amount, user_id,))
                conn.commit()
                with open('bonus.text', 'w') as file:
                    json.dump(data, file, indent=2)
                    bot.answer_callback_query(call.id)
                    bot.send_message(user_id, "You have recieved {} Birr bonus!".format(amount))
                
            else:
                clock = time()-data[str(user_id)]['time']
                if int(clock) // 60 // 60 >= 24:
                    data[user_id] = {'amount': amount, 'time': time()}
                    cur.execute("update students set balance = balance + %s where user_id = %s", (amount, user_id,))
                    conn.commit()
                    with open('bonus.text', 'w') as file:
                        json.dump(data, file, indent=2)
                        bot.answer_callback_query(call.id)
                        bot.send_message(user_id, "You have recieved {} Birr bonus!".format(amount))
                else:
                    with open('bonus.text') as file:
                        data = json.load(file)
                    bot.answer_callback_query(call.id, f"You have already recieved {data[str(user_id)]['amount']} "
                                                       f"Birr last 24 Hours. \
at least you have to wait {24-int(clock)//60//60} hours! ", show_alert=True)


@bot.callback_query_handler(func=lambda call: call.data in ['lang', 'editp', 'closeS'], joined=True, not_banned=True)
def on_user_setting(call: types.CallbackQuery):
    bot.answer_callback_query(call.id)
    user_id = call.from_user.id
    msg_id = call.message.message_id
    lang = user_lang(user_id)
    if call.data == 'lang':
        bot.edit_message_text("_Select Language / ቋንቋ ይምረጡ_", user_id, msg_id, reply_markup=language_btn(),
                              parse_mode="Markdown")

    elif call.data == 'editp':
        if lang == 'am':
            bot.edit_message_text("መግለጫዎን ያድሱ", user_id, msg_id, reply_markup=edit_profile(user_id, lang))
        elif lang == 'en':
            bot.edit_message_text('Edit Your Profile', user_id, msg_id, reply_markup=edit_profile(user_id, lang))

    elif call.data == "closeS":
        bot.delete_message(user_id, call.message.id)
        start_message(call.message)


@bot.callback_query_handler(func=lambda call: call.data in ['fname', '_username', 'gender', 'bio', 'back_edit'],
                            joined=True, not_banned=True)
def on_user_profile(call):

    bot.answer_callback_query(call.id)
    user_id = call.from_user.id
    bot.clear_step_handler_by_chat_id(user_id)
    lang = user_lang(user_id)
    conn = connection()
    cur = conn.cursor()
    if call.data == 'fname':
        fname = bot.send_message(user_id, "Enter your name\nYour name can include latters, numbers, undescore and space"
                                 )
        bot.register_next_step_handler(fname, first_)

    elif call.data == '_username':
        fr = types.ForceReply()
        bot.send_message(user_id, "<b>Rule</b>\n a username\n1: must start with dollar ($) sign.\n"
                                  "example <code>$Abebe</code>\n"
                                  "2: only include latters,numbers and underscore (_).\n"
                                  "3: cannot start with numbers or underscore (_) and cannot end with underscore (_).\n"
                                  "4: must be unique\n"
                                  "5: after $ sign minimum length is 5!"
                                  "6: is case insensetive ($username and $USERNAME are the same)", parse_mode="html")
        username = bot.send_message(user_id, "Enter new username", reply_markup=fr)
        bot.register_next_step_handler(username, username_)

    elif call.data == 'bio':
        bio = bot.send_message(user_id, "Write a few words about Your self.\n\nMaximun length is 75!")
        bot.register_next_step_handler(bio, bio_)

    elif call.data == 'gender':
        cur.execute('select gender from students where user_id = %s', (user_id,))
        gn = cur.fetchone()
        gender = None if gn == (None,) else gn[0]
        if lang == 'am':
            text = "ጾታ ይምረጡ"
        else:
            text = "Select Gender"
        bot.edit_message_text(text, user_id, call.message.message_id, reply_markup=user_gender(lang, gender))

    else:
        query = "SELECT name, joined_date, count(user_id),lang,gender,username, bio FROM students JOIN questions on " \
                "user_id = asker_id WHERE user_id = %s"
        cur.execute(query, (user_id,))
        name, joined_date, question, lang, gender, username, bio = cur.fetchone()
        bot.edit_message_text(SettingText.format(name, gender, username, bio, question, tp(time(), joined_date)),
                              user_id, call.message.message_id, parse_mode="HTML", reply_markup=user_setting(lang))
        bot.clear_step_handler_by_chat_id(user_id)


def first_(msg: types.Message):
    """
    function used to edit users' profile name
    :param msg:
    :return:
    """
    user_id = msg.chat.id
    name = msg.text
    name_regex = re.fullmatch(r"[\w\s]+", name)
    try:
        name = name_regex.group()
    except AttributeError:
        bot.send_message(user_id, "Invalid name")
        bot.clear_step_handler_by_chat_id(user_id)
        return
    else:
        db.update_query("UPDATE students SET name = %s WHERE user_id = %s", *(name, user_id))
        lang = user_lang(user_id)
        if lang == 'am':
            text = "መግለጫዎን ያድሱ"
        else:
            text = 'Edit Your Profile'
        bot.send_message(user_id, "Name updated!")
        bot.send_message(user_id, text, reply_markup=edit_profile(user_id, lang))
        bot.delete_message(user_id, msg.message_id - 2)
    finally:
        bot.clear_step_handler_by_chat_id(user_id)
        bot.delete_state(user_id)


def username_(msg):
    """
    function used to edit users' username
    :param msg:
    :return:
    """
    connex = connection()
    user_id = msg.chat.id
    text = msg.text
    cur = connex.cursor()
    lang = user_lang(user_id)
    username = re.search(r'^\$[a-zA-Z]+_?[a-zA-Z\d]+(_?[a-zA-Z\d]+)*', text, re.I)
    if username:
        check = re.search(r'^\$(developer|admin|creator|owner)$', username.group(), re.I)

        if check and user_id != creator_id():
            bot.send_message(user_id, "This username has already taken.")
            fr = types.ForceReply()
            username = bot.send_message(user_id, "Enter new username", reply_markup=fr)
            bot.register_next_step_handler(username, username_)

        else:
            if len(username.group()) < 6:
                username = bot.send_message(user_id, "This username is too short")
                bot.register_next_step_handler(username, username_)
                return

            cur.execute("SELECT username FROM students")
            users = cur.fetchall()
            for i in users:
                if not i[0]:
                    continue
                check = re.search(rf"{username.group()}", i[0], re.IGNORECASE)
                if check:
                    bot.send_message(user_id, "This username is already taken.")
                    fr = types.ForceReply()
                    username = bot.send_message(user_id, "Enter new username", reply_markup=fr)
                    bot.register_next_step_handler(username, username_)
                    return
            else:
                try:
                    db.update_username(user_id, username.group())
                    if lang == 'am':
                        text = "መግለጫዎን ያድሱ"
                    else:
                        text = 'Edit Your Profile'
                    bot.send_message(user_id, "Username updated!")
                    bot.send_message(user_id, text, reply_markup=edit_profile(user_id, lang))
                    bot.delete_message(user_id, msg.message_id - 3)
                except AttributeError:
                    pass
    else:
        bot.send_message(user_id, "Invalid username")


def bio_(msg):
    """
    function used to edit users'  `bio`
    :param msg:
    :return:
    """
    user_id = msg.chat.id
    user_bio = re.search(r'(.*){75}', msg.text, re.DOTALL)

    try:
        db.update_bio(user_id, user_bio.group())
    except AttributeError as e:
        logging.exception(e)

    lang = user_lang(user_id)
    if lang == 'am':
        text = "መግለጫዎን ያድሱ"
    else:
        text = 'Edit Your Profile'
    bot.send_message(user_id, "Bio updated!")
    bot.send_message(user_id, text, reply_markup=edit_profile(user_id, lang))
    bot.delete_message(user_id, msg.message_id - 2)
    bot.clear_step_handler_by_chat_id(user_id)


@bot.callback_query_handler(func=lambda call: call.data in ['male', 'famale', 'back_gender', 'main_gender'],
                            joined=True, not_banned=True)
def gender_edit(call):
    """
    function used to edit users' gender
    :param call:
    :return:
    """
    bot.answer_callback_query(call.id)
    user_id = call.from_user.id
    lang = user_lang(user_id)
    if lang == 'am':
        text = "ጾታ ይምረጡ"
        textp = "መግለጫዎን ያድሱ"
    else:
        text = "Select Gender"
        textp = 'Edit Your Profile'
    kwargs = {"male": '👨', 'famale': "🧑"}
    if call.data in kwargs:
        gen = kwargs.get(call.data)
        db.update_gender(user_id, kwargs[call.data])
        bot.edit_message_text(text, user_id, call.message.message_id, reply_markup=user_gender(lang, gen))

    elif call.data == 'back_gender':
        bot.edit_message_text(textp, user_id, call.message.message_id, reply_markup=edit_profile(user_id, lang))
    else:
        on_user_profile(call)


def channel_text():
    conn = connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT channels FROM bot_setting")
        channels_ = json.loads(cur.fetchone()[0])
    except (TypeError, AttributeError):
        channels_ = {}

    channels = channels_
    chan = [bot.get_chat(c) for c in channels if channels]
    ch = ["@" + c.username for c in chan]
    chan = '\n'.join(ch)
    key = [key for key, val in channels.items()]
    key = [bot.get_chat(k) for k in key]
    ukey = {k.username: {'callback_data': "channel:" + str(k.id)} for k in key}
    ukey.update({"➕ Add": {'callback_data': "bot:add_channel"}, "🔙 Back": {"callback_data": 'bot:back'}})
    return CHANNEL.format(chan), util.quick_markup(ukey)


def admin_text(user_id):
    admins = get_admins()
    if admins.get(str(user_id)):
        admins.pop(str(user_id))
    ad = [bot.get_chat(chat) for chat in admins]
    ad = [user.first_name for user in ad]
    ad = '\n'.join(ad)
    key = [bot.get_chat(key) for key in admins]
    ukey = {k.first_name: {'callback_data': "badm:" + str(k.id)} for k in key}
    ukey.update({"➕ Add": {'callback_data': "bot:add_admin"}, "🔙 Back": {"callback_data": 'bot:back'}})
    return ADMIN.format(ad), util.quick_markup(ukey)


@bot.callback_query_handler(func=lambda call: re.match(r"^bot:", call.data))
def on_bot_setting(call: types.CallbackQuery):
    """
    Branch of backend used to manage bot setting.
    :param call:
    :return:
    """
    conn = connection()
    cur = conn.cursor()
    bot.answer_callback_query(call.id)
    text = call.data.split(':')[1]
    user_id = call.message.chat.id
    msg_id = call.message.message_id
    if text == 'balance':
        btn = types.InlineKeyboardMarkup()
        btn.add(types.InlineKeyboardButton("🆙 Update", callback_data='bot:ubalance'),
                types.InlineKeyboardButton("🔙 Back", callback_data='bot:back'))
        cur.execute("SELECT bbalance FROM bot_setting")
        try:
            birr = cur.fetchone()[0]
        except (TypeError, AttributeError):
            birr = 0
        bot.edit_message_text(f"Current balance: {birr} Birr", user_id, call.message.message_id, reply_markup=btn)

    elif text == 'ubalance':
        bot.edit_message_reply_markup(user_id, msg_id, reply_markup=None)
        bot.send_message(user_id, "Send new balance what a user get when he invite person",
                         reply_markup=types.ForceReply())
        bot.set_state(user_id, BotSetting.balance)

    elif text == 'channels':
        t, k = channel_text()
        bot.edit_message_text(t, call.message.chat.id, call.message.message_id,
                              reply_markup=k, parse_mode='html')

    elif text == 'admins':
        a, k = admin_text(call.message.chat.id)
        bot.edit_message_text(a, call.message.chat.id, call.message.message_id,
                              reply_markup=k, parse_mode='html')

    elif text == 'add_channel':
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, ADD_CHANNEL, reply_markup=bscancel(), parse_mode='html')
        bot.set_state(user_id, BotSetting.channel)

    elif text == 'add_admin':
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, ADD_ADMIN, reply_markup=bscancel(), parse_mode='html')
        bot.set_state(user_id, BotSetting.admin)

    elif text == 'back':
        bot.edit_message_text(f"<b> 🤖 Bot Setting</b>\n\nFrom this menu you can manage your bot setting.", user_id,
                              msg_id, reply_markup=bot_setting_btn(), parse_mode='html')


@bot.message_handler(state=BotSetting.balance, is_number=True, chat_types=['private'])
def set_balance(msg: types.Message):
    """
    Branch of `backend` and used to set `bot balance`.
    `Bot balance` is an amount that will be add to user balance when user invites people using his refferal link.
    :param msg:
    :return:
    """
    conn = connection()
    bot.delete_message(msg.chat.id, msg.message_id-2)
    bot.send_message(msg.chat.id, "Balance updated ✅")
    db.update_bot_balance(msg.text)
    cur = conn.cursor()
    btn = types.InlineKeyboardMarkup()
    btn.add(types.InlineKeyboardButton("🆙 Update", callback_data='bot:ubalance'),
            types.InlineKeyboardButton("🔙 Back", callback_data='bot:back'))
    cur.execute("SELECT bbalance FROM bot_setting")
    try:
        b = cur.fetchone()[0]
    except (TypeError, AttributeError):
        b = None
    bot.send_message(msg.from_user.id, f"Current balance: {b} Birr", reply_markup=btn)
    start_message(msg)
    bot.delete_state(msg.chat.id)


@bot.callback_query_handler(func=lambda call: call.data == 'bscancel', state='*')
def cancel_on_add_admin(call: types.CallbackQuery):
    """

    :param call:
    :return:
    """
    state = bot.get_state(call.message.chat.id)
    bot.answer_callback_query(call.id)
    if state != 'channel' or state != 'admin':
        return
    t, k = channel_text()
    if state == BotSetting.channel:
        bot.edit_message_text(t, call.message.chat.id, call.message.message_id,
                              reply_markup=k, parse_mode='html')
    else:
        a, k = admin_text(call.message.chat.id)
        bot.edit_message_text(a, call.message.chat.id, call.message.message_id,
                              reply_markup=k, parse_mode='html')
    bot.delete_state(call.message.chat.id)


@bot.message_handler(state=BotSetting.channel, is_forwarded=True)
def add_channel(msg: types.Message):
    channel = msg.forward_from_chat
    user_id = msg.from_user.id
    conn = connection()
    cur = conn.cursor()
    try:
        assert channel.type == 'channel', "Must be channel not "+channel.type
        assert channel.username, "the channel must have a username!"
        cur.execute("select channels from bot_setting")
        ujson: dict = json.loads(cur.fetchone()[0])
        ujson.update({str(channel.id): {'send_message': False, 'approve': False, 'force_join': False}})
        cur.execute("update bot_setting set channels = %s", (json.dumps(ujson),))
        conn.commit()
        bot.send_message(user_id, "Channel added successfully ✅")
        text, keyboard = channel_text()
        bot.send_message(user_id, text, reply_markup=keyboard, parse_mode='html')
    except AssertionError as e:
        bot.send_message(user_id, e.args[0])
    except Exception as e:
        pass
    else:
        bot.delete_state(user_id)


def admin_permision(admin_id):
    conn = connection()
    cur = conn.cursor()
    cur.execute("select admins from bot_setting")
    ujson: dict = json.loads(cur.fetchone()[0])
    cur.execute("select status from students where user_id = %s", (admin_id,))
    stat = cur.fetchone()[0]
    per = ['✅' if ujson[str(admin_id)][key] else "❌" for key in ujson.get(str(admin_id))]
    admin = bot.get_chat(admin_id)
    text = ADMINP.format(admin.first_name, *per)
    btn = admin_permision_btn(admin_id, stat, **ujson)
    return text, btn


def channel_permision(channel_id):
    conn = connection()
    cur = conn.cursor()
    cur.execute("select channels from bot_setting")
    ujson: dict = json.loads(cur.fetchone()[0])
    per = ['✅' if ujson[channel_id][key] else "❌" for key in ujson.get(channel_id)]
    channel = bot.get_chat(channel_id)
    text = CHANNELP.format(channel.username, *per)
    btn = channel_btn(channel_id, **ujson)
    return text, btn


@bot.message_handler(state=BotSetting.admin, content_types=util.content_type_media, is_digit=True)
def add_admin(msg: types.Message):
    user_id = msg.from_user.id
    user = int(msg.text)
    conn = connection()
    cur = conn.cursor()
    try:
        assert not db.user_is_not_exist(user), "User not found"
        cur.execute("select status from students where user_id = %s", (user,))
        assert cur.fetchone()[0] not in ['creator', 'admin'], "User is already admin!"
        cur.execute("select admins from bot_setting")
        ujson: dict = json.loads(cur.fetchone()[0])
        ujson.update({
            str(user): {"send_message": False, 'approve_questions': False, 'manage_setting': False, 'ban_user': False,
                        'feedback': False, 'can_see': False}
        })
        cur.execute("update bot_setting set admins = %s", (json.dumps(ujson),))
        conn.commit()
        bot.send_message(user_id, "Admin added successfully ✅")
        text, btn = admin_permision(user)
        bot.send_message(user_id, text, reply_markup=btn, parse_mode='html')

    except AssertionError as e:
        bot.send_message(user_id, e.args[0])
    finally:
        bot.delete_state(user_id)


@bot.callback_query_handler(func=lambda call: re.search(r'channel:', call.data))
def click_channel(call: types.CallbackQuery):
    bot.answer_callback_query(call.id)
    user_id, msg_id = call.from_user.id, call.message.message_id
    channel_id = call.data.split(':')[1]
    t, b = channel_permision(channel_id)
    bot.edit_message_text(t, user_id, msg_id, reply_markup=b, parse_mode='html')


@bot.callback_query_handler(func=lambda call: re.search(r'myc', call.data))
def on_channel_permision(call: types.CallbackQuery):
    bot.answer_callback_query(call.id)
    conn = connection()
    cur = conn.cursor()
    channel_id = call.data.split(":")[1]
    text = call.data.split(":")[2]
    user_id = call.from_user.id
    msg_id = call.message.message_id
    if text == 'back':
        t, b = channel_text()
        bot.edit_message_text(t, user_id, msg_id, reply_markup=b, parse_mode='html')
    elif text == 'remove':
        try:
            cur.execute('select channels from bot_setting')
            ujson: dict = json.loads(cur.fetchone()[0])
            del ujson[channel_id]
            cur.execute('update bot_setting set channels = %s', (json.dumps(ujson),))
            conn.commit()
            t, b = channel_text()
            bot.edit_message_text(t, user_id, msg_id, reply_markup=b, parse_mode='html')
        except (IndexError, KeyError):
            bot.send_message(user_id, "channel not found..")
            bot.delete_message(user_id, msg_id)
    else:
        try:
            cur.execute('select channels from bot_setting')
            ujson: dict = json.loads(cur.fetchone()[0])
            if ujson[channel_id][text]:
                ujson[channel_id][text] = False
            else:
                ujson[channel_id][text] = True
            cur.execute("update bot_setting set channels = %s", (json.dumps(ujson), ))
            conn.commit()
            t, b = channel_permision(channel_id)
            bot.edit_message_text(t, user_id, msg_id, reply_markup=b, parse_mode='html')

        except (IndexError, KeyError):
            bot.send_message(user_id, "channel not found...")
            bot.delete_message(user_id, msg_id)


@bot.callback_query_handler(lambda call: re.search(r"badm", call.data))
def click_admin(call: types.CallbackQuery):
    bot.answer_callback_query(call.id)
    admin_id = call.data.split(':')[1]
    text, btn = admin_permision(admin_id)
    bot.edit_message_text(text, call.from_user.id, call.message.message_id, reply_markup=btn, parse_mode='html')


@bot.callback_query_handler(lambda call: re.search(r'admin:', call.data))
def on_admin_permision(call: types.CallbackQuery):
    conn = connection()
    cur = conn.cursor()
    bot.answer_callback_query(call.id)
    admin_id = call.data.split(":")[2]
    user_id = call.from_user.id
    msg_id = call.message.message_id
    text = call.data.split(":")[1]
    kwargs = {'send_message': "Send message to users and channels", 'manage_setting': "Manage bot setting",
              'approve_questions': "Approve questions", 'ban_user': "Ban user", 'feedback': "Recieve feedback",
              'can_see': "See users profile and Bot Stastics"}

    if text == 'done':
        try:
            cur.execute("update students set status = 'admin' where user_id = %s", (admin_id,))
            conn.commit()
            cur.execute('select admins from bot_setting')
            ujson: dict = json.loads(cur.fetchone()[0])
            per = ["◽ "+kwargs[key] for key, val in ujson.get(admin_id, {}).items()]
            per = '\n'.join(per)
            bot.send_message(int(admin_id), "🎉 Dear user you have been made as an admin on this bot and you have these "
                                            f"permision(s) 👇\n{per}\n\n"
                                            f"💠 [Click here to activate your permision(s)]({DEEPLINK+'start'}",
                                            parse_mode='markdown')
            t, k = admin_text(call.message.chat.id)
            bot.edit_message_text(t, user_id, msg_id, reply_markup=k, parse_mode='html')

        except Exception as e:
            bot.delete_message(user_id, msg_id)

    elif text == 'back':
        t, k = admin_text(call.message.chat.id)
        bot.edit_message_text(t, user_id, msg_id, reply_markup=k, parse_mode='html')
    elif text == 'remove':
        try:
            cur.execute("update students set status = 'member' where user_id = %s", (admin_id,))
            conn.commit()
            cur.execute('select admins from bot_setting')
            ujson: dict = json.loads(cur.fetchone()[0])
            del ujson[admin_id]
            cur.execute('update bot_setting set admins = %s', (json.dumps(ujson),))
            conn.commit()
        except (IndexError, KeyError):
            bot.send_message(user_id, "user not found....")
            bot.delete_message(user_id, msg_id)
        else:
            t, k = admin_text(call.message.chat.id)
            bot.edit_message_text(t, user_id, msg_id, reply_markup=k, parse_mode='html')

    else:
        try:
            cur.execute('select admins from bot_setting')
            ujson: dict = json.loads(cur.fetchone()[0])
            if ujson[admin_id][text]:
                ujson[admin_id][text] = False
            else:
                ujson[admin_id][text] = True
            cur.execute('update bot_setting set admins = %s', (json.dumps(ujson),))
            conn.commit()
        except (IndexError, KeyError):
            bot.send_message(user_id, "user not found...")
            bot.delete_message(user_id, msg_id)
        else:
            t, k = admin_permision(admin_id)
            bot.edit_message_text(t, user_id, msg_id, reply_markup=k, parse_mode='html')


def user_not_joined():
    conn = connection()
    cur = conn.cursor()
    text = ""
    _text = ""
    get = False
    cur.execute('select channels from bot_setting')
    channels: dict = json.loads(cur.fetchone()[0])
    for key, val in channels.items():
        if val.get('force_join'):
            text += "@"+bot.get_chat(int(key)).username+'\n'
            get = True
    if not get:
        return
    cur.execute('select user_id from students')
    users_id = cur.fetchall()
    get_u = False
    for user_id in users_id:
        for ch in text.split('\n'):
            try:
                user = bot.get_chat_member(ch, user_id[0])
                if user.status not in ['administrator', 'creator', 'member']:
                    _text += ch + '\n'
                    get_u = True
            except ApiTelegramException:
                continue
        if get_u:
            try:
                bot.send_message(user_id[0], f"Dear user make sure that you joined our channel(s)\n{_text}")
            except ApiTelegramException:
                continue
        get_u = False
        text = ""
    del text, _text, get, get_u


def show_account_info(msg, text):
    conn = connection()
    cur = conn.cursor()
    data = []

    cur.execute(
        "select name, user_id, joined_date, gender, username, bio, status from "
        "students where account_link = %s",
        (text,))
    data.extend(cur.fetchone())

    if not data[4]:
        data[4] = ''
    name, id, joined_date, gender, username, bio, status = data
    if status == 'banned':
        banned = True
    else:
        banned = False
    admins = json.loads(db.select_query("SELECT admins FROM bot_setting").fetchone()[0])

    kwargs = admins
    if not id == msg.chat.id:
        bot.send_message(msg.chat.id, f"""\
<b> {name} </b> {gender}
--------------------------------------------
<b> Username </b>: {username}
<b> Bio </b>: <code> {bio} </code>\n
<i> Joined {tp(time(), joined_date)} ago </i >
---------------------------------------------
""", reply_markup=user_profile_info(id, banned=banned, admin_id=msg.from_user.id, **kwargs),
                         parse_mode="html")
    else:
        lang = user_lang(msg.chat.id)
        msg.text = "⚙️ Settings" if lang == 'en' else "⚙ ቅንብሮች"
        if lang == 'en':
            english_button(msg)
        else:
            amharic_button(msg)


def user_via_link(msg, text):
    conn = connection()
    cur = conn.cursor()
    if db.user_is_not_exist(msg.chat.id):
        cur.execute("SELECT name, gender FROM students "
                    "WHERE user_id = %s", (text,))

        first, gend = cur.fetchone()

        if not gend:
            gend = ''
        try:
            db.update_invite(text, msg.chat.id)
            bot.send_message(msg.chat.id, f"You were invited by {first} {gend}")
            start_message(msg)
            bot.send_message(text, f"User {util.user_link(msg.from_user)} was Joined by your invitational link",
                             parse_mode='html')
        
        except ApiTelegramException:
            pass
        
    else:
        start_message(msg)


def show_questions(user_id, lang):
    conn = connection()
    cur = conn.cursor()
    showed = False
    cur.execute("""
        SELECT students.name, students.gender,students.account_link, 
        Questions.question,Questions.browse,Questions.type_q,
        Questions.caption, Questions.time, Questions.browse_link, 
        Questions.subject, Questions.status, Questions.question_id FROM students 
        JOIN Questions ON students.user_id = Questions.asker_id
        WHERE students.user_id = %s
        """, (user_id,))
    for ui in cur.fetchall():
        name, gender, acc, q, b, tq, c, t, bl, sub, stat, q_id = ui
        btn = types.InlineKeyboardMarkup()
        burl = types.InlineKeyboardButton(f"Browse ({b})", url=DEEPLINK + bl)
        btn.add(burl)
        time_ = tp(time(), t)
        parse_time = f"<i>{time_} ago</i>" if not time_ == "Just now" else "<i>Just now</i>"
        if stat == 'pending':
            br = on_user_question('pending', q_id)
            parse_time = ''
        elif stat == "canceld":
            br = on_user_question('canceld', q_id)
        elif stat == 'preview':
            br = Panel(q_id)
        elif stat == 'declined':
            br = None
        else:
            br = btn
        showed = True
        try:
            if tq == "text":
                bot.send_message(user_id, f"{sub}\n\n<b>{q}</b>\n\nBy: <a href='{DEEPLINK + acc}'>{name}</a> {gender}"
                                          f"\n{parse_time}",
                                 parse_mode="html", reply_markup=br)
            else:
                system = getattr(bot, f'send_{tq}')
                system(user_id, q,
                caption = f"{sub}\n\n<b>{c}</b>\n\nBy: <a href='{DEEPLINK + acc}'>{name}</a> {gender}"
                f"\n{parse_time}", parse_mode = "html", reply_markup = br)
        except ApiTelegramException:
            continue

    if not showed:
        ask_q = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton("Ask" if lang == 'en' else 'ጠይቅ', callback_data='ask_question')
        ask_q.add(btn)
        if lang == 'en':
            bot.send_message(user_id, "Sorry you don't have any asked question yet.", reply_markup=ask_q)
        elif lang == 'am':
            bot.send_message(user_id, "ይቅርታ እስካሁን ምንም የጠየቁት ጥያቄ የለም ።", reply_markup=ask_q)


def browse(msg, ids):
    conn = connection()
    cur = conn.cursor()
    data = []
    ujson_msg_id = {}
    if 1:
        showed = False
        cur.execute("""
                SELECT Questions.question, Questions.type_q, Questions.caption,Questions.subject,
                students.name, students.gender, students.account_link, Questions.time FROM students JOIN Questions ON 
                Questions.asker_id = students.user_id WHERE Questions.question_id = %s
                """, (ids,))
        for ui in cur.fetchall():
            data.extend(ui)
            if not data[5]:
                data[5] = ""
       
        q, tq, c, subjr, first, gend, acc, q_time = data
        data.clear()
        btn = types.InlineKeyboardMarkup()
        btn.add(types.InlineKeyboardButton("Answer", callback_data=f"answer_{ids}"))
        if tq == 'text':
            bot.send_message(msg.chat.id, f"{subjr}\n\n<b>{q}</b>\n\nBy: <a href='{DEEPLINK + acc}'>{first}</a> {gend}",
                                          reply_markup=btn, parse_mode="html")
        else:
            send_document = getattr(bot, f'send_{tq}')
            send_document(msg.chat.id, q,
                       caption=f"{subjr}\n\n<b>{c}</b>\n\nBy: <a href='{DEEPLINK + acc}'>{first}</a> {gend}",
                       parse_mode="html", reply_markup=btn)
        cur.execute("""
                SELECT students.name, students.user_id, students.gender,students.account_link,
                Answers.answer, Answers.type_ans, Answers.caption, Answers.reply_to, Questions.question_id,
                Answers.answer_id, Answers.user_id, Answers.status, Answers.time, Questions.asker_id FROM students JOIN
                Answers ON students.user_id = Answers.user_id JOIN Questions ON Questions.question_id = 
                Answers.question_id WHERE Questions.question_id = %s ORDER BY Answers.time""", (ids,))
        for data in cur.fetchall():
            first, ui, gend, acc, ans, ta, c, ar, q_id, ans_id, a_id, status, ans_time, asker_id = data
            reply = ujson_msg_id.get(ar)
            time_ = tp(time(), ans_time)
            parse_time = f"<i>{time_} ago</i>" if not time == "Just now" else "<i>Just now</i>"
            msg_id = db.select_query('select msg_id from answers where answer_id = %s', ans_id).fetchone()[0]

            if not gend:
                gend = ""
            if status != 'posted':
                continue
            try:
                if ta == "text":
                    m = bot.send_message(msg.chat.id, f"<b>{ans}</b>\n\nBy: <a href='{DEEPLINK + acc}'>{first}</a> "
                                                      f"{gend}\n{parse_time}".strip(), parse_mode="html",
                                                      reply_markup=on_answer(ui, q_id, ans_id, msg_id),
                                                      reply_to_message_id=reply)

                else:
                    send_document = getattr(bot, f'send_{ta}')
                    m = send_document(msg.chat.id, ans,
                               caption=f"<b>{c}</b>\n\nBy: <a href='{DEEPLINK + acc}'>{first}</a> {gend}"
                                       f"\n{parse_time}".strip(), parse_mode="html", reply_to_message_id=reply,
                               reply_markup=on_answer(ui, q_id, asker_id, msg_id)
                               )
                ujson_msg_id[ans_id] = m.message_id
            except Exception:
                raise

            finally:
                showed = True
            
        if not showed:
            bot.send_message(msg.chat.id, "There is no answer.\nBe the first to answer!")


def send_to_channel(call: types.CallbackQuery, with_comment: bool, channels: Union[str, int, list]):
    media_type = call.message.content_type
    btn = types.InlineKeyboardMarkup()
    media, file, type_, caption = None, None, None, None
    use_copy = False
    if media_type == 'text':
        media = f"#Message\n\n{call.message.text}\n\nBy: Admin 👨‍💻"
        file, type_ = media, 'text'

    elif media_type == 'photo':
        media = call.message.photo[-1].file_id
        caption = f"#Message\n\n{call.message.caption}\n\nBy: Admin 👨‍💻"
        file, type_ = media, 'photo'

    elif media_type == 'video':
        media = call.message.video.file_id
        caption = f"#Message\n\n{call.message.caption}\n\nBy: Admin 👨‍💻"
        file, type_ = media, 'video'
    else:
        use_copy = True
    _channels = channels
    if not use_copy and with_comment:
        from datetime import date
        max_id = db.select_query('select max(id) from admin_post').fetchone()[0]
        if max_id is None:
            max_id = 0
        max_id = max_id + 1
        db.update_query("INSERT INTO admin_post(from_admin, post, type, date, browse, link, caption, to_channel) "
                        "VALUES(%s, %s, %s, %s, %s, %s, %s, %s)", call.message.chat.id, media, type_, date.today(), 0,
                        generator.comment_link(max_id), caption, _channels)
        max_id = db.select_query('select max(id) from admin_post').fetchone()[0]
        link = db.select_query("select link from admin_post WHERE id = %s", max_id).fetchone()[0]
        if with_comment:
            btn.add(types.InlineKeyboardButton("🗯 Comment (0)", url=DEEPLINK+link))

        if not with_comment:
            for channel in channels:
                if media_type == 'text':
                    bot.send_message(channel, media, parse_mode="html", disable_web_page_preview=True)
                elif media_type == 'photo':
                    bot.send_photo(channel, media, caption, 'html')
                elif media_type == 'video':
                    bot.send_video(channel, media, caption=caption, parse_mode='html')

        else:
            if media_type == 'text':
                umsg = bot.send_message(channels, media, parse_mode="html", reply_markup=btn,
                                        disable_web_page_preview=True)
            elif media_type == 'photo':
                umsg = bot.send_photo(channels, media, caption, 'html', reply_markup=btn)
            else:
                umsg = bot.send_video(channels, media, caption=caption, parse_mode='html', reply_markup=btn)
            db.update_query("UPDATE admin_post SET msg_id = %s WHERE id = %s", umsg.message_id, max_id)
    else:
        for channel in channels:
            bot.copy_message(channel, call.message.chat.id, call.message.message_id, parse_mode='html')


def send_to_users(call: types.CallbackQuery):
    conn = connection()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM students")
    users_id = cur.fetchall()
    user_id = [ui for user_id in users_id for ui in user_id]
    try:
        del markups['☑ Done']
        del markups['➕ Add']
    except (IndexError, KeyError):
        pass
    for ui in user_id:
        try:
            bot.copy_message(ui, call.message.chat.id, call.message.message_id, 
                             reply_markup=util.quick_markup(markups), parse_mode='HTML')
        except ApiTelegramException:
            continue
    markups.clear()


def send_comment_browse(msg: types.Message, link):
    post_id = db.select_query("SELECT id from admin_post WHERE link = %s", link).fetchone()[0]
    ujson = {}
    btn = types.InlineKeyboardMarkup()
    btn.add(
        types.InlineKeyboardButton("🗯 Comment", callback_data=f'comment_{post_id}')
    )
    the_post = db.select_query("SELECT post, type, caption FROM admin_post WHERE id = %s", post_id).fetchone()
    message, media_type, caption = the_post
    if media_type == 'text':
        bot.send_message(msg.chat.id, f"<b>{message}</b>", parse_mode='html', reply_markup=btn)
    elif media_type == 'photo':
        bot.send_photo(msg.chat.id, message, caption=f"<b>{caption}</b>", parse_mode='html', reply_markup=btn)
    elif media_type == 'video':
        bot.send_video(msg.chat.id, message, caption=f"<b>{caption}</b>", parse_mode='html', reply_markup=btn)

    users_comment = db.select_query("SELECT comment, user_id, reply_to, id, status, msg_id from comments "
                                    "WHERE to_post = %s ORDER BY time", post_id).fetchall()
    showed = False
    for data_collected in users_comment:
        comment, user_id, reply_to, comment_id, status, msg_id = data_collected
        if not status == 'posted':
            continue
        query = "SELECT name, account_link, gender FROM students WHERE user_id  = %s"
        name, acc, gen = None, None, None
        for nm, ac, gn in db.select_query(query, user_id).fetchall():
            name, acc, gen = nm, ac, gn
        if gen is None:
            gen = ''
        sent = bot.send_message(msg.chat.id, f"<b>{comment}</b>\n\nBy: <a href='{DEEPLINK+acc}'>{name}</a> {gen}",
                                reply_to_message_id=ujson.get(reply_to), parse_mode='html',
                                reply_markup=oncomment(user_id, post_id, comment_id, msg_id))
        ujson[comment_id] = sent.message_id
        showed = True
    if not showed:
        bot.send_message(msg.chat.id, "Be the first to comment!")


def forever():
    schedule.every(12).hours.do(user_not_joined)
    while 1:
        schedule.run_pending()


@app.route('/' + TOKEN, methods=['POST'])
def get_message():
    json_string = request.get_data().decode('utf-8')
    update = types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200


@app.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL + TOKEN)
    return "!", 200



def main():
    bot.add_custom_filter(ChatFilter())
    bot.add_custom_filter(IsDigitFilter())
    bot.add_custom_filter(IsNumberFilter())
    bot.add_custom_filter(StateFilter(bot))
    bot.add_custom_filter(NotBannedFilter())
    bot.add_custom_filter(ForwardFilter())
    bot.add_custom_filter(IsAdminfilter())
    bot.add_custom_filter(FromUserFlter())
    bot.add_custom_filter(TextMatchFilter())
    bot.add_custom_filter(IsDeeplinkFilter())
    bot.add_custom_filter(UserJoinedChannelsFilter(bot))
    bot.enable_saving_states()
    # t1 = threading.Thread(target=forever)
    # t1.start()
    # app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5555)))
    bot.infinity_polling()

if __name__ == "__main__":
    main()
