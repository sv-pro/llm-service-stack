"""Add recursive enhancement columns to enhanced_prompts table

Revision ID: 001
Revises:
Create Date: 2025-11-14 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add new columns for recursive prompt enhancement feature."""
    # Check if table exists, if not create all tables
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if 'enhanced_prompts' not in inspector.get_table_names():
        # Table doesn't exist, create all tables
        # This will be handled by Base.metadata.create_all in the app
        return

    # Check if columns already exist before adding them
    columns = [col['name'] for col in inspector.get_columns('enhanced_prompts')]

    if 'recursive_iterations' not in columns:
        op.add_column('enhanced_prompts',
            sa.Column('recursive_iterations', sa.Integer(), nullable=True))

    if 'recursive_converged' not in columns:
        op.add_column('enhanced_prompts',
            sa.Column('recursive_converged', sa.Integer(), nullable=True))

    if 'recursive_final_similarity' not in columns:
        op.add_column('enhanced_prompts',
            sa.Column('recursive_final_similarity', sa.Float(), nullable=True))

    if 'recursive_history' not in columns:
        op.add_column('enhanced_prompts',
            sa.Column('recursive_history', sa.JSON(), nullable=True))


def downgrade() -> None:
    """Remove recursive enhancement columns."""
    # Check if table and columns exist before trying to drop
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if 'enhanced_prompts' not in inspector.get_table_names():
        return

    columns = [col['name'] for col in inspector.get_columns('enhanced_prompts')]

    if 'recursive_history' in columns:
        op.drop_column('enhanced_prompts', 'recursive_history')

    if 'recursive_final_similarity' in columns:
        op.drop_column('enhanced_prompts', 'recursive_final_similarity')

    if 'recursive_converged' in columns:
        op.drop_column('enhanced_prompts', 'recursive_converged')

    if 'recursive_iterations' in columns:
        op.drop_column('enhanced_prompts', 'recursive_iterations')
