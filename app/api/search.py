from flask import request, jsonify, url_for, g, current_app
from app.api import bp
from app.api.auth import token_auth
from app.api.errors import error_response, bad_request
from app.models import Micropub, Microcon, Tag, User

'''
搜索
'''
'''
@bp.route('/search/', methods=['GET'])
def search():
    q = request.args.get('q', '').strip()
    if q == '':
        return bad_request(message='Enter keyword about micropub, or microcon.')
    if len(q) < 3:
        return bad_request(message='Keyword must be 3 characters or more.')

    category = request.args.get('category', 'micropub')  # 默认搜索微证据
    topic = request.args.get('tag', '').strip().split(' ')  # 默认搜索微证据
    page = request.args.get('page', 1, type=int)
    per_page = min(
        request.args.get(
            'per_page', current_app.config['POSTS_PER_PAGE'], type=int), 100)

    if category == 'micropub':
        pagination = Micropub.query.whooshee_search(q).filter(Micropub.tag.in_(topic)).paginate(page, per_page)
    elif category == 'microcon':
        pagination = Microcon.query.whooshee_search(q).filter(Microcon.tag.in_(topic)).paginate(page, per_page)
    results = pagination.items

    # 总页数
    # print(results)
    # print(per_page)
    # print(pagination)

    print(len(results))
    total_pages, div = divmod(len(results), per_page)
    if div > 0:
        total_pages += 1

    # 不能使用 Micropub.to_collection_dict()，因为查询结果已经分页过了
    to_url_results = []
    for item in results:
        if type(item) == Micropub:
            to_url_results.append(url_for('api.get_micropub', id=item.id))
        elif type(item) == Microcon:
            to_url_results.append(url_for('api.get_microcon', id=item.id))

    data = {
        'items': [item.to_dict() for item in results],
        '_meta': {
            'page': page,
            'per_page': per_page,
            'total_pages': total_pages,
            'total_items': to_url_results
        },
        '_links': {
            'self': url_for('api.search', q=q, page=page, per_page=per_page),
            'next': url_for('api.search', q=q, page=page + 1, per_page=per_page) if page < total_pages else None,
            'prev': url_for('api.search', q=q, page=page - 1, per_page=per_page) if page > 1 else None
        }
    }
    # print(data)
    return jsonify(data=data, message={"Total items": to_url_results, "current page": page})
'''

@bp.route('/search/', methods=['GET'])
def search():
    q = request.args.get('q', '').strip()
    if q == '':
        return bad_request(message='Enter keyword about micropub, microcon, user or tag.')
    if len(q) < 3:
        return bad_request(message='Keyword must be 3 characters or more.')

    category = request.args.get('category', 'micropub') # 默认搜索微证据
    page = request.args.get('page', 1, type=int)
    per_page = min(
        request.args.get(
            'per_page', current_app.config['POSTS_PER_PAGE'], type=int), 100)

    if category == 'user':
        pagination = User.query.whooshee_search(q).paginate(page, per_page)
    elif category == 'tag':
        pagination = Tag.query.whooshee_search(q).paginate(page, per_page)
    elif category == 'micropub':
        pagination = Micropub.query.whooshee_search(q).paginate(page, per_page)
    else: # 'microcon'
        pagination = Microcon.query.whooshee_search(q).paginate(page, per_page)
    results = pagination.items

    # 总页数
    # print(results)
    # print(per_page)
    # print(pagination)

    print(len(results))
    total_pages, div = divmod(len(results), per_page)
    if div > 0:
        total_pages += 1

    # 不能使用 Micropub.to_collection_dict()，因为查询结果已经分页过了
    to_url_results = []
    for item in results:
        if type(item)==Micropub:
            to_url_results.append(url_for('api.get_micropub', id=item.id))
        elif type(item)==Tag:
            to_url_results.append(url_for('api.get_tag', id=item.id))
        elif type(item)==Microcon:
            to_url_results.append(url_for('api.get_microcon', id=item.id))
        elif type(item)==User:
            to_url_results.append(url_for('api.get_user', id=item.id))

    data = {
        'items': [item.to_dict() for item in pagination.items],
        '_meta': {
            'page': page,
            'per_page': per_page,
            'total_pages': total_pages,
            'total_items': to_url_results
        },
        '_links': {
            'self': url_for('api.search', q=q, page=page, per_page=per_page),
            'next': url_for('api.search', q=q, page=page + 1, per_page=per_page) if page < total_pages else None,
            'prev': url_for('api.search', q=q, page=page - 1, per_page=per_page) if page > 1 else None
        }
    }
    # print(data)
    return jsonify(data=data, message={"Total items": to_url_results, "current page": page})

'''
筛选微证据
'''

@bp.route('/micropubs/search/', methods=['GET'])
@token_auth.login_required
def search_micropubs():
    '''
    :return: 按时间返回分页微知识集合
    '''
    q = request.args.get('q', '').strip()
    if q == '':
        return bad_request(message='Enter keyword about micropub, or microcon.')
    if len(q) < 3:
        return bad_request(message='Keyword must be 3 characters or more.')

    topic = request.args.get('tag', '').strip().split(' ')

    page = request.args.get('page', 1, type=int)
    per_page = min(
        request.args.get(
            'per_page', current_app.config['POSTS_PER_PAGE'], type=int), 100)
    data = Micropub.to_collection_dict(
        Micropub.query.whooshee_search(q).filter(Micropub.tag.in_(topic)).order_by(Micropub.timestamp.desc()), page,
        per_page, 'api.get_micropubs')

    # 是否被当前用户关注或点赞
    for item in data["items"]:
        item["is_liked"] = g.current_user.id in item["likers_id"]
        item["is_collected"] = g.current_user.id in item["collecters_id"]
    return jsonify(data)


@bp.route('/micropubs/hot/search/', methods=['GET'])
# @token_auth.login_required # 未登录用户也可以浏览
def search_hot_micropubs():
    '''
    :return: 按热度返回微知识集合
    如果微知识是在当前时间前1小时之外发布的，tmp_views = views - 10(负数也不影响)
    '''

    q = request.args.get('q', '').strip()
    if q == '':
        return bad_request(message='Enter keyword about micropub, or microcon.')
    if len(q) < 3:
        return bad_request(message='Keyword must be 3 characters or more.')

    topic = request.args.get('tag', '').strip().split(' ')

    page = request.args.get('page', 1, type=int)
    per_page = min(
        request.args.get(
            'per_page', current_app.config['POSTS_PER_PAGE'], type=int), 100)
    early_time = datetime.now() - timedelta(hours=1)
    db.engine.execute("update micropubs set tmp_views=views;")
    db.engine.execute("update micropubs set tmp_views=tmp_views-10 where timestamp<?", [early_time])
    data = Micropub.to_collection_dict(
        Micropub.query.whooshee_search(q).filter(Micropub.tag.in_(topic)).order_by(Micropub.tmp_views.desc()), page,
        per_page,
        'api.get_hot_micropubs')
    return jsonify(data)


'''
筛选微猜想
'''
@bp.route('/microcons/search/', methods=['GET'])
@token_auth.login_required
def search_microcons():
    '''
    :return: 按时间降序返回分页微猜想集合
    '''

    q = request.args.get('q', '').strip()
    if q == '':
        return bad_request(message='Enter keyword about micropub, or microcon.')
    if len(q) < 3:
        return bad_request(message='Keyword must be 3 characters or more.')

    topic = request.args.get('tag', '').strip().split(' ')

    status = request.args.get('status', type=str)
    if not status:
        return bad_request('Please provide the status of microcons.')
    status = status.split(',')
    for item in status:
        if item.strip() not in ['0', '1', '-1']:
            return bad_request('Please provide valid status of microcons, 0, 1 or -1.')

    q_list = []
    for item in status:
        q_list.append(Microcon.query.filter(Microcon.status == int(item)))
    final_query = q_list[0]
    for i in range(1, len(q_list)):
        final_query = final_query.union(q_list[i])

    page = request.args.get('page', 1, type=int)
    per_page = min(
        request.args.get(
            'per_page', current_app.config['POSTS_PER_PAGE'], type=int), 100)
    data = Microcon.to_collection_dict(
        final_query.query.whooshee_search(q).filter(Microcon.tag.in_(topic)).order_by(Microcon.timestamp.desc()), page,
        per_page,
        'api.get_microcons')

    # 是否被当前用户关注或点赞
    for item in data["items"]:
        item["is_liked"] = g.current_user.id in item["likers_id"]
        item["is_collected"] = g.current_user.id in item["collecters_id"]
    return jsonify(data)


@bp.route('/microcons/hot/search/', methods=['GET'])
# @token_auth.login_required # 未登录用户也可以浏览
def search_hot_microcons():
    '''
    :return: 按热度返回【通过的】微知识集合
    将1h前发布的微猜想热度-10加入排序
    '''
    q = request.args.get('q', '').strip()
    if q == '':
        return bad_request(message='Enter keyword about micropub, or microcon.')
    if len(q) < 3:
        return bad_request(message='Keyword must be 3 characters or more.')

    topic = request.args.get('tag', '').strip().split(' ')

    page = request.args.get('page', 1, type=int)
    per_page = min(
        request.args.get(
            'per_page', current_app.config['POSTS_PER_PAGE'], type=int), 100)
    early_time = datetime.now() - timedelta(hours=1)
    db.engine.execute("update microcons set tmp_views=views;")
    db.engine.execute("update microcons set tmp_views=tmp_views-10 where timestamp<?", [early_time])
    data = Microcon.to_collection_dict(
        Microcon.query.whooshee_search(q).filter(Microcon.tag.in_(topic)).filter(Microcon.status == 1).order_by(
            Microcon.tmp_views.desc()), page, per_page, 'api.get_hot_microcons')
    return jsonify(data)


'''
筛选推荐
'''

@bp.route('/users/<int:id>/recommend-micropubs/search/', methods=['GET'])
@token_auth.login_required
def search_recommend_micropubs_for_user(id):
    '''
      推荐的微证据
    '''
    q = request.args.get('q', '').strip()
    if q == '':
        return bad_request(message='Enter keyword about micropub, or microcon.')
    if len(q) < 3:
        return bad_request(message='Keyword must be 3 characters or more.')

    topic = request.args.get('tag', '').strip().split(' ')

    user = User.query.get_or_404(id)
    if g.current_user != user:
        return error_response(403)

    k = request.args.get('k', 5, type=int)  # 邻居个数
    n = request.args.get('n', 10, type=int)  # 推荐个数
    model = CF(type=0, k=k, n=n)
    recommend_list = model.recommend_by_user(user)

    # 用热点补齐 n 个
    if len(recommend_list) < n:
        micropubs = Micropub.query.order_by(Micropub.views.desc()).all()
        for micropub in micropubs:
            if micropub not in recommend_list:
                recommend_list.append(micropub)
                if len(recommend_list) == n:
                    break
    micropubs_ids = [micropub.id for micropub in recommend_list]

    page = request.args.get('page', 1, type=int)
    per_page = min(
        request.args.get(
            'per_page', current_app.config['POSTS_PER_PAGE'], type=int), 100)
    data = Micropub.to_collection_dict(
        Micropub.query.whooshee_search(q).filter(Micropub.tag.in_(topic)).filter(Micropub.id.in_(micropubs_ids)), page,
        per_page, 'api.get_recommend_micropubs_for_user', id=id)
    return jsonify(data)


@bp.route('/users/<int:id>/recommend-microcons/search/', methods=['GET'])
@token_auth.login_required
def search_recommend_microcons_for_user(id):
    '''
      推荐的微猜想
    '''
    q = request.args.get('q', '').strip()
    if q == '':
        return bad_request(message='Enter keyword about micropub, or microcon.')
    if len(q) < 3:
        return bad_request(message='Keyword must be 3 characters or more.')

    topic = request.args.get('tag', '').strip().split(' ')

    user = User.query.get_or_404(id)
    if g.current_user != user:
        return error_response(403)

    k = request.args.get('k', 5, type=int)  # 邻居个数
    n = request.args.get('n', 10, type=int)  # 推荐个数
    model = CF(type=1, k=k, n=n)
    recommend_list = model.recommend_by_user(user)

    # 用热点补齐 n 个
    if len(recommend_list) < n:
        microcons = Microcon.query.filter(Microcon.status == 1). \
            order_by(Microcon.views.desc()).all()
        for microcon in microcons:
            if microcon not in recommend_list:
                recommend_list.append(microcon)
                if len(recommend_list) == n:
                    break
    microcons_ids = [microcon.id for microcon in recommend_list]

    page = request.args.get('page', 1, type=int)
    per_page = min(
        request.args.get(
            'per_page', current_app.config['POSTS_PER_PAGE'], type=int), 100)
    data = Microcon.to_collection_dict(
        Microcon.query.whooshee_search(q).filter(Microcon.tag.in_(topic)).filter(Microcon.id.in_(microcons_ids)), page,
        per_page, 'api.get_recommend_microcons_for_user', id=id)
    return jsonify(data)
