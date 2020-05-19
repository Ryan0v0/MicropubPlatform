from flask import request, jsonify, url_for, g, current_app
from app.api import bp
from app.api.auth import token_auth
from app.api.errors import error_response, bad_request
from app.extensions import db
from app.models import Permission, Micropub, Comment, Microcon, Cradle
from app.utils.decorator import permission_required


def comment_for_microkno(is_micropub, data, microknow):
    comment = Comment()
    comment.from_dict(data)
    comment.author = g.current_user

    if is_micropub:
        comment.micropub = microknow
    else:
        comment.microcon = microknow

    # 必须先添加该评论，后续给各用户发送通知时，User.new_recived_comments() 才能是更新后的值
    db.session.add(comment)
    db.session.commit()  # 更新数据库，添加评论记录
    # 添加评论时:
    # 1. 如果是一级评论，只需要给微知识作者发送新评论通知
    # 2. 如果不是一级评论，则需要给微知识作者和该评论的所有祖先的作者发送新评论通知
    users = set()
    users.add(microknow.author)  # 将微知识作者添加进集合中
    if comment.parent:
        ancestors_authors = {c.author for c in comment.get_ancestors()}
        users = users | ancestors_authors
    # 给各用户发送新评论通知
    for u in users:
        u.add_notification('unread_recived_comments_count',
                           u.new_recived_comments())
    db.session.commit()  # 更新数据库，写入新通知
    response = jsonify(comment.to_dict())
    response.status_code = 201
    # HTTP协议要求201响应包含一个值为新资源URL的Location头部
    response.headers['Location'] = url_for('api.get_comment', id=comment.id)
    return response


def comment_for_cradle(data, cradle):
    comment = Comment()
    comment.from_dict(data)
    comment.author = g.current_user
    comment.cradle = cradle

    db.session.add(comment)
    db.session.commit()
    response = jsonify(comment.to_dict())
    response.status_code = 201
    response.headers['Location'] = url_for('api.get_comment', id=comment.id)
    return response


@bp.route('/comments/', methods=['POST'])
@token_auth.login_required
@permission_required(Permission.COMMENT)
def create_comment():
    '''在某篇博客微知识下面发表新评论'''
    data = request.get_json()
    if not data:
        return bad_request('You must micropub JSON data.')
    if 'body' not in data or not data.get('body').strip():
        return bad_request('Body is required.')

    is_micropub = bool(('micropub_id' in data) and data.get('micropub_id').strip())
    is_microcon = bool(('microcon_id' in data) and data.get('microcon_id').strip())
    is_cradle = bool(('cradle_id' in data) and data.get('cradle_id').strip())
    print(is_micropub, is_microcon, is_cradle)
    count = is_micropub + is_microcon + is_cradle

    if count != 1:
        return bad_request('One of micropub, microcon or cradle id required.')

    if is_cradle:
        cradle = Cradle.query.get_or_404(int(data.get('cradle_id')))
        return comment_for_cradle(data, cradle)
    else:
        if is_micropub:
            microknow = Micropub.query.get_or_404(int(data.get('micropub_id')))
        else:
            microknow = Microcon.query.get_or_404(int(data.get('microcon_id')))
            if microknow.status == 0:
                return bad_request('Microcon {} is in judging status,'
                                   ' you can not comment to it now.'.format(microknow.id))
        return comment_for_microkno(is_micropub, data, microknow)


# 创建多级评论

@bp.route('/comments/', methods=['GET'])
@token_auth.login_required
def get_comments():
    '''返回评论集合，分页'''
    page = request.args.get('page', 1, type=int)
    per_page = min(
        request.args.get(
            'per_page', current_app.config['COMMENTS_PER_PAGE'], type=int), 100)
    data = Comment.to_collection_dict(
        Comment.query.order_by(Comment.timestamp.desc()), page, per_page,
        'api.get_comments')
    return jsonify(data)


@bp.route('/comments/<int:id>', methods=['GET'])
@token_auth.login_required
def get_comment(id):
    '''返回单个评论'''
    comment = Comment.query.get_or_404(id)
    return jsonify(comment.to_dict())


def delete_comment_of_micropub(comment):
    if g.current_user != comment.author \
            and g.current_user != comment.micropub.author \
            and not g.current_user.can(
            Permission.ADMIN):
        return False
        # 删除评论时:
        # 1. 如果是一级评论，只需要给微知识作者发送新评论通知
        # 2. 如果不是一级评论，则需要给微知识作者和该评论的所有祖先的作者发送新评论通知
    users = set()
    users.add(comment.micropub.author)  # 将微知识作者添加进集合中
    if comment.parent:
        ancestors_authors = {c.author for c in comment.get_ancestors()}
        users = users | ancestors_authors
    # 必须先删除该评论，后续给各用户发送通知时，User.new_recived_comments() 才能是更新后的值
    db.session.delete(comment)
    db.session.commit()  # 更新数据库，删除评论记录
    # 给各用户发送新评论通知
    for u in users:
        u.add_notification('unread_recived_comments_count',
                           u.new_recived_comments())
    db.session.commit()  # 更新数据库，写入新通知
    return True

def delete_comment_of_microcon(comment):
    if g.current_user != comment.author \
            and g.current_user != comment.microcon.author \
            and not g.current_user.can(
            Permission.ADMIN):
        return False
        # 删除评论时:
        # 1. 如果是一级评论，只需要给微知识作者发送新评论通知
        # 2. 如果不是一级评论，则需要给微知识作者和该评论的所有祖先的作者发送新评论通知
    users = set()
    users.add(comment.microcon.author)  # 将微知识作者添加进集合中
    if comment.parent:
        ancestors_authors = {c.author for c in comment.get_ancestors()}
        users = users | ancestors_authors
    # 必须先删除该评论，后续给各用户发送通知时，User.new_recived_comments() 才能是更新后的值
    db.session.delete(comment)
    db.session.commit()  # 更新数据库，删除评论记录
    # 给各用户发送新评论通知
    for u in users:
        u.add_notification('unread_recived_comments_count',
                           u.new_recived_comments())
    db.session.commit()  # 更新数据库，写入新通知
    return True


def delete_comment_of_cradle(comment):
    '''
    删除对孵化器的评论
    :param comment: 评论
    :return: 是否删除成功
    '''
    if g.current_user != comment.author \
            and g.currnet_user != comment.cradle.sponsor \
            and not g.current_user.can(Permission.ADMIN):
        return False
    db.session.delete(comment)
    db.session.commit()
    return True


@bp.route('/comments/<int:id>', methods=['DELETE'])
@token_auth.login_required
def delete_comment(id):
    '''删除单个评论'''
    comment = Comment.query.get_or_404(id)
    if comment.micropub and not delete_comment_of_micropub(comment):
        return error_response(403)

    if comment.microcon and not delete_comment_of_microcon(comment):
        return error_response(403)

    if comment.cradle and not delete_comment_of_cradle(comment):
        return error_response(403)
    return jsonify({
        'status': 'success',
        'message': 'You have deleted comment {}'.format(id)
    })
    # return '', 204


###
# 评论被点赞或被取消点赞
###
@bp.route('/comments/<int:id>/like', methods=['GET'])
@token_auth.login_required
@permission_required(Permission.COMMENT)
def like_comment(id):
    '''点赞评论'''
    comment = Comment.query.get_or_404(id)
    if not comment.liked_by(g.current_user):
        return  jsonify({
            'status': 'failed',
            'message': 'You aready liked comment {}'.format(id)
        })

    # 给评论作者发送新点赞通知
    comment.author.add_notification('unread_comments_likes_count',
                                    comment.author.new_comments_likes())
    db.session.commit()
    return jsonify({
        'status': 'success',
        'message': 'You are now liking comment {}.'.format(id)
    })


@bp.route('/comments/<int:id>/unlike', methods=['GET'])
@token_auth.login_required
@permission_required(Permission.COMMENT)
def unlike_comment(id):
    '''取消点赞评论'''
    comment = Comment.query.get_or_404(id)
    if not comment.unliked_by(g.current_user):
        return jsonify({
            'status': 'failed',
            'message': 'You already unliked comment {}'.format(id)
        })
    # 给评论作者发送新点赞通知(需要自动减1)
    comment.author.add_notification('unread_comments_likes_count',
                                    comment.author.new_comments_likes())
    db.session.commit()
    return jsonify({
        'status': 'success',
        'message': 'You are not liking comment {} anymore.'.format(id)
    })
