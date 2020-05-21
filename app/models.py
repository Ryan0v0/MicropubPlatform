import base64
from datetime import datetime, timedelta
from hashlib import md5
import json
import jwt
from time import time
from werkzeug.security import generate_password_hash, check_password_hash
from flask import url_for, current_app
from app.extensions import db, whooshee
from app.utils.elasticsearch import add_to_index, remove_from_index, query_index, es_highlight
from sqlalchemy import text


class SearchableMixin(object):
    @classmethod
    def search(cls, query, page, per_page, ids=None):
        total, hits, highlights = query_index(cls.__tablename__, query, page, per_page, ids)

        if total == 0:
            return 0, cls.query.filter_by(id=0)  # 如果没有匹配到搜索词，则故意返回空的 BaseQuery

        hit_ids = []  # 匹配到的记录，id 列表
        when = []
        for i in range(len(hits)):
            hit_ids.append(hits[i][0])
            when.append((hits[i][0], i))
        # 将 hit_ids 列表转换成对应排序顺序(ES搜索得分高排在前面)的 BaseQuery，请参考: https://stackoverflow.com/questions/6332043/sql-order-by-multiple-values-in-specific-order/6332081#6332081
        hits_basequery = cls.query.filter(cls.id.in_(hit_ids)).order_by(db.case(when, value=cls.id))
        # 再遍历 BaseQuery，将要搜索的字段值中关键词高亮
        for obj in hits_basequery:
            for field, need_highlight in obj.__searchable__:
                if need_highlight:  # 只有设置为 True 的字段才高亮关键字
                    source = getattr(obj, field)  # 原字段的值
                    highlight_source = es_highlight(source, highlights)  # 关键字高亮后的字段值
                    setattr(obj, field, highlight_source)

        return total, hits_basequery

    @classmethod
    def receive_after_insert(cls, mapper, connection, target):
        '''监听 SQLAlchemy 'after_insert' 事件
           请参考: https://docs.sqlalchemy.org/en/13/orm/events.html#mapper-events
           add_to_index(target.__tablename__, target)
        '''

    @classmethod
    def before_commit(cls, session):
        session._changes = {
            'update': list(session.dirty)
        }

    @classmethod
    def after_commit(cls, session):
        for obj in session._changes['update']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        session._changes = None

    @classmethod
    def receive_after_delete(cls, mapper, connection, target):
        # 监听 SQLAlchemy 'after_delete' 事件
        remove_from_index(target.__tablename__, target)

    @classmethod
    def reindex(cls):
        # 刷新指定数据模型中的所有数据的索引
        for obj in cls.query:
            add_to_index(cls.__tablename__, obj)


db.event.listen(db.session, 'before_commit', SearchableMixin.before_commit)
db.event.listen(db.session, 'after_commit', SearchableMixin.after_commit)



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
    db.Column('timestamp', db.DateTime, default=datetime.now)
)

# 评论点赞
comments_likes = db.Table(
    'comments_likes',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('comment_id', db.Integer, db.ForeignKey('comments.id')),
    db.Column('timestamp', db.DateTime, default=datetime.now)
)

# 黑名单(user_id 屏蔽 block_id)
blacklist = db.Table(
    'blacklist',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('block_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('timestamp', db.DateTime, default=datetime.now)
)

# 点赞微知识
micropubs_likes = db.Table(
    'micropubs_likes',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('micropub_id', db.Integer, db.ForeignKey('micropubs.id')),
    db.Column('timestamp', db.DateTime, default=datetime.now)
)

# 收藏微知识
micropubs_collects = db.Table(
    'micropubs_collects',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('micropub_id', db.Integer, db.ForeignKey('micropubs.id')),
    db.Column('timestamp', db.DateTime, default=datetime.now)
)

# 点赞微猜想
microcons_likes = db.Table(
    'microcons_likes',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('microcon_id', db.Integer, db.ForeignKey('microcons.id')),
    db.Column('timestamp', db.DateTime, default=datetime.now)
)

# 收藏微猜想
microcons_collects = db.Table(
    'microcons_collects',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('microcon_id', db.Integer, db.ForeignKey('microcons.id')),
    db.Column('timestamp', db.DateTime, default=datetime.now)
)

# 微猜想引用微证据
microcons_micropubs = db.Table(
    'microcons_micropubs',
    db.Column('micropub_id', db.Integer, db.ForeignKey('micropubs.id')),
    db.Column('microcon_id', db.Integer, db.ForeignKey('microcons.id')),
    db.Column('timestamp', db.DateTime, default=datetime.now)
)

# 通过微猜想
microcons_pros = db.Table(
    'microcons_pors',
    db.Column('microcon_id', db.Integer, db.ForeignKey('microcons.id')),
    db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('timestamp', db.DateTime, default=datetime.now),
    db.Column('reason', db.String(255))
)

# 否决微猜想
microcons_cons = db.Table(
    'microcons_cons',
    db.Column('microcon_id', db.Integer, db.ForeignKey('microcons.id')),
    db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('timestamp', db.DateTime, default=datetime.now),
    db.Column('reason', db.String(255))
)

# 标签如何新建？？
@whooshee.register_model('content')
class Tag(db.Model):
    __tablename__ = 'tags'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(64), index=True)
    micropub_id = db.Column(db.Integer, db.ForeignKey('micropubs.id'))
    microcon_id = db.Column(db.Integer, db.ForeignKey('microcons.id'))

    def __repr__(self):
        return '<Tag {}>'.format(self.content)

    def to_dict(self):
        data = {
            'id': self.id,
            'content': self.content,
            'micropub_id': self.micropub_id,
            '_links': {
                'self': url_for('api.get_tag', id=self.id),
                'micropub': url_for('api.get_micropub', id=self.micropub_id),
            }
        }
        return data

    def from_dict(self, data):
        if 'content' in data:
            setattr(self, 'content', data['content'])

class Permission:
    '''权限认证中的各种操作，对应二进制的位，比如
    FOLLOW: 0b00000001，转换为十六进制为 0x01
    COMMENT: 0b00000010，转换为十六进制为 0x02
    WRITE: 0b00000100，转换为十六进制为 0x04
    SPONSOR: 0b00001000, 转换为十六进制为 0x08
    ADMIN: 0b10000000，转换为十六进制为 0x80

    中间还预留了第 4、5、6、7 共4位二进制位，以备后续增加操作权限
    '''
    # 关注其它用户的权限
    FOLLOW = 0x01
    # 发表评论、评论点赞与踩的权限
    COMMENT = 0x02
    # 撰写微知识的权限
    WRITE = 0x04
    # 管理网站的权限(对应管理员角色)
    ADMIN = 0x80
    # 发起微话题的权限(对应赞助商角色)
    SPONSOR = 0x08

class Role(PaginatedAPIMixin, db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(255), unique=True)
    name = db.Column(db.String(255))  # 角色名称
    default = db.Column(db.Boolean, default=False, index=True)  # 当新增用户时，是否将当前角色作为默认角色赋予新用户
    permissions = db.Column(db.Integer)  # 角色拥有的权限，各操作对应一个二进制位，能执行某项操作的角色，其位会被设为 1
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __init__(self, **kwargs):
        super(Role, self).__init__(**kwargs)
        if self.permissions is None:
            self.permissions = 0

    @staticmethod
    def insert_roles():
        '''应用部署时，应该主动执行此函数，添加以下角色
        注意: 未登录的用户，可以浏览，但不能评论或点赞等
        shutup:        0b0000 0000 (0x00) 用户被关小黑屋，收回所有权限
        reader:        0b0000 0011 (0x03) 读者，可以关注别人、评论与点赞，但不能发表微知识
        author:        0b0000 0111 (0x07) 作者，可以关注别人、评论与点赞，发表微知识
        administrator: 0b1000 0111 (0x87) 超级管理员，拥有全部权限
        sponsor:       0b0000 1011 (0x0B) 赞助商，可以关注别人、评论与点赞，但不能发表微知识，另外可以发起微话题
        以后如果要想添加新角色，或者修改角色的权限，修改 roles 数组，再运行函数即可
        '''
        roles = {
            'shutup': ('小黑屋', ()),
            'reader': ('读者', (Permission.FOLLOW, Permission.COMMENT)),
            'author': ('作者', (Permission.FOLLOW, Permission.COMMENT, Permission.WRITE)),
            'administrator': ('管理员', (Permission.FOLLOW, Permission.COMMENT, Permission.WRITE, Permission.ADMIN)),
            'sponsor': ('赞助商', (Permission.FOLLOW, Permission.COMMENT, Permission.SPONSOR))
        }
        default_role = 'author'
        for r in roles:  # r 是字典的键
            role = Role.query.filter_by(slug=r).first()
            if role is None:
                role = Role(slug=r, name=roles[r][0])
            role.reset_permissions()
            for perm in roles[r][1]:
                role.add_permission(perm)
            role.default = (role.slug == default_role)
            db.session.add(role)
        db.session.commit()

    def reset_permissions(self):
        self.permissions = 0

    def has_permission(self, perm):
        return self.permissions & perm == perm

    def add_permission(self, perm):
        if not self.has_permission(perm):
            self.permissions += perm

    def remove_permission(self, perm):
        if self.has_permission(perm):
            self.permissions -= perm

    def get_permissions(self):
        '''获取角色的具体操作权限列表'''
        p = [(Permission.FOLLOW, 'follow'), (Permission.COMMENT, 'comment'), (Permission.WRITE, 'write'),
             (Permission.ADMIN, 'admin'), (Permission.SPONSOR, 'sponsor')]
        # 过滤掉没有权限，注意不能用 for 循环，因为遍历列表时删除元素可能结果并不是你想要的，参考: https://segmentfault.com/a/1190000007214571
        new_p = filter(lambda x: self.has_permission(x[0]), p)
        return ','.join([x[1] for x in new_p])  # 用逗号拼接成str

    def to_dict(self):
        data = {
            'id': self.id,
            'slug': self.slug,
            'name': self.name,
            'default': self.default,
            'permissions': self.permissions,
            '_links': {
                'self': url_for('api.get_role', id=self.id)
            }
        }
        return data

    def from_dict(self, data):
        for field in ['slug', 'name', 'permissions']:
            if field in data:
                setattr(self, field, data[field])

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<Role {}>'.format(self.name)

@whooshee.register_model('username', 'name', 'about_me')
class User(PaginatedAPIMixin, db.Model):
    # 设置数据库表名，Post模型中的外键 user_id 会引用 users.id
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))  # 不保存原始密码
    name = db.Column(db.String(64))
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text())
    member_since = db.Column(db.DateTime(), default=datetime.now)
    last_seen = db.Column(db.DateTime(), default=datetime.now)
    # 反向引用，直接查询出当前用户的所有博客微知识; 同时，Post实例中会有 author 属性
    # cascade 用于级联删除，当删除user时，该user下面的所有micropubs都会被级联删除
    micropubs = db.relationship('Micropub', backref='author', lazy='dynamic',
                                cascade='all, delete-orphan')
    microcons = db.relationship('Microcon', backref='author', lazy='dynamic',
                                cascade='all, delete-orphan')

    # followeds 是该用户关注了哪些用户列表
    # followers 是该用户的粉丝列表
    followeds = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')
    # 用户发表的评论列表
    comments = db.relationship('Comment', backref='author', lazy='dynamic',
                               cascade='all, delete-orphan')
    # 用户最后一次查看 收到的评论 页面的时间，用来判断哪些收到的评论是新的
    last_recived_comments_read_time = db.Column(db.DateTime)
    # 用户最后一次查看 用户的粉丝 页面的时间，用来判断哪些粉丝是新的
    last_follows_read_time = db.Column(db.DateTime)
    # 用户最后一次查看 收到的微知识被喜欢 页面的时间，用来判断哪些喜欢是新的
    last_micropubs_likes_read_time = db.Column(db.DateTime)
    last_microcons_likes_read_time = db.Column(db.DateTime)
    # 用户最后一次查看 收到的评论点赞 页面的时间，用来判断哪些点赞是新的
    last_comments_likes_read_time = db.Column(db.DateTime)
    # 用户最后一次查看 关注的人的博客 页面的时间，用来判断哪些微知识是新的
    last_followeds_micropubs_read_time = db.Column(db.DateTime)
    last_followeds_microcons_read_time = db.Column(db.DateTime)
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
    # 用户所属的角色
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    # 用户的RQ后台任务
    tasks = db.relationship('Task', backref='user', lazy='dynamic')

    # 用户的孵化器列表，一对多，一方
    cradles = db.relationship('Cradle', backref='sponsor',
                              lazy='dynamic', cascade='all, delete-orphan')
    # 用户在孵化器中引用的微知识列表，一对多，一方
    microknos_cites = db.relationship('MicroknosCites', backref='user',
                              lazy='dynamic', cascade='all, delete-orphan')


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
            'microcons_count': self.microcons.count(),
            'followeds_micropubs_count': self.followeds_micropubs().count(),
            'followeds_microcons_count': self.followeds_microcons().count(),
            'comments_count': self.comments.count(),
            'confirmed': self.confirmed,
            'role_id': self.role_id,
            'role_name': Role.query.get_or_404(self.role_id).name,
            '_links': {
                'self': url_for('api.get_user', id=self.id),
                'avatar': self.avatar(128),
                'followeds': url_for('api.get_followeds', id=self.id),
                'followers': url_for('api.get_followers', id=self.id),
                'micropubs': url_for('api.get_user_micropubs', id=self.id),
                'microcons': url_for('api.get_user_microcons', id=self.id),
                'followeds_microcons': url_for('api.get_user_followeds_microcons', id=self.id),
                'followeds_micropubs': url_for('api.get_user_followeds_micropubs', id=self.id),
                'comments': url_for('api.get_user_comments', id=self.id),
                'role': url_for('api.get_role', id=self.role_id)
            }
        }
        if include_email:
            data['email'] = self.email
        return data

    def from_dict(self, data, new_user=False):
        for field in ['username', 'email', 'name', 'location', 'about_me', 'confirmed', 'role_id']:
            if field in data:
                setattr(self, field, data[field])
        if new_user and 'password' in data:
            self.set_password(data['password'])
            # 新建用户时，给用户自动分配角色
            if self.role is None:
                if self.email in current_app.config['ADMINS']:
                    self.role = Role.query.filter_by(slug='administrator').first()
                else:
                    self.role = Role.query.filter_by(default=True).first()

    def ping(self):
        '''更新用户的最后访问时间'''
        self.last_seen = datetime.now()
        db.session.add(self)

    def get_jwt(self, expires_in=3600):
        '''用户登录后，发放有效的 JWT'''
        now = datetime.now()
        payload = {
            'user_id': self.id,
            'confirmed': self.confirmed,
            'user_name': self.name if self.name else self.username,
            'user_avatar': base64.b64encode(self.avatar(24).
                                            encode('utf-8')).decode('utf-8'),
            'permissions': self.role.get_permissions(),
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
        return User.query.get(payload.get('user_id')) #

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

    # 当前用户关注的用户的所有微证据列表
    def followeds_microcons(self):
        followed = Microcon.query.join(followers, (followers.c.followed_id == Microcon.author_id)). \
            filter(followers.c.follower_id == self.id)
        return followed.order_by(Microcon.timestamp.desc())

    def add_notification(self, name, data):
        '''给用户实例对象增加通知'''
        # 如果具有相同名称的通知已存在，则先删除该通知
        self.notifications.filter_by(name=name).delete()
        # 为用户添加通知，写入数据库
        n = Notification(name=name, payload_json=json.dumps(data), user=self)
        db.session.add(n)
        return n

    def new_recived_comments(self):
        '''用户收到的新评论计数
        包括:
        1. 用户的所有微知识下面新增的评论
        2. 用户发表的评论(或下面的子孙)被人回复了
        '''
        last_read_time = self.last_recived_comments_read_time or datetime(1900, 1, 1)
        # 用户发布的所有微知识
        user_micropubs_ids = [micropub.id for micropub in self.micropubs.all()]
        # 用户微知识下面的新评论, 即评论的 micropub_id 在 user_micropubs_ids 集合中，且评论的 author 不是自己(微知识的作者)
        q1 = set(Comment.query.filter(Comment.micropub_id.in_(user_micropubs_ids), Comment.author != self).all())

        # 用户发表的评论被人回复了，找到每个用户评论的所有子孙
        q2 = set()
        for c in self.comments:
            q2 = q2 | c.get_descendants()
        q2 = q2 - set(self.comments.all())  # 除去子孙中，用户自己发的(因为是多级评论，用户可能还会在子孙中盖楼)，自己回复的不用通知
        # 用户收到的总评论集合为 q1 与 q2 的并集
        recived_comments = q1 | q2
        # 最后，再过滤掉 last_read_time 之前的评论
        return len([c for c in recived_comments if c.timestamp > last_read_time])

    def new_follows(self):
        '''用户的新粉丝计数'''
        last_read_time = self.last_follows_read_time or datetime(1900, 1, 1)
        return self.followers.filter(followers.c.timestamp > last_read_time).count()

    def new_comments_likes(self):
        '''用户收到的新评论点赞计数'''
        last_read_time = self.last_comments_likes_read_time or datetime(1900, 1, 1)
        # 当前用户发表的所有评论当中，哪些被点赞了
        comments = self.comments.join(comments_likes).all()
        # 新的点赞记录计数
        new_likes_count = 0
        for c in comments:
            # 获取点赞时间
            for u in c.likers:
                if u != self:  # 用户自己点赞自己的评论不需要被通知
                    res = db.engine.execute(
                        "select * from comments_likes where user_id={} and comment_id={}".format(u.id, c.id))
                    timestamp = datetime.strptime(list(res)[0][2], '%Y-%m-%d %H:%M:%S.%f')
                    # 判断本条点赞记录是否为新的
                    if timestamp > last_read_time:
                        new_likes_count += 1
        return new_likes_count

    def new_followeds_micropubs(self):
        '''用户关注的人的新发布的微知识计数'''
        last_read_time = self.last_followeds_micropubs_read_time or datetime(1900, 1, 1)
        return self.followeds_micropubs().filter(Micropub.timestamp > last_read_time).count()

    # 用户关注的人新发布的微猜想数
    def new_followeds_microcons(self):
        last_read_time = self.last_followeds_microcons_read_time or datetime(1900, 1, 1)
        return self.followeds_microcons().filter(Microcon.timestamp > last_read_time).count()

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
        '''用户收到的微知识被点赞的新计数'''
        last_read_time = self.last_micropubs_likes_read_time or datetime(1900, 1, 1)
        # 当前用户发布的微知识当中，哪些微知识被喜欢了
        micropubs = self.micropubs.join(micropubs_likes).all()
        # 新的喜欢记录计数
        new_likes_count = 0
        for p in micropubs:
            # 获取喜欢时间
            for u in p.likers:
                if u != self:  # 用户自己喜欢自己的微知识不需要被通知
                    res = db.engine.execute(
                        "select * from micropubs_likes where user_id={} and micropub_id={}".format(u.id, p.id))
                    timestamp = datetime.strptime(list(res)[0][2], '%Y-%m-%d %H:%M:%S.%f')
                    # 判断本条喜欢记录是否为新的
                    if timestamp > last_read_time:
                        new_likes_count += 1
        return new_likes_count

    # 用户新收到的微猜想点赞
    def new_microcons_likes(self):
        last_read_time = self.last_microcons_likes_read_time or datetime(1900, 1, 1)
        microcons = self.microcons.join(microcons_likes).all()
        new_likes_count = 0
        for p in microcons:
            for u in p.likers:
                if u != self:  # 用户自己引用自己的微知识不需要被通知
                    res = db.engine.execute(
                        "select * from microcons_likes where user_id={} and microcon_id={}".format(u.id, p.id))
                    timestamp = datetime.strptime(list(res)[0][2], '%Y-%m-%d %H:%M:%S.%f')
                    if timestamp > last_read_time:
                        new_likes_count += 1
        return new_likes_count

    def generate_confirm_jwt(self, expires_in=3600):
        '''生成确认账户的 JWT'''
        now = datetime.now()
        payload = {
            'user_id': self.id,
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
        now = datetime.now()
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

    def can(self, perm):
        '''检查用户是否有指定的权限'''
        return self.role is not None and self.role.has_permission(perm)

    def is_administrator(self):
        '''检查用户是否为管理员'''
        return self.can(Permission.ADMIN)

    def get_task_in_progress(self, name):
        '''检查指定任务名的RQ任务是否还在运行中'''
        return Task.query.filter_by(name=name, user=self, complete=False).first()

    def launch_task(self, name, description, *args, **kwargs):
        '''用户启动一个新的后台任务'''
        rq_job = current_app.task_queue.enqueue('app.utils.tasks.' + name, *args, **kwargs)
        task = Task(id=rq_job.get_id(), name=name, description=description, user=self)
        db.session.add(task)
        db.session.commit()
        return task

    def get_tasks_in_progress(self):
        '''返回用户所有正在运行中的后台任务'''
        return Task.query.filter_by(user=self, complete=False).all()

    def __repr__(self):
        return '<User {}>'.format(self.username)

@whooshee.register_model('title', 'summary', 'reference')
class Micropub(PaginatedAPIMixin, db.Model):
# class Micropub(SearchableMixin, PaginatedAPIMixin, db.Model):
    __tablename__ = 'micropubs'
    __searchable__ = [('title', True), ('summary', True), ('body', False)]
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), index=True)
    summary = db.Column(db.String(255))
    reference = db.Column(db.String(255))  # 参考文献格式引用
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    tags = db.relationship('Tag', backref='micropub', lazy='dynamic',
                           cascade='all, delete-orphan')
    timestamp = db.Column(db.DateTime, index=True, default=datetime.now)
    views = db.Column(db.Integer, default=0)  # 浏览人次，用于评估热度
    tmp_views = db.Column(db.Integer, default=0) # 用于产生热榜
    # 微证据与点赞/收藏它的人是多对多关系
    likers = db.relationship('User', secondary=micropubs_likes,
                             backref=db.backref('liked_micropubs', lazy='dynamic'), lazy='dynamic')
    collecters = db.relationship('User', secondary=micropubs_collects,
                                 backref=db.backref('collected_micropubs', lazy='dynamic'), lazy='dynamic')
    # 评论
    comments = db.relationship('Comment', backref='micropub', lazy='dynamic',
                               cascade='all, delete-orphan')
    # 用户在孵化器中引用的微知识，一对多，一方
    microknos_cites = db.relationship('MicroknosCites', backref='micropub',
                                      lazy='dynamic', cascade='all, delete-orphan')

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
            'reference': self.reference,
            'author_id': self.author_id,
            'tags': [tag.content for tag in self.tags],  # 需要数量吗
            'timestamp': self.timestamp,
            'views': self.views,
            'likes': self.likers.count(),
            'likers_id': [user.id for user in self.likers],
            'collects': self.collecters.count(),
            'collecters_id': [user.id for user in self.collecters],
            'comments': [comment.to_dict() for comment in self.comments],
            '_links': {
                'self': url_for('api.get_micropub', id=self.id),  # 有啥用
                'author_url': url_for('api.get_user', id=self.author_id),
                'tag_urls': [url_for('api.get_tag', id=tag.id) for tag in self.tags]
            }
        }
        return data

    def add_tags(self, tags):  # 以 content list 的形式传入参数
        for tag in tags:
            new_tag = Tag()
            new_tag.from_dict({'content': tag})
            new_tag.micropub = self  # important
            db.session.add(new_tag)
            db.session.commit()

    def updata_tags(self, tags):  # 先删除再新建
        for tag in self.tags:
            db.session.delete(tag)
            db.session.commit()
        self.add_tags(tags)

    def from_dict(self, data, add_new=False):
        for field in ['title', 'summary', 'reference', 'timestamp']:
            if field in data:
                setattr(self, field, data[field])
        if 'tags' in data:
            if add_new:
                self.add_tags(data['tags'])
            else:
                self.updata_tags(data['tags'])

    # 该微证据是否被某用户点赞
    def is_liked_by(self, user):
        return user in self.likers

    # 点赞微证据
    def liked_by(self, user):
        if not self.is_liked_by(user):
            self.likers.append(user)
            # 切记要先添加点赞记录到数据库
            # 因为 new_micropubs_likes() 会查询 micropubs_likes 关联表
            # db.session.add(self)
            db.session.commit()
            return True
        return False

    # 取消点赞
    def unliked_by(self, user):
        if self.is_liked_by(user):
            self.likers.remove(user)
            # db.session.add(self)
            db.session.commit()
            return True
        return False

    # 该微证据是否被某用户收藏
    def is_collected_by(self, user):
        return user in self.collecters

    # 收藏微证据
    def collected_by(self, user):
        if not self.is_collected_by(user):
            self.collecters.append(user)
            db.session.commit()
            return True
        return False

    # 取消收藏
    def uncollected_by(self, user):
        if self.is_collected_by(user):
            self.collecters.remove(user)
            db.session.commit()
            return True
        return False

    def viewed(self):
        self.views += 1

# db.event.listen(Micropub.body, 'set', Micropub.on_changed_body)  # body 字段有变化时，执行 on_changed_body() 方法


# db.event.listen(Micropub, 'after_insert', Micropub.receive_after_insert)
# db.event.listen(Micropub, 'after_delete', Micropub.receive_after_delete)

@whooshee.register_model('title', 'summary')
class Microcon(PaginatedAPIMixin, db.Model):
    __tablename__ = 'microcons'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), index=True)
    summary = db.Column(db.String(255))
    # 引用微证据，多对多关系
    micropubs = db.relationship('Micropub', secondary=microcons_micropubs,
                                backref=db.backref('derived_microcons', lazy='dynamic'), lazy='dynamic')
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    tags = db.relationship('Tag', backref='microcon', lazy='dynamic',
                           cascade='all, delete-orphan')
    timestamp = db.Column(db.DateTime, index=True, default=datetime.now)
    views = db.Column(db.Integer, default=0)  # 浏览人次，用于评估热度
    tmp_views = db.Column(db.Integer, default=0)  # 用于产生热榜
    # status = db.Column(db.Integer, default=0) # 对个人而言？评审中 0， 已通过 1， 已否决 -1
    # 微猜想与通过或者否决它的人是多对多关系
    pros = db.relationship('User', secondary=microcons_pros,
                           backref=db.backref('proed_micocons'), lazy='dynamic')
    cons = db.relationship('User', secondary=microcons_cons,
                           backref=db.backref('coned_microcons'), lazy='dynamic')
    # 微猜想与点赞/收藏它的人是多对多关系
    likers = db.relationship('User', secondary=microcons_likes,
                             backref=db.backref('liked_microcons', lazy='dynamic'), lazy='dynamic')
    collecters = db.relationship('User', secondary=microcons_collects,
                                 backref=db.backref('collected_microcons', lazy='dynamic'), lazy='dynamic')
    # 评论
    comments = db.relationship('Comment', backref='microcon', lazy='dynamic',
                               cascade='all, delete-orphan')
    # 微猜想评审状态，0：待评审；1：已通过；-1 已否决
    status = db.Column(db.Integer, default=0)
    # 用户在孵化器中引用的微知识，一对多，一方
    microknos_cites = db.relationship('MicroknosCites', backref='microcon',
                                      lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return '<Micropub {}>'.format(self.title)

    def to_dict(self):
        data = {
            'id': self.id,
            'title': self.title,
            'summary': self.summary,
            'micropubs': [micropub.id for micropub in self.micropubs],
            'author_id': self.author_id,
            'tags': [tag.content for tag in self.tags],  # 需要数量吗
            'timestamp': self.timestamp,
            'status': self.status,
            'pros_num': self.pros.count(),
            'pros': [self.pros_to_dict(item) for item in self.pros],
            'cons_num': self.cons.count(),
            'cons': [self.cons_to_dict(item) for item in self.cons],
            'views': self.views,
            'likes': self.likers.count(),
            'likers_id': [user.id for user in self.likers],
            'collects': self.collecters.count(),
            'collecters_id': [user.id for user in self.collecters],
            'comments': [comment.to_dict() for comment in self.comments],
            '_links': {
                'self': url_for('api.get_microcon', id=self.id),  # 有啥用
                'author_url': url_for('api.get_user', id=self.author_id),
                'tags_urls': [url_for('api.get_tag', id=tag.id) for tag in self.tags],
                'micropubs_urls': [url_for('api.get_micropub', id=micropub.id)
                                   for micropub in self.micropubs]
            }
        }
        return data

    def pros_to_dict(self, pro):
        item = db.engine.execute("select * from microcons_pors where microcon_id=? and user_id=?",
                                 [self.id, pro.id])
        item = list(item)[0]
        data = {
            'user_id': item[1],
            'timestamp': item[2],
            'reason': item[3]
        }
        return data

    def cons_to_dict(self, con):
        item = db.engine.execute("select * from microcons_cons where microcon_id=? and user_id=?",
                                 [self.id, con.id])
        item = list(item)[0]
        data = {
            'user_id': item[1],
            'timestamp': item[2],
            'reason': item[3]
        }
        return data

    def add_tags(self, tags):  # 以 content list 的形式传入参数
        for tag in tags:
            new_tag = Tag()
            new_tag.from_dict({'content': tag})
            new_tag.microcon = self  # important
            db.session.add(new_tag)
            db.session.commit()

    def updata_tags(self, tags):  # 先删除再新建
        for tag in self.tags:
            db.session.delete(tag)
            db.session.commit()
        self.add_tags(tags)

    def add_micropubs(self, micropubs):
        for m in micropubs:
            self.micropubs.append(m)
            db.session.commit()

    def update_micropubs(self, micropubs):
        for m in self.micropubs:
            self.micropubs.remove(m)
        self.add_micropubs(micropubs)

    def from_dict(self, data, add_new=False):
        for field in ['title', 'summary', 'timestamp']:
            if field in data:
                setattr(self, field, data[field])
        if 'tags' in data:
            if add_new:
                self.add_tags(data['tags'])
            else:
                self.updata_tags(data['tags'])
        if 'micropubs' in data:  # 修改微猜想引用的
            if add_new:
                self.add_micropubs(data['micropubs'])
            else:
                self.update_micropubs(data['micropubs'])

    # 该微猜想是否被某用户点赞
    def is_liked_by(self, user):
        return user in self.likers

    # 点赞微猜想
    def liked_by(self, user):
        if not self.is_liked_by(user):
            self.likers.append(user)
            # 切记要先添加点赞记录到数据库
            # 因为 new_micropubs_likes() 会查询 micropubs_likes 关联表
            # db.session.add(self)
            db.session.commit()
            return True
        return False

    # 取消点赞
    def unliked_by(self, user):
        if self.is_liked_by(user):
            self.likers.remove(user)
            # db.session.add(self)
            db.session.commit()
            return True
        return False

    # 该微猜想是否被某用户收藏
    def is_collected_by(self, user):
        return user in self.collecters

    # 收藏微猜想
    def collected_by(self, user):
        if not self.is_collected_by(user):
            self.collecters.append(user)
            db.session.commit()
            return True
        return False

    # 取消收藏
    def uncollected_by(self, user):
        if self.is_collected_by(user):
            self.collecters.remove(user)
            db.session.commit()
            return True
        return False

    def viewed(self):
        self.views += 1

    def is_judged_by(self, user):
        return (user in self.pros) or (user in self.cons)

    def proed_by(self, user, reason):
        if not self.is_judged_by(user):
            self.pros.append(user)
            db.session.commit()
            db.engine.execute("update microcons_pors set reason=? "
                              "where microcon_id=? and user_id=?", [reason, self.id, user.id])
            return True
        return False

    def coned_by(self, user, reason):
        if not self.is_judged_by(user):
            self.cons.append(user)
            db.session.commit()
            db.engine.execute("update microcons_cons set reason=? "
                              "where microcon_id=? and user_id=?", [reason, self.id, user.id])
            return True
        return False

#
class Comment(PaginatedAPIMixin, db.Model):
    __tablename__ = 'comments'
    # __table_args__ = {"extend_existing": True}   # 如果表已经被创建过,需要加这个参数提供扩展

    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.now)
    mark_read = db.Column(db.Boolean, default=False)  # 微知识作者会收到评论提醒，可以标为已读
    disabled = db.Column(db.Boolean, default=False)  # 屏蔽显示
    # 评论与对它点赞的人是多对多关系
    likers = db.relationship('User', secondary=comments_likes, backref=db.backref('liked_comments', lazy='dynamic'),
                             lazy='dynamic')
    # 外键，评论作者的 id
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    # 外键，评论所属微知识的 id
    micropub_id = db.Column(db.Integer, db.ForeignKey('micropubs.id'))
    microcon_id = db.Column(db.Integer, db.ForeignKey('microcons.id'))
    # 自引用的多级评论实现
    parent_id = db.Column(db.Integer, db.ForeignKey('comments.id', ondelete='CASCADE'))
    # 级联删除的 cascade 必须定义在 "多" 的那一侧，所以不能这样定义: parent = db.relationship('Comment', backref='children', remote_side=[id], cascade='all, delete-orphan')
    parent = db.relationship('Comment', backref=db.backref('children', cascade='all, delete-orphan'), remote_side=[id])

    cradle_id = db.Column(db.Integer, db.ForeignKey('cradles.id'))

    def __repr__(self):
        return '<Comment {}>'.format(self.id)

    def get_descendants(self):
        '''获取评论的所有子孙'''
        data = set()

        def descendants(comment):
            if comment.children:
                data.update(comment.children)
                for child in comment.children:
                    descendants(child)

        descendants(self)
        return data

    def get_ancestors(self):
        '''获取评论的所有祖先'''
        data = []

        def ancestors(comment):
            if comment.parent:
                data.append(comment.parent)
                ancestors(comment.parent)

        ancestors(self)
        return data

    def to_dict(self):
        data = {
            'id': self.id,
            'body': self.body,
            'timestamp': self.timestamp,
            'mark_read': self.mark_read,
            'disabled': self.disabled,
            'likers_id': [user.id for user in self.likers],
            'author': {
                'id': self.author.id,
                'username': self.author.username,
                'name': self.author.name,
                'avatar': self.author.avatar(128)
            },
            'micropub': {
                'id': self.micropub.id,
                'title': self.micropub.title,
                'author_id': self.micropub.author.id
            } if self.micropub else None,
            'microcon': {
                'id': self.microcon.id,
                'title': self.microcon.title,
                'author_id': self.microcon.author.id
            } if self.microcon else None,
            'cradle': {
                'id': self.cradle.id,
                'title': self.cradle.title,
                'body': self.cradle.body,
                'sponsor': {
                    'id': self.cradle.sponsor.id,
                    'username': self.cradle.sponsor.username,
                    'name': self.cradle.sponsor.name,
                    'avatar': self.cradle.sponsor.avatar(128)
                }
            } if self.cradle else None,
            'parent_id': self.parent.id if self.parent else None,
            # 'children': [child.to_dict() for child in self.children] if self.children else None,
            '_links': {
                'self': url_for('api.get_comment', id=self.id),
                'author_url': url_for('api.get_user', id=self.author_id),
                'cradle_url': url_for('api.get_cradle', id=self.cradle_id) if self.cradle else None,
                'micropub_url': url_for('api.get_micropub', id=self.micropub_id) if self.micropub else None,
                'microcon_url': url_for('api.get_microcon', id=self.microcon_id) if self.microcon else None,
                'parent_url': url_for('api.get_comment', id=self.parent.id) if self.parent else None,
                'children_url': [url_for('api.get_comment', id=child.id) for child in
                                 self.children] if self.children else None
            }
        }
        return data

    def from_dict(self, data):
        for field in ['body', 'timestamp', 'mark_read', 'disabled', 'author_id', 'parent_id',
                      'micropub_id','microcon_id']:
            if field in data:
                setattr(self, field, data[field])

    def is_liked_by(self, user):
        '''判断用户 user 是否已经对该评论点过赞'''
        return user in self.likers

    def liked_by(self, user):
        '''点赞'''
        if not self.is_liked_by(user):
            self.likers.append(user)
            db.session.commit()
            return True
        return False

    def unliked_by(self, user):
        '''取消点赞'''
        if self.is_liked_by(user):
            self.likers.remove(user)
            db.session.commit()
            return True
        return False


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
    timestamp = db.Column(db.DateTime, index=True, default=datetime.now)
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


class Task(PaginatedAPIMixin, db.Model):
    __tablename__ = 'tasks'
    # 不使用默认的整数主键，而是用 RQ 为每个任务生成的字符串ID
    id = db.Column(db.String(36), primary_key=True)
    # 任务名
    name = db.Column(db.String(128), index=True)
    # 任务描述
    description = db.Column(db.String(128))
    # 任务所属的用户
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    # 是否已执行完成
    complete = db.Column(db.Boolean, default=False)

    def get_progress(self):
        '''返回Task对象实时的进度'''
        try:
            # 通过Task.id，返回RQ job实例
            rq_job = current_app.task_queue.fetch_job(self.id)
        except Exception:
            rq_job = None
        return rq_job.meta.get('progress', 0) if rq_job is not None else 100

    def to_dict(self):
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'progress': self.get_progress(),
            'complete': self.complete,
            '_links': {
                'user_url': url_for('api.get_user', id=self.user.id)
            }
        }
        return data

    def __repr__(self):
        return '<Task {}>'.format(self.id)


class DDL(PaginatedAPIMixin, db.Model):
    __tablename__ = 'ddls'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.now) # 创建或最后一次修改时间
    deadline = db.Column(db.DateTime, index=True)                           # 截至时间
    cradle_id = db.Column(db.Integer, db.ForeignKey('cradles.id')) # 一对多，多方
    passed = db.Column(db.Boolean, default=False)  # 是否截止

    def __repr__(self):
        return '<DDL {}>'.format(self.id)

    def to_dict(self):
        self.passed = self.deadline < datetime.now() # TODO
        data = {
            'id': self.id,
            'timestamp': self.timestamp,
            'deanline': self.deadline,
            'body': self.body,
            'passed': self.passed,
            'cradle': {
                'id': self.cradle.id,
                'sponsor': self.cradle.sponsor_id,
                'title': self.cradle.title
            },
            '_links': {
                'self': url_for('api.get_ddl', id=self.id),
                'cradle_url': url_for('api.get_cradle', id=self.cradle_id)
            }
        }
        return data

    def from_dict(self, data):
        for field in ['body', 'timestamp', 'deadline']:
            if field in data:
                setattr(self, field, data[field])


# 孵化器中的微知识引用
class MicroknosCites(PaginatedAPIMixin, db.Model):
    __tablename__ = 'microknos_cites'
    id = db.Column(db.Integer, primary_key=True)
    micropub_id = db.Column(db.Integer, db.ForeignKey('micropubs.id')) # 一对多，多方
    microcon_id = db.Column(db.Integer, db.ForeignKey('microcons.id')) # 一对多，多方
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))         # 一对多，多方
    timestamp = db.Column(db.DateTime, index=True, default=datetime.now)
    cradle_id = db.Column(db.Integer, db.ForeignKey('cradles.id'))     # 一对多，多方
    reason = db.Column(db.TEXT)

    def __repr__(self):
        return '<MicroknosCites {}>'.format(self.id)

    def to_dict(self):
        data = {
            '_links':{
                'self': url_for('api.get_microkno_cite', id=self.id),
                'micropub_url': url_for('api.get_micropub', id=self.micropub_id) if self.micropub else None,
                'microcon_url': url_for('api.get_microcon', id=self.microcon_id) if self.microcon else None,
                'user_url': url_for('api.get_user', id=self.user_id),
                'cradle_url': url_for('api.get_cradle', id=self.cradle_id),
            },
            'micropub': self.micropub.to_dict() if self.micropub else None,
            'microcon': self.microcon.to_dict() if self.microcon else None,
            'user': {
                'id': self.user.id,
                'username': self.user.username,
                'name': self.user.name,
                'avatar': self.user.avatar(128)
            },
            'cradle': {
                'id': self.cradle.id,
                'title': self.cradle.title,
                'body': self.cradle.body,
                'sponsor': {
                    'id': self.cradle.sponsor.id,
                    'username': self.cradle.sponsor.username,
                    'name': self.cradle.sponsor.name,
                    'avatar': self.cradle.sponsor.avatar(128)
                },
            },
            'timestamp': self.timestamp,
            'reason': self.reason,
        }
        return data

    def from_dict(self, data):
        for field in ['reason', 'timestamp']:
            if field in data:
                setattr(self, field, data[field])


class Cradle(PaginatedAPIMixin, db.Model):
    __tablename__ = 'cradles'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.TEXT)
    body = db.Column(db.TEXT)
    sponsor_id = db.Column(db.Integer, db.ForeignKey('users.id'))                   # 一对多，多方
    timestamp = db.Column(db.DateTime, index=True, default=datetime.now)
    comments = db.relationship('Comment', backref='cradle', lazy='dynamic',         # 一对多，一方
                               cascade='all, delete-orphan')
    microknos = db.relationship('MicroknosCites', backref='cradle', lazy='dynamic', # 一对多，一方
                               cascade='all, delete-orphan')
    ddls = db.relationship('DDL', backref='cradle', lazy='dynamic',                 # 一对多，一方
                               cascade='all, delete-orphan')

    def __repr__(self):
        return '<Cradle {}>'.format(self.id)

    def to_dict(self):
        data = {
            'id': self.id,
            'title': self.title,
            'body': self.body,
            'sponsor': {
                'id': self.sponsor.id,
                'username': self.sponsor.username,
                'name': self.sponsor.name,
                'avatar': self.sponsor.avatar(128)
            },
            'timestamp': self.timestamp,
            'ddls': [item.to_dict() for item in self.ddls],
            'comments': [item.to_dict() for item in self.comments],
            'microknos': [item.to_dict() for item in self.microknos],
            '_links':{
                'self': url_for('api.get_cradle', id=self.id),
                'sponsor_url': url_for('api.get_user', id=self.sponsor_id),
                'ddls_url': url_for('api.get_ddls_of_cradle', id=self.id),
                'comments_url': url_for('api.get_comments_of_cradle', id=self.id),
                'microknos_url': url_for('api.get_microknos_cites_of_cradle', id=self.id),
            }
        }
        return data

    def from_dict(self, data):
        for field in ['body', 'title', 'timestamp']:
            if field in data:
                setattr(self, field, data[field])

    def add_ddl(self, ddl):
        self.ddls.append(ddl)
        # TODO 向关注该孵化器的人发提醒