"""init tables

Revision ID: 0001
Revises:
Create Date: 2025-01-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('email', sa.String(255), unique=True, index=True, nullable=False),
    )

    op.create_table(
        'disaster_types',
        sa.Column('disaster_type_id', sa.Integer(), primary_key=True, index=True),
        sa.Column('disaster_code', sa.String(100), nullable=False),
        sa.Column('disaser_name', sa.String(100), nullable=True),
        sa.Column('description', sa.String(255), nullable=True),
    )

    op.create_table(
        'disaster_impacts',
        sa.Column('impact_id', sa.Integer(), primary_key=True, index=True),
        sa.Column('user__disaster_id', sa.Integer(), nullable=False),
        sa.Column('safty_status', sa.String(50), nullable=True),
        sa.Column('residence_status', sa.String(50), nullable=False),
        sa.Column('injury_level', sa.String(50), nullable=False),
        sa.Column('can_go_out', sa.Boolean(), nullable=True),
        sa.Column('available_time', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_table(
        'flood_impacts',
        sa.Column('flood_impact_id', sa.BigInteger(), primary_key=True, index=True),
        sa.Column('flood_level', sa.String(50), nullable=False),
        sa.Column('water_drain_status', sa.String(50), nullable=False),
        sa.Column('damage_house', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('damage_vehicle', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('electric_problem', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('water_problem', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('impact_id', sa.Integer(), sa.ForeignKey('disaster_impacts.impact_id'), nullable=False),
    )

    op.create_table(
        'typhoon_impacts',
        sa.Column('typhoon_impact_id', sa.BigInteger(), primary_key=True, index=True),
        sa.Column('roof_damage', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('window_damage', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('structure_damage', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('vehicle_damage', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('electric_problem', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('water_problem', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('impact_id', sa.Integer(), sa.ForeignKey('disaster_impacts.impact_id'), nullable=False),
    )

    op.create_table(
        'earthquake_impacts',
        sa.Column('earth_impact_id', sa.BigInteger(), primary_key=True, index=True),
        sa.Column('aftershock_feeling', sa.String(50), nullable=False),
        sa.Column('building_crack', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('house_damage', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('vehicle_damage', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('electric_problem', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('water_problem', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('impact_id', sa.Integer(), sa.ForeignKey('disaster_impacts.impact_id'), nullable=False),
    )

    op.create_table(
        'fire_impacts',
        sa.Column('fire_impact_id', sa.BigInteger(), primary_key=True, index=True),
        sa.Column('fire_damage_scope', sa.String(50), nullable=False),
        sa.Column('smoke_inhalation', sa.String(50), nullable=False),
        sa.Column('house_damage', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('soot_damage', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('debris_exist', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('vehicle_damage', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('electric_problem', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('water_problem', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('impact_id', sa.Integer(), sa.ForeignKey('disaster_impacts.impact_id'), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('fire_impacts')
    op.drop_table('earthquake_impacts')
    op.drop_table('typhoon_impacts')
    op.drop_table('flood_impacts')
    op.drop_table('disaster_impacts')
    op.drop_table('disaster_types')
    op.drop_table('users')
