import asyncio
from uuid import UUID, uuid4
import pytest
from sqlalchemy import select, func
from src.modules.db_models import *
from src.modules.courses.service import CoursesService
from src.modules.courses.repository import CourseRepository
from src.modules.students.repository import StudentRepository
from src.modules.student_courses.repository import StudentCoursesRepository
from src.modules.users.models_dto import UserDTO
from src.modules.integrations_vk.models_dto import ClaimChallengeRequest, ResolveRecipientRequest
from src.modules.integrations_vk.exception import IdentityError
from tests_unit.integrations_vk.domain.test_identity import child, issue, PASSWORD, rev, linked

pytestmark=pytest.mark.asyncio


def workspace_service(w,session):
    svc=CoursesService.__new__(CoursesService)
    svc.session_db=session;svc.course_repo=CourseRepository(session)
    svc.student_repo=StudentRepository(session);svc.student_courses_repo=StudentCoursesRepository(session)
    from src.modules.teachers.repository import TeacherRepository
    svc.teacher_repo=TeacherRepository(session)
    return svc


async def test_public_workspace_creation_race_with_identity_ensure(world):
    w=world;c,_=await linked(w)
    actor=UserDTO.model_validate(await w.session.get(User,w.ids['t1']))
    async def public():
        async with w.db.factory() as s:return await workspace_service(w,s).personal_workspace(actor,w.ids['s1'],True)
    async def integration():
        async with w.db.factory() as s:return await w.service(s).resolve_invite(w.ids['t1'],UUID(c['recipient_id']),
            ResolveRecipientRequest(operation_id=uuid4(),expected_revision=2,mode='own_student',student_user_id=w.ids['s1']))
    result=await asyncio.wait_for(asyncio.gather(public(),integration(),public()),timeout=10)
    assert result[0].id==result[2].id
    assert await w.session.scalar(select(func.count()).select_from(Course))==1
    assert await w.session.scalar(select(func.count()).select_from(StudentCourse))==1


async def test_challenge_claim_concurrent_failures_are_limited(world):
    w=world;c=await child(w)
    async def invalid():
        async with w.db.factory() as s:
            try:await w.service(s).claim_challenge(ClaimChallengeRequest(operation_id=uuid4(),actor_context=c['actor_context'],secret='x'*43))
            except IdentityError as e:return e.code
    failures=await asyncio.wait_for(asyncio.gather(*(invalid() for _ in range(8))),timeout=10)
    assert failures.count('NOT_FOUND')==5 and failures.count('RATE_LIMITED')==3


async def test_fresh_challenge_same_contact_two_users_and_two_finalize_operations(world):
    w=world;c=await child(w);a=await issue(w);b=await issue(w,'other')
    await w.svc.claim_challenge(ClaimChallengeRequest(operation_id=uuid4(),actor_context=c['actor_context'],secret=a.secret))
    await w.svc.claim_challenge(ClaimChallengeRequest(operation_id=uuid4(),actor_context=c['actor_context'],secret=b.secret))
    async def confirm(user,ch):
        async with w.db.factory() as s:
            try:return await w.service(s).confirm_challenge(w.ids[user],'same-session',PASSWORD,ch.challenge_id,rev(2))
            except IdentityError as e:return e.code
    outcomes=await asyncio.wait_for(asyncio.gather(confirm('s1',a),confirm('other',b)),timeout=10)
    assert outcomes.count('IDENTITY_COLLISION')==1
    assert await w.session.scalar(select(func.count()).select_from(ExternalIdentityLink))==1


async def test_relink_different_contact_cannot_merge_canonical_recipient(world):
    w=world;c,_=await linked(w)
    await w.svc.unlink(w.ids['s1'],'same-session',PASSWORD,w.connection,rev())
    new=await child(w,'102');ch=await issue(w)
    await w.svc.claim_challenge(ClaimChallengeRequest(operation_id=uuid4(),actor_context=new['actor_context'],secret=ch.secret))
    with pytest.raises(IdentityError,match='IDENTITY_COLLISION'):
        await w.svc.confirm_challenge(w.ids['s1'],'same-session',PASSWORD,ch.challenge_id,rev(2))
    old=await w.session.get(BookingRecipient,UUID(c['recipient_id']))
    fresh=await w.session.get(BookingRecipient,UUID(new['recipient_id']))
    assert old.linked_student_user_id==w.ids['s1'] and fresh.linked_student_user_id is None


async def test_invitation_preserves_refresh_reset_revoke_and_public_create(world):
    w=world
    from src.modules.users.models import UserRole
    from src.modules.users.models_dto import RegisterUserRequestDTO
    from src.modules.students.repository import StudentRepository
    from src.modules.teachers.repository import TeacherRepository
    users=w.svc.users
    users.student_repo=StudentRepository(w.session);users.teacher_repo=TeacherRepository(w.session)
    actor=UserDTO.model_validate(await w.session.get(User,w.ids['t1']))
    response=await users.create_user(RegisterUserRequestDTO(username='public-synthetic',role=UserRole.STUDENT,
        first_name='Public',last_name='Synthetic',school_grade=6),actor)
    user=await w.session.get(User,response.id)
    assert not user.is_activated and response.activation_link and user.username=='public-synthetic'
    assert await w.session.scalar(select(func.count()).select_from(TeacherStudent))==3
    from src.modules.account_invitations.service import InvitationService
    invitations=InvitationService(users)
    first=response.activation_link.split('=')[1]
    replacement=await invitations.issue(user.id,'invite',actor)
    with pytest.raises(Exception):await invitations.consume(first,'invite','New-synthetic-123')
    await invitations.consume(replacement.activation_link.split('=')[1],'invite','New-synthetic-123')
    admin=UserDTO.model_validate(await w.session.get(User,w.ids['admin']))
    # Actual refresh tokens are revoked by reset consume, not just auth_version.
    w.session.add(RefreshToken(user_id=user.id,digest='synthetic-refresh',family_id=uuid4().hex,
        expires_at=w.svc.clock()+__import__('datetime').timedelta(days=1)))
    await w.session.commit()
    reset=await invitations.issue(user.id,'reset',admin)
    await invitations.consume(reset.activation_link.split('=')[1],'reset','Reset-synthetic-456')
    token=(await w.session.scalars(select(RefreshToken).where(RefreshToken.user_id==user.id))).one()
    assert token.is_revoked
    await w.session.refresh(user);assert user.auth_version==2


@pytest.mark.parametrize('failures', [2,3])
async def test_changed_discovery_retries_whole_transaction_with_bounded_budget(world,monkeypatch,failures):
    from src.modules.integrations_vk.service import RetryDiscovery
    w=world;c=await child(w);original=w.svc.repo.schedules;attempts=0
    async def changed(ids):
        nonlocal attempts
        attempts+=1
        if attempts<=failures:raise RetryDiscovery()
        await original(ids)
    monkeypatch.setattr(w.svc.repo,'schedules',changed)
    request=ResolveRecipientRequest(operation_id=uuid4(),expected_revision=1,mode='new_student')
    if failures==3:
        with pytest.raises(IdentityError,match='RETRY_LATER'):
            await w.svc.resolve_invite(w.ids['t1'],UUID(c['recipient_id']),request)
        assert await w.session.scalar(select(func.count()).select_from(IdentityOperation))==0
    else:
        assert (await w.svc.resolve_invite(w.ids['t1'],UUID(c['recipient_id']),request)).invitation
        assert await w.session.scalar(select(func.count()).select_from(Course))==1
    assert attempts==3


@pytest.mark.parametrize('case',['archive','expired','history_revoked','multiple'])
async def test_resolution_never_restores_unwritable_or_ambiguous_workspace(world,case):
    from datetime import timedelta
    from src.modules.courses.models import AvatarCoursesType
    w=world;c,_=await linked(w)
    for n in range(2 if case=='multiple' else 1):
        course=Course(teacher_id=w.teacher_ids[0],name='Synthetic',slug=f'synthetic-{n}',
            avatar_type=AvatarCoursesType.DEFAULT,is_deleted=case=='archive')
        w.session.add(course);await w.session.flush()
        w.session.add(StudentCourse(course_id=course.id,student_id=w.student_ids[0],
            expires_at=w.svc.clock()-timedelta(seconds=1) if case=='expired' else None,
            history_revoked=case=='history_revoked'))
    await w.session.commit()
    with pytest.raises(IdentityError,match='COURSE_NOT_WRITABLE'):
        await w.svc.resolve_invite(w.ids['t1'],UUID(c['recipient_id']),ResolveRecipientRequest(
            operation_id=uuid4(),expected_revision=2,mode='own_student',student_user_id=w.ids['s1']))
    assert await w.session.scalar(select(func.count()).select_from(Course))==(2 if case=='multiple' else 1)


async def test_expired_claim_durable_rejection_and_actor_context_expiry(world):
    from datetime import timedelta
    w=world;c=await child(w);ch=await issue(w)
    row=await w.session.get(IdentityChallenge,ch.challenge_id)
    row.expires_at=w.svc.clock()-timedelta(seconds=1);await w.session.commit()
    data=ClaimChallengeRequest(operation_id=uuid4(),actor_context=c['actor_context'],secret=ch.secret)
    with pytest.raises(IdentityError,match='CHALLENGE_EXPIRED'):await w.svc.claim_challenge(data)
    assert await w.session.scalar(select(func.count()).select_from(ExternalIdentityLink))==0
    ctx=(await w.session.scalars(select(VkActorContext))).one()
    ctx.expires_at=w.svc.clock()-timedelta(seconds=1);await w.session.commit()
    with pytest.raises(IdentityError,match='NOT_FOUND'):await w.svc.actor_context(c['actor_context'])


@pytest.mark.parametrize('code',['40P01','40001'])
async def test_database_retry_rolls_back_all_stages_before_retry(world,monkeypatch,code):
    from sqlalchemy.exc import DBAPIError
    import src.modules.integrations_vk.service as module
    w=world;c=await child(w);original=module.stage_link_student;calls=0
    class SyntheticDBError(Exception):sqlstate=code
    async def transient(*args,**kwargs):
        nonlocal calls
        result=await original(*args,**kwargs);calls+=1
        if calls==1:raise DBAPIError('synthetic',None,SyntheticDBError())
        return result
    monkeypatch.setattr(module,'stage_link_student',transient)
    result=await w.svc.resolve_invite(w.ids['t1'],UUID(c['recipient_id']),ResolveRecipientRequest(
        operation_id=uuid4(),expected_revision=1,mode='new_student'))
    assert result.invitation and calls==2
    assert await w.session.scalar(select(func.count()).select_from(User))==7
    assert await w.session.scalar(select(func.count()).select_from(Course))==1


async def test_public_admin_can_still_create_teacher(world):
    from src.modules.users.models_dto import RegisterUserRequestDTO
    from src.modules.users.models import UserRole
    w=world
    actor=UserDTO.model_validate(await w.session.get(User,w.ids['admin']))
    result=await w.svc.users.create_user(RegisterUserRequestDTO(username='synthetic-new-teacher',
        role=UserRole.TEACHER,first_name='New',last_name='Teacher'),actor)
    assert result.activation_link
    teacher=(await w.session.scalars(select(Teacher).where(Teacher.user_id==result.id))).one()
    assert teacher.first_name=='New'
