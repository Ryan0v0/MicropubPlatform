"""add sponsor

Revision ID: a15f34263f6c
Revises: 517a109f635f
Create Date: 2020-05-19 12:33:59.235079

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a15f34263f6c'
down_revision = '517a109f635f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('cradles',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('title', sa.TEXT(), nullable=True),
    sa.Column('body', sa.TEXT(), nullable=True),
    sa.Column('sponsor_id', sa.Integer(), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['sponsor_id'], ['users.id'], name=op.f('fk_cradles_sponsor_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_cradles'))
    )
    with op.batch_alter_table('cradles', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_cradles_timestamp'), ['timestamp'], unique=False)

    op.create_table('ddls',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('body', sa.Text(), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('cradle_id', sa.Integer(), nullable=True),
    sa.Column('passed', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['cradle_id'], ['cradles.id'], name=op.f('fk_ddls_cradle_id_cradles')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_ddls'))
    )
    with op.batch_alter_table('ddls', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_ddls_timestamp'), ['timestamp'], unique=False)

    op.create_table('microknos_cites',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('micropub_id', sa.Integer(), nullable=True),
    sa.Column('microcon_id', sa.Integer(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('cradle_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['cradle_id'], ['cradles.id'], name=op.f('fk_microknos_cites_cradle_id_cradles')),
    sa.ForeignKeyConstraint(['microcon_id'], ['microcons.id'], name=op.f('fk_microknos_cites_microcon_id_microcons')),
    sa.ForeignKeyConstraint(['micropub_id'], ['micropubs.id'], name=op.f('fk_microknos_cites_micropub_id_micropubs')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_microknos_cites_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_microknos_cites'))
    )
    with op.batch_alter_table('microknos_cites', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_microknos_cites_timestamp'), ['timestamp'], unique=False)

    with op.batch_alter_table('comments', schema=None) as batch_op:
        batch_op.add_column(sa.Column('cradle_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(batch_op.f('fk_comments_cradle_id_cradles'), 'cradles', ['cradle_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('comments', schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f('fk_comments_cradle_id_cradles'), type_='foreignkey')
        batch_op.drop_column('cradle_id')

    with op.batch_alter_table('microknos_cites', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_microknos_cites_timestamp'))

    op.drop_table('microknos_cites')
    with op.batch_alter_table('ddls', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_ddls_timestamp'))

    op.drop_table('ddls')
    with op.batch_alter_table('cradles', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_cradles_timestamp'))

    op.drop_table('cradles')
    # ### end Alembic commands ###
