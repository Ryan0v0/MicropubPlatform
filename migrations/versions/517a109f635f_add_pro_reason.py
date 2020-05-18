"""add pro reason

Revision ID: 517a109f635f
Revises: ca7037a8accb
Create Date: 2020-05-18 22:16:16.406461

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '517a109f635f'
down_revision = 'ca7037a8accb'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('microcons_cons', schema=None) as batch_op:
        batch_op.add_column(sa.Column('reason', sa.String(length=255), nullable=True))

    with op.batch_alter_table('microcons_pors', schema=None) as batch_op:
        batch_op.add_column(sa.Column('reason', sa.String(length=255), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('microcons_pors', schema=None) as batch_op:
        batch_op.drop_column('reason')

    with op.batch_alter_table('microcons_cons', schema=None) as batch_op:
        batch_op.drop_column('reason')

    # ### end Alembic commands ###
