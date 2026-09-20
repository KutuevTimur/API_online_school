from tests.fixturs.fixturs_db import session_db, not_open_session_db
from tests.fixturs.replace_services import (
    user_service_fixture,
    courses_service_fixture,
    compression_images_fixture,
    handler_images_fixture,
    handler_documents_fixture,
    path_builder_fixture,
)
from tests.fixturs.fixtures import (
    app_fastapi,
    config_fix,
    client_for_tests,
    lifespan_for_tests,
    cleaning_paths_fix,
)

from tests.modules.users.fixtures import create_user_fixture
from tests.modules.refresh_tokens.fixtures import create_refresh_token_fixture
from tests.modules.courses.fixtures import create_course_fixture
from tests.modules.handlers_files.fixtures import (
    create_upload_file_fixture,
    create_image_bytes_fixture,
)
from tests.modules.lessons.fixtures.fixtures import create_lesson_fixture

# New fixtures
from tests.modules.student_courses.fixtures import create_student_course_fixture
from tests.modules.lesson_students.fixtures import create_lesson_student_fixture
from tests.modules.homeworks.fixtures import create_homework_fixture
from tests.modules.lectures.fixtures import create_lecture_fixture
from tests.modules.homework_submissions.fixtures import create_homework_submission_fixture

__all__ = [
    "lifespan_for_tests",
    "app_fastapi",
    "not_open_session_db",
    "client_for_tests",

    # _?? _'?????+??
    "config_fix",
    "cleaning_paths_fix",
    "session_db",

    # _?????+>
    "user_service_fixture",
    "courses_service_fixture",
    "compression_images_fixture",
    "handler_images_fixture",
    "handler_documents_fixture",
    "path_builder_fixture",

    # _?>????
    "create_user_fixture",
    "create_refresh_token_fixture",
    "create_course_fixture",
    "create_lesson_fixture",
    "create_student_course_fixture",
    "create_lesson_student_fixture",
    "create_homework_fixture",
    "create_lecture_fixture",
    "create_homework_submission_fixture",

    # _-"?????  '???+
    "create_upload_file_fixture",
    "create_image_bytes_fixture",
]
