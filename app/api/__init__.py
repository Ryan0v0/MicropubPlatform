from flask import Blueprint

bp = Blueprint('api', __name__)

# 写在最后是为了防止循环导入，ping.py文件也会导入 bp
from app.api import ping, tokens, errors, roles, users, micropub, notifications, messages, \
    tags, microcon, comments, recommend
# from app.api import recommend