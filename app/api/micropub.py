from flask import request, jsonify, url_for, g, current_app
from app.api import bp
from app.api.auth import token_auth
from app.api.errors import error_response, bad_request
from app.extensions import db
from app.models import Micropub


@bp.route('/micropubs/', methods=['POST'])
@token_auth.login_required
def create_micropub():
    '''添加一篇新微知识'''
    data = request.get_json()
    if not data:
        return bad_request('You must micropub JSON data.')
    message = {}
    if 'title' not in data or not data.get('title').strip():
        message['title'] = 'Title is required.'
    elif len(data.get('title')) > 255:
        message['title'] = 'Title must less than 255 characters.'
    if 'body' not in data or not data.get('body').strip():
        message['body'] = 'Body is required.'
    if message:
        return bad_request(message)

    micropub = Micropub()
    micropub.from_dict(data)
    micropub.author = g.current_user  # 通过 auth.py 中 verify_token() 传递过来的（同一个request中，需要先进行 Token 认证）
    db.session.add(micropub)
    # 给微知识作者的所有粉丝发送新微知识通知
    for user in micropub.author.followers:
        user.add_notification('unread_followeds_micropubs_count',
                              user.new_followeds_micropubs())
    db.session.commit()
    response = jsonify(micropub.to_dict())
    response.status_code = 201
    # HTTP协议要求201响应包含一个值为新资源URL的Location头部
    response.headers['Location'] = url_for('api.get_micropub', id=micropub.id)
    return response


@bp.route('/micropubs/', methods=['GET'])
def get_micropubs():
    '''返回微知识集合，分页'''
    page = request.args.get('page', 1, type=int)
    per_page = min(
        request.args.get(
            'per_page', current_app.config['POSTS_PER_PAGE'], type=int), 100)
    data = Micropub.to_collection_dict(
        Micropub.query.order_by(Micropub.timestamp.desc()), page, per_page,
        'api.get_micropubs')
    return jsonify(data)


@bp.route('/micropubs/<int:id>', methods=['GET'])
def get_micropub(id):
    '''返回一篇微知识'''
    micropub = Micropub.query.get_or_404(id)
    micropub.views += 1
    db.session.add(micropub)
    db.session.commit()
    data = micropub.to_dict()
    # 下一篇微知识
    next_basequery = Micropub.query.order_by(Micropub.timestamp.desc()).filter(Micropub.timestamp > micropub.timestamp)
    if next_basequery.all():
        data['next_id'] = next_basequery[-1].id
        data['next_title'] = next_basequery[-1].title
        data['_links']['next'] = url_for('api.get_micropub', id=next_basequery[-1].id)
    else:
        data['_links']['next'] = None
    # 上一篇微知识
    prev_basequery = Micropub.query.order_by(Micropub.timestamp.desc()).filter(Micropub.timestamp < micropub.timestamp)
    if prev_basequery.first():
        data['prev_id'] = prev_basequery.first().id
        data['prev_title'] = prev_basequery.first().title
        data['_links']['prev'] = url_for('api.get_micropub', id=prev_basequery.first().id)
    else:
        data['_links']['prev'] = None
    return jsonify(data)


@bp.route('/micropubs/<int:id>', methods=['PUT'])
@token_auth.login_required
def update_micropub(id):
    '''修改一篇微知识'''
    micropub = Micropub.query.get_or_404(id)
    if g.current_user != micropub.author:
        return error_response(403)

    data = request.get_json()
    if not data:
        return bad_request('You must micropub JSON data.')
    message = {}
    if 'title' not in data or not data.get('title').strip():
        message['title'] = 'Title is required.'
    elif len(data.get('title')) > 255:
        message['title'] = 'Title must less than 255 characters.'
    if 'body' not in data or not data.get('body').strip():
        message['body'] = 'Body is required.'
    if message:
        return bad_request(message)

    micropub.from_dict(data)
    db.session.commit()
    return jsonify(micropub.to_dict())


@bp.route('/micropubs/<int:id>', methods=['DELETE'])
@token_auth.login_required
def delete_micropub(id):
    '''删除一篇微知识'''
    micropub = Micropub.query.get_or_404(id)
    if g.current_user != micropub.author:
        return error_response(403)
    db.session.delete(micropub)
    # 给微知识作者的所有粉丝发送新微知识通知(需要自动减1)
    for user in micropub.author.followers:
        user.add_notification('unread_followeds_micropubs_count',
                              user.new_followeds_micropubs())
    db.session.commit()
    return '', 204

###
# 微知识被引用/收藏 或 被取消引用/取消收藏
###
@bp.route('/micropubs/<int:id>/like', methods=['GET'])
@token_auth.login_required
def like_micropub(id):
    '''引用微知识'''
    micropub = Micropub.query.get_or_404(id)
    micropub.liked_by(g.current_user)
    db.session.add(micropub)
    # 切记要先提交，先添加引用记录到数据库，因为 new_micropubs_likes() 会查询 micropubs_likes 关联表
    db.session.commit()
    # 给微知识作者发送新引用通知
    micropub.author.add_notification('unread_micropubs_likes_count',
                                 micropub.author.new_micropubs_likes())
    db.session.commit()
    return jsonify({
        'status': 'success',
        'message': 'You are now liking this micropub.'
    })


@bp.route('/micropubs/<int:id>/unlike', methods=['GET'])
@token_auth.login_required
def unlike_micropub(id):
    '''取消引用微知识'''
    micropub = Micropub.query.get_or_404(id)
    micropub.unliked_by(g.current_user)
    db.session.add(micropub)
    # 切记要先提交，先添加引用记录到数据库，因为 new_micropubs_likes() 会查询 micropubs_likes 关联表
    db.session.commit()
    # 给微知识作者发送新引用通知(需要自动减1)
    micropub.author.add_notification('unread_micropubs_likes_count',
                                 micropub.author.new_micropubs_likes())
    db.session.commit()
    return jsonify({
        'status': 'success',
        'message': 'You are not liking this micropub anymore.'
    })
