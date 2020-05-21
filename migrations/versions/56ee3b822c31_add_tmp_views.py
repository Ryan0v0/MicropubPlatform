"""add tmp_views

Revision ID: 56ee3b822c31
Revises: 98719838fd82
Create Date: 2020-05-20 22:10:47.939475

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '56ee3b822c31'
down_revision = '98719838fd82'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('microcons', schema=None) as batch_op:
        batch_op.add_column(sa.Column('tmp_views', sa.Integer(), nullable=True))

    with op.batch_alter_table('micropubs', schema=None) as batch_op:
        batch_op.add_column(sa.Column('tmp_views', sa.Integer(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('micropubs', schema=None) as batch_op:
        batch_op.drop_column('tmp_views')

    with op.batch_alter_table('microcons', schema=None) as batch_op:
        batch_op.drop_column('tmp_views')

    # ### end Alembic commands ###
