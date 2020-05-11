from flask import request, jsonify, url_for, g, current_app
from app.api import bp
from app.api.auth import token_auth
from app.api.errors import error_response, bad_request
from app.extensions import db
from app.models import Permission, Micropub, Comment
from app.utils.decorator import permission_required


@bp.route('/micropubs/', methods=['POST'])
@token_auth.login_required
@permission_required(Permission.WRITE)
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
    if g.current_user != micropub.author and not g.current_user.can(Permission.ADMIN):
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
    if g.current_user != micropub.author and not g.current_user.can(Permission.ADMIN):
        return error_response(403)
    db.session.delete(micropub)
    # 给微知识作者的所有粉丝发送新微知识通知(需要自动减1)
    for user in micropub.author.followers:
        user.add_notification('unread_followeds_micropubs_count',
                              user.new_followeds_micropubs())
    db.session.commit()
    return '', 204


###
# 与博客微知识资源相关的资源
##
@bp.route('/micropubs/<int:id>/comments/', methods=['GET'])
def get_micropub_comments(id):
    '''返回当前微知识下面的一级评论'''
    micropub = Micropub.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    per_page = min(
        request.args.get(
            'per_page', current_app.config['COMMENTS_PER_PAGE'], type=int), 100)
    # 先获取一级评论
    data = Comment.to_collection_dict(
        micropub.comments.filter(Comment.parent==None).order_by(Comment.timestamp.desc()), page, per_page,
        'api.get_micropub_comments', id=id)
    # 再添加子孙到一级评论的 descendants 属性上
    for item in data['items']:
        comment = Comment.query.get(item['id'])
        descendants = [child.to_dict() for child in comment.get_descendants()]
        # 按 timestamp 排序一个字典列表
        from operator import itemgetter
        item['descendants'] = sorted(descendants, key=itemgetter('timestamp'))
    return jsonify(data)


###
# 微知识被喜欢/收藏 或 被取消喜欢/取消收藏
###
@bp.route('/micropubs/<int:id>/like', methods=['GET'])
@token_auth.login_required
def like_micropub(id):
    '''喜欢微知识'''
    micropub = Micropub.query.get_or_404(id)
    micropub.liked_by(g.current_user)
    db.session.add(micropub)
    # 切记要先提交，先添加喜欢记录到数据库，因为 new_micropubs_likes() 会查询 micropubs_likes 关联表
    db.session.commit()
    # 给微知识作者发送新喜欢通知
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
    '''取消喜欢微知识'''
    micropub = Micropub.query.get_or_404(id)
    micropub.unliked_by(g.current_user)
    db.session.add(micropub)
    # 切记要先提交，先添加喜欢记录到数据库，因为 new_micropubs_likes() 会查询 micropubs_likes 关联表
    db.session.commit()
    # 给微知识作者发送新喜欢通知(需要自动减1)
    micropub.author.add_notification('unread_micropubs_likes_count',
                                 micropub.author.new_micropubs_likes())
    db.session.commit()
    return jsonify({
        'status': 'success',
        'message': 'You are not liking this micropub anymore.'
    })


@bp.route('/micropubs/export-micropubs/', methods=['GET'])
@token_auth.login_required
@permission_required(Permission.WRITE)
def export_micropubs():
    '''导出当前用户的所有微知识，RQ 后台任务'''
    if g.current_user.get_task_in_progress('export_micropubs'):  # 如果用户已经有同名的后台任务在运行中时
        return bad_request('上一个导出微知识的后台任务尚未结束')
    else:
        # 将 app.utils.tasks.export_micropubs 放入任务队列中
        g.current_user.launch_task('export_micropubs', '正在导出微知识...', kwargs={'user_id': g.current_user.id})
        return jsonify(message='正在运行导出微知识后台任务')


###
# 全文搜索
###
@bp.route('/search/', methods=['GET'])
def search():
    '''Elasticsearch全文检索博客微知识'''
    q = request.args.get('q')
    if not q:
        return bad_request(message='keyword is required.')

    page = request.args.get('page', 1, type=int)
    per_page = min(
        request.args.get(
            'per_page', current_app.config['POSTS_PER_PAGE'], type=int), 100)

    total, hits_basequery = Micropub.search(q, page, per_page)
    # 总页数
    total_pages, div = divmod(total, per_page)
    if div > 0:
        total_pages += 1

    # 不能使用 Micropub.to_collection_dict()，因为查询结果已经分页过了
    data = {
        'items': [item.to_dict() for item in hits_basequery],
        '_meta': {
            'page': page,
            'per_page': per_page,
            'total_pages': total_pages,
            'total_items': total
        },
        '_links': {
            'self': url_for('api.search', q=q, page=page, per_page=per_page),
            'next': url_for('api.search', q=q, page=page + 1, per_page=per_page) if page < total_pages else None,
            'prev': url_for('api.search', q=q, page=page - 1, per_page=per_page) if page > 1 else None
        }
    }
    return jsonify(data=data, message='Total items: {}, current page: {}'.format(total, page))


@bp.route('/search/micropub-detail/<int:id>', methods=['GET'])
def get_search_micropub(id):
    '''从搜索结果列表页跳转到微知识详情'''
    q = request.args.get('q')
    page = request.args.get('page', type=int)
    per_page = request.args.get('per_page', type=int)

    if q and page and per_page:  # 说明是从搜索结果页中过来查看微知识详情的，所以要高亮关键字
        total, hits_basequery = Micropub.search(q, page, per_page)
        micropub = hits_basequery.first()  # 只会有唯一的一篇微知识
        data = micropub.to_dict()  # 会高亮关键字
    else:
        micropub = Micropub.query.get_or_404(id)
        data = micropub.to_dict()  # 不会高亮关键字

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
