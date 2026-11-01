"""F01.2 identity storage. No transport, booking or live configuration."""
from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import (Boolean, CheckConstraint, DateTime, ForeignKey, ForeignKeyConstraint,
                        Index, Integer, String, UniqueConstraint, Uuid, func, text)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from src.core.database.database import Base


class ScopedRow:
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    connection_id: Mapped[UUID] = mapped_column(ForeignKey('vk_connections.id'), nullable=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default='1')


def scoped_constraints(table: str) -> tuple:
    return (UniqueConstraint('connection_id', 'id', name=f'uq_{table}_scope'),
            CheckConstraint('revision > 0', name=f'ck_{table}_revision'))


class IntegrationConnection(Base):
    __tablename__ = 'vk_connections'
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    installation_id: Mapped[UUID] = mapped_column(Uuid, nullable=False, unique=True, default=uuid4)
    group_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class ConnectionTeacher(Base):
    __tablename__ = 'vk_connection_teachers'
    connection_id: Mapped[UUID] = mapped_column(ForeignKey('vk_connections.id'), primary_key=True)
    teacher_user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), primary_key=True)


class ExternalContact(ScopedRow, Base):
    __tablename__ = 'vk_contacts'
    __table_args__ = (*scoped_constraints('vk_contacts'),
        UniqueConstraint('connection_id', 'subject', name='uq_vk_contact_subject'),
        CheckConstraint("permission IN ('unknown','allowed','denied','unreachable')", name='ck_vk_permission'),
        CheckConstraint('permission_version > 0 AND attempts >= 0 AND attempt_window >= 0', name='ck_vk_contact_counters'))
    subject: Mapped[str] = mapped_column(String(64), nullable=False)
    verified_sender_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    permission: Mapped[str] = mapped_column(String(16), nullable=False, default='unknown')
    permission_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    permission_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    attempt_window: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class BookingRecipient(ScopedRow, Base):
    __tablename__ = 'vk_recipients'
    __table_args__ = (*scoped_constraints('vk_recipients'),
        ForeignKeyConstraint(['connection_id', 'child_contact_id'], ['vk_contacts.connection_id', 'vk_contacts.id']),
        UniqueConstraint('connection_id', 'child_contact_id', name='uq_vk_recipient_child'),
        Index('uq_vk_recipient_user', 'connection_id', 'linked_student_user_id', unique=True,
              postgresql_where=text('linked_student_user_id IS NOT NULL')),
        CheckConstraint('grade IS NULL OR grade BETWEEN 1 AND 11', name='ck_vk_grade'))
    child_contact_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    grade: Mapped[int | None] = mapped_column(Integer)
    linked_student_user_id: Mapped[int | None] = mapped_column(ForeignKey('users.id'))


class RecipientTeacher(Base):
    __tablename__ = 'vk_recipient_teachers'
    __table_args__ = (ForeignKeyConstraint(['connection_id', 'recipient_id'],
                                         ['vk_recipients.connection_id', 'vk_recipients.id']),
        ForeignKeyConstraint(['connection_id', 'teacher_user_id'],
                            ['vk_connection_teachers.connection_id', 'vk_connection_teachers.teacher_user_id']))
    connection_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    recipient_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    teacher_user_id: Mapped[int] = mapped_column(Integer, primary_key=True)


class ExternalIdentityLink(ScopedRow, Base):
    __tablename__ = 'vk_identity_links'
    __table_args__ = (*scoped_constraints('vk_identity_links'),
        ForeignKeyConstraint(['connection_id', 'contact_id'], ['vk_contacts.connection_id', 'vk_contacts.id']),
        CheckConstraint("purpose IN ('student','teacher')", name='ck_vk_identity_purpose'),
        Index('uq_vk_active_identity', 'contact_id', 'purpose', unique=True,
              postgresql_where=text('revoked_at IS NULL')),
        Index('uq_vk_active_identity_user', 'connection_id', 'user_id', 'purpose', unique=True,
              postgresql_where=text('revoked_at IS NULL')))
    contact_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    purpose: Mapped[str] = mapped_column(String(16), nullable=False)
    verified_method: Mapped[str] = mapped_column(String(32), nullable=False)
    verified_by: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    verified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ParentGrant(ScopedRow, Base):
    __tablename__ = 'vk_parent_grants'
    __table_args__ = (*scoped_constraints('vk_parent_grants'),
        ForeignKeyConstraint(['connection_id', 'parent_contact_id'], ['vk_contacts.connection_id', 'vk_contacts.id']),
        ForeignKeyConstraint(['connection_id', 'recipient_id'], ['vk_recipients.connection_id', 'vk_recipients.id']),
        ForeignKeyConstraint(['connection_id', 'teacher_user_id'],
                            ['vk_connection_teachers.connection_id', 'vk_connection_teachers.teacher_user_id']),
        UniqueConstraint('connection_id', 'parent_contact_id', 'recipient_id', 'teacher_user_id', name='uq_vk_parent_triple'),
        Index('ix_vk_grants_teacher_state', 'teacher_user_id', 'state'),
        CheckConstraint("state IN ('pending','confirmed','rejected','revoked')", name='ck_vk_grant_state'),
        CheckConstraint("state != 'confirmed' OR (approved_by IS NOT NULL AND approved_at IS NOT NULL AND proof_reference IS NOT NULL)", name='ck_vk_grant_proof'))
    parent_contact_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    recipient_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    teacher_user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    state: Mapped[str] = mapped_column(String(16), nullable=False, default='pending')
    approved_by: Mapped[int | None] = mapped_column(ForeignKey('users.id'))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    proof_reference: Mapped[UUID | None] = mapped_column(Uuid)


class IdentityChallenge(ScopedRow, Base):
    __tablename__ = 'vk_identity_challenges'
    __table_args__ = (*scoped_constraints('vk_identity_challenges'),
        ForeignKeyConstraint(['connection_id', 'claimed_contact_id'], ['vk_contacts.connection_id', 'vk_contacts.id']),
        CheckConstraint("purpose IN ('student','teacher')", name='ck_vk_challenge_purpose'))
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    purpose: Mapped[str] = mapped_column(String(16), nullable=False)
    digest: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    session_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    auth_version: Mapped[int] = mapped_column(Integer, nullable=False)
    expected_link_revision: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    claimed_contact_id: Mapped[UUID | None] = mapped_column(Uuid)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class IdentityOperation(Base):
    __tablename__ = 'vk_identity_operations'
    __table_args__ = (
        UniqueConstraint('owner_key', 'action', 'operation_id', name='uq_vk_identity_operation'),
        Index('uq_vk_contact_operation', 'connection_id', 'operation_id', unique=True,
              postgresql_where=text('actor_contact_id IS NOT NULL')),
        ForeignKeyConstraint(['connection_id', 'actor_contact_id'], ['vk_contacts.connection_id', 'vk_contacts.id']),
        CheckConstraint('(actor_user_id IS NULL) != (actor_contact_id IS NULL)', name='ck_vk_operation_actor'),
        CheckConstraint("(state = 'committed' AND result IS NOT NULL AND error_code IS NULL) OR (state = 'rejected' AND result IS NULL AND error_code IS NOT NULL)", name='ck_vk_operation_result'))
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    connection_id: Mapped[UUID] = mapped_column(ForeignKey('vk_connections.id'), nullable=False)
    operation_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    owner_key: Mapped[str] = mapped_column(String(128), nullable=False)
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey('users.id'))
    actor_contact_id: Mapped[UUID | None] = mapped_column(Uuid)
    action: Mapped[str] = mapped_column(String(40), nullable=False)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    state: Mapped[str] = mapped_column(String(16), nullable=False, default='committed')
    error_code: Mapped[str | None] = mapped_column(String(40))
    result: Mapped[dict | None] = mapped_column(JSONB(none_as_null=True), nullable=True)


class VkActorContext(ScopedRow, Base):
    __tablename__ = 'vk_actor_contexts'
    __table_args__ = (*scoped_constraints('vk_actor_contexts'),
        ForeignKeyConstraint(['connection_id', 'contact_id'], ['vk_contacts.connection_id', 'vk_contacts.id']))
    contact_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    digest: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    contact_revision: Mapped[int] = mapped_column(Integer, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
