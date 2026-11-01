import asyncio
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4
import pytest
from sqlalchemy import select, func, text
from src.modules.db_models import *
from src.modules.integrations_vk.booking_service import BookingService
from src.modules.integrations_vk.models_dto import *
from src.modules.integrations_vk.exception import IdentityError
from tests_unit.integrations_vk.domain.test_identity import child, linked, rev, count
from tests_unit.integrations_vk.domain.test_regressions import workspace_service

pytestmark = pytest.mark.asyncio
START = datetime(2030, 1, 7, 7, tzinfo=UTC)  # Monday, 10:00 Moscow


def svc(w, session=None):
    identity = w.service(session or w.session)
    return BookingService(identity.session, identity.users)


async def window(w, start=START, teacher='t1'):
    data = PublishWindowsRequest(operation_id=uuid4(), connection_id=w.connection,
        week_start=start.astimezone(__import__('zoneinfo').ZoneInfo('Europe/Moscow')).date()-timedelta(days=start.astimezone(__import__('zoneinfo').ZoneInfo('Europe/Moscow')).weekday()),
        items=[WindowItem(start_at=start,end_at=start+timedelta(minutes=55))])
    op = await svc(w).publish(w.ids[teacher], data)
    return UUID(op.result['window_ids'][0])


async def prepared(w, kid, wid, revision=1):
    return await svc(w).prepare(PrepareBookingRequest(actor_context=kid['actor_context'],
        recipient_id=UUID(kid['recipient_id']), window_id=wid, expected_revision=revision))


def confirm(kid, prepared, revision=1):
    return ConfirmBookingRequest(actor_context=kid['actor_context'],handle=prepared['handle'],
        operation_id=prepared['operation_id'],expected_revision=revision)


async def book(w, kid, wid=None):
    wid = wid or await window(w)
    p = await prepared(w,kid,wid)
    return await svc(w).confirm_booking(confirm(kid,p))


async def test_unknown_booking_receipt_and_atomic_resolve(world):
    w=world;kid=await child(w);wid=await window(w);p=await prepared(w,kid,wid);data=confirm(kid,p)
    result=await svc(w).confirm_booking(data)
    bid=UUID(result.result['booking_id'])
    assert result.result['lesson_id'] is None and await count(w,Lesson)==0
    assert (await svc(w).booking_view(w.ids['t1'],bid)).access_state=='unresolved'
    assert (await svc(w).confirm_booking(data)).result==result.result
    assert (await svc(w).connector_receipt(kid['actor_context'],data.operation_id)).result==result.result
    with pytest.raises(IdentityError,match='PAYLOAD_MISMATCH'):
        await svc(w).confirm_booking(data.model_copy(update={'expected_revision':2}))
    response=await svc(w).resolve_booking(w.ids['t1'],bid,BookingResolveRequest(operation_id=uuid4(),
        expected_revision=1,expected_recipient_revision=1,mode='new_student'))
    assert response.invitation and await count(w,Lesson)==1 and await count(w,LessonStudent)==1
    assert await count(w,BookingEvent)==2
    assert (await svc(w).confirm_booking(data)).result==result.result  # immutable, no new lesson
    lesson=(await w.session.scalars(select(Lesson))).one()
    assert lesson.lesson_price_kopecks is None and lesson.duration_minutes==55


@pytest.mark.parametrize('price',[None,0,123456])
async def test_known_snapshot_not_repriced(world,price):
    w=world;kid,_=await linked(w)
    pair=(await w.session.scalars(select(TeacherStudent).where(TeacherStudent.student_id==w.student_ids[0]))).one()
    pair.lesson_price_kopecks=price;await w.session.commit()
    op=await book(w,kid)
    assert op.result['lesson_id'] and await count(w,Lesson)==1
    pair.lesson_price_kopecks=999999;await w.session.commit()
    lesson=await w.session.get(Lesson,op.result['lesson_id'])
    assert lesson.lesson_price_kopecks==price
    row=await w.session.get(Booking,UUID(op.result['booking_id']))
    assert row.lesson_price_kopecks==price


async def test_two_connections_two_children_one_slot(world):
    w=world;a=await child(w);b=await child(w,'102');wid=await window(w)
    pa,pb=await prepared(w,a,wid),await prepared(w,b,wid)
    async def run(kid,p):
        async with w.db.factory() as s:
            try:return await svc(w,s).confirm_booking(confirm(kid,p))
            except IdentityError as e:return e.code
    result=await asyncio.wait_for(asyncio.gather(run(a,pa),run(b,pb)),10)
    assert sum(isinstance(r,OperationResult) for r in result)==1
    assert await count(w,Booking)==1 and await count(w,BookingEvent)==1


async def test_parent_child_confirm_race_and_revoke(world):
    w=world;kid=await child(w)
    parent=await w.svc.observe_trusted(w.connection,'700','202','202',w.ids['t1'],
        Candidate(first_name='Child',last_name='Synthetic'),child_subject='101')
    grant=(await w.session.scalars(select(ParentGrant))).one()
    await w.svc.decide_grant(w.ids['t1'],grant.id,'confirm',rev())
    wid=await window(w);a=await prepared(w,kid,wid);b=await prepared(w,parent,wid)
    async def run(k,p):
        async with w.db.factory() as s:
            try:return await svc(w,s).confirm_booking(confirm(k,p))
            except IdentityError as e:return e.code
    result=await asyncio.wait_for(asyncio.gather(run(kid,a),run(parent,b)),10)
    assert sum(isinstance(r,OperationResult) for r in result)==1 and await count(w,Booking)==1
    await w.svc.decide_grant(w.ids['t1'],grant.id,'revoke',rev(2))
    with pytest.raises(IdentityError,match='GRANT_REVOKED'):
        await prepared(w,parent,await window(w,START+timedelta(hours=2)))


@pytest.mark.parametrize('cause',['normal','closed','past','other'])
async def test_cancel_reopen_revision_old_callbacks(world,cause):
    w=world;kid=await child(w);wid=await window(w);p=await prepared(w,kid,wid)
    original=await svc(w).confirm_booking(confirm(kid,p));bid=UUID(original.result['booking_id'])
    service=svc(w)
    if cause=='closed':await service.close(w.ids['t1'],wid,rev(2))
    if cause=='past':service.clock=lambda:START+timedelta(days=1)
    if cause=='other':
        from src.modules.lessons.models import LessonStatus
        w.session.add(Course(teacher_id=w.teacher_ids[0],name='Other',slug='other',avatar_type='default'))
        await w.session.flush();course=(await w.session.scalars(select(Course))).one()
        w.session.add(Lesson(teacher_id=w.teacher_ids[0],course_id=course.id,title='Other',scheduled_at=START))
        await w.session.commit()
    await service.cancel(w.ids['t1'],bid,rev())
    row=await w.session.get(BookingWindow,wid);await w.session.refresh(row)
    assert row.status==('published' if cause=='normal' else 'closed')
    assert (await svc(w).confirm_booking(confirm(kid,p))).result==original.result
    assert await count(w,Booking)==1
    if cause=='normal':
        newer=await prepared(w,kid,wid,row.revision)
        await svc(w).confirm_booking(confirm(kid,newer,row.revision))
        assert await count(w,Booking)==2


async def test_handle_expiry_foreign_and_date_contract(world):
    w=world;kid=await child(w);other=await child(w,'102');wid=await window(w);p=await prepared(w,kid,wid)
    with pytest.raises(IdentityError,match='NOT_FOUND'):
        await svc(w).confirm_booking(confirm(other,p))
    handle=(await w.session.scalars(select(BookingInteraction))).one()
    handle.expires_at=datetime.now(UTC)-timedelta(seconds=1);await w.session.commit()
    with pytest.raises(IdentityError,match='HANDLE_EXPIRED'):await svc(w).confirm_booking(confirm(kid,p))
    assert await count(w,Booking)==0
    from pydantic import ValidationError
    with pytest.raises(ValidationError):PublishWindowsRequest(operation_id=uuid4(),connection_id=w.connection,
        week_start='2030-01-08',items=[{'start_at':START,'end_at':START+timedelta(minutes=55)}])
    with pytest.raises(ValidationError):WindowItem(start_at=START.replace(tzinfo=None),end_at=START+timedelta(minutes=55))
    # Adjacent intervals, Moscow midnight and end of week are valid.
    await window(w,START+timedelta(minutes=55))
    await window(w,datetime(2030,1,13,20,5,tzinfo=UTC))


async def test_materialize_batch_idempotent_and_past_review(world):
    w=world;kid=await child(w)
    a=await book(w,kid);b=await book(w,kid,await window(w,START+timedelta(hours=2)))
    bid=UUID(a.result['booking_id'])
    service=svc(w);service.clock=lambda:START+timedelta(hours=1)
    request=BookingResolveRequest(operation_id=uuid4(),expected_revision=1,expected_recipient_revision=1,mode='new_student')
    with pytest.raises(IdentityError,match='REVIEW_REQUIRED'):await service.resolve_booking(w.ids['t1'],bid,request)
    assert await count(w,User)==6 and await count(w,Lesson)==0
    request=request.model_copy(update={'operation_id':uuid4(),'review_past':True})
    result=await service.resolve_booking(w.ids['t1'],bid,request)
    assert result.invitation and await count(w,Lesson)==2
    repeated=await service.resolve_booking(w.ids['t1'],bid,request)
    assert repeated.invitation is None and await count(w,Lesson)==2


@pytest.mark.parametrize('stage',['lesson','recipient','deadline','event','audit'])
async def test_failure_rolls_back_whole_confirm(world,monkeypatch,stage):
    w=world;kid,_=await linked(w);wid=await window(w);p=await prepared(w,kid,wid)
    from src.modules.integrations_vk import booking_service, booking_stages
    original=booking_service.stage_lesson_with_snapshot
    async def fail(*args,**kwargs):
        if stage=='lesson':raise RuntimeError('injected')
        await original(*args,**kwargs)
        raise RuntimeError('injected')
    if stage in {'lesson','recipient'}:monkeypatch.setattr(booking_service,'stage_lesson_with_snapshot',fail)
    elif stage=='deadline':
        from src.modules.homework_placements.service import HomeworkPlacementsService
        async def recalc(*args):raise RuntimeError('injected')
        monkeypatch.setattr(HomeworkPlacementsService,'recalculate_course',recalc)
    elif stage=='audit':
        from src.modules.audit_events.service import AuditEventsService
        def audit(*args):raise RuntimeError('injected')
        monkeypatch.setattr(AuditEventsService,'stage',audit)
    else:
        from sqlalchemy import event
        def injected(*args):raise RuntimeError('injected')
        event.listen(BookingEvent,'before_insert',injected)
    try:
        with pytest.raises(RuntimeError,match='injected'):await svc(w).confirm_booking(confirm(kid,p))
    finally:
        if stage=='event':event.remove(BookingEvent,'before_insert',injected)
    assert await count(w,Booking)==0 and await count(w,Lesson)==0 and await count(w,BookingEvent)==0
    row=await w.session.get(BookingWindow,wid);assert row.status=='published' and row.revision==1


async def test_http_scope_and_openapi(world):
    from tests_unit.integrations_vk.domain.test_http import client,HEADERS
    w=world;kid=await child(w);op=await book(w,kid);bid=op.result['booking_id']
    async with client(w,'s1') as c:
        assert (await c.get('/teacher-planning/bookings/'+bid,headers=HEADERS)).status_code==404
        assert (await c.post('/integrations/vk/bookings/confirm',json={'actor_context':'x'*43,'handle':'y'*43,'expected_revision':1,'operation_id':str(uuid4())},headers=HEADERS)).status_code==401
    async with client(w,'t2') as c:
        assert (await c.get('/teacher-planning/bookings/'+bid,headers=HEADERS)).status_code==404
    async with client(w,'t1') as c:
        assert (await c.get('/teacher-planning/bookings/'+bid,headers=HEADERS)).status_code==200
        schema=(await c.get('/openapi.json')).json()
        assert schema['components']['schemas']['ConfirmBookingRequest']['additionalProperties'] is False
        assert '/teacher-planning/bookings/{id}/materialize' in schema['paths']


def lessons_service(w,s,regular=False):
    from src.modules.lessons.service import LessonsService,RegularLessonsService
    from src.modules.lessons.repository import LessonsRepository
    from src.modules.courses.repository import CourseRepository
    from src.modules.students.repository import StudentRepository
    from src.modules.teachers.repository import TeacherRepository
    return (RegularLessonsService if regular else LessonsService)(LessonsRepository(s),CourseRepository(s),
        StudentRepository(s),TeacherRepository(s),s)


async def workspace(w):
    from src.modules.users.models_dto import UserDTO
    return await workspace_service(w,w.session).personal_workspace(
        UserDTO.model_validate(await w.session.get(User,w.ids['t1'])),w.ids['s1'],True)


@pytest.mark.parametrize('order',['bot_first','teacher_first','parallel'])
async def test_site_bot_ordering_real_sessions_and_warning(world,order):
    from src.modules.lessons.models_dto import CreateLessonRequestDTO
    w=world;kid=await child(w);wid=await window(w);p=await prepared(w,kid,wid);course=await workspace(w)
    async def teacher():
        async with w.db.factory() as s:
            return await lessons_service(w,s).create_lesson(w.ids['t1'],CreateLessonRequestDTO(
                course_id=course.id,student_user_id=w.ids['s1'],title='Site',scheduled_at=START))
    async def bot():
        async with w.db.factory() as s:
            try:return await svc(w,s).confirm_booking(confirm(kid,p))
            except IdentityError as e:return e.code
    if order=='bot_first':
        b=await bot();t=await teacher();assert t.warnings[0].booking_ids==[UUID(b.result['booking_id'])]
    elif order=='teacher_first':
        t=await teacher();assert await bot()=='SLOT_UNAVAILABLE'
    else:
        b,t=await asyncio.wait_for(asyncio.gather(bot(),teacher()),10)
        assert b=='SLOT_UNAVAILABLE' or t.warnings
    assert await count(w,Lesson)==1


async def test_regular_series_sees_booking_and_requires_warning_ack(world):
    from src.modules.lessons.models_dto import PreviewRegularLessonsRequestDTO,ConfirmRegularLessonsRequestDTO
    from src.modules.base.exception import StaleUpdate
    w=world;kid=await child(w);op=await book(w,kid);course=await workspace(w)
    service=lessons_service(w,w.session,True)
    request=PreviewRegularLessonsRequestDTO.model_validate({'operation_id':str(uuid4()),'action':'create',
        'weeks':2,'lesson':{'course_id':course.id,'student_user_id':w.ids['s1'],'title':'Series','scheduled_at':START.isoformat()}})
    preview=await service.preview_regular(w.ids['t1'],request)
    assert preview.preview.occurrences[0].conflict_booking_ids==[UUID(op.result['booking_id'])]
    with pytest.raises(StaleUpdate):await service.confirm_regular(w.ids['t1'],request.operation_id,
        ConfirmRegularLessonsRequestDTO(preview_revision=1))
    done=await service.confirm_regular(w.ids['t1'],request.operation_id,
        ConfirmRegularLessonsRequestDTO(preview_revision=1,acknowledge_conflicts=True))
    assert await count(w,Lesson)==2 and await count(w,Booking)==1


async def test_teacher_cancel_move_restore_and_purge(world):
    from src.modules.lessons.models_dto import UpdateLessonRequestDTO
    from src.modules.lessons.models import LessonStatus
    from src.modules.course_lifecycle.service import LifecycleService
    from src.modules.course_lifecycle.repository import LifecycleRepository
    from src.modules.course_lifecycle.models_dto import PurgeCourseRequest
    w=world;kid,_=await linked(w);op=await book(w,kid);lid=op.result['lesson_id'];bid=UUID(op.result['booking_id'])
    service=lessons_service(w,w.session)
    lesson=await w.session.get(Lesson,lid);course_id=lesson.course_id
    await service.update_lesson(w.ids['t1'],lid,UpdateLessonRequestDTO(expected_updated_at=lesson.updated_at,
        scheduled_at=START+timedelta(days=1)))
    row=await w.session.get(BookingWindow,(await w.session.get(Booking,bid)).window_id)
    assert row.status=='consumed' and await count(w,BookingWindow)==1
    await w.session.refresh(lesson)
    await service.update_lesson(w.ids['t1'],lid,UpdateLessonRequestDTO(expected_updated_at=lesson.updated_at,status=LessonStatus.CANCELLED))
    await w.session.refresh(row);assert row.status=='published'
    # Ordinary restore can overlap a new booking but must show the warning.
    lesson.is_deleted=True;lesson.status=LessonStatus.SCHEDULED;lesson.scheduled_at=START
    await w.session.commit()
    other=await child(w,'102')
    p=await prepared(w,other,row.id,row.revision);await svc(w).confirm_booking(confirm(other,p,row.revision))
    lifecycle=LifecycleService(LifecycleRepository(w.session),None)
    restored=await lifecycle.restore(w.ids['admin'],'lesson',lid)
    assert restored.warnings and restored.warnings[0].booking_ids
    course=await w.session.get(Course,course_id)
    with pytest.raises(IdentityError,match='PURGE_BLOCKED'):
        await lifecycle.purge(w.ids['admin'],course.id,PurgeCourseRequest(confirm_course_id=course.id,confirm_name=course.name))


async def test_d04_pending_recalculated_frozen_unchanged_and_archive_d12(world):
    from src.modules.homework_placements.service import HomeworkPlacementsService
    from src.modules.teacher_planning.repository import TeacherPlanningRepository
    from src.modules.lessons.models_dto import CreateLessonRequestDTO
    w=world;kid,_=await linked(w);course=await workspace(w)
    prior=await lessons_service(w,w.session).create_lesson(w.ids['t1'],CreateLessonRequestDTO(
        course_id=course.id,student_user_id=w.ids['s1'],title='Prior',scheduled_at=START-timedelta(days=1)))
    ls=(await w.session.scalars(select(LessonStudent))).one()
    pending=Homework(lesson_student_id=ls.id,title='Pending');frozen=Homework(lesson_student_id=ls.id,title='Frozen')
    w.session.add_all([pending,frozen]);await w.session.flush()
    placements=HomeworkPlacementsService(w.session)
    p=await placements.original(pending);f=await placements.original(frozen)
    w.session.add(HomeworkSubmission(homework_id=frozen.id,attempt_number=1,status='checked',checked_by=w.teacher_ids[0]))
    await w.session.commit()
    snapshot=(f.due_at,f.due_lesson_id,frozen.deadline)
    op=await book(w,kid)
    await w.session.refresh(p);await w.session.refresh(f);await w.session.refresh(frozen)
    assert p.due_lesson_id==op.result['lesson_id'] and (f.due_at,f.due_lesson_id,frozen.deadline)==snapshot
    teacher_planning=TeacherPlanningRepository(w.session)
    stats=await teacher_planning.weekly_earnings(w.ids['t1'],START.date())
    assert stats['lesson_count']==1
    c=await w.session.get(Course,course.id);c.is_deleted=True;await w.session.commit()
    assert (await teacher_planning.weekly_earnings(w.ids['t1'],START.date()))['lesson_count']==0


@pytest.mark.parametrize('winner',['close','confirm'])
async def test_close_confirm_serialized_connections(world,winner):
    w=world;kid=await child(w);wid=await window(w);p=await prepared(w,kid,wid)
    async with w.db.factory() as first, w.db.factory() as second:
        await svc(w,first).repo.schedules([w.ids['t1']])
        async def blocked():
            if winner=='close':
                try:return await svc(w,second).confirm_booking(confirm(kid,p))
                except IdentityError as e:return e.code
            try:return await svc(w,second).close(w.ids['t1'],wid,rev())
            except IdentityError as e:return e.code
        task=asyncio.create_task(blocked())
        # First owns the schedule prefix; second cannot commit ahead of it.
        if winner=='close':
            await svc(w,first).close(w.ids['t1'],wid,rev())
            assert await asyncio.wait_for(task,10)=='STALE_REVISION'
            assert await count(w,Booking)==0
        else:
            await svc(w,first).confirm_booking(confirm(kid,p))
            assert await asyncio.wait_for(task,10)=='STALE_REVISION'
            assert await count(w,Booking)==1


@pytest.mark.parametrize('winner',['price','confirm'])
async def test_price_confirm_serialized_connections(world,winner):
    from src.modules.teacher_planning.service import TeacherPlanningService
    from src.modules.teacher_planning.repository import TeacherPlanningRepository
    from src.modules.teacher_planning.models_dto import UpdateLessonPriceDTO
    from src.modules.users.models_dto import UserDTO
    w=world;kid,_=await linked(w);wid=await window(w);p=await prepared(w,kid,wid)
    actor=UserDTO.model_validate(await w.session.get(User,w.ids['t1']))
    async with w.db.factory() as first,w.db.factory() as second:
        await svc(w,first).repo.schedules([w.ids['t1']])
        async def price(s):
            return await TeacherPlanningService(TeacherPlanningRepository(s)).price(actor,w.ids['s1'],
                UpdateLessonPriceDTO(lesson_price_kopecks=5000,expected_price_kopecks=None))
        task=asyncio.create_task(svc(w,second).confirm_booking(confirm(kid,p)) if winner=='price' else price(second))
        if winner=='price':await price(first)
        else:await svc(w,first).confirm_booking(confirm(kid,p))
        await asyncio.wait_for(task,10)
    lesson=(await w.session.scalars(select(Lesson))).one()
    assert lesson.lesson_price_kopecks==(5000 if winner=='price' else None)


@pytest.mark.parametrize('stage',['account','workspace','enrollment','materialize','invite','receipt'])
async def test_resolve_rollback_keeps_confirmed_booking(world,monkeypatch,stage):
    w=world;kid=await child(w);op=await book(w,kid);bid=UUID(op.result['booking_id'])
    from src.modules.integrations_vk import service
    from src.modules.integrations_vk import stages
    from src.modules.account_invitations.service import InvitationService
    if stage=='account':target,name=service,'stage_create_inactive_student'
    elif stage=='workspace':target,name=service,'stage_ensure_workspace'
    elif stage=='enrollment':target,name=stages,'stage_enroll'
    elif stage=='materialize':target,name=service,'stage_materialize'
    elif stage=='invite':target,name=InvitationService,'stage_issue'
    if stage!='receipt':
        original=getattr(target,name)
        async def fail(*a,**kw):
            await original(*a,**kw)
            raise RuntimeError('injected')
        monkeypatch.setattr(target,name,fail)
    else:
        from sqlalchemy import event
        def injected(mapper,connection,row):
            if row.action=='recipient_resolve':raise RuntimeError('injected')
        event.listen(IdentityOperation,'before_insert',injected)
    try:
        with pytest.raises(RuntimeError,match='injected'):
            await svc(w).resolve_booking(w.ids['t1'],bid,BookingResolveRequest(operation_id=uuid4(),
                expected_revision=1,expected_recipient_revision=1,mode='new_student'))
    finally:
        if stage=='receipt':event.remove(IdentityOperation,'before_insert',injected)
    assert await count(w,User)==6 and await count(w,Course)==0 and await count(w,Lesson)==0
    assert await count(w,BookingEvent)==1 and await count(w,AccountInvitation)==0
    booking=await w.session.get(Booking,bid)
    assert booking.status=='confirmed' and booking.lesson_id is None and booking.revision==1


async def test_ambiguous_archived_workspace_foreign_scope_and_second_teacher(world):
    w=world;kid,_=await linked(w);await child(w,teacher='t2')
    foreign=await book(w,kid,await window(w,teacher='t2'))
    assert foreign.result['lesson_id'] is None
    with pytest.raises(IdentityError,match='NOT_FOUND'):
        await svc(w).booking_view(w.ids['t1'],UUID(foreign.result['booking_id']))
    course=await workspace(w)
    other=Course(teacher_id=w.teacher_ids[0],name='Legacy',slug='legacy',avatar_type='default')
    w.session.add(other);await w.session.flush()
    w.session.add(StudentCourse(course_id=other.id,student_id=w.student_ids[0]));await w.session.commit()
    wid=await window(w,START+timedelta(hours=2));p=await prepared(w,kid,wid)
    with pytest.raises(IdentityError,match='COURSE_NOT_WRITABLE'):await svc(w).confirm_booking(confirm(kid,p))
    course_row=await w.session.get(Course,course.id);other_row=await w.session.get(Course,other.id)
    course_row.is_deleted=True;other_row.is_deleted=True;await w.session.commit()
    p=await prepared(w,kid,wid)
    with pytest.raises(IdentityError,match='COURSE_NOT_WRITABLE'):await svc(w).confirm_booking(confirm(kid,p))


async def test_booking_schema_constraints_and_downgrade_guard(world):
    from sqlalchemy.exc import IntegrityError
    from tests_unit.integrations_vk.domain.db import downgrade
    w=world;kid=await child(w);op=await book(w,kid)
    for sql in ("UPDATE vk_bookings SET revision=0", "UPDATE vk_bookings SET lesson_price_kopecks=-1",
                "UPDATE vk_bookings SET connection_id=:foreign", "UPDATE vk_booking_windows SET week_start=week_start+1"):
        with pytest.raises(IntegrityError):
            async with w.session.begin_nested():await w.session.execute(text(sql),{'foreign':w.second})
    # Commit the read transaction before testing DDL with another connection.
    await w.session.rollback()
    with pytest.raises(RuntimeError,match='Refusing to discard VK booking'):
        async with w.db.engine.begin() as c:await c.run_sync(lambda conn:downgrade(conn,'f01220261102'))


async def test_timeout_retry_receipt_ttl_and_page_contract(world,monkeypatch):
    w=world;kid=await child(w);wid=await window(w);p=await prepared(w,kid,wid)
    data=confirm(kid,p)
    from src.modules.integrations_vk import booking_service
    original=booking_service.slot_busy
    async def timeout(*a,**kw):raise TimeoutError('synthetic before commit')
    with monkeypatch.context() as patch:
        patch.setattr(booking_service,'slot_busy',timeout)
        with pytest.raises(TimeoutError):await svc(w).confirm_booking(data)
    with pytest.raises(IdentityError,match='NOT_FOUND'):
        await svc(w).connector_receipt(kid['actor_context'],data.operation_id)
    first=await svc(w).confirm_booking(data)
    handle=(await w.session.scalars(select(BookingInteraction))).one()
    handle.expires_at=datetime.now(UTC)-timedelta(seconds=1);await w.session.commit()
    # Lost response after commit: even expired button returns immutable receipt.
    assert (await svc(w).confirm_booking(data)).result==first.result
    second=await window(w,START+timedelta(hours=2))
    page=await svc(w).list_windows(w.ids['t1'],w.connection,START.date(),limit=1)
    assert len(page.items)==1 and page.next_cursor
    next_page=await svc(w).list_windows(w.ids['t1'],w.connection,START.date(),cursor=page.next_cursor,limit=1)
    assert len(next_page.items)==1 and next_page.items[0].window_id!=page.items[0].window_id
    available=await svc(w).available_windows(kid['actor_context'],w.ids['t1'],START.date())
    assert [v.window_id for v in available]==[second]
    with pytest.raises(IdentityError,match='INVALID_REQUEST'):
        await svc(w).list_bookings(w.ids['t1'],w.connection,START.date()+timedelta(days=1))


@pytest.mark.parametrize('action',['restore','series'])
@pytest.mark.parametrize('winner',['teacher','bot'])
async def test_restore_series_confirm_two_connections(world,action,winner):
    from src.modules.lessons.models_dto import PreviewRegularLessonsRequestDTO, ConfirmRegularLessonsRequestDTO
    from src.modules.course_lifecycle.service import LifecycleService
    from src.modules.course_lifecycle.repository import LifecycleRepository
    w=world;kid=await child(w);course=await workspace(w)
    archived=None
    if action=='restore':
        archived=Lesson(course_id=course.id,teacher_id=w.teacher_ids[0],title='Restore',scheduled_at=START,is_deleted=True)
        w.session.add(archived);await w.session.commit()
    wid=await window(w);p=await prepared(w,kid,wid)
    request=PreviewRegularLessonsRequestDTO.model_validate({'operation_id':str(uuid4()),'action':'create',
        'weeks':1,'lesson':{'course_id':course.id,'student_user_id':w.ids['s1'],'title':'Series','scheduled_at':START.isoformat()}})
    if action=='series':await lessons_service(w,w.session,True).preview_regular(w.ids['t1'],request)
    async def teacher(s):
        if action=='restore':return await LifecycleService(LifecycleRepository(s),None).restore(w.ids['admin'],'lesson',archived.id)
        service=lessons_service(w,s,True)
        from src.modules.lessons.exception import RegularPreviewChanged
        try:
            return await service.confirm_regular(w.ids['t1'],request.operation_id,
                ConfirmRegularLessonsRequestDTO(preview_revision=1,acknowledge_conflicts=True))
        except RegularPreviewChanged:
            assert winner=='bot'
            refreshed=await service.get_operation(w.ids['t1'],request.operation_id)
            assert refreshed.preview.occurrences[0].conflict_booking_ids
            return await service.confirm_regular(w.ids['t1'],request.operation_id,
                ConfirmRegularLessonsRequestDTO(preview_revision=refreshed.preview_revision,acknowledge_conflicts=True))
    async def bot(s):
        try:return await svc(w,s).confirm_booking(confirm(kid,p))
        except IdentityError as e:return e.code
    async with w.db.factory() as first,w.db.factory() as second:
        await svc(w,first).repo.schedules([w.ids['t1']])
        task=asyncio.create_task(bot(second) if winner=='teacher' else teacher(second))
        result=await teacher(first) if winner=='teacher' else await bot(first)
        other=await asyncio.wait_for(task,10)
    assert await count(w,Lesson)==1
    if winner=='teacher':assert other=='SLOT_UNAVAILABLE' and await count(w,Booking)==0
    else:
        assert await count(w,Booking)==1
        if action=='restore':assert other.warnings[0].booking_ids


async def test_materialize_concurrent_after_self_link_future_snapshot_null(world):
    w=world;kid=await child(w)
    op=await book(w,kid);bid=UUID(op.result['booking_id'])
    await linked(w)
    recipient=await w.session.get(BookingRecipient,UUID(kid['recipient_id']));await w.session.refresh(recipient)
    async def materialize():
        async with w.db.factory() as s:
            try:return await svc(w,s).materialize(w.ids['t1'],bid,MaterializeRequest(operation_id=uuid4(),
                expected_revision=1,expected_recipient_revision=recipient.revision))
            except IdentityError as e:return e.code
    results=await asyncio.wait_for(asyncio.gather(materialize(),materialize()),10)
    assert sum(isinstance(r,OperationResult) for r in results)==1 and 'STALE_REVISION' in results
    assert await count(w,Lesson)==1 and await count(w,BookingEvent)==2
    lesson=(await w.session.scalars(select(Lesson))).one();assert lesson.lesson_price_kopecks is None
