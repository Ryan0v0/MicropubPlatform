from flask import request, jsonify, g, current_app
from app.api import bp
from app.api.auth import token_auth
from app.api.errors import bad_request, error_response
from app.extensions import db
from app.models import Cradle, MicroknosCites, DDL, Comment
from app.utils.decorator import permission_required, Permission

'''
    增删改查
    1. 创建孵化器（仅包含标题、内容、赞助商）
    2. 删除孵化器
    3. 修改孵化器
    3.0 修改孵化器的标题、内容
    3.1 修改孵化器的 ddl
    3.1.1 向孵化器增加 ddl（ddls.py）
    3.1.2 删除孵化器中的 ddl (ddls.py)
    3.1.3 修改孵化器中的 ddl（ddls.py）
    3.2 修改孵化器中的评论
    3.2.1 向孵化器增加评论 （comments.py）
    3.2.2 删除孵化器中的评论 （comments.py）
    3.3 修改孵化器中的微知识
    3.3.1 向孵化器添加微知识 （microkno_cites.py）
    3.3.2 删除孵化器中的微知识 （microkno_cites.py）
    4. 获取孵化器 
    4.0 获取某一用户的孵化器们（users.py）
    4.1 获取某一孵化器
    4.2 获取孵化器集合
    4.3 获取某一孵化器的评论
    4.4 获取某一孵化器的ddl
    4.5 获取某一孵化器的微知识引用
'''

def validation_check_of_create_cradle(data):
    message = {}
    if 'title' not in data or not data.get('title').strip():
        message['title'] = 'Please provide a valid title.'

    if 'body' not in data or not data.get('body').strip():
        message['body'] = 'Please provide a valid body.'

    return message


@bp.route('/cradles/', methods=['POST'])
@token_auth.login_required
@permission_required(Permission.SPONSOR)
def create_cradle():
    '''
    创建孵化器，仅基本信息：标题、内容、赞助商
    :return:
    '''
    data = request.get_json()
    if not data:
        return bad_request('You must micropub JSON data.')

    error_message = validation_check_of_create_cradle(data)
    if error_message:
        return bad_request(error_message)

    cradle = Cradle()
    cradle.from_dict(data)
    cradle.sponsor = g.current_user
    db.session.add(cradle)
    db.session.commit()

    return jsonify(cradle.to_dict())


@bp.route('/cradles/<int:id>', methods=['DELETE'])
@token_auth.login_required
@permission_required(Permission.SPONSOR)
def delete_cradle(id):
    '''
    删除孵化器
    :param id:  孵化器 ID
    :return:
    '''
    cradle = Cradle.query.get_or_404(id)
    if g.current_user != cradle.sponsor:
        return error_response(403)

    db.session.delete(cradle)
    db.session.commit()

    return jsonify({
        'status': 'success',
        'message': 'You have deleted cradle {}'.format(id)
    })


@bp.route('/cradles/<int:id>', methods=['PUT'])
@token_auth.login_required
@permission_required(Permission.SPONSOR)
def update_cradle(id):
    '''
    修改孵化器，仅基本信息：标题、内容、赞助商
    :param id: 孵化器 ID
    :return:
    '''
    data = request.get_json()
    if not data:
        return bad_request('You must micropub JSON data.')

    error_message = validation_check_of_create_cradle(data)
    if error_message:
        return bad_request(error_message)

    cradle = Cradle.query.get_or_404(id)
    if g.current_user != cradle.sponsor:
        return error_response(403)

    cradle.from_dict(data)
    db.session.commit()

    data = cradle.to_dict()
    return jsonify(data)


@bp.route('/cradles/', methods=['GET'])
@token_auth.login_required
def get_cradles():
    '''
    获取孵化器集合
    :return:
    '''
    page = request.args.get('page', 1, type=int)
    per_page = min(
        request.args.get(
            'per_page', current_app.config['POSTS_PER_PAGE'], type=int), 100)
    data = Cradle.to_collection_dict(
        Cradle.query.order_by(Cradle.timestamp.desc()),
        page, per_page, 'api.get_cradles')
    return jsonify(data)


@bp.route('/cradles/<int:id>', methods=['GET'])
@token_auth.login_required
def get_cradle(id):
    '''
    获取某个孵化器
    :return:
    '''
    cradle = Cradle.query.get_or_404(id)
    data = cradle.to_dict()
    return jsonify(data)


@bp.route('/cradles/<int:id>/comments', methods=['GET'])
@token_auth.login_required
def get_comments_of_cradle(id):
    '''
    获取某个孵化器的评论集合
    :return:
    '''
    cradle = Cradle.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    per_page = min(
        request.args.get(
            'per_page', current_app.config['POSTS_PER_PAGE'], type=int), 100)
    data = Comment.to_collection_dict(
        cradle.comments.order_by(Comment.timestamp.desc()),
        page, per_page, 'api.get_comments_of_cradle', id=id)
    return jsonify(data)

@bp.route('/cradles/<int:id>/ddls', methods=['GET'])
@token_auth.login_required
def get_ddls_of_cradle(id):
    '''
    获取某个孵化器的ddl集合
    :return:
    '''
    cradle = Cradle.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    per_page = min(
        request.args.get(
            'per_page', current_app.config['POSTS_PER_PAGE'], type=int), 100)
    data = DDL.to_collection_dict(
        cradle.ddls.order_by(DDL.deadline),
        page, per_page, 'api.get_ddls_of_cradle', id=id)
    return jsonify(data)


@bp.route('/cradles/<int:id>/microknos-cites', methods=['GET'])
@token_auth.login_required
def get_microknos_cites_of_cradle(id):
    '''
    获取某个孵化器的微知识引用集合
    :return:
    '''
    cradle = Cradle.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    per_page = min(
        request.args.get(
            'per_page', current_app.config['POSTS_PER_PAGE'], type=int), 100)
    data = MicroknosCites.to_collection_dict(
        cradle.microknos.order_by(MicroknosCites.timestamp.desc()),
        page, per_page, 'api.get_microknos_cites_of_cradle', id=id)
    return jsonify(data)









