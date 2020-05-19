from flask import request, jsonify, url_for, g, current_app
from app.api import bp
from app.api.auth import token_auth
from app.api.errors import error_response, bad_request
from app.models import Micropub, Microcon, Tag, User


@bp.route('/search/', methods=['GET'])
def search():
    q = request.args.get('q', '').strip()
    if q == '':
        return bad_request(message='Enter keyword about micropub, microcon, user or tag.')

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
    total_pages, div = divmod(results, per_page)
    if div > 0:
        total_pages += 1

    # 不能使用 Micropub.to_collection_dict()，因为查询结果已经分页过了
    data = {
        'items': [item.to_dict() for item in pagination],
        '_meta': {
            'page': page,
            'per_page': per_page,
            'total_pages': total_pages,
            'total_items': results
        },
        '_links': {
            'self': url_for('api.search', q=q, page=page, per_page=per_page),
            'next': url_for('api.search', q=q, page=page + 1, per_page=per_page) if page < total_pages else None,
            'prev': url_for('api.search', q=q, page=page - 1, per_page=per_page) if page > 1 else None
        }
    }
    return jsonify(data=data, message='Total items: {}, current page: {}'.format(results, page))
