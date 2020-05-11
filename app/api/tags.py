from flask import jsonify, g
from app.api import bp
from app.api.auth import token_auth
from app.models import Tag
from app.api.errors import error_response

@bp.route('/tags/<int:id>', methods=['GET'])
@token_auth.login_required
def get_tag(id):
    tag = Tag.query.get_or_404(id)
    if g.current_user != tag.micropub.author:
        return error_response(403)
    data = tag.to_dict()
    return jsonify(data)
