from flask import request, jsonify, g, current_app
from app.api import bp
from app.api.auth import token_auth
from app.api.errors import bad_request, error_response
from app.extensions import db
from app.models import Cradle, MicroknosCites, Micropub, Microcon
from app.utils.decorator import permission_required, Permission


def validation_check_of_cite_microkno(data):
    message = {}
    is_micropub = bool('micropub' in data and data.get('micropub').strip())
    is_microcon = bool('microcon' in data and data.get('microcon').strip())
    if is_micropub + is_microcon != 1:
        message['microkno'] = 'One of micorpub or microcon is needed.'

    if 'cradle' not in data or not data.get('cradle').strip():
        message['cradle'] = 'Please provide a valid cradle.'

    if 'reason' not in data or not data.get('reason').strip():
        message['reason'] = 'Please provide a valid reason of citing the microknowledge.'
    return message


@bp.route('/microknos-cites/', methods=['POST'])
@token_auth.login_required
def create_microkno_cite():
    '''
    向孵化器中添加微知识
    :param id: 孵化器 ID
    :return:
    '''
    data = request.get_json()
    if not data:
        return bad_request('You must micropub JSON data.')

    message = validation_check_of_cite_microkno(data)
    if message:
        return bad_request(message)

    cradle = Cradle.query.get_or_404(int(data.get('cradle')))

    microknocite = MicroknosCites()
    microknocite.from_dict(data)
    db.session.add(microknocite)

    if 'micropub' in data:
        micropub = Micropub.query.get(int(data.get('micropub')))
        if not micropub:
            return bad_request('The cited micropub does not exist.')
        microknocite.micropub = micropub
    else:
        microcon = Microcon.query.get(int(data.get('microcon')))
        if not microcon:
            return bad_request('The cited microcon does not exist.')
        microknocite.microcon = microcon

    microknocite.user = g.current_user
    microknocite.cradle = cradle
    db.session.commit()

    data = microknocite.to_dict()
    return jsonify(data)


@bp.route('/microknos-cites/<int:id>', methods=['GET'])
@token_auth.login_required
def get_microkno_cite(id):
    '''
    获取某个向孵化器中添加的微知识
    :param id: 微知识添加 ID
    :return:
    '''
    microknocite = MicroknosCites.query.get_or_404(id)
    if g.current_user != microknocite.user:
        return error_response(403)
    data = microknocite.to_dict()
    return jsonify(data)


@bp.route('/microknos-cites/<int:id>', methods=['DELETE'])
@token_auth.login_required
def cancel_microkno_cite(id):
    '''
    解除向孵化器中的微知识添加
    :param id: 微知识添加 ID
    :return:
    '''
    microknocite = MicroknosCites.query.get_or_404(id)
    if g.current_user != microknocite.user \
            and g.current_user != microknocite.cradle.sponsor:
        return error_response(403)

    db.session.delete(microknocite)
    db.session.commit()
    return jsonify({
        'status': 'success',
        'message': 'You have cancled microkno cite {}'.format(id)
    })

