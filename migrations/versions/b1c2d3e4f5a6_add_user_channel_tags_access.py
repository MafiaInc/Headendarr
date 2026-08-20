"""add user_channel_tags association for per-user channel group access

Revision ID: b1c2d3e4f5a6
Revises: a6b7c8d9e0f1
Create Date: 2026-08-20 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b1c2d3e4f5a6"
down_revision = "a6b7c8d9e0f1"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "user_channel_tags",
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "channel_tag_id",
            sa.Integer(),
            sa.ForeignKey("channel_tags.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.UniqueConstraint("user_id", "channel_tag_id", name="uq_user_channel_tags_user_tag"),
    )


def downgrade():
    op.drop_table("user_channel_tags")
