from flask import request, jsonify, url_for, g, current_app
from app.api import bp
from app.api.auth import token_auth
from app.api.errors import error_response, bad_request
from app.extensions import db
from app.models import Microcon, Tag, Micropub
from datetime import datetime, timedelta
from app.utils.decorator import permission_required, Permission, admin_required

'''
增删改查
1. 新建微猜想
2. 查询微猜想集合   # 按热度返回
3. 查询单条猜想据
4. 修改微猜想      （仅通过评审前）
5. 点赞微猜想
6. 取消点赞微猜想
7. 收藏微猜想
8. 取消收藏微猜想
9. 评论微猜想        （应在 comments.py 中）
10. 删除评论微猜想   （应在 comments.py 中）
11. 删除微猜想       （不支持，同 4）   
12. 按标签查找微猜想
13. 通过微猜想 （不需要设置取消通过或者取消否决吧）
14. 否决微猜想   
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

    # 微证据
    if 'micropubs_ids' not in data or len(data.get('micropubs_ids')) != 2:
        message['micropubs'] = 'Two micropub cites are required.'
    else:
        micropubs_ids = data.get('micropubs_ids')
        micropubs = []
        for index, m_id in enumerate(micropubs_ids):
            m = Micropub.query.filter(Micropub.id==m_id).first()
            if m == None:
                message['micropubs'] = 'The cited micropub does not exist.'
            else:
                micropubs.append(m)
        if (not message.get('micropubs')) and (micropubs[0] == micropubs[1]):
            message['micropubs'] = 'You can not cite the same micropub twice.'

        if not message:
            data['micropubs'] = micropubs

    # 标签
    if 'tags' not in data or data.get('tags') == []:
        message['tags'] = 'Tag is required.'
    else:
        for tag in data.get('tags'):
            if len(tag) > 64:
                message['tags'] = 'Tag must less than 64 characters.'
                break
    return message

# 创建微猜想
@bp.route('/microcons/', methods=['POST'])
@token_auth.login_required
@permission_required(Permission.WRITE)
def create_microcon():
    data = request.get_json()

    # 合法性检查
    if not data:
        return bad_request('You must micropub JSON data.')
    error_message = validation_check(data)
    if error_message:
        return bad_request(error_message)

    # 创建新猜想
    microcon = Microcon()
    microcon.from_dict(data, add_new=True)
    microcon.author = g.current_user
    db.session.add(microcon)
    db.session.commit()

    # 给微猜想作者的所有粉丝发送新微猜想通知
    for user in microcon.author.followers:
        user.add_notification('unread_followeds_micrcons_count',
                              user.new_followeds_microcons())
    db.session.commit()

    # 返回创建结果
    response = jsonify(microcon.to_dict())
    response.status_code = 201
    response.headers['Location'] = url_for('api.get_microcon', id=microcon.id)
    return response


@bp.route('/microcons/', methods=['GET'])
@token_auth.login_required
def get_microcons():
    '''
    :return: 按时间降序返回分页微猜想集合
    '''
    status =request.args.get('status', type=str)
    if not status:
        return bad_request('Please provide the status of microcons.')
    status = status.split(',')
    for item in status:
        if item.strip() not in ['0', '1', '-1']:
            return bad_request('Please provide valid status of microcons, 0, 1 or -1.')

    q_list = []
    for item in status:
        q_list.append(Microcon.query.filter(Microcon.status==int(item)))
    final_query = q_list[0]
    for i in range(1, len(q_list)):
        final_query = final_query.union(q_list[i])

    page = request.args.get('page', 1, type=int)
    per_page = min(
        request.args.get(
            'per_page', current_app.config['POSTS_PER_PAGE'], type=int), 100)
    data = Microcon.to_collection_dict(
        final_query.order_by(Microcon.timestamp.desc()), page, per_page,
        'api.get_microcons')

    # 是否被当前用户关注或点赞
    for item in data["items"]:
        item["is_liked"] = g.current_user.id in item["likers_id"]
        item["is_collected"] = g.current_user.id in item["collecters_id"]
    return jsonify(data)

@bp.route('/microcons/hot', methods=['GET'])
# @token_auth.login_required # 未登录用户也可以浏览
def get_hot_microcons():
    '''
    :return: 按热度返回【通过的】微知识集合
    将1h前发布的微猜想热度-10加入排序
    '''
    '''
    data = Microcon.query.order_by(Microcon.views.desc()).all()
    if Microcon.query.count() < 50:
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
    db.engine.execute("update microcons set tmp_views=views;")
    db.engine.execute("update microcons set tmp_views=tmp_views-10 where timestamp<?", [early_time])
    data = Microcon.to_collection_dict(
        Microcon.query.filter(Microcon.status==1).order_by(Microcon.tmp_views.desc()), page, per_page,
        'api.get_hot_microcons')
    return jsonify(data)


@bp.route('/microcons/<int:id>', methods=['GET'])
@token_auth.login_required # 未登录用户不能查看微猜想详情
def get_microcon(id):
    '''
    :param id: 微猜想 ID
    :return: 该微猜想的详细信息
    '''
    microcon = Microcon.query.get_or_404(id)

    microcon.viewed()
    db.session.add(microcon)
    db.session.commit()
    data = microcon.to_dict()

    data["is_liked"] = g.current_user.id in data["likers_id"]
    data["is_collected"] = g.current_user.id in data["collecters_id"]

    # 下一篇微猜想
    next_basequery = Microcon.query.order_by(Microcon.timestamp.desc()).\
        filter(Microcon.timestamp > microcon.timestamp)
    if next_basequery.all():
        data['next_id'] = next_basequery[-1].id
        data['next_title'] = next_basequery[-1].title
        data['_links']['next'] = url_for('api.get_microcon', id=next_basequery[-1].id)
    else:
        data['_links']['next'] = None

    # 上一篇微猜想
    prev_basequery = Microcon.query.order_by(Microcon.timestamp.desc()).\
        filter(Microcon.timestamp < microcon.timestamp)
    if prev_basequery.first():
        data['prev_id'] = prev_basequery.first().id
        data['prev_title'] = prev_basequery.first().title
        data['_links']['prev'] = url_for('api.get_microcon', id=prev_basequery.first().id)
    else:
        data['_links']['prev'] = None
    return jsonify(data)


@bp.route('/microcons/<int:id>', methods=['PUT'])
@token_auth.login_required
@permission_required(Permission.WRITE)
def update_microcon(id):
    '''
    :param id: 微证据 ID
    :return: 修改后的微知识
    '''
    microcon = Microcon.query.get_or_404(id)

    # 权限检查
    if g.current_user != microcon.author:
        return error_response(403)
    if microcon.status != 0:
        return error_response(403)

    # 合法性检查
    data = request.get_json()
    if not data:
        return bad_request('You must micropub JSON data.')
    error_message = validation_check(data)
    if error_message:
        return bad_request(error_message)

    microcon.from_dict(data)
    db.session.commit()
    return jsonify(microcon.to_dict())


# 删除微猜想
# 既然普通用户不能删除，，那就不考虑评审状态了
@bp.route('/microcons/<int:id>', methods=['DELETE'])
@token_auth.login_required
def delete_microcon(id):
    '''
    :param id: 微证据 ID
    :return:   被删除的微证据和成功信息
    '''
    microcon = Microcon.query.get_or_404(id)
    if not (g.current_user.can(Permission.ADMIN)
            or (microcon.status == 0 and g.current_user == microcon)):
        return error_response(403)

    # 403
    author = microcon.author
    db.session.delete(microcon)
    db.session.commit()

    # 给微猜想作者的所有粉丝发送新微证据通知
    for user in author.followers:
        user.add_notification('unread_followeds_microcons_count',
                              user.new_followeds_microcons())

    db.session.commit()
    return jsonify({
        'status': 'success',
        'message': 'You deleted microcon {}.'.format(id)
    })


# 点赞微猜想
@bp.route('/microcons/<int:id>/like', methods=['GET'])
@token_auth.login_required
@permission_required(Permission.COMMENT)
def like_microcon(id):
    microcon = Microcon.query.get_or_404(id)
    if microcon.status == 0:
        return bad_request('Microcon {} is in judging status, you can not like it now.'.format(id))

    if not microcon.liked_by(g.current_user):
        return jsonify({
            'status': 'failed',
            'message': 'You already liked microcon {}.'.format(id)
        })

    microcon.author.add_notification('unread_microcons_likes_count',
                                 microcon.author.new_microcons_likes())
    db.session.commit()

    return jsonify({
        'status': 'success',
        'message': 'You are now liking microcon {}.'.format(id)
    })

# 取消点赞微猜想
@bp.route('/microcons/<int:id>/unlike', methods=['GET'])
@token_auth.login_required
@permission_required(Permission.COMMENT)
def unlike_microcon(id):
    microcon = Microcon.query.get_or_404(id)
    if not microcon.unliked_by(g.current_user):
        return jsonify({
            'status': 'failed',
            'message': 'You already unliked microcon {}'.format(id)
        })


    microcon.author.add_notification('unread_microcons_likes_count',
                                 microcon.author.new_microcons_likes())
    db.session.commit()

    return jsonify({
        'status': 'success',
        'message': 'You are not liking microcon {} anymore.'.format(id)
    })


# 收藏微猜想
@bp.route('/microcons/<int:id>/collect', methods=['GET'])
@token_auth.login_required
def collect_microcon(id):
    microcon = Microcon.query.get_or_404(id)
    if microcon.status == 0:
        return bad_request('Microcon {} is in judging status, you can not collect it now.'.format(id))

    if not microcon.collected_by(g.current_user):
        return jsonify({
            'status': 'failed',
            'message': 'You already collected microcon {}.'.format(id)
        })

    return jsonify({
        'status': 'success',
        'message': 'You are now collecting microcon {}.'.format(id)
    })


# 取消收藏微证据
@bp.route('/microcons/<int:id>/uncollect', methods=['GET'])
@token_auth.login_required
def uncollect_microcon(id):
    microcon = Microcon.query.get_or_404(id)

    if not microcon.uncollected_by(g.current_user):
        return jsonify({
            'status': 'failed',
            'message': 'You already uncollected microcon {}.'.format(id)
        })

    return jsonify({
        'status': 'success',
        'message': 'You are not liking microcon {} anymore.'.format(id)
    })


# 查找具有某些 tag 中的某一个或几个的【通过的】微猜想
@bp.route('/microcons/search-by-tags/', methods=['POST'])
@token_auth.login_required
def get_microcons_by_tags():
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
    data = Microcon.to_collection_dict(
        Microcon.query.filter(Microcon.status==1).join(Tag).filter(Tag.content.in_(tags_contents)).
            order_by(Microcon.timestamp.desc()),
        page, per_page, 'api.get_microcons_by_tags')

    return jsonify(data)

# 通过微猜想
@bp.route('/microcons/<int:id>/pro', methods=['POST'])
@token_auth.login_required
@permission_required(Permission.COMMENT)
def pro_microcon(id):
    microcon = Microcon.query.get_or_404(id)
    if g.current_user == microcon.author: # 不能审核自己
        return error_response(403)
    if microcon.status != 0:
        return jsonify({
            'status': 'failed',
            'message': 'This micropub is already in {} state'.
                format('proed' if microcon.status == 1 else 'coned')
        })
    data = request.get_json()
    if 'reason' not in data or not data.get('reason').strip():
        return bad_request('Please provide the reason of proing microcon {}'.format(id))
    elif len(data.get('reason').strip()) > 255:
        return bad_request('The maximum length of proing reason is 255.')

    if not microcon.proed_by(g.current_user, data.get('reason').strip()):
        return jsonify({
            'status': 'failed',
            'message': 'You have aready judged microcon {}.'.format(id)
        })
    if microcon.pros.count() >= 3:
        microcon.status = 1
        db.session.commit()
    return jsonify({
        'status': 'success',
        'message': 'You are proing microcon {}.'.format(id)
    })

# 否决微猜想
@bp.route('/microcons/<int:id>/con', methods=['POST'])
@token_auth.login_required
@permission_required(Permission.COMMENT)
def con_microcon(id):
    microcon = Microcon.query.get_or_404(id)
    if g.current_user == microcon.author: # 不能审核自己
        return error_response(403)
    if microcon.status != 0:
        return jsonify({
            'status': 'failed',
            'message': 'This micropub is already in {} state'.
                format('proed' if microcon.status == 1 else 'coned')
        })

    data = request.get_json()
    if 'reason' not in data or not data.get('reason').strip():
        return bad_request('Please provide the reason of coning microcon {}'.format(id))
    elif len(data.get('reason').strip()) > 255:
        return bad_request('The maximum length of coning reason is 255.')

    if not microcon.coned_by(g.current_user, data.get('reason').strip()):
        return jsonify({
            'status': 'failed',
            'message': 'You have aready judged microcon {}.'.format(id)
        })
    if microcon.cons.count() >= 3:
        microcon.status = -1
        db.session.commit()
    return jsonify({
        'status': 'success',
        'message': 'You are coning microcon {}.'.format(id)
    })



