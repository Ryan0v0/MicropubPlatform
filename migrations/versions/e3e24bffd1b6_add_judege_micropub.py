"""add judege micropub

Revision ID: e3e24bffd1b6
Revises: 03e839257e15
Create Date: 2020-05-22 11:47:58.887352

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e3e24bffd1b6'
down_revision = '03e839257e15'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('micropubs_cons',
    sa.Column('micropub_id', sa.Integer(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('reason', sa.String(length=255), nullable=True),
    sa.ForeignKeyConstraint(['micropub_id'], ['micropubs.id'], name=op.f('fk_micropubs_cons_micropub_id_micropubs'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_micropubs_cons_user_id_users'), ondelete='CASCADE')
    )
    op.create_table('micropubs_pors',
    sa.Column('micropub_id', sa.Integer(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('reason', sa.String(length=255), nullable=True),
    sa.ForeignKeyConstraint(['micropub_id'], ['micropubs.id'], name=op.f('fk_micropubs_pors_micropub_id_micropubs'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_micropubs_pors_user_id_users'), ondelete='CASCADE')
    )
    with op.batch_alter_table('micropubs', schema=None) as batch_op:
        batch_op.add_column(sa.Column('status', sa.Integer(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('micropubs', schema=None) as batch_op:
        batch_op.drop_column('status')

    op.drop_table('micropubs_pors')
    op.drop_table('micropubs_cons')
    # ### end Alembic commands ###
