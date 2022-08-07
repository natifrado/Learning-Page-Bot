from telebot import types
from system import creator_id

def language_btn():
    both_btn = types.InlineKeyboardMarkup()
    en_btn = types.InlineKeyboardButton(text="🇬🇧 English",callback_data='en')
    am_btn = types.InlineKeyboardButton(text="🇪🇹 አማርኛ",callback_data='am')
    #back=types.InlineKeyboardButton(text="🔙 Back" if lang == 'am' else "🔙 ተመለስ",callback_data='backwithdr')
    both_btn.add(en_btn,am_btn)
    return both_btn

def am_phone():
    all= types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn = types.KeyboardButton("📱 ስልክ ቁጥር ላክ",request_contact=True)
    all.add(btn)
    return all

def en_phone():
    all= types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn = types.KeyboardButton("📱Send Phone Number",request_contact=True)
    all.add(btn)
    return all

def remove_btns():
    both_btn = types.ReplyKeyboardRemove(selective=True)
    return both_btn

def user_gender(lang, gen):
    all_btns = types.InlineKeyboardMarkup(row_width=5)
    umale = types.InlineKeyboardButton(text="👨 ወንድ"+" ✅" if gen == '👨' else "👨 ወንድ", callback_data="male")
    ufamale = types.InlineKeyboardButton(text="🧑 ሴት"+" ✅" if gen =='🧑' else "🧑 ሴት", callback_data="famale")
    male = types.InlineKeyboardButton(text='👨 Male'+" ✅" if gen == '👨'  else '👨 Male', callback_data="male")
    famale = types.InlineKeyboardButton(text='🧑 Famale'+" ✅" if gen == '🧑' else '🧑 Famale', callback_data="famale")
    back = types.InlineKeyboardButton(text="🔙 Back" if lang == 'en' else "🔙 ተመለስ",callback_data='back_gender')
    menu = types.InlineKeyboardButton(text="🏠 Main Menu" if lang == 'en' else "🏠 ዋና ገጽ",callback_data='main_gender')
    all_btns.add(male if lang == 'en' else umale, famale if lang == 'en' else ufamale)
    all_btns.add(back,menu)
    return all_btns

def books_btn(lang, type_book, grade):
    all_btn = types.InlineKeyboardMarkup(row_width=3)
    en = types.InlineKeyboardButton("🇬🇧 English",callback_data=f'book:english:{type_book}:{grade}')
    am = types.InlineKeyboardButton("🇪🇹 አማርኛ",callback_data=f'book:amharic:{type_book}:{grade}')
    chem = types.InlineKeyboardButton("🧪 Chemistry",callback_data=f'book:chemistry:{type_book}:{grade}')
    math = types.InlineKeyboardButton("🧮 Math",callback_data=f'book:math:{type_book}:{grade}')
    phy = types.InlineKeyboardButton("🔭 Physics ",callback_data=f'book:physics:{type_book}:{grade}')
    geo = types.InlineKeyboardButton("🧭 Geography",callback_data=f'book:geography:{type_book}:{grade}')
    his = types.InlineKeyboardButton("🌏 History",callback_data=f'book:history:{type_book}:{grade}')
    ict = types.InlineKeyboardButton("💻 ICT",callback_data=f'book:ict:{type_book}:{grade}')
    bio = types.InlineKeyboardButton("🔬 Biology",callback_data=f'book:biology:{type_book}:{grade}')
    civ = types.InlineKeyboardButton("⚖ Civics",callback_data=f'book:civics:{type_book}:{grade}')
    hep = types.InlineKeyboardButton("⚽️ HPE",callback_data=f'book:hpe:{type_book}')
    back = types.InlineKeyboardButton(text="🔙 Back" if lang == 'en' else "🔙 ተመለስ", callback_data=f'book:back:{type_book}')
    menu = types.InlineKeyboardButton(text="🏠 Main Menu" if lang == 'en' else "🏠 ዋና ገጽ", callback_data='book:main')
    all_btn.add(math, phy, chem, bio, civ, geo, ict, hep, his, en, am)
    all_btn.add(back, menu)
    return all_btn

def user_setting(lang):
    all_btn = types.InlineKeyboardMarkup(row_width=5)
    lan = types.InlineKeyboardButton(text="🌐 Language" if lang == 'en' else "🌐 ቋንቋ",callback_data='lang')
    edit_p = types.InlineKeyboardButton(text='📝 Edit Profile' if lang == 'en' else "📝 መግለጫ አድስ",callback_data='editp')
    close = types.InlineKeyboardButton(text='❌ Close' if lang == 'en' else "❌ ዝጋ",callback_data='closeS')
    all_btn.add(lan,edit_p)
    all_btn.add(close)
    return all_btn

def on_user_question(status, q_id):
    btn = types.InlineKeyboardMarkup()
    c = types.InlineKeyboardButton("❌ Cancel", callback_data=f'q:cancel:{q_id}')
    rs = types.InlineKeyboardButton("✔ Resubmit", callback_data=f'q:resubmit:{q_id}')

    if status == 'pending':
        btn.add(c)
    else:
        btn.add(rs)
    return btn


def main_buttons(l, user_id, **kwargs):
    all_btn = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    #home = types.KeyboardButton()
    send_m = types.KeyboardButton("📝 Send Message")
    bot_s = types.KeyboardButton("🤖 Bot Setting")
    statics = types.KeyboardButton("📊 Statics")
    que = types.KeyboardButton("🧩 Questions")
    books = types.KeyboardButton("📚 Books" if l == 'en' else "📚መጽሐፍት")
    ask = types.KeyboardButton("🗣 Ask Question" if l == 'en' else "🗣 ጥያቄ ጠይቅ" )
    ques = types.KeyboardButton("🙋‍♂ My Questions" if l == 'en'  else "🙋‍♂ የኔ ጥያቄዎች")
    invite = types.KeyboardButton("👨‍👩‍👦‍👦 Invite" if l == 'en' else "👨‍👩‍👦‍👦 ጋብዝ")
    setting = types.KeyboardButton("⚙️ Settings" if l == 'en'  else "⚙️ ቅንብሮች")
    feedback = types.KeyboardButton("💬 Feedback" if l == 'en' else "💬 አስታየት")
    all_btn.add(send_m if user_id == creator_id() or kwargs.get(str(user_id), {}).get('send_message') else "",
                bot_s if user_id == creator_id() or kwargs.get(str(user_id), {}).get('manage_setting') else "",
                statics if user_id == creator_id() or kwargs.get(str(user_id), {}).get('can_see') else "",
                que if user_id == creator_id() or kwargs.get(str(user_id), {}).get('approve_questions') else "")
    all_btn.add(books, ask)
    all_btn.add(ques, invite)
    all_btn.add(setting, feedback)
    return all_btn


def on_book_click(id, exist=False):
    btn = types.InlineKeyboardMarkup()
    if exist:
        btn.add(types.InlineKeyboardButton("💳 Balance", callback_data=f'ubook:bl:{id}'),
        types.InlineKeyboardButton("🗑 Delete", callback_data=f'ubook:dl:{id}'))
    else:
        btn.add(types.InlineKeyboardButton("➕ Add", callback_data=f'ubook:add:{id}'))
        
    btn.add(types.InlineKeyboardButton("🔙 Back", callback_data=f'ubook:back:{id}'))   
    return btn 


def user_profile_info(user_id, banned=False, admin_id=None, **kwargs):
    all = types.InlineKeyboardMarkup(row_width=3)
    btn = []
    chat = types.InlineKeyboardButton("📝 Send Message", callback_data=f'user:chat:{user_id}')
    ban = types.InlineKeyboardButton("🚷" if not banned else "✅" , callback_data=f'user:ban:{user_id}'
                    if not banned else f"user:unban:{user_id}")
    sp = types.InlineKeyboardButton("👤" , callback_data=f'user:show:{user_id}')
    all.add(chat)
    if admin_id == creator_id() or kwargs.get(str(admin_id), {}).get(
        'ban_user'):
        btn.append(ban)
    if admin_id == creator_id() or kwargs.get(str(admin_id), {}).get(
        'can_see'):
        btn.append(sp)
    all.add(*btn)
    return all


def on_user_(user_id, banned=False, admin_id=None, **kwargs):
    all = types.InlineKeyboardMarkup(row_width=3)
    chat = types.InlineKeyboardButton("📤", callback_data=f'user:reply:{user_id}' )
    ban = types.InlineKeyboardButton("🚷" if not banned else "✅", callback_data=f'user:ban:{user_id}'
    if not banned else f"user:unban:{user_id}")
    btn = []
    sp = types.InlineKeyboardButton("👤", callback_data=f'user:show:{user_id}')
    if admin_id == creator_id() or kwargs.get(str(admin_id), {}).get(
        'ban_member'):
        btn.append(ban)
    if admin_id == creator_id() or kwargs.get(str(admin_id), {}).get(
        'can_see'):
        btn.append(sp)
    all.add(chat, *btn)
    return all


def on_answer(user_id, question_id, answer_id, msg_id):
    btn = types.InlineKeyboardMarkup()
    btn.add(
        types.InlineKeyboardButton("↩ Reply", callback_data=f'reply:{user_id}:{question_id}:{answer_id}:{msg_id}'),
        types.InlineKeyboardButton("⚠ Report", callback_data=f'report:{user_id}')
    )
    return btn

def types_book_am():
    all_btn = types.InlineKeyboardMarkup(row_width=2)
    edu = types.InlineKeyboardButton("📖 Student Book",callback_data='edus')
    edut = types.InlineKeyboardButton("📚 Teachers Guide",callback_data='edut')
    ref = types.InlineKeyboardButton("📓 Reference Book",callback_data='edutref')
    all_btn.add(edu, edut, ref)
    return all_btn

def edit_profile(id:int,lang):
    all_btn = types.InlineKeyboardMarkup(row_width=2)
    edit_fname = types.InlineKeyboardButton("🙍‍♂️ Edit Name",callback_data='fname')
    edit_username = types.InlineKeyboardButton("💲 Edit Username",callback_data='_username')
    edit_bio = types.InlineKeyboardButton("🎈 Edit Bio",callback_data='bio')
    back = types.InlineKeyboardButton(text="🔙 Back" if lang == 'en' else "🔙 ተመለስ",callback_data='back_edit')
    gender = types.InlineKeyboardButton(f"🚻 Edit Gender",callback_data='gender')
    all_btn.add(edit_fname, edit_username, edit_bio, gender, back)
    return all_btn

def cashout_btn(user_id):
    btn = types.InlineKeyboardMarkup()
    btn.add(types.InlineKeyboardButton("✔ Transfer done", callback_data=f'cout_done:{user_id}'))
    return btn


def question_btn(q_id):
    all_btn = types.InlineKeyboardMarkup(row_width=5)
    approve = types.InlineKeyboardButton(text="⏫ Approve", callback_data=f'uq_approve_{q_id}')
    disapp =types.InlineKeyboardButton(text="⏬ Decline", callback_data=f'uq_decline_{q_id}')
    all_btn.add(approve, disapp)
    return all_btn

def on_comment(post_id, comment_id):
    all_btn = types.InlineKeyboardMarkup(row_width=3)
    send = types.InlineKeyboardButton(text="✅", callback_data=f'ucomments_{post_id}_{comment_id}')
    edit = types.InlineKeyboardButton(text="✍", callback_data=f'ucommente_{post_id}_{comment_id}')
    delete = types.InlineKeyboardButton(text="🗑", callback_data=f'ucommentd_{post_id}_{comment_id}')
    all_btn.add(send, edit, delete)
    return all_btn


def members_button(max_id: int, curret_row: int):
    btn = types.InlineKeyboardMarkup(row_width=5)
    btn_list, x = [], 0
    if max_id > 10:
        row_ = max_id // 10
        left = max_id % 10
        if curret_row <= 5:
            btn_list.append(types.InlineKeyboardButton(f"1" if curret_row == 1 else f"◀ 1",
                                                       callback_data=f'members_1'))
        else:
            btn_list.append(types.InlineKeyboardButton(f"⏪ 1", callback_data=f'members_1'))
        if curret_row == 1 and row_ == 1 and left:
            btn_list.append(
                types.InlineKeyboardButton(f"▶ {curret_row + 1}", callback_data=f'members_{curret_row + 1}'))
        if curret_row - 2 > row_:
            btn_list.append(
                types.InlineKeyboardButton(f"◀ {curret_row - 2}", callback_data=f'members_{curret_row - 2}'))
        if curret_row - 1 > 1:
            btn_list.append(
                types.InlineKeyboardButton(f"◀ {curret_row - 1}", callback_data=f'members_{curret_row - 1}'))

        if not curret_row == 1:
            btn_list.append(types.InlineKeyboardButton(f"{curret_row}", callback_data=f'members_{curret_row}'))
        if row_ >= curret_row or left:
            for i in range(1, 2):
                if (curret_row + i) > row_:
                    break
                btn_list.append(
                    types.InlineKeyboardButton(f"▶ {curret_row + i}", callback_data=f'members_{curret_row + i}'))
            if not curret_row == row_ and not left:
                btn_list.append(types.InlineKeyboardButton(f"⏩ {row_}" if curret_row + 5 <= row_ else f"▶ {row_}",
                                                           callback_data=f'members_{row_}'))
        if not curret_row == row_+1 and left:
            if True:
                btn_list.append(types.InlineKeyboardButton(f"⏩ {row_ + 1}" if curret_row + 5 <= row_ else f"▶ {row_ + 1}",
                                                        callback_data=f'members_{row_ + 1}'))
        if not curret_row == row_ and not left:
            if True:
                btn_list.append(types.InlineKeyboardButton(f"⏩ {row_}" if curret_row + 5 <= row_ else f"▶ {row_}",
                                                       callback_data=f'members_{row_}'))
    btn.add(*btn_list)
    return btn



def bot_setting_btn():
    btns = types.InlineKeyboardMarkup(row_width=2)
    btns.add(
        types.InlineKeyboardButton("💳 Balance", callback_data='bot:balance'),
        types.InlineKeyboardButton("📣 Channels", callback_data='bot:channels'),
        types.InlineKeyboardButton("🛃 Manage Admins", callback_data='bot:admins')

    )
    return btns

def cancel(user_lang):

    btn = types.ReplyKeyboardMarkup(resize_keyboard=True)
    can = types.KeyboardButton("❌ Cancel" if user_lang == 'en' else "❌ ሰርዝ")
    return btn.add(can)


def Panel(q_id):
    all_btn=types.InlineKeyboardMarkup()
    send = types.InlineKeyboardButton(text="✅", callback_data=f'send_{q_id}')
    edit=types.InlineKeyboardButton(text="✍", callback_data=f'edit_{q_id}')
    delete = types.InlineKeyboardButton(text="🗑", callback_data=f'del_{q_id}')
    all_btn.add(send, edit, delete)
    return all_btn

def withdraw(lang, link):
    if lang == 'am':
        txt = "t.me/share/url?url=ሰላም👋+በሀገራችን%20ውስጥ%20ለሀገራችን%20ከ7-12%ላሉ%20ተማሪዎች%20" \
          "የተሰራ%20የጥያቄና%20መልስ%20ቦት%20ያውቁ%20"\
          f"ኖሯል?%20ከታች%20በሚገኘው%20ሊንክ%20እርሶም%20ተሳታፊ%20ይሁኑ።+{link}"
    else:
        txt = 't.me/share/url?url=Hey👋+do+you+ever+know+in+our+country+for+grade+7-12+students+question+and+answer+' \
              f'platform+bot?+join+via+bellow+link+{link}'
    all_btn = types.InlineKeyboardMarkup(row_width=5)
    withdr =types.InlineKeyboardButton(text="💳 Withdraw" if lang == 'en' else "💳 ወጪ አርግ",callback_data='withdr')
    share = types.InlineKeyboardButton(text="⤴ Share" if lang == 'en' else '⤴ አጋራ', url=txt)
    bonus = types.InlineKeyboardButton(text="🎁 Bonus",callback_data='bonus')
    bt = types.InlineKeyboardButton(text="💸 Transfer Birr" if lang == 'en' else "💸 ብር አስተላልፍ",callback_data='bt')
    all_btn.add(withdr, bonus)
    all_btn.add(bt)
    all_btn.add(share)
    return all_btn

def grade(lang, type_book):
    all_btn = types.InlineKeyboardMarkup(row_width=3)
    #g6 = types.InlineKeyboardButton(text="6️⃣",callback_data='g6')
    g7 = types.InlineKeyboardButton(text="7",callback_data=f'grade_7_{type_book}')
    g8 = types.InlineKeyboardButton(text="8",callback_data=f'grade_8_{type_book}')
    g9 = types.InlineKeyboardButton(text="9",callback_data=f'grade_9_{type_book}')
    g10 = types.InlineKeyboardButton(text="10",callback_data=f'grade_10_{type_book}')
    g11 = types.InlineKeyboardButton(text="11",callback_data=f'grade_11_{type_book}')
    g12 = types.InlineKeyboardButton(text="12",callback_data=f'grade_12_{type_book}')
    back=types.InlineKeyboardButton(text="🔙 Back" if lang == 'en' else "🔙 ተመለስ",callback_data='backgrade')
    all_btn.add(g7,g8,g9)
    all_btn.add(g10,g11,g12)
    all_btn.add(back)
    return all_btn

def comment_btn(post_id, c_id):
    all_btn=types.InlineKeyboardMarkup(row_width=3)
    send = types.InlineKeyboardButton(text="✅",callback_data=f'sendcom_{post_id}_{c_id}')
    edit=types.InlineKeyboardButton(text="✍",callback_data=f'editcom_{post_id}_{c_id}')
    delete = types.InlineKeyboardButton(text="🗑",callback_data=f'delcom_{post_id}_{c_id}')
    all_btn.add(send, edit, delete)
    return all_btn

def subject_btn(lang):
    all_btn = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    en = types.KeyboardButton("🇬🇧 English")
    am = types.KeyboardButton("🇪🇹 አማርኛ")
    chem = types.KeyboardButton("🧪 Chemistry")
    math = types.KeyboardButton("🧮 Math")
    phy = types.KeyboardButton("🔭 Physics")
    geo = types.KeyboardButton("🧭 Geography")
    his = types.KeyboardButton("🌏 History")
    ict = types.KeyboardButton("💻 ICT")
    bio = types.KeyboardButton("🔬 Biology")
    civ = types.KeyboardButton("⚖ Civics")
    hep = types.KeyboardButton("⚽️ HPE")
    can = types.KeyboardButton("❌ Cancel" if lang =='en' else "❌ ሰርዝ")
    all_btn.add(math, phy, chem, bio, ict, geo, civ, his, hep, en, am, can)
    return all_btn

def amounts(lang):
    all_btn = types.InlineKeyboardMarkup(row_width=2)
    _5 = types.InlineKeyboardButton(text="5 Birr", callback_data='5-birr')
    _10 = types.InlineKeyboardButton(text="10 Birr", callback_data='10-birr')
    _15 = types.InlineKeyboardButton(text="15 Birr", callback_data='15-birr')
    _20 = types.InlineKeyboardButton(text="20 Birr", callback_data='20-birr')
    _25 = types.InlineKeyboardButton(text="25 Birr", callback_data='25-birr')
    _50 = types.InlineKeyboardButton(text="50 Birr", callback_data='50-birr')
    _75 = types.InlineKeyboardButton(text="75 Birr", callback_data='75-birr')
    _100 = types.InlineKeyboardButton(text="100 Birr", callback_data='100-birr')
    back = types.InlineKeyboardButton(text="🔙 Back" if lang == 'en' else "🔙 ተመለስ", callback_data='backwithdr')
    all_btn.add(_15, _20, _25, _50, _75, _100)
    #all_btn.add(_20,_25,_50)
    #all_btn.add(_75,_100)
    all_btn.add(back)
    return all_btn

def answer_btn(q_id, ans_id):
    all_btn = types.InlineKeyboardMarkup(row_width=3)
    send = types.InlineKeyboardButton(text="✅", callback_data=f'SendAnswer_{q_id}_{ans_id}')
    edit = types.InlineKeyboardButton(text="✍", callback_data=f'EditAnswer_{q_id}_{ans_id}')
    delete = types.InlineKeyboardButton(text="🗑", callback_data=f'DelAnswer_{q_id}_{ans_id}')
    all_btn.add(send, edit, delete)
    return all_btn

def bscancel():
    btn = types.InlineKeyboardMarkup()
    btn.add(types.InlineKeyboardButton("🚫 Cancel", callback_data='bscancel'))
    return btn

def oncomment(user_id, post_id, comment_id, msg_id):
    btn = types.InlineKeyboardMarkup()
    btn.add(
        types.InlineKeyboardButton("↩ Reply", callback_data=f'creply:{user_id}:{post_id}:{comment_id}:{msg_id}'),
        types.InlineKeyboardButton("⚠ Report", callback_data=f'creport:{user_id}')
    )
    return btn

def admin_permision_btn(user_id, stat, **kwargs):
    btn = types.InlineKeyboardMarkup(row_width=2)
    btn.add(*[types.InlineKeyboardButton("📝 Message ✅" if kwargs.get(user_id, {}).get("send_message")
                                         else "📝 Message ❌", callback_data=f'admin:send_message:{user_id}'),
              types.InlineKeyboardButton("Approve  ✅" if kwargs.get(user_id, {}).get("approve_questions")
                                         else "Approve ❌", callback_data=f'admin:approve_questions:{user_id}'),
              types.InlineKeyboardButton("💭 Feedback ✅" if kwargs.get(user_id,{}).get("feedback") else "💭 Feedback ❌",
                                         callback_data=f'admin:feedback:{user_id}'),
              types.InlineKeyboardButton("🚷 Ban ✅" if kwargs.get(user_id,{}).get("ban_user") else "🚷 Ban ❌",
                                         callback_data=f'admin:ban_user:{user_id}'),
              types.InlineKeyboardButton("🛠 Manage ✅" if kwargs.get(user_id, {}).get("manage_setting") else "🛠 Manage ❌",
                                         callback_data=f'admin:manage_setting:{user_id}'),
              types.InlineKeyboardButton(
                  "👤 Profile ✅" if kwargs.get(user_id, {}).get("can_see") else "👤 Profile ❌",
                  callback_data=f'admin:can_see:{user_id}'),
              types.InlineKeyboardButton("➖ Remove", callback_data=f'admin:remove:{user_id}'),
              ]
            )

    info = []
    try:
        for key in kwargs.get(user_id):
            info.append(
    kwargs.get(user_id, {}).get(key))
    except:
        info.append(False)
    if not False in info:
              types.InlineKeyboardButton("👨‍💻 Ownership", callback_data=f'admin:owner:{user_id}')
    if not stat == 'admin':
        btn.add(types.InlineKeyboardButton("✅ Done", callback_data=f'admin:done:{user_id}'))
    else:
        btn.add(types.InlineKeyboardButton("🔙 Back", callback_data=f'admin:back:{user_id}'))

    return btn

def channel_btn(channel_id, **kwargs):
    btn = types.InlineKeyboardMarkup(row_width=2)
    btn.add(
        types.InlineKeyboardButton("Message ✅" if kwargs.get(channel_id, {}).get('send_message') else "Message ❌",
                                   callback_data=f"myc:{channel_id}:send_message"),
        types.InlineKeyboardButton("Approve ✅" if kwargs.get(channel_id, {}).get('approve') else "Approve ❌",
                               callback_data=f"myc:{channel_id}:approve"),
        types.InlineKeyboardButton("Join ✅" if kwargs.get(channel_id, {}).get('force_join') else "Join ❌",
                                   callback_data=f'myc:{channel_id}:force_join'),
    )
    btn.add(
        types.InlineKeyboardButton("➖ Remove", callback_data=f"myc:{channel_id}:remove"),
        types.InlineKeyboardButton("🔙 Back", callback_data=f'myc:{channel_id}:back')
    )
    return btn

subj = ["🇬🇧 English", "🇪🇹 አማርኛ", "🧪 Chemistry", "🧮 Math", "🔭 Physics", "⚽️ HPE", "🔬 Biology", "💻 ICT", "🌏 History",
      "🧭 Geography", "⚖ Civics"]

am_btns = ["📚መጽሐፍት", "🙋‍♂ የኔ ጥያቄዎች", "👨‍👩‍👦‍👦 ጋብዝ","⚙️ ቅንብሮች", "🗣 ጥያቄ ጠይቅ", "💬 አስታየት"]

en_btns = ["🙋‍♂ My Questions", "📚 Books", "💬 Feedback", "👨‍👩‍👦‍👦 Invite", "⚙️ Settings", "🗣 Ask Question"]
