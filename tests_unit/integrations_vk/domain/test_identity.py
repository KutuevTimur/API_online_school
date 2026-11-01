import asyncio
from datetime import timedelta
from uuid import UUID, uuid4
import pytest
from sqlalchemy import func, select
from src.modules.db_models import *
from src.modules.integrations_vk.exception import IdentityError
from src.modules.integrations_vk.models_dto import (
    Candidate, IssueChallengeRequest, ClaimChallengeRequest, RevisionRequest, ResolveRecipientRequest,
)
from src.modules.integrations_vk.service import digest

pytestmark = pytest.mark.asyncio
PASSWORD = 'Synthetic-only-123'


async def child(w, subject='101', teacher='t1', service=None, connection=None):
    return await (service or w.svc).observe_trusted(connection or w.connection,
        '701' if connection == w.second else '700', subject, subject, w.ids[teacher],
        Candidate(first_name='Имя', last_name='Synthetic', grade=5))


def rev(n=1, op=None):
    return RevisionRequest(operation_id=op or uuid4(), expected_revision=n)


async def issue(w, key='s1', session='same-session', service=None, connection=None):
    return await (service or w.svc).issue_challenge(w.ids[key], session, PASSWORD,
        IssueChallengeRequest(operation_id=uuid4(), connection_id=connection or w.connection,
                              purpose='teacher' if key.startswith('t') else 'student'))


async def linked(w, key='s1', subject='101'):
    c = await child(w, subject)
    challenge = await issue(w, key)
    await w.svc.claim_challenge(ClaimChallengeRequest(operation_id=uuid4(), actor_context=c['actor_context'], secret=challenge.secret))
    await w.svc.confirm_challenge(w.ids[key], 'same-session', PASSWORD, challenge.challenge_id, rev(2))
    return c, challenge


async def count(w, model):
    return await w.session.scalar(select(func.count()).select_from(model))


async def test_parent_child_race_canonical_and_no_profile_overwrite(world):
    w=world
    async def observe(parent):
        async with w.db.factory() as s:
            return await w.service(s).observe_trusted(w.connection, '700', '202' if parent else '101',
                '202' if parent else '101', w.ids['t1'], Candidate(first_name='First',last_name='Candidate'),
                child_subject='101' if parent else None)
    parent, kid = await asyncio.gather(observe(True), observe(False))
    assert parent['recipient_id'] == kid['recipient_id']
    assert await count(w, BookingRecipient)==1 and await count(w, ParentGrant)==1
    r=await w.session.get(BookingRecipient, UUID(kid['recipient_id']))
    original=(r.first_name,r.last_name,r.grade)
    await child(w)
    await w.session.refresh(r)
    assert (r.first_name,r.last_name,r.grade)==original and r.linked_student_user_id is None


async def test_new_student_atomic_invite_receipt_replay_activation(world):
    w=world;c=await child(w); rid=UUID(c['recipient_id'])
    request=ResolveRecipientRequest(operation_id=uuid4(),expected_revision=1,mode='new_student')
    before=await count(w,User)
    response=await w.svc.resolve_invite(w.ids['t1'],rid,request)
    assert response.invitation.activation_link.startswith('/activate#token=')
    recipient=await w.session.get(BookingRecipient,rid)
    user=await w.session.get(User,recipient.linked_student_user_id)
    assert user.is_active and not user.is_activated and user.username.startswith('student-')
    assert await count(w,User)==before+1 and await count(w,Course)==1 and await count(w,StudentCourse)==1
    assert await count(w,AccountInvitation)==1 and await count(w,AuditEvent)==1
    replay=await w.svc.resolve_invite(w.ids['t1'],rid,request)
    assert replay.operation==response.operation and replay.invitation is None
    receipt=(await w.session.scalars(select(IdentityOperation))).one()
    raw=response.invitation.activation_link.split('=')[1]
    assert raw not in str(receipt.result)
    from src.modules.account_invitations.service import InvitationService
    await InvitationService(w.svc.users).consume(raw,'invite','New-synthetic-456')
    await w.session.refresh(user)
    assert user.is_activated and user.auth_version==1 and await count(w,Course)==1
    assert await count(w,Lesson)==0
    with pytest.raises(Exception):
        await InvitationService(w.svc.users).consume(raw,'invite','Another-456')


@pytest.mark.parametrize('stage', ['student','pair','course','enroll','invite','audit'])
async def test_failure_injection_rolls_back_entire_graph(world,monkeypatch,stage):
    w=world;c=await child(w)
    from src.modules.integrations_vk import service, stages
    from src.modules.account_invitations.service import InvitationService
    from src.modules.audit_events.service import AuditEventsService
    if stage=='student': owner,name=service,'stage_create_inactive_student'
    elif stage=='pair': owner,name=service,'stage_link_student'
    elif stage=='course': owner,name=service,'stage_ensure_workspace'
    elif stage=='enroll': owner,name=stages,'stage_enroll'
    elif stage=='invite': owner,name=InvitationService,'stage_issue'
    else: owner,name=AuditEventsService,'stage'
    original=getattr(owner,name)
    if stage=='audit':
        def fail(*args,**kw):
            original(*args,**kw);raise RuntimeError('synthetic injection')
    else:
        async def fail(*args,**kw):
            await original(*args,**kw);raise RuntimeError('synthetic injection')
    monkeypatch.setattr(owner,name,fail)
    before={m:await count(w,m) for m in (User,Student,TeacherStudent,Course,StudentCourse,AccountInvitation,AccountAudit,AuditEvent,IdentityOperation,ExternalIdentityLink)}
    with pytest.raises(RuntimeError,match='synthetic injection'):
        await w.svc.resolve_invite(w.ids['t1'],UUID(c['recipient_id']),ResolveRecipientRequest(
            operation_id=uuid4(),expected_revision=1,mode='new_student'))
    assert {m:await count(w,m) for m in before}==before
    r=await w.session.get(BookingRecipient,UUID(c['recipient_id']))
    assert r.linked_student_user_id is None and r.revision==1


async def test_two_concurrent_resolve_same_operation_and_different_operation(world):
    w=world;c=await child(w);r=UUID(c['recipient_id'])
    request=ResolveRecipientRequest(operation_id=uuid4(),expected_revision=1,mode='new_student')
    async def resolve(data):
        async with w.db.factory() as s:
            try:return await w.service(s).resolve_invite(w.ids['t1'],r,data)
            except IdentityError as e:return e.code
    a,b=await asyncio.gather(resolve(request),resolve(request))
    assert a.operation==b.operation and sum(x.invitation is not None for x in (a,b))==1
    assert await count(w,Course)==1
    c=await child(w,'102');r=UUID(c['recipient_id'])
    results=await asyncio.gather(*(resolve(ResolveRecipientRequest(operation_id=uuid4(),expected_revision=1,mode='new_student')) for _ in range(2)))
    assert sum(isinstance(x,str) and x=='STALE_REVISION' for x in results)==1
    assert await count(w,Course)==2


async def test_self_protocol_same_session_claim_once_and_replay(world):
    w=world;c=await child(w);data=IssueChallengeRequest(operation_id=uuid4(),connection_id=w.connection,purpose='student')
    issued=await w.svc.issue_challenge(w.ids['s1'],'session',PASSWORD,data)
    replay=await w.svc.issue_challenge(w.ids['s1'],'session',PASSWORD,data)
    assert replay.challenge_id==issued.challenge_id and replay.secret is None
    assert await count(w,ExternalIdentityLink)==0
    claim=ClaimChallengeRequest(operation_id=uuid4(),actor_context=c['actor_context'],secret=issued.secret)
    result=await w.svc.claim_challenge(claim)
    assert await w.svc.claim_challenge(claim)==result and await count(w,ExternalIdentityLink)==0
    await w.svc.confirm_challenge(w.ids['s1'],'session',PASSWORD,issued.challenge_id,rev(2))
    assert await count(w,ExternalIdentityLink)==1
    with pytest.raises(IdentityError,match='NOT_FOUND'):
        await w.svc.confirm_challenge(w.ids['s1'],'session',PASSWORD,issued.challenge_id,rev(2))
    assert (await w.session.get(BookingRecipient,UUID(c['recipient_id']))).linked_student_user_id==w.ids['s1']


async def test_two_claims_compete_and_only_claimed_contact_can_finalize(world):
    w=world;c1=await child(w);c2=await child(w,'102');challenge=await issue(w)
    async def claim(c):
        async with w.db.factory() as s:
            try:return await w.service(s).claim_challenge(ClaimChallengeRequest(
                operation_id=uuid4(),actor_context=c['actor_context'],secret=challenge.secret))
            except IdentityError as e:return e.code
    results=await asyncio.gather(claim(c1),claim(c2))
    assert sum(x=='IDENTITY_COLLISION' for x in results)==1
    row=await w.session.get(IdentityChallenge,challenge.challenge_id)
    assert row.claimed_contact_id is not None and await count(w,ExternalIdentityLink)==0
    data=rev(2)
    async def confirm():
        async with w.db.factory() as s:
            try:return await w.service(s).confirm_challenge(w.ids['s1'],'same-session',PASSWORD,challenge.challenge_id,data)
            except IdentityError as e:return e.code
    a,b=await asyncio.gather(confirm(),confirm())
    assert a==b and await count(w,ExternalIdentityLink)==1


@pytest.mark.parametrize('case', ['wrong_session','wrong_user','wrong_password','expired','auth_version','inactive','deactivated','wrong_group','wrong_role','stale'])
async def test_challenge_negative_matrix(world,case):
    w=world;c=await child(w);ch=await issue(w)
    claim=ClaimChallengeRequest(operation_id=uuid4(),actor_context=c['actor_context'],secret=ch.secret)
    if case=='wrong_group':
        c2=await child(w,'103',connection=w.second)
        with pytest.raises(IdentityError,match='NOT_FOUND'):
            await w.svc.claim_challenge(claim.model_copy(update={'actor_context':c2['actor_context']}))
        return
    if case=='wrong_role':
        with pytest.raises(IdentityError,match='SCOPE_DENIED'):
            await w.svc.issue_challenge(w.ids['s1'],'s',PASSWORD,IssueChallengeRequest(operation_id=uuid4(),connection_id=w.connection,purpose='teacher'))
        return
    await w.svc.claim_challenge(claim)
    if case=='expired':
        row=await w.session.get(IdentityChallenge,ch.challenge_id);row.expires_at=w.svc.clock()-timedelta(seconds=1);await w.session.commit()
    if case in {'auth_version','inactive','deactivated'}:
        user=await w.session.get(User,w.ids['s1'])
        if case=='auth_version':user.auth_version+=1
        elif case=='inactive':user.is_active=False
        else:user.is_activated=False
        await w.session.commit()
    with pytest.raises(IdentityError):
        await w.svc.confirm_challenge(w.ids['other'] if case=='wrong_user' else w.ids['s1'],
            'other-session' if case=='wrong_session' else 'same-session',
            'wrong' if case=='wrong_password' else PASSWORD,ch.challenge_id,rev(1 if case=='stale' else 2))
    assert await count(w,ExternalIdentityLink)==0


async def test_forwarded_secret_requires_original_session_and_masked_review(world):
    w=world;attacker=await child(w,'666');ch=await issue(w)
    await w.svc.claim_challenge(ClaimChallengeRequest(operation_id=uuid4(),actor_context=attacker['actor_context'],secret=ch.secret))
    with pytest.raises(IdentityError,match='NOT_FOUND'):
        await w.svc.confirm_challenge(w.ids['s1'],'attacker-session',PASSWORD,ch.challenge_id,rev(2))
    status=await w.svc.status(w.ids['s1'],'same-session')
    assert status.challenges[0]['claimed_contact']=='…66' and await count(w,ExternalIdentityLink)==0
    assert (await w.svc.status(w.ids['other'],'same-session')).challenges==[]


async def test_rate_limit_is_actor_scoped_and_failed_attempts_persist(world):
    w=world;c=await child(w)
    for _ in range(5):
        with pytest.raises(IdentityError,match='NOT_FOUND'):
            await w.svc.claim_challenge(ClaimChallengeRequest(operation_id=uuid4(),actor_context=c['actor_context'],secret='x'*43))
    good=await issue(w)
    with pytest.raises(IdentityError,match='RATE_LIMITED'):
        await w.svc.claim_challenge(ClaimChallengeRequest(operation_id=uuid4(),actor_context=c['actor_context'],secret=good.secret))
    other=await child(w,'102')
    await w.svc.claim_challenge(ClaimChallengeRequest(operation_id=uuid4(),actor_context=other['actor_context'],secret=good.secret))


async def test_contact_collision_never_reassigns_user(world):
    w=world;c,_=await linked(w);ch=await issue(w,'other')
    with pytest.raises(IdentityError,match='IDENTITY_COLLISION'):
        await w.svc.claim_challenge(ClaimChallengeRequest(operation_id=uuid4(),actor_context=c['actor_context'],secret=ch.secret))
    assert (await w.session.get(BookingRecipient,UUID(c['recipient_id']))).linked_student_user_id==w.ids['s1']


async def test_unlink_revokes_context_preserves_recipient_and_receipt(world):
    w=world;c,ch=await linked(w)
    data=rev()
    op=await w.svc.unlink(w.ids['s1'],'same-session',PASSWORD,w.connection,data)
    assert await w.svc.unlink(w.ids['s1'],'same-session',PASSWORD,w.connection,data)==op
    assert await count(w,BookingRecipient)==1
    with pytest.raises(IdentityError,match='NOT_FOUND'):await w.svc.actor_context(c['actor_context'])
    assert (await w.session.get(BookingRecipient,UUID(c['recipient_id']))).linked_student_user_id==w.ids['s1']
    assert (await w.svc.status(w.ids['s1'],'same-session')).items==[]


async def test_parent_scope_confirm_reject_revoke_no_login_grants(world):
    w=world
    p=await w.svc.observe_trusted(w.connection,'700','202','202',w.ids['t1'],Candidate(first_name='Child',last_name='Candidate'),child_subject='101')
    rid,gid=UUID(p['recipient_id']),UUID(p['grant_id'])
    with pytest.raises(IdentityError,match='GRANT_PENDING'):await w.svc.require_parent(p['actor_context'],rid,w.ids['t1'])
    with pytest.raises(IdentityError,match='NOT_FOUND'):await w.svc.decide_grant(w.ids['t2'],gid,'confirm',rev())
    with pytest.raises(IdentityError,match='SCOPE_DENIED'):
        await w.svc.resolve_invite(w.ids['t1'],rid,ResolveRecipientRequest(operation_id=uuid4(),expected_revision=1,mode='new_student'))
    await w.svc.decide_grant(w.ids['t1'],gid,'confirm',rev())
    assert (await w.svc.require_parent(p['actor_context'],rid,w.ids['t1'])).state=='confirmed'
    with pytest.raises(IdentityError,match='NOT_FOUND'):await w.svc.require_parent(p['actor_context'],rid,w.ids['t2'])
    assert await count(w,ExternalIdentityLink)==0 and await count(w,AccountInvitation)==0
    await w.svc.decide_grant(w.ids['t1'],gid,'revoke',rev(2))
    with pytest.raises(IdentityError,match='GRANT_REVOKED'):await w.svc.require_parent(p['actor_context'],rid,w.ids['t1'])
    # Replay of the original decision is still only its immutable receipt.
    p2=await w.svc.observe_trusted(w.connection,'700','203','203',w.ids['t2'],Candidate(first_name='Child',last_name='Other'),child_subject='101')
    await w.svc.decide_grant(w.ids['t2'],UUID(p2['grant_id']),'reject',rev())
    assert (await w.session.get(ParentGrant,gid)).state=='revoked'


@pytest.mark.parametrize('case', ['foreign_teacher','active_without_self_link','disabled','second_teacher','new_for_known'])
async def test_resolve_negative_access_matrix(world,case):
    w=world;c=await child(w);rid=UUID(c['recipient_id']);actor=w.ids['t1'];mode='own_student';target=w.ids['s1']
    if case=='foreign_teacher':actor=w.ids['t2']
    if case=='second_teacher':
        c=await child(w,teacher='t2');rid=UUID(c['recipient_id']);actor=w.ids['t2'];target=w.ids['s2']
    if case=='disabled':
        u=await w.session.get(User,w.ids['s2']);u.is_active=False;await w.session.commit();target=u.id
    if case=='new_for_known':
        await linked(w);mode='new_student';target=None
    with pytest.raises(IdentityError):
        await w.svc.resolve_invite(actor,rid,ResolveRecipientRequest(operation_id=uuid4(),expected_revision=2 if case=='new_for_known' else 1,mode=mode,student_user_id=target))
    assert await count(w,Course)==0


async def test_inactive_existing_no_duplicate_profile_update_reissue_reset(world):
    w=world;c=await child(w);rid=UUID(c['recipient_id']);before=await count(w,User)
    first=await w.svc.resolve_invite(w.ids['t1'],rid,ResolveRecipientRequest(operation_id=uuid4(),expected_revision=1,mode='own_student',student_user_id=w.ids['s2']))
    second=await w.svc.resolve_invite(w.ids['t1'],rid,ResolveRecipientRequest(operation_id=uuid4(),expected_revision=2,mode='own_student',student_user_id=w.ids['s2']))
    assert await count(w,User)==before and await count(w,Course)==1
    student=await w.session.get(Student,w.student_ids[1]);assert student.first_name=='Synthetic'
    from src.modules.account_invitations.service import InvitationService
    invitations=InvitationService(w.svc.users)
    with pytest.raises(Exception):await invitations.consume(first.invitation.activation_link.split('=')[1],'invite','After-reissue-123')
    await invitations.consume(second.invitation.activation_link.split('=')[1],'invite','After-reissue-123')
    from src.modules.users.models_dto import UserDTO
    admin=UserDTO.model_validate(await w.session.get(User,w.ids['admin']))
    reset=await invitations.issue(w.ids['s2'],'reset',admin)
    await invitations.consume(reset.activation_link.split('=')[1],'reset','After-reset-456')
    assert await count(w,ExternalIdentityLink)==1 and await count(w,Course)==1
    user=await w.session.get(User,w.ids['s2']);assert user.auth_version==2


async def test_second_teacher_only_after_admin_pair_and_active_self_link(world):
    w=world;c,_=await linked(w);rid=UUID(c['recipient_id']);await child(w,teacher='t2')
    request=ResolveRecipientRequest(operation_id=uuid4(),expected_revision=2,mode='own_student',student_user_id=w.ids['s1'])
    with pytest.raises(IdentityError,match='ADMIN_LINK_REQUIRED'):await w.svc.resolve_invite(w.ids['t2'],rid,request)
    from src.modules.teacher_students.service import TeacherStudentService
    from src.modules.teacher_students.models_dto import LinkTeacherStudentRequestDTO
    await TeacherStudentService(w.session).link(LinkTeacherStudentRequestDTO(teacher_user_id=w.ids['t2'],student_user_id=w.ids['s1']),w.ids['admin'])
    response=await w.svc.resolve_invite(w.ids['t2'],rid,request.model_copy(update={'operation_id':uuid4()}))
    assert response.invitation is None and await count(w,Course)==1 and await count(w,User)==6


async def test_operation_payload_mismatch_and_terminal_receipt_owner(world):
    w=world;c=await child(w);rid=UUID(c['recipient_id']);data=ResolveRecipientRequest(operation_id=uuid4(),expected_revision=1,mode='own_student',student_user_id=w.ids['s1'])
    with pytest.raises(IdentityError,match='SCOPE_DENIED'):await w.svc.resolve_invite(w.ids['t1'],rid,data)
    # A domain collision is durable; changing its payload never reuses the UUID.
    data=data.model_copy(update={'student_user_id':w.ids['other'],'operation_id':uuid4()})
    with pytest.raises(IdentityError,match='ADMIN_LINK_REQUIRED'):await w.svc.resolve_invite(w.ids['t1'],rid,data)
    saved=await w.svc.operation_status(w.ids['t1'],data.operation_id,'recipient_resolve')
    assert saved.state=='rejected' and saved.error['code']=='ADMIN_LINK_REQUIRED'
    with pytest.raises(IdentityError,match='NOT_FOUND'):await w.svc.operation_status(w.ids['t2'],data.operation_id,'recipient_resolve')
    with pytest.raises(IdentityError,match='PAYLOAD_MISMATCH'):
        await w.svc.resolve_invite(w.ids['t1'],rid,data.model_copy(update={'mode':'new_student','student_user_id':None}))


async def test_disabled_connection_and_user_block_context(world):
    w=world;c,_=await linked(w)
    u=await w.session.get(User,w.ids['s1']);u.is_active=False;await w.session.commit()
    with pytest.raises(IdentityError,match='ACCOUNT_BLOCKED'):await w.svc.actor_context(c['actor_context'])
    u.is_active=True;connection=await w.session.get(IntegrationConnection,w.connection);connection.enabled=False;await w.session.commit()
    with pytest.raises(IdentityError,match='CONNECTION_DISABLED'):await w.svc.actor_context(c['actor_context'])
