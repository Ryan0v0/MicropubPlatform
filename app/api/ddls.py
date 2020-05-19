from flask import request, jsonify, g, current_app
from app.api import bp
from app.api.auth import token_auth
from app.api.errors import bad_request
from app.extensions import db
from app.models import Cradle, DDL
from datetime import datetime
from app.utils.decorator import permission_required, Permission

def validation_check_of_create_ddl(data):
    message = {}
    if 'body' not in data or not data.get('body').strip():
        message['body'] = 'Please provide valid body.'
    if 'deadline' not in data or not data.get('deadline').strip():
        message['deadline'] = 'Please provide valid deadline.'
    elif datetime.strptime(data.get('deadline'), "%Y-%m-%d %H:%M") <= datetime.utcnow(): # TODO deadline 转时间
        message['deadline'] = 'Deadline should not be earlier than current time.'

    if 'cradle' not in data or not data.get('cradle').strip():
        message['cradle'] = 'Please provide valid cradle.'
    return message


@bp.route('/ddls/', methods=['POST'])
@token_auth.login_required
@permission_required(Permission.SPONSOR)
def create_ddl():
    '''
    向孵化器添加 ddl
    :return:
    '''
    data = request.get_json()
    if not data:
        return bad_request('You must micropub JSON data.')

    error_message = validation_check_of_create_ddl(data)
    if error_message:
        return bad_request(error_message)
    data['deadline'] = datetime.strptime(data.get('deadline'), "%Y-%m-%d %H:%M")

    cradle = Cradle.query.get_or_404(int(data.get('cradle')))
    if g.current_user != cradle.sponsor:
        return bad_request(403)

    ddl = DDL()
    ddl.from_dict(data)
    db.session.add(ddl)
    cradle.add_ddl(ddl)
    db.session.commit()

    data = ddl.to_dict()
    return jsonify(data)


@bp.route('/ddls/<int:id>', methods=['DELETE'])
@token_auth.login_required
@permission_required(Permission.SPONSOR)
def delete_ddl(id):
    '''
    删除 DDL
    :param id: DDL ID
    :return:
    '''
    ddl = DDL.query.get_or_404(id)
    if g.current_user != ddl.cradle.sponsor:
        return bad_request(403)
    db.session.delete(ddl)
    db.session.commit()

    data = ddl.to_dict()
    return jsonify(data)


@bp.route('/ddls/', methods=['PUT'])
@token_auth.login_required
def update_ddl(id):
    '''
       修改 DDL
       :param id: DDL ID
       :return:
    '''
    data = request.get_json()
    if not data:
        return bad_request('You must micropub JSON data.')

    error_message = validation_check_of_create_ddl(data)
    if error_message:
        return bad_request(error_message)

    ddl = DDL.query.get_or_404(id)
    if g.current_user != ddl.cradle.sponsor:
        return bad_request(403)

    ddl.from_dict(data)
    db.session.commit()

    data = ddl.to_dict()
    return jsonify(data)


@bp.route('/ddls/<int:id>', methods=['GET'])
@token_auth.login_required
def get_ddl(id):
    '''
       修改 DDL
       :param id: DDL ID
       :return:
    '''
    data = request.get_json()
    if not data:
        return bad_request('You must micropub JSON data.')

    error_message = validation_check_of_create_ddl(data)
    if error_message:
        return bad_request(error_message)

    ddl = DDL.query.get_or_404(id)
    if g.current_user != ddl.cradle.sponsor:
        return bad_request(403)

    ddl.from_dict(data)
    db.session.commit()

    data = ddl.to_dict()
    return jsonify(data)


