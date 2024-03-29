from flask import request, jsonify, url_for, g, current_app
from app.api import bp
from app.api.auth import token_auth
from app.api.errors import error_response, bad_request
from app.extensions import db
from app.models import Permission, Micropub, Comment, Tag
from app.utils.decorator import permission_required
from datetime import datetime, timedelta
from app.utils.decorator import permission_required, Permission, admin_required

'''
增删改查
1.√ 新建微证据
2.√ 查询微证据集合   # 按热度返回
3.√ 查询单条微证据
4.√ 修改微证据        （不支持，或者需要解决被微猜想引用后修改的问题）
5.√ 点赞微证据
6.√ 取消点赞微证据
7.√ 收藏微证据
8.√ 取消收藏微证据
9.  评论微证据        （应在 comments.py 中）
10. 删除评论微证据   （应在 comments.py 中）
11.√ 删除微证据       （不支持，同 4）   
12.√ 按标签查找微证据
'''

# 合法性检查
def validation_check(data):
    message = {}
    # 标题
    if 'title' not in data or not data.get('title').strip():
        message['title'] = 'Title is required.'
    elif len(data.get('title')) > 255:
        message['title'] = 'Title must less than 255 characters.'
    # 概述
    if 'summary' not in data or not data.get('summary').strip():
        message['summary'] = 'Summary is required.'
    elif len(data.get('summary')) > 250:
        message['summary'] = 'Summary must less than 250 characters.'
    # 引用
    if 'reference' not in data or not data.get('reference').strip():
        message['reference'] = 'Reference is required.'
    elif len(data.get('reference')) > 255:
        message['reference'] = 'Reference must less than 255 characters.'
    # 标签
    if 'tags' not in data or data.get('tags') == []:
        message['tags'] = 'Tag is required.'
    else:
        for tag in data.get('tags'):
            if len(tag) > 64:
                message['tags'] = 'Tag must less than 64 characters.'
                break
    return message

@bp.route('/micropubs/', methods=['POST'])
@token_auth.login_required
@permission_required(Permission.WRITE)
def create_micropub():
    '''添加一篇新微知识'''
    data = request.get_json()

    # 合法性检查
    if not data:
        return bad_request('You must micropub JSON data.')
    error_message = validation_check(data)
    if error_message:
        return bad_request(error_message)

    # 创建新证据
    micropub = Micropub()
    micropub.from_dict(data, add_new=True)
    micropub.author = g.current_user

    db.session.add(micropub)
    db.session.commit()

    # 给微证据作者的所有粉丝发送新微证据通知
    for user in micropub.author.followers:
        user.add_notification('unread_followeds_micropubs_count',
                              user.new_followeds_micropubs())
    db.session.commit()

    # 返回创建结果
    response = jsonify(micropub.to_dict())
    response.status_code = 201
    response.headers['Location'] = url_for('api.get_micropub', id=micropub.id)
    return response


@bp.route('/micropubs/', methods=['GET'])
@token_auth.login_required
def get_micropubs():
    '''
    :return: 按时间返回分页微知识集合
    '''
    status = request.args.get('status', type=str)
    if not status:
        return bad_request('Please provide the status of micropubs.')
    status = status.split(',')
    for item in status:
        if item.strip() not in ['0', '1', '-1']:
            return bad_request('Please provide valid status of micropubs, 0, 1 or -1.')

    q_list = []
    for item in status:
        q_list.append(Micropub.query.filter(Micropub.status == int(item)))
    final_query = q_list[0]
    for i in range(1, len(q_list)):
        final_query = final_query.union(q_list[i])

    page = request.args.get('page', 1, type=int)
    per_page = min(
        request.args.get(
            'per_page', current_app.config['POSTS_PER_PAGE'], type=int), 100)
    data = Micropub.to_collection_dict(
        final_query.order_by(Micropub.timestamp.desc()), page, per_page,
        'api.get_micropubs')

    # 是否被当前用户关注或点赞
    for item in data["items"]:
        item["is_liked"] = g.current_user.id in item["likers_id"]
        item["is_collected"] = g.current_user.id in item["collecters_id"]
    return jsonify(data)


@bp.route('/micropubs/hot', methods=['GET'])
# @token_auth.login_required # 未登录用户也可以浏览
def get_hot_micropubs():
    '''
    :return: 按热度返回微知识集合
    如果微知识是在当前时间前1小时之外发布的，tmp_views = views - 10(负数也不影响)
    '''
    '''
    data = Micropub.query.order_by(Micropub.views.desc()).all()
    if Micropub.query.count() < 50:
        data = data[:10]
    else: # TODO
        data = data[:10]
    return jsonify([item.to_dict() for item in data])
    '''
    page = request.args.get('page', 1, type=int)
    per_page = min(
        request.args.get(
            'per_page', current_app.config['POSTS_PER_PAGE'], type=int), 100)
    early_time = datetime.now() - timedelta(hours=1)
    db.engine.execute("update micropubs set tmp_views=views;")
    db.engine.execute("update micropubs set tmp_views=tmp_views-10 where timestamp<?", [early_time])
    data = Micropub.to_collection_dict(
        Micropub.query.filter(Micropub.status==1).order_by(Micropub.tmp_views.desc()), page, per_page,
        'api.get_hot_micropubs')
    return jsonify(data)

@bp.route('/micropubs/<int:id>', methods=['GET'])
@token_auth.login_required # 未登录用户不能查看微证据详情
def get_micropub(id):
    '''
    :param id: 微证据 ID
    :return: 该微证据的详细信息
    '''
    micropub = Micropub.query.get_or_404(id)

    micropub.viewed()
    db.session.add(micropub)
    db.session.commit()
    data = micropub.to_dict()

    data["is_liked"] = g.current_user.id in data["likers_id"]
    data["is_collected"] = g.current_user.id in data["collecters_id"]

    # 下一篇微证据
    next_basequery = Micropub.query.order_by(Micropub.timestamp.desc()).\
        filter(Micropub.timestamp > micropub.timestamp)
    if next_basequery.all():
        data['next_id'] = next_basequery[-1].id
        data['next_title'] = next_basequery[-1].title
        data['_links']['next'] = url_for('api.get_micropub', id=next_basequery[-1].id)
    else:
        data['_links']['next'] = None

    # 上一篇微证据
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
@permission_required(Permission.WRITE)
def update_micropub(id):
    '''
    :param id: 微证据 ID
    :return: 修改后的微知识
    评审阶段可以修改，修改后评审消息清空
    '''
    micropub = Micropub.query.get_or_404(id)

    # 权限检查
    if g.current_user != micropub.author:
        return error_response(403)
    if micropub.status != 0:
        return error_response(403)

    # 合法性检查
    data = request.get_json()
    if not data:
        return bad_request('You must micropub JSON data.')
    error_message = validation_check(data)
    if error_message:
        return bad_request(error_message)

    micropub.from_dict(data)
    micropub.remove_all_judge()
    db.session.commit()
    return jsonify(micropub.to_dict())


@bp.route('/micropubs/<int:id>', methods=['DELETE'])
@token_auth.login_required
def delete_micropub(id):
    '''
    :param id: 微证据 ID
    :return:   被删除的微证据和成功信息
    '''
    micropub = Micropub.query.get_or_404(id)
    if not (g.current_user.can(Permission.ADMIN)
            or (micropub.status == 0 and g.current_user == micropub)):
        return error_response(403)

    author = micropub.author
    db.session.delete(micropub)
    db.session.commit()

    # 给微证据作者的所有粉丝发送新微证据通知(需要自动减1)
    for user in author.followers:
        user.add_notification('unread_followeds_micropubs_count',
                              user.new_followeds_micropubs())
    db.session.commit()

    return jsonify({
        'status': 'success',
        'message': 'You deleted micropub {}.'.format(id)
    })


# 点赞微证据
@bp.route('/micropubs/<int:id>/like', methods=['GET'])
@token_auth.login_required
@permission_required(Permission.COMMENT)
def like_micropub(id):
    micropub = Micropub.query.get_or_404(id)

    if micropub.status == 0:
        return bad_request('Micropub {} is in judging status, you can not like it now.'.format(id))


    if not micropub.liked_by(g.current_user):
        return jsonify({
            'status': 'failed',
            'message': 'You already liked micropub {}.'.format(id)
        })

    micropub.author.add_notification('unread_micropubs_likes_count',
                                 micropub.author.new_micropubs_likes())
    db.session.commit()
    return jsonify({
        'status': 'success',
        'message': 'You are now liking micropub {}.'.format(id)
    })

# 取消点赞微证据
@bp.route('/micropubs/<int:id>/unlike', methods=['GET'])
@token_auth.login_required
@permission_required(Permission.COMMENT)
def unlike_micropub(id):
    micropub = Micropub.query.get_or_404(id)
    if not micropub.unliked_by(g.current_user):
        return jsonify({
            'status': 'failed',
            'message': 'You already unliked micropub {}'.format(id)
        })

    # 给微知识作者发送新引用通知(需要自动减1)
    micropub.author.add_notification('unread_micropubs_likes_count',
                                 micropub.author.new_micropubs_likes())
    db.session.commit()
    return jsonify({
        'status': 'success',
        'message': 'You are not liking micropub {} anymore.'.format(id)
    })

# 收藏微证据
@bp.route('/micropubs/<int:id>/collect', methods=['GET'])
@token_auth.login_required
def collect_micropub(id):
    micropub = Micropub.query.get_or_404(id)
    if micropub.status == 0:
        return bad_request('Micropub {} is in judging status, you can not like it now.'.format(id))

    if not micropub.collected_by(g.current_user):
        return jsonify({
            'status': 'failed',
            'message': 'You already collected micropub {}.'.format(id)
        })
    return jsonify({
        'status': 'success',
        'message': 'You are now collecting micropub {}.'.format(id)
    })

# 取消收藏微证据
@bp.route('/micropubs/<int:id>/uncollect', methods=['GET'])
@token_auth.login_required
def uncollect_micropub(id):
    micropub = Micropub.query.get_or_404(id)

    if not micropub.uncollected_by(g.current_user):
        return jsonify({
            'status': 'failed',
            'message': 'You already uncollected micropub {}.'.format(id)
        })
    return jsonify({
        'status': 'success',
        'message': 'You are not collecting micropub {} anymore.'.format(id)
    })


# 查找具有某些 tag 中的某一个或几个的通过的微证据
@bp.route('/micropubs/search-by-tags/', methods=['POST'])
@token_auth.login_required
def get_micropubs_by_tags():
    data = request.get_json()

    if not data:
        return bad_request('You must micropub JSON data.')
    if 'tags' not in data or data.get('tags') == []:
        return bad_request('Tag is required.')
    tags_contents = data.get('tags')

    page = request.args.get('page', 1, type=int)
    per_page = min(
        request.args.get(
            'per_page', current_app.config['POSTS_PER_PAGE'], type=int), 100)
    data = Micropub.to_collection_dict(
        Micropub.query.filter(Micropub.status==1).join(Tag).filter(Tag.content.in_(tags_contents)).
            order_by(Micropub.timestamp.desc()),
        page, per_page, 'api.get_micropubs_by_tags')

    for item in data['items']:
        item['is_liked'] = g.current_user.id in item['likers_id']
        item['is_collected'] = g.current_user.id in item['collecters_id']

    return jsonify(data)

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
'''
@bp.route('/search/', methods=['GET'])
def search():
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
def get_search_micropub(id): # 从搜索结果列表页跳转到微知识详情
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
'''


# 通过微证据
@bp.route('/micropubs/<int:id>/pro', methods=['POST'])
@token_auth.login_required
@permission_required(Permission.COMMENT)
def pro_micropub(id):
    micropub = Micropub.query.get_or_404(id)
    if g.current_user == micropub.author: # 不能审核自己
        return error_response(403)
    if micropub.status != 0:
        return jsonify({
            'status': 'failed',
            'message': 'This micropub is already in {} state'.
                format('proed' if micropub.status == 1 else 'coned')
        })
    data = request.get_json()
    if 'reason' not in data or not data.get('reason').strip():
        return bad_request('Please provide the reason of proing micropub {}'.format(id))
    elif len(data.get('reason').strip()) > 255:
        return bad_request('The maximum length of proing reason is 255.')

    if not micropub.proed_by(g.current_user, data.get('reason').strip()):
        return jsonify({
            'status': 'failed',
            'message': 'You have aready judged micropub {}.'.format(id)
        })
    if micropub.pros.count() >= 3:
        micropub.status = 1
        db.session.commit()
    return jsonify({
        'status': 'success',
        'message': 'You are proing micropub {}.'.format(id)
    })

# 否决微证据
@bp.route('/micropubs/<int:id>/con', methods=['POST'])
@token_auth.login_required
@permission_required(Permission.COMMENT)
def con_micropub(id):
    micropub = Micropub.query.get_or_404(id)
    if g.current_user == micropub.author: # 不能审核自己
        return error_response(403)
    if micropub.status != 0:
        return jsonify({
            'status': 'failed',
            'message': 'This micropub is already in {} state'.
                format('proed' if micropub.status == 1 else 'coned')
        })

    data = request.get_json()
    if 'reason' not in data or not data.get('reason').strip():
        return bad_request('Please provide the reason of coning micropub {}'.format(id))
    elif len(data.get('reason').strip()) > 255:
        return bad_request('The maximum length of coning reason is 255.')

    if not micropub.coned_by(g.current_user, data.get('reason').strip()):
        return jsonify({
            'status': 'failed',
            'message': 'You have aready judged micropub {}.'.format(id)
        })
    if micropub.cons.count() >= 3:
        micropub.status = -1
        db.session.commit()
    return jsonify({
        'status': 'success',
        'message': 'You are coning micropub {}.'.format(id)
    })

