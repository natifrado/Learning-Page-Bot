import random
import string
import hashlib

hash = hashlib.md5()

lower = string.ascii_lowercase
upper = string.ascii_uppercase
nums = string.digits
def account_link():
    acc_link = ''
    acc_link += lower
    acc_link += nums
    link = "".join(random.sample(acc_link,25))
    hash.update(b'%s'%link.encode('utf-8'))
    return hash.hexdigest()

def invite_link(id: int):

    return f'i{id}'

def verification_code():
    ver_code = ''
    ver_code+=nums
    code="".join(random.sample(ver_code,6))
    return code

def question_link():
    
    acc_link = ''
    acc_link+=lower
    acc_link+=upper
    acc_link+=nums
    link="".join(random.sample(acc_link, 32))
    hash.update(link.encode('utf-8'))
    return hash.hexdigest()

def comment_link(id_):
    id_ = str(id(id_))
    hash.update(id_.encode('utf-8'))
    return hash.hexdigest()[:20]

def comment_hash_link():
    acc_link = ''
    acc_link += lower
    acc_link += upper
    acc_link += nums
    link = "".join(random.sample(acc_link, 32))
    hash.update(link.encode('utf-8'))
    return hash.hexdigest()[:24]


def browse_link():
    acc_link = ''
    acc_link+=lower
    acc_link+=upper
    acc_link+=nums
    link = "".join(random.sample(acc_link, 20))
    hash.update(link.encode('utf-8'))
    return hash.hexdigest()

def answer_link():
    acc_link = ''
    acc_link+=lower
    acc_link+=upper
    acc_link+=nums
    link = "".join(random.sample(acc_link, 20))
    hash.update(link.encode('utf-8'))
    return hash.hexdigest()
