import base64
from datetime import datetime, timedelta
from hashlib import md5
import json
import jwt
from time import time
from werkzeug.security import generate_password_hash, check_password_hash
from flask import url_for, current_app
from app.extensions import db


class PaginatedAPIMixin(object):
    @staticmethod
    def to_collection_dict(query, page, per_page, endpoint, **kwargs):
        # 如果当前没有任何资源时，或者前端请求的 page 越界时，都会抛出 404 错误
        # 由 @bp.app_errorhandler(404) 自动处理，即响应 JSON 数据：{ error: "Not Found" }
        resources = query.paginate(page, per_page)
        data = {
            'items': [item.to_dict() for item in resources.items],
            '_meta': {
                'page': page,
                'per_page': per_page,
                'total_pages': resources.pages,
                'total_items': resources.total
            },
            '_links': {
                'self': url_for(endpoint, page=page, per_page=per_page,
                                **kwargs),
                'next': url_for(endpoint, page=page + 1, per_page=per_page,
                                **kwargs) if resources.has_next else None,
                'prev': url_for(endpoint, page=page - 1, per_page=per_page,
                                **kwargs) if resources.has_prev else None
            }
        }
        return data


# 粉丝关注他人
followers = db.Table(
    'followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('timestamp', db.DateTime, default=datetime.utcnow)
)

# 黑名单(user_id 屏蔽 block_id)
blacklist = db.Table(
    'blacklist',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('block_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('timestamp', db.DateTime, default=datetime.utcnow)
)

# 引用微知识
micropubs_likes = db.Table(
    'micropubs_likes',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('micropub_id', db.Integer, db.ForeignKey('micropubs.id')),
    db.Column('timestamp', db.DateTime, default=datetime.utcnow)
)


class User(PaginatedAPIMixin, db.Model):
    # 设置数据库表名，Micropub模型中的外键 user_id 会引用 users.id
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))  # 不保存原始密码
    name = db.Column(db.String(64))
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text())
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    # 反向引用，直接查询出当前用户的所有博客微知识; 同时，Micropub实例中会有 author 属性
    # cascade 用于级联删除，当删除user时，该user下面的所有micropubs都会被级联删除
    micropubs = db.relationship('Micropub', backref='author', lazy='dynamic',
                            cascade='all, delete-orphan')
    # followeds 是该用户关注了哪些用户列表
    # followers 是该用户的粉丝列表
    followeds = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')
    # 用户最后一次查看 用户的粉丝 页面的时间，用来判断哪些粉丝是新的
    last_follows_read_time = db.Column(db.DateTime)
    # 用户最后一次查看 收到的微知识被引用 页面的时间，用来判断哪些引用是新的
    last_micropubs_likes_read_time = db.Column(db.DateTime)
    # 用户最后一次查看 关注的人的博客 页面的时间，用来判断哪些微知识是新的
    last_followeds_micropubs_read_time = db.Column(db.DateTime)
    # 用户的通知
    notifications = db.relationship('Notification', backref='user',
                                    lazy='dynamic', cascade='all, delete-orphan')
    # 用户发送的私信
    messages_sent = db.relationship('Message', foreign_keys='Message.sender_id',
                                    backref='sender', lazy='dynamic',
                                    cascade='all, delete-orphan')
    # 用户接收的私信
    messages_received = db.relationship('Message',
                                        foreign_keys='Message.recipient_id',
                                        backref='recipient', lazy='dynamic',
                                        cascade='all, delete-orphan')
    # 用户最后一次查看私信的时间
    last_messages_read_time = db.Column(db.DateTime)
    # harassers 骚扰者(被拉黑的人)
    # sufferers 受害者
    harassers = db.relationship(
        'User', secondary=blacklist,
        primaryjoin=(blacklist.c.user_id == id),
        secondaryjoin=(blacklist.c.block_id == id),
        backref=db.backref('sufferers', lazy='dynamic'), lazy='dynamic')
    # 用户注册后，需要先确认邮箱
    confirmed = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        '''设置用户密码，保存为 Hash 值'''
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        '''验证密码与保存的 Hash 值是否匹配'''
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        '''用户头像'''
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(digest, size)

    def to_dict(self, include_email=False):
        data = {
            'id': self.id,
            'username': self.username,
            'name': self.name,
            'location': self.location,
            'about_me': self.about_me,
            'member_since': self.member_since.isoformat() + 'Z',
            'last_seen': self.last_seen.isoformat() + 'Z',
            'followeds_count': self.followeds.count(),
            'followers_count': self.followers.count(),
            'micropubs_count': self.micropubs.count(),
            'followeds_micropubs_count': self.followeds_micropubs().count(),
            'confirmed': self.confirmed,
            '_links': {
                'self': url_for('api.get_user', id=self.id),
                'avatar': self.avatar(128),
                'followeds': url_for('api.get_followeds', id=self.id),
                'followers': url_for('api.get_followers', id=self.id),
                'micropubs': url_for('api.get_user_micropubs', id=self.id),
                'followeds_micropubs': url_for('api.get_user_followeds_micropubs', id=self.id)
            }
        }
        if include_email:
            data['email'] = self.email
        return data

    def from_dict(self, data, new_user=False):
        for field in ['username', 'email', 'name', 'location', 'about_me']:
            if field in data:
                setattr(self, field, data[field])
        if new_user and 'password' in data:
            self.set_password(data['password'])

    def ping(self):
        '''更新用户的最后访问时间'''
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    def get_jwt(self, expires_in=3600):
        '''用户登录后，发放有效的 JWT'''
        now = datetime.utcnow()
        payload = {
            'user_id': self.id,
            'confirmed': self.confirmed,
            'user_name': self.name if self.name else self.username,
            'user_avatar': base64.b64encode(self.avatar(24).
                                            encode('utf-8')).decode('utf-8'),
            'exp': now + timedelta(seconds=expires_in),
            'iat': now
        }
        return jwt.encode(
            payload,
            current_app.config['SECRET_KEY'],
            algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_jwt(token):
        '''验证 JWT 的有效性'''
        try:
            payload = jwt.decode(
                token,
                current_app.config['SECRET_KEY'],
                algorithms=['HS256'])
        except (jwt.exceptions.ExpiredSignatureError,
                jwt.exceptions.InvalidSignatureError,
                jwt.exceptions.DecodeError) as e:
            # Token过期，或被人修改，那么签名验证也会失败
            return None
        return User.query.get(payload.get('user_id'))

    def is_following(self, user):
        '''判断当前用户是否已经关注了 user 这个用户对象，如果关注了，下面表达式左边是1，否则是0'''
        return self.followeds.filter(
            followers.c.followed_id == user.id).count() > 0

    def follow(self, user):
        '''当前用户开始关注 user 这个用户对象'''
        if not self.is_following(user):
            self.followeds.append(user)

    def unfollow(self, user):
        '''当前用户取消关注 user 这个用户对象'''
        if self.is_following(user):
            self.followeds.remove(user)

    def followeds_micropubs(self):
        '''获取当前用户的关注者的所有博客列表'''
        followed = Micropub.query.join(
            followers, (followers.c.followed_id == Micropub.author_id)).filter(
                followers.c.follower_id == self.id)
        # 包含当前用户自己的博客列表
        # own = Micropub.query.filter_by(user_id=self.id)
        # return followed.union(own).order_by(Micropub.timestamp.desc())
        return followed.order_by(Micropub.timestamp.desc())

    def add_notification(self, name, data):
        '''给用户实例对象增加通知'''
        # 如果具有相同名称的通知已存在，则先删除该通知
        self.notifications.filter_by(name=name).delete()
        # 为用户添加通知，写入数据库
        n = Notification(name=name, payload_json=json.dumps(data), user=self)
        db.session.add(n)
        return n

    def new_follows(self):
        '''用户的新粉丝计数'''
        last_read_time = self.last_follows_read_time or datetime(1900, 1, 1)
        return self.followers.filter(followers.c.timestamp > last_read_time).count()

    def new_followeds_micropubs(self):
        '''用户关注的人的新发布的微知识计数'''
        last_read_time = self.last_followeds_micropubs_read_time or datetime(1900, 1, 1)
        return self.followeds_micropubs().filter(Micropub.timestamp > last_read_time).count()

    def new_recived_messages(self):
        '''用户未读的私信计数'''
        last_read_time = self.last_messages_read_time or datetime(1900, 1, 1)
        return Message.query.filter_by(recipient=self).filter(
            Message.timestamp > last_read_time).count()

    def is_blocking(self, user):
        '''判断当前用户是否已经拉黑了 user 这个用户对象，如果拉黑了，下面表达式左边是1，否则是0'''
        return self.harassers.filter(
            blacklist.c.block_id == user.id).count() > 0

    def block(self, user):
        '''当前用户开始拉黑 user 这个用户对象'''
        if not self.is_blocking(user):
            self.harassers.append(user)

    def unblock(self, user):
        '''当前用户取消拉黑 user 这个用户对象'''
        if self.is_blocking(user):
            self.harassers.remove(user)

    def new_micropubs_likes(self):
        '''用户收到的微知识被引用的新计数'''
        last_read_time = self.last_micropubs_likes_read_time or datetime(1900, 1, 1)
        # 当前用户发布的微知识当中，哪些微知识被引用了
        micropubs = self.micropubs.join(micropubs_likes).all()
        # 新的引用记录计数
        new_likes_count = 0
        for p in micropubs:
            # 获取引用时间
            for u in p.likers:
                if u != self:  # 用户自己引用自己的微知识不需要被通知
                    res = db.engine.execute("select * from micropubs_likes where user_id={} and micropub_id={}".format(u.id, p.id))
                    timestamp = datetime.strptime(list(res)[0][2], '%Y-%m-%d %H:%M:%S.%f')
                    # 判断本条引用记录是否为新的
                    if timestamp > last_read_time:
                        new_likes_count += 1
        return new_likes_count

    def generate_confirm_jwt(self, expires_in=3600):
        '''生成确认账户的 JWT'''
        now = datetime.utcnow()
        payload = {
            'confirm': self.id,
            'exp': now + timedelta(seconds=expires_in),
            'iat': now
        }
        return jwt.encode(
            payload,
            current_app.config['SECRET_KEY'],
            algorithm='HS256').decode('utf-8')

    def verify_confirm_jwt(self, token):
        '''用户点击确认邮件中的URL后，需要检验 JWT，如果检验通过，则把新添加的 confirmed 属性设为 True'''
        try:
            payload = jwt.decode(
                token,
                current_app.config['SECRET_KEY'],
                algorithms=['HS256'])
        except (jwt.exceptions.ExpiredSignatureError,
                jwt.exceptions.InvalidSignatureError,
                jwt.exceptions.DecodeError) as e:
            # Token过期，或被人修改，那么签名验证也会失败
            return False
        if payload.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def generate_reset_password_jwt(self, expires_in=3600):
        '''生成重置账户密码的 JWT'''
        now = datetime.utcnow()
        payload = {
            'reset_password': self.id,
            'exp': now + timedelta(seconds=expires_in),
            'iat': now
        }
        return jwt.encode(
            payload,
            current_app.config['SECRET_KEY'],
            algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_reset_password_jwt(token):
        '''用户点击重置密码邮件中的URL后，需要检验 JWT
        如果检验通过，则返回 JWT 中存储的 id 所对应的用户实例'''
        try:
            payload = jwt.decode(
                token,
                current_app.config['SECRET_KEY'],
                algorithms=['HS256'])
        except (jwt.exceptions.ExpiredSignatureError,
                jwt.exceptions.InvalidSignatureError,
                jwt.exceptions.DecodeError) as e:
            # Token过期，或被人修改，那么签名验证也会失败
            return None
        return User.query.get(payload.get('reset_password'))


class Micropub(PaginatedAPIMixin, db.Model):
    __tablename__ = 'micropubs'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    summary = db.Column(db.Text)
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    views = db.Column(db.Integer, default=0)
    # 外键, 直接操纵数据库当user下面有micropubs时不允许删除user，下面仅仅是 ORM-level “delete” cascade
    # db.ForeignKey('users.id', ondelete='CASCADE') 会同时在数据库中指定 FOREIGN KEY level “ON DELETE” cascade
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    # 博客微知识与引用/收藏它的人是多对多关系
    likers = db.relationship('User', secondary=micropubs_likes, backref=db.backref('liked_micropubs', lazy='dynamic'), lazy='dynamic')

    def __repr__(self):
        return '<Micropub {}>'.format(self.title)

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        '''
        target: 有监听事件发生的 Micropub 实例对象
        value: 监听哪个字段的变化
        '''
        if not target.summary:  # 如果前端不填写摘要，是空str，而不是None
            target.summary = value[:200] + '  ... ...'  # 截取 body 字段的前200个字符给 summary

    def to_dict(self):
        data = {
            'id': self.id,
            'title': self.title,
            'summary': self.summary,
            'body': self.body,
            'timestamp': self.timestamp,
            'views': self.views,
            'likers_id': [user.id for user in self.likers],
            'likers': [
                {
                    'id': user.id,
                    'username': user.username,
                    'name': user.name,
                    'avatar': user.avatar(128)
                } for user in self.likers
            ],
            'author': {
                'id': self.author.id,
                'username': self.author.username,
                'name': self.author.name,
                'avatar': self.author.avatar(128)
            },
            'likers_count': self.likers.count(),
            '_links': {
                'self': url_for('api.get_micropub', id=self.id),
                'author_url': url_for('api.get_user', id=self.author_id)
            }
        }
        return data

    def from_dict(self, data):
        for field in ['title', 'summary', 'body', 'timestamp', 'views']:
            if field in data:
                setattr(self, field, data[field])

    def is_liked_by(self, user):
        '''判断用户 user 是否已经收藏过该微知识'''
        return user in self.likers

    def liked_by(self, user):
        '''收藏'''
        if not self.is_liked_by(user):
            self.likers.append(user)

    def unliked_by(self, user):
        '''取消收藏'''
        if self.is_liked_by(user):
            self.likers.remove(user)


db.event.listen(Micropub.body, 'set', Micropub.on_changed_body)  # body 字段有变化时，执行 on_changed_body() 方法

class Notification(db.Model):  # 不需要分页
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    timestamp = db.Column(db.Float, index=True, default=time)
    payload_json = db.Column(db.Text)

    def __repr__(self):
        return '<Notification {}>'.format(self.id)

    def get_data(self):
        return json.loads(str(self.payload_json))

    def to_dict(self):
        data = {
            'id': self.id,
            'name': self.name,
            'user': {
                'id': self.user.id,
                'username': self.user.username,
                'name': self.user.name,
                'avatar': self.user.avatar(128)
            },
            'timestamp': self.timestamp,
            'payload': self.get_data(),
            '_links': {
                'self': url_for('api.get_notification', id=self.id),
                'user_url': url_for('api.get_user', id=self.user_id)
            }
        }
        return data

    def from_dict(self, data):
        for field in ['body', 'timestamp']:
            if field in data:
                setattr(self, field, data[field])


class Message(PaginatedAPIMixin, db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def __repr__(self):
        return '<Message {}>'.format(self.id)

    def to_dict(self):
        data = {
            'id': self.id,
            'body': self.body,
            'timestamp': self.timestamp,
            'sender': self.sender.to_dict(),
            'recipient': self.recipient.to_dict(),
            '_links': {
                'self': url_for('api.get_message', id=self.id),
                'sender_url': url_for('api.get_user', id=self.sender_id),
                'recipient_url': url_for('api.get_user', id=self.recipient_id)
            }
        }
        return data

    def from_dict(self, data):
        for field in ['body', 'timestamp']:
            if field in data:
                setattr(self, field, data[field])
