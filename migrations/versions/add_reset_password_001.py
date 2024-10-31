"""Add reset password functionality

Revision ID: add_reset_password_001
Revises: 
Create Date: 2024-10-29 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_reset_password_001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Säkerställ att kolumnerna finns i club-tabellen
    with op.batch_alter_table('club', schema=None) as batch_op:
        # Först, kontrollera om kolumnerna redan finns
        columns = [col['name'] for col in sa.inspect(op.get_bind()).get_columns('club')]
        
        if 'reset_token' not in columns:
            batch_op.add_column(sa.Column('reset_token', sa.String(length=100), nullable=True))
            batch_op.create_unique_constraint('uq_club_reset_token', ['reset_token'])
        
        if 'reset_token_expiry' not in columns:
            batch_op.add_column(sa.Column('reset_token_expiry', sa.DateTime(), nullable=True))
        
        if 'password_hash' in columns:
            # Ändra längden på password_hash om den redan finns
            batch_op.alter_column('password_hash',
                                existing_type=sa.String(length=128),
                                type_=sa.String(length=255),
                                existing_nullable=True)

def downgrade():
    with op.batch_alter_table('club', schema=None) as batch_op:
        batch_op.drop_column('reset_token_expiry')
        batch_op.drop_constraint('uq_club_reset_token', type_='unique')
        batch_op.drop_column('reset_token')
        # Vi behåller password_hash men ändrar tillbaka längden
        batch_op.alter_column('password_hash',
                            existing_type=sa.String(length=255),
                            type_=sa.String(length=128),
                            existing_nullable=True) 