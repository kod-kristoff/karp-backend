"""init db

Revision ID: 5bb29472d33f
Revises:
Create Date: 2018-12-12 13:48:19.255822

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy_utils import UUIDType
from sqlalchemy_json import JSON


# revision identifiers, used by Alembic.
revision = "5bb29472d33f"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # op.create_table(
    #     "dummy_entry",
    #     sa.Column("id", sa.Integer(), nullable=False),
    #     sa.Column("body", sa.Text(), nullable=False),
    #     sa.Column("deleted", sa.Boolean(), nullable=True),
    #     sa.Column("entry_id", sa.String(length=30), nullable=False),
    #     sa.PrimaryKeyConstraint("id"),
    #     sa.UniqueConstraint("entry_id", name="entry_id_unique_constraint"),
    # )
    # op.create_table(
    #     "dummy_history",
    #     sa.Column("id", sa.Integer(), nullable=False),
    #     sa.Column("entry_id", sa.Integer(), nullable=False),
    #     sa.Column("user_id", sa.Text(), nullable=False),
    #     sa.Column(
    #         "timestamp", sa.DateTime(), server_default=sa.text("now()"), nullable=False
    #     ),
    #     sa.Column("body", sa.Text(), nullable=True),
    #     sa.Column("op", sa.Enum("ADD", "DELETE", "UPDATE"), nullable=False),
    #     sa.Column("version", sa.Integer(), nullable=False),
    #     sa.Column("message", sa.Text(), nullable=True),
    #     sa.PrimaryKeyConstraint("id"),
    #     sa.UniqueConstraint(
    #         "entry_id", "version", name="entry_id_version_unique_constraint"
    #     ),
    # )
    op.create_table(
        "resources",
        sa.Column("id", UUIDType(), nullable=False),
        sa.Column("resource_id", sa.String(length=30), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.Float(), nullable=False),
        sa.Column("config_file", JSON(), nullable=False),
        sa.Column("entry_json_schema", JSON(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=True),
        sa.Column("deleted", sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "resource_id", "version", name="resource_version_unique_constraint"
        ),
    )


def downgrade():
    op.drop_table("resources")
    # op.drop_table("dummy_history")
    # op.drop_table("dummy_entry")
