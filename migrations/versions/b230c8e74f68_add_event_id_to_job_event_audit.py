from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "b230c8e74f68"
down_revision = "89dba25a7b46"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "job_event_audit",
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=True),
    )

    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto";')

    op.execute(
        """
        UPDATE job_event_audit
        SET event_id = gen_random_uuid()
        WHERE event_id IS NULL;
        """
    )

    op.alter_column(
        "job_event_audit",
        "event_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False,
    )

    op.create_unique_constraint(
        "uq_job_event_audit_event_id",
        "job_event_audit",
        ["event_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_job_event_audit_event_id",
        "job_event_audit",
        type_="unique",
    )
    op.drop_column("job_event_audit", "event_id")
