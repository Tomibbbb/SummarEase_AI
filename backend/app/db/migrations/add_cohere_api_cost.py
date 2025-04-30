"""
Migration script to add cohere_api_cost column to usage_statistics table.
"""
from sqlalchemy import Column, Float
from alembic import op

def upgrade():
    """Add cohere_api_cost column to usage_statistics table."""
    op.add_column('usage_statistics', Column('cohere_api_cost', Float, default=0.0))

def downgrade():
    """Remove cohere_api_cost column from usage_statistics table."""
    op.drop_column('usage_statistics', 'cohere_api_cost')