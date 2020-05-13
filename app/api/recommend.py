from flask import request, jsonify, g
from app.api import bp
from app.api.auth import token_auth
from app.api.errors import bad_request
from app.models import User
from numpy import sqrt

class CF:
  def __init__(self, type, k = 5, n = 10):
    self.type = type        # 0：推荐微证据， 1：推荐微猜想
    self.k = k              # 邻居个数
    self.n = n              # 推荐个数
    self.user_rating = {}   # 用户评分字典，key：用户, value: 微知识评分列表 [(微知识， 用户评分)]
    self.item_users = {}    # 微知识用户字典，key 微知识，value：评分过该微知识的用户列表
    self.neighbors = []     # 邻居列表
    self.recommend = [] # 推荐列表


  def recommend_by_user(self, user):
    '''
      基于用户的推荐
    '''
    self.build_dict()
    self.get_k_nearest_neignbors(user)
    self.get_recommend_list(user)
    recommend_list = [item[0] for item in self.recommend]
    return recommend_list


  def get_recommend_list(self, user):
    '''
      获取推荐列表
    '''
    self.recommend = []

    # 建立推荐字典
    recommend_dict = {}
    for neighbor in self.neighbors:
      another_user, dist = neighbor
      microknos = self.user_rating[another_user]
      for rating in microknos:
        microkno = rating[0]
        recommend_dict[microkno] = recommend_dict.get(microkno, 0) + dist
 
    # 建立推荐列表
    for key in recommend_dict:
      self.recommend.append((key, recommend_dict[key]))
    self.recommend.sort(reverse=True, key=lambda x: x[1])
    self.recommend = self.recommend[:self.n]


  def build_dict(self):
    '''
      创建 user_rating 字典和 item_users 字典
      点赞记 1 分，收藏记 2 分，相当于满分 3 分
    '''
    self.user_rating = {}
    users = User.query.all()
    for user in users:

      # 用户点赞了的微知识
      if self.type == 0:
        user_likes = set(user.liked_micropubs.all())
      elif self.type == 1:
        user_likes = set(user.liked_microcons.all())

      # 用户收藏了的微知识
      if self.type == 0:
        user_collects = set(user.collected_micropubs.all())
      elif self.type == 1:
        user_collects = set(user.collected_micropubs.all())

      user_both = user_likes & user_collects
      user_likes_only = user_likes - user_both
      user_collects_only = user_collects - user_both

      self.user_rating[user] = []
      for microkno in user_likes_only:
        self.user_rating[user].append((microkno, 1))
        self.item_users.setdefault(microkno, []).append(user)

      for microkno in user_collects_only:
        self.user_rating[user].append((microkno, 2))
        self.item_users.setdefault(microkno, []).append(user)

      for microkno in user_both:
        self.user_rating[user].append((microkno, 3))
        self.item_users.setdefault(microkno, []).append(user)


  # 找到某用户的相邻用户
  def get_k_nearest_neignbors(self, user):
    '''
      找到某用户的 k 近邻用户
    '''
    self.neighbors = []

    # 获取和用户评分过同一微知识的用户
    neighbors = set()
    for rating in self.user_rating[user]:
      microkno = rating[0]
      for another_user in self.item_users[microkno]:
          if another_user != user:
            neighbors.add(another_user)

    # 计算这些用户与此用户的相似度并排序
    for another_user in neighbors:
      dist = self.get_cost(user, another_user)
      self.neighbors.append([another_user, dist])
    self.neighbors.sort(reverse=True, key=lambda x : x[1])
    self.neighbors = self.neighbors[:self.k]

  def get_micropub_rating_pairs(self, user, another_user):
    '''
      获取两用户微知识评分的并集得的评分字典
      key：微知识
      value：微知识评分对 (user.raging, another_user.rating)
    '''
    item_rating_pairs = {}
    for pair in self.user_rating[user]:
      micropub, rating = pair
      item_rating_pairs[micropub] = [rating, 0]
    for pair in self.user_rating[another_user]:
      micropub, rating = pair
      if micropub not in item_rating_pairs:
        item_rating_pairs[micropub] = [0, rating]
      else:
        item_rating_pairs[micropub][1] = rating
    return item_rating_pairs
 
  # 计算余弦距离
  def get_cost(self, user, another_user):
    # 获取 user 和 another_user 评分微知识并集的评分对
    micropub_ratings = self.get_micropub_rating_pairs(user, another_user)

    x = 0.0
    y = 0.0
    z = 0.0
    for v in micropub_ratings.items():
      x += float(v[1][0]) * float(v[1][0])
      y += float(v[1][1]) * float(v[1][1])
      z += float(v[1][0]) * float(v[1][1])
    if z == 0.0:
      return 0
    return z / sqrt(x * y)


@bp.route('/users/<int:id>/recommend-micropubs', methods=['GET'])
@token_auth.login_required
def get_recommend_micropubs_for_user(id):
  '''
    推荐的微证据
  '''
  user = User.query.get_or_404(id)
  if g.current_user != user:
    return bad_request(403)

  k = request.args.get('k', 5, type=int)  # 邻居个数
  n = request.args.get('n', 10, type=int) # 推荐个数
  model = CF(type=0, k=k, n=n)
  recommend_list = model.recommend_by_user(user)
  return jsonify([item.to_dict() for item in recommend_list])

@bp.route('/users/<int:id>/recommend-microcons', methods=['GET'])
@token_auth.login_required
def get_recommend_microcons_for_user(id):
  '''
    推荐的微证据
  '''
  user = User.query.get_or_404(id)
  if g.current_user != user:
    return bad_request(403)

  k = request.args.get('k', 5, type=int)  # 邻居个数
  n = request.args.get('n', 10, type=int) # 推荐个数
  model = CF(type=1, k=k, n=n)
  recommend_list = model.recommend_by_user(user)
  return jsonify([item.to_dict() for item in recommend_list])

# TODO 推荐用户