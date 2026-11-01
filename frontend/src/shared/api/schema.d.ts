export interface paths {
    "/account_invitations/consume": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Consume */
        post: operations["consume_account_invitations_consume_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/account_invitations/issue": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Issue */
        post: operations["issue_account_invitations_issue_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/file-deletions/retry": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Retry Cleanup */
        post: operations["retry_cleanup_admin_file_deletions_retry_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/users": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Users */
        get: operations["list_users_admin_users_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/users/{user_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** User Detail */
        get: operations["user_detail_admin_users__user_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/users/{user_id}/course-storage": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Teacher Course Storage */
        get: operations["teacher_course_storage_admin_users__user_id__course_storage_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/users/{user_id}/storage-quota": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Storage Quota */
        patch: operations["storage_quota_admin_users__user_id__storage_quota_patch"];
        trace?: never;
    };
    "/audit-events": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Audit Events */
        get: operations["audit_events_audit_events_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/auth/browser/login": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Login */
        post: operations["login_auth_browser_login_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/auth/browser/logout": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Logout */
        post: operations["logout_auth_browser_logout_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/auth/browser/refresh": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Refresh */
        post: operations["refresh_auth_browser_refresh_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/auth/change_password/{user_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Change Password
         * @description Смена собственного пароля с проверкой текущего.
         *     Чужой пароль, включая admin/teacher запрос, меняется только через reset-ссылку.
         */
        post: operations["change_password_auth_change_password__user_id__post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/auth/login": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Login */
        post: operations["login_auth_login_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/auth/logout": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Logout
         * @description Отзывает своё семейство сессии; повторный вызов возвращает 200.
         */
        post: operations["logout_auth_logout_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/auth/refresh_tokens": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Refresh Tokens */
        post: operations["refresh_tokens_auth_refresh_tokens_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/auth/register": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Register User
         * @description :raises UserAlreadyExists: 409 Если email занят
         *     :raises PermissionErrorService: 403 Если создаёт нового пользователя не учитель
         */
        post: operations["register_user_auth_register_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/auth/register_by_admin": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Register User By Admin
         * @description Legacy alias: authenticated ADMIN only; master password grants no access.
         */
        post: operations["register_user_by_admin_auth_register_by_admin_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/courses": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Courses */
        get: operations["get_courses_courses_get"];
        put?: never;
        /** Create Course */
        post: operations["create_course_courses_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/courses/personal/{student_user_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Read Personal Workspace */
        get: operations["read_personal_workspace_courses_personal__student_user_id__get"];
        put?: never;
        /** Start Personal Workspace */
        post: operations["start_personal_workspace_courses_personal__student_user_id__post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/courses/{course_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Course By Id */
        get: operations["get_course_by_id_courses__course_id__get"];
        put?: never;
        post?: never;
        /** Delete Course */
        delete: operations["delete_course_courses__course_id__delete"];
        options?: never;
        head?: never;
        /** Update Course */
        patch: operations["update_course_courses__course_id__patch"];
        trace?: never;
    };
    "/courses/{course_id}/avatar": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Course Avatar */
        get: operations["get_course_avatar_courses__course_id__avatar_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Update Avatar */
        patch: operations["update_avatar_courses__course_id__avatar_patch"];
        trace?: never;
    };
    "/courses/{course_id}/purge": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Purge Course */
        post: operations["purge_course_courses__course_id__purge_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/courses/{course_id}/restore": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Restore Course */
        post: operations["restore_course_courses__course_id__restore_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/courses/{course_id}/students": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Получить список всех учеников, прикрепленных к курсу */
        get: operations["get_students_for_course_courses__course_id__students_get"];
        put?: never;
        /** Зачислить ученика на курс */
        post: operations["enroll_student_to_course_courses__course_id__students_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/courses/{course_id}/students/me": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        /** Отчислить текущего ученика */
        delete: operations["unenroll_current_student_from_course_courses__course_id__students_me_delete"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/courses/{course_id}/students/{user_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        /** Отчислить ученика */
        delete: operations["unenroll_student_from_course_courses__course_id__students__user_id__delete"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/courses/{course_id}/students/{user_id}/history-access": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** History Access */
        patch: operations["history_access_courses__course_id__students__user_id__history_access_patch"];
        trace?: never;
    };
    "/homeworks": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get list of homeworks for a student's lesson */
        get: operations["get_homeworks_list_homeworks_get"];
        put?: never;
        /**
         * Create a homework for a student's lesson
         * @description Deadline follows the next lesson of this course and student. Manual deadline is unavailable.
         */
        post: operations["create_homework_homeworks_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/homeworks/available-debts": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Available Debts */
        get: operations["available_debts_homeworks_available_debts_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/homeworks/my": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get all homeworks for the current student across all lessons */
        get: operations["get_my_homeworks_homeworks_my_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/homeworks/my/page": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get My Homeworks Page */
        get: operations["get_my_homeworks_page_homeworks_my_page_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/homeworks/{homework_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Homework Detail */
        get: operations["homework_detail_homeworks__homework_id__get"];
        put?: never;
        post?: never;
        /** Delete a specific homework */
        delete: operations["delete_homework_homeworks__homework_id__delete"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/homeworks/{homework_id}/debts": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Add Homework Debt */
        post: operations["add_homework_debt_homeworks__homework_id__debts_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/homeworks/{homework_id}/file": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Download a specific homework file (PDF) */
        get: operations["download_homework_file_homeworks__homework_id__file_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/homeworks/{homework_id}/placements": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Homework Placement History */
        get: operations["homework_placement_history_homeworks__homework_id__placements_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/homeworks/{homework_id}/submissions": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get all attempts for a homework */
        get: operations["get_homework_submissions_homeworks__homework_id__submissions_get"];
        put?: never;
        /** Submit a homework attempt */
        post: operations["create_homework_submission_homeworks__homework_id__submissions_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/lectures": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get list of uploaded lectures */
        get: operations["get_lectures_list_lectures_get"];
        put?: never;
        /** Upload a lecture (PDF) for a student's lesson */
        post: operations["upload_lecture_lectures_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/lectures/my": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get list of uploaded lectures for the current student across all lessons */
        get: operations["get_my_lectures_lectures_my_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/lectures/{lecture_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Lecture Detail */
        get: operations["lecture_detail_lectures__lecture_id__get"];
        put?: never;
        post?: never;
        /** Delete a specific lecture */
        delete: operations["delete_lecture_lectures__lecture_id__delete"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/lectures/{lecture_id}/file": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Download a specific lecture (PDF) */
        get: operations["download_lecture_lectures__lecture_id__file_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/lessons": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Get list of lessons
         * @description Get lessons with pagination, date filtering, sorting and course_id filter. For students, returns enrolled lessons. For teachers, returns created lessons.
         */
        get: operations["get_lessons_lessons_get"];
        put?: never;
        /** Create a new lesson */
        post: operations["create_lesson_lessons_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/lessons/regular/operations/{operation_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Regular Operation */
        get: operations["get_regular_operation_lessons_regular_operations__operation_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/lessons/regular/operations/{operation_id}/confirm": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Confirm Regular Lessons */
        post: operations["confirm_regular_lessons_lessons_regular_operations__operation_id__confirm_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/lessons/regular/previews": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Preview Regular Lessons */
        post: operations["preview_regular_lessons_lessons_regular_previews_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/lessons/regular/series/{series_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Regular Series */
        get: operations["get_regular_series_lessons_regular_series__series_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/lessons/{lesson_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get specific lesson */
        get: operations["get_lesson_lessons__lesson_id__get"];
        put?: never;
        post?: never;
        /** Delete a lesson */
        delete: operations["delete_lesson_lessons__lesson_id__delete"];
        options?: never;
        head?: never;
        /** Update a lesson */
        patch: operations["update_lesson_lessons__lesson_id__patch"];
        trace?: never;
    };
    "/lessons/{lesson_id}/restore": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Restore Lesson */
        post: operations["restore_lesson_lessons__lesson_id__restore_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/lessons/{lesson_id}/students": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Lesson Students */
        get: operations["get_lesson_students_lessons__lesson_id__students_get"];
        put?: never;
        /** Add a student to a lesson */
        post: operations["add_student_to_lesson_lessons__lesson_id__students_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/lessons/{lesson_id}/students/{student_user_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        /** Remove a student from a lesson */
        delete: operations["remove_student_from_lesson_lessons__lesson_id__students__student_user_id__delete"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/notifications": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Notifications */
        get: operations["notifications_notifications_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/notifications/unread": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Unread */
        get: operations["unread_notifications_unread_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/notifications/{notification_id}/read": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Mark Read */
        patch: operations["mark_read_notifications__notification_id__read_patch"];
        trace?: never;
    };
    "/notifications/{notification_id}/target": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Target */
        get: operations["target_notifications__notification_id__target_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/submissions/review-queue": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Current submitted answers awaiting my review */
        get: operations["get_review_queue_submissions_review_queue_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/submissions/{submission_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get a specific attempt by ID */
        get: operations["get_homework_submission_submissions__submission_id__get"];
        put?: never;
        post?: never;
        /** Delete a submission */
        delete: operations["delete_homework_submission_submissions__submission_id__delete"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/submissions/{submission_id}/files/{file_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Download a specific file attached to an attempt */
        get: operations["get_homework_submission_file_submissions__submission_id__files__file_id__get"];
        /** Replace one answer attachment atomically */
        put: operations["replace_submission_file_submissions__submission_id__files__file_id__put"];
        post?: never;
        /** Remove one answer attachment */
        delete: operations["delete_submission_file_submissions__submission_id__files__file_id__delete"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/submissions/{submission_id}/review": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Final review with optional photo/PDF feedback */
        patch: operations["review_homework_submission_with_files_submissions__submission_id__review_patch"];
        trace?: never;
    };
    "/submissions/{submission_id}/student": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Update attempt as Student (Only if not CHECKED) */
        patch: operations["update_homework_submission_student_submissions__submission_id__student_patch"];
        trace?: never;
    };
    "/submissions/{submission_id}/submit": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Submit the current answer (idempotent) */
        post: operations["submit_homework_submission_submissions__submission_id__submit_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/submissions/{submission_id}/teacher": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Update attempt as Teacher (Status, Grade, Comment) */
        patch: operations["update_homework_submission_teacher_submissions__submission_id__teacher_patch"];
        trace?: never;
    };
    "/teacher-planning/lessons/{lesson_id}/students/{student_user_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Mark Material Not Needed */
        patch: operations["mark_material_not_needed_teacher_planning_lessons__lesson_id__students__student_user_id__patch"];
        trace?: never;
    };
    "/teacher-planning/reminders": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Reminders */
        get: operations["reminders_teacher_planning_reminders_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/teacher-planning/students": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Planning Students */
        get: operations["planning_students_teacher_planning_students_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/teacher-planning/students/{student_user_id}/norm": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        /** Save Norm */
        put: operations["save_norm_teacher_planning_students__student_user_id__norm_put"];
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/teacher-planning/students/{student_user_id}/price": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Student Price */
        get: operations["student_price_teacher_planning_students__student_user_id__price_get"];
        /** Save Student Price */
        put: operations["save_student_price_teacher_planning_students__student_user_id__price_put"];
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/teacher-planning/weekly-earnings": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Weekly Earnings */
        get: operations["weekly_earnings_teacher_planning_weekly_earnings_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/teacher_students": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Links */
        get: operations["list_links_teacher_students_get"];
        put?: never;
        /** Link Teacher Student */
        post: operations["link_teacher_student_teacher_students_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/teacher_students/{teacher_user_id}/{student_user_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        /** End Link */
        delete: operations["end_link_teacher_students__teacher_user_id___student_user_id__delete"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/users/me": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Me */
        get: operations["get_me_users_me_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/users/students": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Students */
        get: operations["get_students_users_students_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/users/teachers": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Teachers */
        get: operations["get_teachers_users_teachers_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/users/{user_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Public Profile */
        get: operations["get_public_profile_users__user_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Update User */
        patch: operations["update_user_users__user_id__patch"];
        trace?: never;
    };
    "/users/{user_id}/account-status": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Update Account Status */
        patch: operations["update_account_status_users__user_id__account_status_patch"];
        trace?: never;
    };
    "/users/{user_id}/avatar": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Avatar */
        get: operations["get_avatar_users__user_id__avatar_get"];
        put?: never;
        post?: never;
        /** Delete Avatar */
        delete: operations["delete_avatar_users__user_id__avatar_delete"];
        options?: never;
        head?: never;
        /** Update Avatar */
        patch: operations["update_avatar_users__user_id__avatar_patch"];
        trace?: never;
    };
    "/users/{user_id}/school-grade": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Update School Grade */
        patch: operations["update_school_grade_users__user_id__school_grade_patch"];
        trace?: never;
    };
    "/users/{user_id}/storage": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Storage Usage */
        get: operations["storage_usage_users__user_id__storage_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
}
export type webhooks = Record<string, never>;
export interface components {
    schemas: {
        /** AddDebtRequestDTO */
        AddDebtRequestDTO: {
            /** Lesson Id */
            lesson_id: number;
        };
        /** AddStudentToLessonRequestDTO */
        AddStudentToLessonRequestDTO: {
            /** Student User Id */
            student_user_id: number;
        };
        /** AdminAccountStatusRequestDTO */
        AdminAccountStatusRequestDTO: {
            /** Is Active */
            is_active: boolean;
        };
        /** AdminTeacherStudentResponseDTO */
        AdminTeacherStudentResponseDTO: {
            /** Active */
            active: boolean;
            /** Ended At */
            ended_at: string | null;
            student: components["schemas"]["MinimalProfileResponseDTO"];
            /** Student User Id */
            student_user_id: number;
            teacher: components["schemas"]["MinimalProfileResponseDTO"];
            /** Teacher User Id */
            teacher_user_id: number;
        };
        /** AdminUserResponseDTO */
        AdminUserResponseDTO: {
            /** Avatar Path */
            avatar_path?: string | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Description */
            description?: string | null;
            /** Email */
            email?: string | null;
            /** First Name */
            first_name?: string | null;
            /** Is Activated */
            is_activated: boolean;
            /** Is Active */
            is_active: boolean;
            /** Last Name */
            last_name?: string | null;
            /** Middle Name */
            middle_name?: string | null;
            role: components["schemas"]["UserRole"];
            /** School Grade */
            school_grade?: number | null;
            /** User Id */
            user_id: number;
            /** Username */
            username: string;
        };
        /** AuditEventResponseDTO */
        AuditEventResponseDTO: {
            /** Action */
            action: string;
            /** Actor User Id */
            actor_user_id: number;
            /** Correlation Id */
            correlation_id: string;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Id */
            id: number;
            /** Object Id */
            object_id: number;
            /** Object Type */
            object_type: string;
            /** Result */
            result: string;
            /** Source */
            source: string;
        };
        /**
         * AvatarCoursesType
         * @description Если CUSTOM, то обязательно заполняется avatar_path. Т.е. заливается по кастомному пути
         * @enum {string}
         */
        AvatarCoursesType: "default" | "custom" | "python" | "mathematics" | "russian_language";
        /** Body_create_homework_homeworks_post */
        Body_create_homework_homeworks_post: {
            /** Description */
            description?: string | null;
            /** File */
            file?: string | null;
            /** Lesson Id */
            lesson_id: number;
            /** Student User Id */
            student_user_id: number;
            /** Title */
            title: string;
        };
        /** Body_create_homework_submission_homeworks__homework_id__submissions_post */
        Body_create_homework_submission_homeworks__homework_id__submissions_post: {
            /** Files */
            files?: string[] | null;
            /** Text Content */
            text_content?: string | null;
        };
        /** Body_login_auth_browser_login_post */
        Body_login_auth_browser_login_post: {
            /** Client Id */
            client_id?: string | null;
            /**
             * Client Secret
             * Format: password
             */
            client_secret?: string | null;
            /** Grant Type */
            grant_type?: string | null;
            /**
             * Password
             * Format: password
             */
            password: string;
            /**
             * Scope
             * @default
             */
            scope: string;
            /** Username */
            username: string;
        };
        /** Body_login_auth_login_post */
        Body_login_auth_login_post: {
            /** Client Id */
            client_id?: string | null;
            /**
             * Client Secret
             * Format: password
             */
            client_secret?: string | null;
            /** Grant Type */
            grant_type?: string | null;
            /**
             * Password
             * Format: password
             */
            password: string;
            /**
             * Scope
             * @default
             */
            scope: string;
            /** Username */
            username: string;
        };
        /** Body_replace_submission_file_submissions__submission_id__files__file_id__put */
        Body_replace_submission_file_submissions__submission_id__files__file_id__put: {
            /** Expected Version */
            expected_version?: number | null;
            /** File */
            file: string;
        };
        /** Body_review_homework_submission_with_files_submissions__submission_id__review_patch */
        Body_review_homework_submission_with_files_submissions__submission_id__review_patch: {
            /** Expected Version */
            expected_version: string;
            /** Files */
            files?: string[] | null;
            /** Grade */
            grade: string;
            /** Teacher Comment */
            teacher_comment?: string | null;
        };
        /** Body_update_avatar_courses__course_id__avatar_patch */
        Body_update_avatar_courses__course_id__avatar_patch: {
            /** Avatar */
            avatar: string;
        };
        /** Body_update_avatar_users__user_id__avatar_patch */
        Body_update_avatar_users__user_id__avatar_patch: {
            /** Avatar */
            avatar: string;
        };
        /** Body_update_homework_submission_student_submissions__submission_id__student_patch */
        Body_update_homework_submission_student_submissions__submission_id__student_patch: {
            /** Expected Version */
            expected_version?: number | null;
            /** Files */
            files?: string[] | null;
            /** Text Content */
            text_content?: string | null;
        };
        /** Body_upload_lecture_lectures_post */
        Body_upload_lecture_lectures_post: {
            /** File */
            file: string;
            /** Lesson Id */
            lesson_id: number;
            /** Student User Id */
            student_user_id: number;
        };
        /** BrowserTokenResponse */
        BrowserTokenResponse: {
            /** Access Token */
            access_token: string;
            /** Token Type */
            token_type: string;
        };
        /** ChangePasswordRequestDTO */
        ChangePasswordRequestDTO: {
            /** Current Password */
            current_password: string;
            /** New Password */
            new_password: string;
        };
        /** CleanupResponse */
        CleanupResponse: {
            /** Completed */
            completed: number;
            /** Failed */
            failed: number;
        };
        /** ConfirmRegularLessonsRequestDTO */
        ConfirmRegularLessonsRequestDTO: {
            /**
             * Acknowledge Conflicts
             * @default false
             */
            acknowledge_conflicts: boolean;
            /** Preview Revision */
            preview_revision: number;
        };
        /** ConsumeInvitationRequest */
        ConsumeInvitationRequest: {
            /** New Password */
            new_password: string;
            /**
             * Purpose
             * @enum {string}
             */
            purpose: "invite" | "reset";
            /** Token */
            token: string;
        };
        /** ConsumeInvitationResponse */
        ConsumeInvitationResponse: {
            /** Success */
            success: boolean;
        };
        /** CourseStorageUsage */
        CourseStorageUsage: {
            /** Bytes */
            bytes: number;
            /** Course Id */
            course_id: number;
        };
        /** CoursesResponseDTO */
        CoursesResponseDTO: {
            /**
             * Access Mode
             * @default read_only
             * @enum {string}
             */
            access_mode: "active" | "read_only";
            /** Avatar Path */
            avatar_path?: string | null;
            avatar_type: components["schemas"]["AvatarCoursesType"];
            /** Call Url */
            call_url?: string | null;
            /**
             * Can Create Lesson
             * @default false
             */
            can_create_lesson: boolean;
            /**
             * Can Manage
             * @default false
             */
            can_manage: boolean;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Deleted At */
            deleted_at?: string | null;
            /** Description */
            description?: string | null;
            /** Id */
            id: number;
            /** Is Deleted */
            is_deleted: boolean;
            /** Name */
            name: string;
            /** Read Only Reason */
            read_only_reason?: ("course_archived" | "lesson_archived" | "enrollment_ended" | "access_expired" | "teacher_link_ended" | "history_only" | "role_read_only") | null;
            /** Slug */
            slug: string;
            /**
             * Teacher Name
             * @default
             */
            teacher_name: string;
            /** Teacher User Id */
            teacher_user_id: number;
            /**
             * Updated At
             * Format: date-time
             */
            updated_at: string;
        };
        /** CreateCourseDTORequest */
        CreateCourseDTORequest: {
            /** Call Url */
            call_url?: string | null;
            /** Description */
            description?: string | null;
            /** Name */
            name: string;
            /** Slug */
            slug: string;
        };
        /** CreateLessonRequestDTO */
        CreateLessonRequestDTO: {
            /** Call Url Override */
            call_url_override?: string | null;
            /** Course Id */
            course_id: number;
            /** Description */
            description?: string | null;
            /**
             * Duration Minutes
             * @default 55
             */
            duration_minutes: number;
            /**
             * Scheduled At
             * Format: date-time
             */
            scheduled_at: string;
            /** @default scheduled */
            status: components["schemas"]["LessonStatus"];
            /** Student User Id */
            student_user_id?: number | null;
            /** Title */
            title: string;
            /** Topic */
            topic?: string | null;
        };
        /** DeadlineEventResponseDTO */
        DeadlineEventResponseDTO: {
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Due At */
            due_at: string | null;
            /** Due Lesson Id */
            due_lesson_id: number | null;
            /** Id */
            id: number;
            /** Reason */
            reason: string;
        };
        /** EnrollStudentRequestDTO */
        EnrollStudentRequestDTO: {
            /** Student User Id */
            student_user_id: number;
        };
        /** FileDescriptorDTO */
        FileDescriptorDTO: {
            /** Display Name */
            display_name: string;
            /** Download Url */
            download_url: string;
            /** Id */
            id: number;
            /** Mime Type */
            mime_type: string;
            /** Size Bytes */
            size_bytes?: number | null;
        };
        /** HTTPValidationError */
        HTTPValidationError: {
            /** Detail */
            detail?: components["schemas"]["ValidationError"][];
        };
        /** HistoryAccessRequest */
        HistoryAccessRequest: {
            /** Revoked */
            revoked: boolean;
        };
        /**
         * HomeworkListStatus
         * @enum {string}
         */
        HomeworkListStatus: "all" | "todo" | "submitted" | "checked";
        /** HomeworkResponseDTO */
        HomeworkResponseDTO: {
            /**
             * Access Mode
             * @default read_only
             * @enum {string}
             */
            access_mode: "active" | "read_only";
            /**
             * Already Added
             * @default false
             */
            already_added: boolean;
            /**
             * Can Manage
             * @default false
             */
            can_manage: boolean;
            /**
             * Can Review
             * @default false
             */
            can_review: boolean;
            /**
             * Can Submit
             * @default false
             */
            can_submit: boolean;
            /** Course Id */
            course_id?: number | null;
            /** Course Name */
            course_name?: string | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Deadline */
            deadline?: string | null;
            /** Deadline Frozen At */
            deadline_frozen_at?: string | null;
            /** Description */
            description?: string | null;
            /** Due Lesson Id */
            due_lesson_id?: number | null;
            file?: components["schemas"]["FileDescriptorDTO"] | null;
            /** Id */
            id: number;
            /** Lesson Id */
            lesson_id?: number | null;
            /** Lesson Title */
            lesson_title?: string | null;
            /** Original File Name */
            original_file_name?: string | null;
            /** Original File Type */
            original_file_type?: string | null;
            /** Pdf File Name */
            pdf_file_name?: string | null;
            /** Placement Id */
            placement_id?: number | null;
            /** Placement Kind */
            placement_kind?: string | null;
            /** Placement Lesson Id */
            placement_lesson_id?: number | null;
            /** Read Only Reason */
            read_only_reason?: ("course_archived" | "lesson_archived" | "enrollment_ended" | "access_expired" | "teacher_link_ended" | "history_only" | "role_read_only") | null;
            /** Student User Id */
            student_user_id?: number | null;
            /** Submission Status */
            submission_status?: string | null;
            /** Teacher User Id */
            teacher_user_id?: number | null;
            /** Title */
            title: string;
            /**
             * Updated At
             * Format: date-time
             */
            updated_at: string;
            /** Working Submission Id */
            working_submission_id?: number | null;
        };
        /** HomeworkSubmissionFileResponseDTO */
        HomeworkSubmissionFileResponseDTO: {
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            file?: components["schemas"]["FileDescriptorDTO"] | null;
            /** Id */
            id: number;
            /** Original File Name */
            original_file_name?: string | null;
            /** Original File Type */
            original_file_type?: string | null;
            /** Pdf File Name */
            pdf_file_name?: string | null;
        };
        /**
         * HomeworkSubmissionResponseDTO
         * @description Данные ответа для клиента
         */
        HomeworkSubmissionResponseDTO: {
            /** Attempt Number */
            attempt_number: number;
            /** Checked At */
            checked_at?: string | null;
            /**
             * Checked By
             * @description user_id of the reviewing teacher
             */
            checked_by?: number | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /**
             * Files
             * @default []
             */
            files: components["schemas"]["HomeworkSubmissionFileResponseDTO"][];
            /** Grade */
            grade?: number | null;
            /** Homework Id */
            homework_id: number;
            /** Id */
            id: number;
            /**
             * Is Working
             * @default true
             */
            is_working: boolean;
            /**
             * Review Files
             * @default []
             */
            review_files: components["schemas"]["HomeworkSubmissionFileResponseDTO"][];
            status: components["schemas"]["HomeworkSubmissionStatus"];
            /** Submitted At */
            submitted_at?: string | null;
            /** Teacher Comment */
            teacher_comment?: string | null;
            /** Text Content */
            text_content?: string | null;
            /**
             * Updated At
             * Format: date-time
             */
            updated_at: string;
            /**
             * Version
             * @default 1
             */
            version: number;
        };
        /**
         * HomeworkSubmissionStatus
         * @enum {string}
         */
        HomeworkSubmissionStatus: "draft" | "submitted" | "checked";
        /** InvitationResponse */
        InvitationResponse: {
            /** Activation Link */
            activation_link?: string | null;
            /** Expires At */
            expires_at?: string | null;
        };
        /** InvitationUserResponse */
        InvitationUserResponse: {
            /** Activation Link */
            activation_link?: string | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Email */
            email?: string | null;
            /** Expires At */
            expires_at?: string | null;
            /** Id */
            id: number;
            role: components["schemas"]["UserRole"];
            /** Username */
            username: string;
        };
        /** IssueInvitationRequest */
        IssueInvitationRequest: {
            /**
             * Purpose
             * @enum {string}
             */
            purpose: "invite" | "reset";
            /** User Id */
            user_id: number;
        };
        /** LectureResponseDTO */
        LectureResponseDTO: {
            /**
             * Access Mode
             * @default read_only
             * @enum {string}
             */
            access_mode: "active" | "read_only";
            /**
             * Can Manage
             * @default false
             */
            can_manage: boolean;
            /** Course Id */
            course_id?: number | null;
            /** Course Name */
            course_name?: string | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            file?: components["schemas"]["FileDescriptorDTO"] | null;
            /** Id */
            id: number;
            /** Lesson Id */
            lesson_id?: number | null;
            /** Lesson Title */
            lesson_title?: string | null;
            /** Original File Name */
            original_file_name: string;
            /** Original File Type */
            original_file_type: string;
            /** Pdf File Name */
            pdf_file_name: string;
            /** Read Only Reason */
            read_only_reason?: ("course_archived" | "lesson_archived" | "enrollment_ended" | "access_expired" | "teacher_link_ended" | "history_only" | "role_read_only") | null;
            /** Student User Id */
            student_user_id?: number | null;
            /** Teacher User Id */
            teacher_user_id?: number | null;
            /**
             * Updated At
             * Format: date-time
             */
            updated_at: string;
        };
        /** LessonPriceDTO */
        LessonPriceDTO: {
            /** Lesson Price Kopecks */
            lesson_price_kopecks: number | null;
        };
        /** LessonRecipientResponseDTO */
        LessonRecipientResponseDTO: {
            /**
             * Access Mode
             * @default read_only
             * @enum {string}
             */
            access_mode: "active" | "read_only";
            /**
             * Can Manage
             * @default false
             */
            can_manage: boolean;
            /** Display Name */
            display_name: string;
            /** Read Only Reason */
            read_only_reason?: ("course_archived" | "lesson_archived" | "enrollment_ended" | "access_expired" | "teacher_link_ended" | "history_only" | "role_read_only") | null;
            /** School Grade */
            school_grade?: number | null;
            /** Student User Id */
            student_user_id: number;
            /** Username */
            username: string;
        };
        /** LessonResponseDTO */
        LessonResponseDTO: {
            /**
             * Access Mode
             * @default read_only
             * @enum {string}
             */
            access_mode: "active" | "read_only";
            /** Call Url Override */
            call_url_override?: string | null;
            /**
             * Can Manage
             * @default false
             */
            can_manage: boolean;
            /** Course Id */
            course_id: number;
            /** Course Name */
            course_name?: string | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Deleted At */
            deleted_at?: string | null;
            /** Description */
            description?: string | null;
            /**
             * Duration Minutes
             * @default 55
             */
            duration_minutes: number;
            /** Effective Call Url */
            effective_call_url?: string | null;
            /**
             * Has Homework
             * @default false
             */
            has_homework: boolean;
            /**
             * Has Lecture
             * @default false
             */
            has_lecture: boolean;
            /** Id */
            id: number;
            /**
             * Is Deleted
             * @default false
             */
            is_deleted: boolean;
            /** Read Only Reason */
            read_only_reason?: ("course_archived" | "lesson_archived" | "enrollment_ended" | "access_expired" | "teacher_link_ended" | "history_only" | "role_read_only") | null;
            /** Recipient Materials */
            recipient_materials?: components["schemas"]["RecipientMaterialStatusDTO"][];
            /** Regular Original At */
            regular_original_at?: string | null;
            /** Regular Series Id */
            regular_series_id?: string | null;
            /**
             * Scheduled At
             * Format: date-time
             */
            scheduled_at: string;
            /** @default scheduled */
            status: components["schemas"]["LessonStatus"];
            /** Student Labels */
            student_labels?: components["schemas"]["LessonStudentLabelDTO"][];
            /** Teacher User Id */
            teacher_user_id: number;
            /** Title */
            title: string;
            /** Topic */
            topic?: string | null;
            /**
             * Updated At
             * Format: date-time
             */
            updated_at: string;
            /** Warnings */
            warnings?: components["schemas"]["ScheduleWarning"][];
        };
        /**
         * LessonStatus
         * @enum {string}
         */
        LessonStatus: "scheduled" | "completed" | "cancelled";
        /** LessonStudentLabelDTO */
        LessonStudentLabelDTO: {
            /** Display Name */
            display_name: string;
            /** User Id */
            user_id: number;
        };
        /** LessonStudentResponseDTO */
        LessonStudentResponseDTO: {
            /** Access Ended At */
            access_ended_at?: string | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Id */
            id: number;
            /** Lesson Id */
            lesson_id: number;
            /** Student User Id */
            student_user_id: number;
        };
        /** LinkTeacherStudentRequestDTO */
        LinkTeacherStudentRequestDTO: {
            /** Student User Id */
            student_user_id: number;
            /** Teacher User Id */
            teacher_user_id: number;
        };
        /**
         * ListView
         * @enum {string}
         */
        ListView: "all" | "active" | "archive";
        /** LogoutRequest */
        LogoutRequest: {
            /** Refresh Token */
            refresh_token: string;
        };
        /** LogoutResponse */
        LogoutResponse: {
            /** Success */
            success: boolean;
        };
        /** MinimalProfileResponseDTO */
        MinimalProfileResponseDTO: {
            /** Avatar Path */
            avatar_path?: string | null;
            /** First Name */
            first_name: string;
            /** Last Name */
            last_name: string;
            /** School Grade */
            school_grade?: number | null;
            /** User Id */
            user_id: number;
            /** Username */
            username: string;
        };
        /** MinimalStudentResponseDTO */
        MinimalStudentResponseDTO: {
            /** Avatar Path */
            avatar_path?: string | null;
            /** First Name */
            first_name: string;
            /** Last Name */
            last_name: string;
            /** School Grade */
            school_grade?: number | null;
            /** User Id */
            user_id: number;
        };
        /** NormRequestDTO */
        NormRequestDTO: {
            /**
             * Expected Revision
             * @default 0
             */
            expected_revision: number;
            /**
             * Kind
             * @default regular
             * @enum {string}
             */
            kind: "regular" | "exception";
            /**
             * Paused
             * @default false
             */
            paused: boolean;
            /** Target */
            target?: number | null;
            /**
             * Week
             * Format: date
             */
            week: string;
        };
        /** NormRevisionDTO */
        NormRevisionDTO: {
            /** Revision */
            revision: number;
        };
        /** NotificationResponseDTO */
        NotificationResponseDTO: {
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Event Type */
            event_type: string;
            /** Id */
            id: number;
            /** Object Id */
            object_id: number;
            /** Object Type */
            object_type: string;
            /** Read At */
            read_at: string | null;
        };
        /** NotificationTargetDTO */
        NotificationTargetDTO: {
            /** Available */
            available: boolean;
            /** Homework Id */
            homework_id?: number | null;
            /** Message */
            message?: string | null;
            /** Object Id */
            object_id?: number | null;
            /** Object Type */
            object_type?: ("lesson" | "homework" | "submission") | null;
        };
        /** PaginationResponseDTO[AdminTeacherStudentResponseDTO] */
        PaginationResponseDTO_AdminTeacherStudentResponseDTO_: {
            /** Items */
            items: components["schemas"]["AdminTeacherStudentResponseDTO"][];
            /** Limit */
            limit?: number | null;
            /** Offset */
            offset?: number | null;
            /** Total */
            total: number;
        };
        /** PaginationResponseDTO[AdminUserResponseDTO] */
        PaginationResponseDTO_AdminUserResponseDTO_: {
            /** Items */
            items: components["schemas"]["AdminUserResponseDTO"][];
            /** Limit */
            limit?: number | null;
            /** Offset */
            offset?: number | null;
            /** Total */
            total: number;
        };
        /** PaginationResponseDTO[AuditEventResponseDTO] */
        PaginationResponseDTO_AuditEventResponseDTO_: {
            /** Items */
            items: components["schemas"]["AuditEventResponseDTO"][];
            /** Limit */
            limit?: number | null;
            /** Offset */
            offset?: number | null;
            /** Total */
            total: number;
        };
        /** PaginationResponseDTO[CoursesResponseDTO] */
        PaginationResponseDTO_CoursesResponseDTO_: {
            /** Items */
            items: components["schemas"]["CoursesResponseDTO"][];
            /** Limit */
            limit?: number | null;
            /** Offset */
            offset?: number | null;
            /** Total */
            total: number;
        };
        /** PaginationResponseDTO[HomeworkResponseDTO] */
        PaginationResponseDTO_HomeworkResponseDTO_: {
            /** Items */
            items: components["schemas"]["HomeworkResponseDTO"][];
            /** Limit */
            limit?: number | null;
            /** Offset */
            offset?: number | null;
            /** Total */
            total: number;
        };
        /** PaginationResponseDTO[HomeworkSubmissionResponseDTO] */
        PaginationResponseDTO_HomeworkSubmissionResponseDTO_: {
            /** Items */
            items: components["schemas"]["HomeworkSubmissionResponseDTO"][];
            /** Limit */
            limit?: number | null;
            /** Offset */
            offset?: number | null;
            /** Total */
            total: number;
        };
        /** PaginationResponseDTO[LectureResponseDTO] */
        PaginationResponseDTO_LectureResponseDTO_: {
            /** Items */
            items: components["schemas"]["LectureResponseDTO"][];
            /** Limit */
            limit?: number | null;
            /** Offset */
            offset?: number | null;
            /** Total */
            total: number;
        };
        /** PaginationResponseDTO[LessonRecipientResponseDTO] */
        PaginationResponseDTO_LessonRecipientResponseDTO_: {
            /** Items */
            items: components["schemas"]["LessonRecipientResponseDTO"][];
            /** Limit */
            limit?: number | null;
            /** Offset */
            offset?: number | null;
            /** Total */
            total: number;
        };
        /** PaginationResponseDTO[LessonResponseDTO] */
        PaginationResponseDTO_LessonResponseDTO_: {
            /** Items */
            items: components["schemas"]["LessonResponseDTO"][];
            /** Limit */
            limit?: number | null;
            /** Offset */
            offset?: number | null;
            /** Total */
            total: number;
        };
        /** PaginationResponseDTO[NotificationResponseDTO] */
        PaginationResponseDTO_NotificationResponseDTO_: {
            /** Items */
            items: components["schemas"]["NotificationResponseDTO"][];
            /** Limit */
            limit?: number | null;
            /** Offset */
            offset?: number | null;
            /** Total */
            total: number;
        };
        /** PaginationResponseDTO[PlanningStudentDTO] */
        PaginationResponseDTO_PlanningStudentDTO_: {
            /** Items */
            items: components["schemas"]["PlanningStudentDTO"][];
            /** Limit */
            limit?: number | null;
            /** Offset */
            offset?: number | null;
            /** Total */
            total: number;
        };
        /** PaginationResponseDTO[RecipientReminderDTO] */
        PaginationResponseDTO_RecipientReminderDTO_: {
            /** Items */
            items: components["schemas"]["RecipientReminderDTO"][];
            /** Limit */
            limit?: number | null;
            /** Offset */
            offset?: number | null;
            /** Total */
            total: number;
        };
        /** PaginationResponseDTO[ReviewQueueItemDTO] */
        PaginationResponseDTO_ReviewQueueItemDTO_: {
            /** Items */
            items: components["schemas"]["ReviewQueueItemDTO"][];
            /** Limit */
            limit?: number | null;
            /** Offset */
            offset?: number | null;
            /** Total */
            total: number;
        };
        /** PaginationResponseDTO[StudentCourseResponseDTO] */
        PaginationResponseDTO_StudentCourseResponseDTO_: {
            /** Items */
            items: components["schemas"]["StudentCourseResponseDTO"][];
            /** Limit */
            limit?: number | null;
            /** Offset */
            offset?: number | null;
            /** Total */
            total: number;
        };
        /** PaginationResponseDTO[Union[PublicProfileResponseDTO, MinimalProfileResponseDTO]] */
        PaginationResponseDTO_Union_PublicProfileResponseDTO__MinimalProfileResponseDTO__: {
            /** Items */
            items: (components["schemas"]["PublicProfileResponseDTO"] | components["schemas"]["MinimalProfileResponseDTO"])[];
            /** Limit */
            limit?: number | null;
            /** Offset */
            offset?: number | null;
            /** Total */
            total: number;
        };
        /** PaginationResponseDTO[Union[PublicProfileResponseDTO, TeacherStudentProfileResponseDTO, MinimalProfileResponseDTO]] */
        PaginationResponseDTO_Union_PublicProfileResponseDTO__TeacherStudentProfileResponseDTO__MinimalProfileResponseDTO__: {
            /** Items */
            items: (components["schemas"]["PublicProfileResponseDTO"] | components["schemas"]["TeacherStudentProfileResponseDTO"] | components["schemas"]["MinimalProfileResponseDTO"])[];
            /** Limit */
            limit?: number | null;
            /** Offset */
            offset?: number | null;
            /** Total */
            total: number;
        };
        /** PlacementResponseDTO */
        PlacementResponseDTO: {
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Due At */
            due_at: string | null;
            /** Due Lesson Id */
            due_lesson_id: number | null;
            /** Events */
            events: components["schemas"]["DeadlineEventResponseDTO"][];
            /** Frozen */
            frozen: boolean;
            /** Homework Id */
            homework_id: number;
            /** Id */
            id: number;
            /** Kind */
            kind: string;
            /** Lesson Id */
            lesson_id: number;
        };
        /** PlanningStudentDTO */
        PlanningStudentDTO: {
            /** First Name */
            first_name: string;
            /** Last Name */
            last_name: string;
            /** Missing Homework */
            missing_homework: number;
            /** Missing Lecture */
            missing_lecture: number;
            /** Norm Revision */
            norm_revision: number;
            /** Paused */
            paused: boolean;
            /** Scheduled Count */
            scheduled_count: number;
            /** Target */
            target: number | null;
            /** User Id */
            user_id: number;
            /** Username */
            username: string;
        };
        /** PreviewRegularLessonsRequestDTO */
        PreviewRegularLessonsRequestDTO: {
            /**
             * Action
             * @enum {string}
             */
            action: "create" | "extend" | "stop" | "cancel_future";
            lesson?: components["schemas"]["RegularLessonSpecDTO"] | null;
            /**
             * Operation Id
             * Format: uuid
             */
            operation_id: string;
            /** Series Id */
            series_id?: string | null;
            /**
             * Weeks
             * @default 4
             */
            weeks: number;
        };
        /** PublicProfileResponseDTO */
        PublicProfileResponseDTO: {
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Email */
            email?: string | null;
            /** Id */
            id: number;
            role: components["schemas"]["UserRole"];
            student?: components["schemas"]["StudentsResponseDTO"] | null;
            teacher?: components["schemas"]["TeachersResponseDTO"] | null;
            /** Username */
            username: string;
        };
        /** PurgeCourseRequest */
        PurgeCourseRequest: {
            /** Confirm Course Id */
            confirm_course_id: number;
            /** Confirm Name */
            confirm_name: string;
        };
        /** PurgeResponse */
        PurgeResponse: {
            cleanup: components["schemas"]["CleanupResponse"];
            /** Course Id */
            course_id: number;
        };
        /** RecipientMaterialStatusDTO */
        RecipientMaterialStatusDTO: {
            /** Has Homework */
            has_homework: boolean;
            /** Has Lecture */
            has_lecture: boolean;
            /** Homework Not Needed */
            homework_not_needed: boolean;
            /** Lecture Not Needed */
            lecture_not_needed: boolean;
            /** Needs Homework */
            needs_homework: boolean;
            /** Needs Lecture */
            needs_lecture: boolean;
            /** Student User Id */
            student_user_id: number;
        };
        /** RecipientReminderDTO */
        RecipientReminderDTO: {
            /** Course Id */
            course_id: number;
            /** Course Name */
            course_name: string;
            /** First Name */
            first_name: string;
            /** Has Homework */
            has_homework: boolean;
            /** Has Lecture */
            has_lecture: boolean;
            /** Homework Not Needed */
            homework_not_needed: boolean;
            /** Last Name */
            last_name: string;
            /** Lecture Not Needed */
            lecture_not_needed: boolean;
            /** Lesson Id */
            lesson_id: number;
            /** Needs Homework */
            needs_homework: boolean;
            /** Needs Lecture */
            needs_lecture: boolean;
            /**
             * Scheduled At
             * Format: date-time
             */
            scheduled_at: string;
            /** Student User Id */
            student_user_id: number;
            /** Title */
            title: string;
        };
        /** RefreshTokenRequest */
        RefreshTokenRequest: {
            /** Refresh Token */
            refresh_token: string;
        };
        /** RegisterUserByAdminRequestDTO */
        RegisterUserByAdminRequestDTO: {
            /** Description */
            description?: string | null;
            /** Email */
            email?: string | null;
            /** First Name */
            first_name: string;
            /** Last Name */
            last_name: string;
            /** Lesson Price Kopecks */
            lesson_price_kopecks?: number | null;
            /** Middle Name */
            middle_name?: string | null;
            /** Password For Admin */
            password_for_admin?: string | null;
            role: components["schemas"]["UserRole"];
            /** School Grade */
            school_grade?: number | null;
            /** Username */
            username: string;
        };
        /** RegisterUserRequestDTO */
        RegisterUserRequestDTO: {
            /** Description */
            description?: string | null;
            /** Email */
            email?: string | null;
            /** First Name */
            first_name: string;
            /** Last Name */
            last_name: string;
            /** Lesson Price Kopecks */
            lesson_price_kopecks?: number | null;
            /** Middle Name */
            middle_name?: string | null;
            role: components["schemas"]["UserRole"];
            /** School Grade */
            school_grade?: number | null;
            /** Username */
            username: string;
        };
        /** RegularLessonSpecDTO */
        RegularLessonSpecDTO: {
            /** Call Url Override */
            call_url_override?: string | null;
            /** Course Id */
            course_id: number;
            /** Description */
            description?: string | null;
            /**
             * Duration Minutes
             * @default 55
             */
            duration_minutes: number;
            /**
             * Scheduled At
             * Format: date-time
             */
            scheduled_at: string;
            /**
             * Status
             * @default scheduled
             * @constant
             */
            status: "scheduled";
            /** Student User Id */
            student_user_id: number;
            /** Title */
            title: string;
            /** Topic */
            topic?: string | null;
        };
        /** RegularOccurrencePreviewDTO */
        RegularOccurrencePreviewDTO: {
            /** Conflict Lesson Ids */
            conflict_lesson_ids?: number[];
            /** Conflict Occurrence Dates */
            conflict_occurrence_dates?: string[];
            /** Duration Minutes */
            duration_minutes: number;
            /** Lesson Id */
            lesson_id?: number | null;
            /**
             * Scheduled At
             * Format: date-time
             */
            scheduled_at: string;
        };
        /** RegularOperationResponseDTO */
        RegularOperationResponseDTO: {
            /**
             * Action
             * @enum {string}
             */
            action: "create" | "extend" | "stop" | "cancel_future";
            /**
             * Operation Id
             * Format: uuid
             */
            operation_id: string;
            preview: components["schemas"]["RegularPreviewDTO"];
            /** Preview Revision */
            preview_revision: number;
            result?: components["schemas"]["RegularOperationResultDTO"] | null;
            /**
             * State
             * @enum {string}
             */
            state: "preview" | "committed";
        };
        /** RegularOperationResultDTO */
        RegularOperationResultDTO: {
            /** Lesson Ids */
            lesson_ids: number[];
            /**
             * Series Id
             * Format: uuid
             */
            series_id: string;
            /** Series Revision */
            series_revision: number;
            /** Stopped */
            stopped: boolean;
        };
        /** RegularPreviewDTO */
        RegularPreviewDTO: {
            /** Count */
            count: number;
            /** Course Id */
            course_id: number;
            /** Last Date */
            last_date: string | null;
            /** Occurrences */
            occurrences: components["schemas"]["RegularOccurrencePreviewDTO"][];
            /** Series Revision */
            series_revision?: number | null;
            /** Student User Id */
            student_user_id: number;
            /**
             * Timezone
             * @default Europe/Moscow
             * @constant
             */
            timezone: "Europe/Moscow";
            /** Title */
            title: string;
        };
        /** RegularSeriesResponseDTO */
        RegularSeriesResponseDTO: {
            /**
             * Anchor At
             * Format: date-time
             */
            anchor_at: string;
            /** Course Id */
            course_id: number;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Revision */
            revision: number;
            spec: components["schemas"]["RegularLessonSpecDTO"];
            /** Stopped */
            stopped: boolean;
            /** Student User Id */
            student_user_id: number;
            /**
             * Through At
             * Format: date-time
             */
            through_at: string;
        };
        /** ReminderRequestDTO */
        ReminderRequestDTO: {
            /** Homework Not Needed */
            homework_not_needed?: boolean | null;
            /** Lecture Not Needed */
            lecture_not_needed?: boolean | null;
        };
        /** ReviewQueueItemDTO */
        ReviewQueueItemDTO: {
            /** Attempt Number */
            attempt_number: number;
            /** Checked At */
            checked_at?: string | null;
            /**
             * Checked By
             * @description user_id of the reviewing teacher
             */
            checked_by?: number | null;
            /** Course Id */
            course_id: number;
            /** Course Name */
            course_name: string;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /**
             * Files
             * @default []
             */
            files: components["schemas"]["HomeworkSubmissionFileResponseDTO"][];
            /** Grade */
            grade?: number | null;
            /** Homework Id */
            homework_id: number;
            /** Homework Title */
            homework_title: string;
            /** Id */
            id: number;
            /**
             * Is Working
             * @default true
             */
            is_working: boolean;
            /** Lesson Id */
            lesson_id: number;
            /**
             * Review Files
             * @default []
             */
            review_files: components["schemas"]["HomeworkSubmissionFileResponseDTO"][];
            status: components["schemas"]["HomeworkSubmissionStatus"];
            /** Student First Name */
            student_first_name: string;
            /** Student Last Name */
            student_last_name: string;
            /** Student User Id */
            student_user_id: number;
            /** Student Username */
            student_username: string;
            /** Submitted At */
            submitted_at?: string | null;
            /** Teacher Comment */
            teacher_comment?: string | null;
            /** Text Content */
            text_content?: string | null;
            /**
             * Updated At
             * Format: date-time
             */
            updated_at: string;
            /**
             * Version
             * @default 1
             */
            version: number;
        };
        /** ScheduleWarning */
        ScheduleWarning: {
            /**
             * Code
             * @default teacher_time_overlap
             */
            code: string;
            /** Lesson Ids */
            lesson_ids: number[];
        };
        /** StorageQuotaRequest */
        StorageQuotaRequest: {
            /** Limit Bytes */
            limit_bytes: number;
        };
        /** StorageQuotaResponse */
        StorageQuotaResponse: {
            /** Courses */
            courses: components["schemas"]["CourseStorageUsage"][];
            /** Limit Bytes */
            limit_bytes: number;
            /** Used Bytes */
            used_bytes: number;
            /** User Id */
            user_id: number;
            /** Warning */
            warning: ("near_limit" | "critical" | "full") | null;
        };
        /** StudentCourseResponseDTO */
        StudentCourseResponseDTO: {
            /** Access Ended At */
            access_ended_at?: string | null;
            /** Course Id */
            course_id: number;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Deleted At */
            deleted_at?: string | null;
            /** Expires At */
            expires_at: string | null;
            /**
             * History Revoked
             * @default false
             */
            history_revoked: boolean;
            /** Id */
            id: number;
            /** Is Deleted */
            is_deleted: boolean;
            /**
             * Started At
             * Format: date-time
             */
            started_at: string;
            student?: components["schemas"]["MinimalStudentResponseDTO"] | null;
            /** Student User Id */
            student_user_id: number;
            /**
             * Updated At
             * Format: date-time
             */
            updated_at: string;
        };
        /**
         * StudentSort
         * @enum {string}
         */
        StudentSort: "attention" | "recent" | "grade_asc" | "grade_desc" | "name";
        /** StudentsResponseDTO */
        StudentsResponseDTO: {
            /** Avatar Path */
            avatar_path?: string | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** First Name */
            first_name: string;
            /** Last Name */
            last_name: string;
            /** Middle Name */
            middle_name?: string | null;
            /** School Grade */
            school_grade?: number | null;
            /**
             * Updated At
             * Format: date-time
             */
            updated_at: string;
            /** User Id */
            user_id: number;
        };
        /** TeacherCourseStorageUsage */
        TeacherCourseStorageUsage: {
            /** Bytes */
            bytes: number;
            /** Course Id */
            course_id: number;
            /** Course Name */
            course_name: string;
        };
        /** TeacherStorageResponse */
        TeacherStorageResponse: {
            /** Courses */
            courses: components["schemas"]["TeacherCourseStorageUsage"][];
            /** Used Bytes */
            used_bytes: number;
            /** User Id */
            user_id: number;
        };
        /** TeacherStudentProfileResponseDTO */
        TeacherStudentProfileResponseDTO: {
            /** Avatar Path */
            avatar_path?: string | null;
            /** First Name */
            first_name: string;
            /** Last Name */
            last_name: string;
            /** Missing Homework */
            missing_homework: number;
            /** Missing Lecture */
            missing_lecture: number;
            /** School Grade */
            school_grade?: number | null;
            /** User Id */
            user_id: number;
            /** Username */
            username: string;
        };
        /** TeacherStudentResponseDTO */
        TeacherStudentResponseDTO: {
            /** Active */
            active: boolean;
            /** Student User Id */
            student_user_id: number;
            /** Teacher User Id */
            teacher_user_id: number;
        };
        /** TeachersResponseDTO */
        TeachersResponseDTO: {
            /** Avatar Path */
            avatar_path?: string | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Description */
            description?: string | null;
            /** First Name */
            first_name: string;
            /** Last Name */
            last_name: string;
            /** Middle Name */
            middle_name?: string | null;
            /**
             * Updated At
             * Format: date-time
             */
            updated_at: string;
            /** User Id */
            user_id: number;
        };
        /** TokenResponse */
        TokenResponse: {
            /** Access Token */
            access_token: string;
            /** Refresh Token */
            refresh_token: string;
            /** Token Type */
            token_type: string;
        };
        /** UnreadCountDTO */
        UnreadCountDTO: {
            /** Unread */
            unread: number;
        };
        /** UpdateCourseDTORequest */
        UpdateCourseDTORequest: {
            avatar_type?: components["schemas"]["AvatarCoursesType"] | null;
            /** Call Url */
            call_url?: string | null;
            /** Description */
            description?: string | null;
            /** Expected Updated At */
            expected_updated_at?: string | null;
            /** Is Deleted */
            is_deleted?: boolean | null;
            /** Name */
            name?: string | null;
            /** Slug */
            slug?: string | null;
        };
        /** UpdateLessonPriceDTO */
        UpdateLessonPriceDTO: {
            /** Expected Price Kopecks */
            expected_price_kopecks: number | null;
            /** Lesson Price Kopecks */
            lesson_price_kopecks: number | null;
        };
        /** UpdateLessonRequestDTO */
        UpdateLessonRequestDTO: {
            /** Call Url Override */
            call_url_override?: string | null;
            /** Description */
            description?: string | null;
            /** Duration Minutes */
            duration_minutes?: number | null;
            /** Expected Updated At */
            expected_updated_at?: string | null;
            /** Scheduled At */
            scheduled_at?: string | null;
            status?: components["schemas"]["LessonStatus"] | null;
            /** Title */
            title?: string | null;
            /** Topic */
            topic?: string | null;
        };
        /** UpdateSchoolGradeRequestDTO */
        UpdateSchoolGradeRequestDTO: {
            /** Expected School Grade */
            expected_school_grade: number | null;
            /** School Grade */
            school_grade: number | null;
        };
        /**
         * UpdateSubmissionTeacherRequestDTO
         * @description Final review of the exact answer version opened by the teacher.
         */
        UpdateSubmissionTeacherRequestDTO: {
            /** Expected Version */
            expected_version: number;
            /** Grade */
            grade: number;
            /**
             * Status
             * @default checked
             * @constant
             */
            status: "checked";
            /** Teacher Comment */
            teacher_comment?: string | null;
        };
        /** UpdateUserDataRequestDTO */
        UpdateUserDataRequestDTO: {
            /** Description */
            description?: string | null;
            /** Email */
            email?: string | null;
            /** First Name */
            first_name?: string | null;
            /** Last Name */
            last_name?: string | null;
            /** Middle Name */
            middle_name?: string | null;
            /** Username */
            username?: string | null;
        };
        /** UserAvatarResponseDTO */
        UserAvatarResponseDTO: {
            /** Avatar Path */
            avatar_path: string;
        };
        /** UserResponse */
        UserResponse: {
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Email */
            email?: string | null;
            /** Id */
            id: number;
            role: components["schemas"]["UserRole"];
            /** Username */
            username: string;
        };
        /**
         * UserRole
         * @enum {string}
         */
        UserRole: "admin" | "teacher" | "student";
        /** ValidationError */
        ValidationError: {
            /** Context */
            ctx?: Record<string, never>;
            /** Input */
            input?: unknown;
            /** Location */
            loc: (string | number)[];
            /** Message */
            msg: string;
            /** Error Type */
            type: string;
        };
        /** WeeklyEarningsDTO */
        WeeklyEarningsDTO: {
            /** Completed Count */
            completed_count: number;
            /** Lesson Count */
            lesson_count: number;
            /** Total Kopecks */
            total_kopecks: number;
            /** Unpriced Count */
            unpriced_count: number;
            /**
             * Week
             * Format: date
             */
            week: string;
        };
    };
    responses: never;
    parameters: never;
    requestBodies: never;
    headers: never;
    pathItems: never;
}
export type $defs = Record<string, never>;
export interface operations {
    consume_account_invitations_consume_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ConsumeInvitationRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ConsumeInvitationResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    issue_account_invitations_issue_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["IssueInvitationRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InvitationResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    retry_cleanup_admin_file_deletions_retry_post: {
        parameters: {
            query?: {
                limit?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CleanupResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_users_admin_users_get: {
        parameters: {
            query?: {
                role?: components["schemas"]["UserRole"] | null;
                is_active?: boolean | null;
                is_activated?: boolean | null;
                q?: string | null;
                limit?: number;
                offset?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PaginationResponseDTO_AdminUserResponseDTO_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    user_detail_admin_users__user_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                user_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AdminUserResponseDTO"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    teacher_course_storage_admin_users__user_id__course_storage_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                user_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TeacherStorageResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    storage_quota_admin_users__user_id__storage_quota_patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                user_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["StorageQuotaRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["StorageQuotaResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    audit_events_audit_events_get: {
        parameters: {
            query?: {
                limit?: number;
                offset?: number;
                actor_user_id?: number | null;
                action?: string | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PaginationResponseDTO_AuditEventResponseDTO_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    login_auth_browser_login_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/x-www-form-urlencoded": components["schemas"]["Body_login_auth_browser_login_post"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BrowserTokenResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    logout_auth_browser_logout_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["LogoutResponse"];
                };
            };
        };
    };
    refresh_auth_browser_refresh_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BrowserTokenResponse"];
                };
            };
        };
    };
    change_password_auth_change_password__user_id__post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                user_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ChangePasswordRequestDTO"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UserResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    login_auth_login_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/x-www-form-urlencoded": components["schemas"]["Body_login_auth_login_post"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TokenResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    logout_auth_logout_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["LogoutRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["LogoutResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    refresh_tokens_auth_refresh_tokens_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RefreshTokenRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TokenResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    register_user_auth_register_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RegisterUserRequestDTO"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InvitationUserResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    register_user_by_admin_auth_register_by_admin_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RegisterUserByAdminRequestDTO"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InvitationUserResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_courses_courses_get: {
        parameters: {
            query?: {
                limit?: number;
                offset?: number;
                /** @description Фильтр по создателю курса */
                teacher_user_id?: number | null;
                /**
                 * @deprecated
                 * @description Deprecated; role scope is always enforced
                 */
                my_courses?: boolean | null;
                view?: components["schemas"]["ListView"];
                student_user_id?: number | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PaginationResponseDTO_CoursesResponseDTO_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_course_courses_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CreateCourseDTORequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CoursesResponseDTO"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    read_personal_workspace_courses_personal__student_user_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                student_user_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CoursesResponseDTO"] | null;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    start_personal_workspace_courses_personal__student_user_id__post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                student_user_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CoursesResponseDTO"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_course_by_id_courses__course_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                course_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CoursesResponseDTO"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    delete_course_courses__course_id__delete: {
        parameters: {
            query?: {
                /** @description Удалить безвозвратно */
                hard?: boolean;
            };
            header?: never;
            path: {
                course_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CoursesResponseDTO"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_course_courses__course_id__patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                course_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["UpdateCourseDTORequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CoursesResponseDTO"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_course_avatar_courses__course_id__avatar_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                course_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_avatar_courses__course_id__avatar_patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                course_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "multipart/form-data": components["schemas"]["Body_update_avatar_courses__course_id__avatar_patch"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UserAvatarResponseDTO"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    purge_course_courses__course_id__purge_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                course_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["PurgeCourseRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PurgeResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    restore_course_courses__course_id__restore_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                course_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CoursesResponseDTO"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_students_for_course_courses__course_id__students_get: {
        parameters: {
            query?: {
                limit?: number;
                offset?: number;
            };
            header?: never;
            path: {
                course_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PaginationResponseDTO_StudentCourseResponseDTO_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    enroll_student_to_course_courses__course_id__students_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                course_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["EnrollStudentRequestDTO"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["StudentCourseResponseDTO"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    unenroll_current_student_from_course_courses__course_id__students_me_delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                course_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    unenroll_student_from_course_courses__course_id__students__user_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                course_id: number;
                user_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    history_access_courses__course_id__students__user_id__history_access_patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                course_id: number;
                user_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["HistoryAccessRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_homeworks_list_homeworks_get: {
        parameters: {
            query: {
                lesson_id: number;
                student_user_id: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HomeworkResponseDTO"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_homework_homeworks_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "multipart/form-data": components["schemas"]["Body_create_homework_homeworks_post"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HomeworkResponseDTO"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    available_debts_homeworks_available_debts_get: {
        parameters: {
            query: {
                lesson_id: number;
                student_user_id: number;
                limit?: number;
                offset?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PaginationResponseDTO_HomeworkResponseDTO_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_my_homeworks_homeworks_my_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HomeworkResponseDTO"][];
                };
            };
        };
    };
    get_my_homeworks_page_homeworks_my_page_get: {
        parameters: {
            query?: {
                limit?: number;
                offset?: number;
                course_id?: number | null;
                status?: components["schemas"]["HomeworkListStatus"];
                view?: components["schemas"]["ListView"];
                overdue_only?: boolean;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PaginationResponseDTO_HomeworkResponseDTO_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    homework_detail_homeworks__homework_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                homework_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HomeworkResponseDTO"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    delete_homework_homeworks__homework_id__delete: {
        parameters: {
            query: {
                lesson_id: number;
                student_user_id: number;
            };
            header?: never;
            path: {
                homework_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HomeworkResponseDTO"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    add_homework_debt_homeworks__homework_id__debts_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                homework_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["AddDebtRequestDTO"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PlacementResponseDTO"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    download_homework_file_homeworks__homework_id__file_get: {
        parameters: {
            query: {
                lesson_id: number;
                student_user_id: number;
            };
            header?: never;
            path: {
                homework_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    homework_placement_history_homeworks__homework_id__placements_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                homework_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PlacementResponseDTO"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_homework_submissions_homeworks__homework_id__submissions_get: {
        parameters: {
            query?: {
                limit?: number;
                offset?: number;
                /** @description Сортировка по дате (asc/desc) */
                sort_date?: string;
            };
            header?: never;
            path: {
                homework_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PaginationResponseDTO_HomeworkSubmissionResponseDTO_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_homework_submission_homeworks__homework_id__submissions_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                homework_id: number;
            };
            cookie?: never;
        };
        requestBody?: {
            content: {
                "multipart/form-data": components["schemas"]["Body_create_homework_submission_homeworks__homework_id__submissions_post"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HomeworkSubmissionResponseDTO"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_lectures_list_lectures_get: {
        parameters: {
            query: {
                /** @description Фильтр по уроку */
                lesson_id: number;
                /** @description Фильтр по студенту */
                student_user_id: number;
                limit?: number;
                offset?: number;
                /** @description От даты */
                from_date?: string | null;
                /** @description До даты */
                to_date?: string | null;
                /** @description Сортировка по дате (asc/desc) */
                sort_date?: string;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PaginationResponseDTO_LectureResponseDTO_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    upload_lecture_lectures_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "multipart/form-data": components["schemas"]["Body_upload_lecture_lectures_post"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["LectureResponseDTO"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_my_lectures_lectures_my_get: {
        parameters: {
            query?: {
                course_id?: number | null;
                view?: components["schemas"]["ListView"];
                limit?: number;
                offset?: number;
                /** @description От даты */
                from_date?: string | null;
                /** @description До даты */
                to_date?: string | null;
                /** @description Сортировка по дате (asc/desc) */
                sort_date?: string;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PaginationResponseDTO_LectureResponseDTO_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    lecture_detail_lectures__lecture_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                lecture_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["LectureResponseDTO"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    delete_lecture_lectures__lecture_id__delete: {
        parameters: {
            query: {
                /** @description ID урока */
                lesson_id: number;
                /** @description ID студента */
                student_user_id: number;
            };
            header?: never;
            path: {
                lecture_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["LectureResponseDTO"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    download_lecture_lectures__lecture_id__file_get: {
        parameters: {
            query: {
                /** @description ID урока */
                lesson_id: number;
                /** @description ID студента */
                student_user_id: number;
            };
            header?: never;
            path: {
                lecture_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_lessons_lessons_get: {
        parameters: {
            query?: {
                limit?: number;
                offset?: number;
                /** @description От даты */
                from_date?: string | null;
                /** @description До даты */
                to_date?: string | null;
                /** @description Фильтр по курсу */
                course_id?: number | null;
                status?: components["schemas"]["LessonStatus"] | null;
                view?: components["schemas"]["ListView"];
                student_user_id?: number | null;
                /** @description Сортировка по дате (asc/desc) */
                sort_date?: string;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PaginationResponseDTO_LessonResponseDTO_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_lesson_lessons_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CreateLessonRequestDTO"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["LessonResponseDTO"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_regular_operation_lessons_regular_operations__operation_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                operation_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RegularOperationResponseDTO"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    confirm_regular_lessons_lessons_regular_operations__operation_id__confirm_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                operation_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ConfirmRegularLessonsRequestDTO"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RegularOperationResponseDTO"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    preview_regular_lessons_lessons_regular_previews_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["PreviewRegularLessonsRequestDTO"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RegularOperationResponseDTO"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_regular_series_lessons_regular_series__series_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                series_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RegularSeriesResponseDTO"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_lesson_lessons__lesson_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                lesson_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["LessonResponseDTO"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    delete_lesson_lessons__lesson_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                lesson_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["LessonResponseDTO"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_lesson_lessons__lesson_id__patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                lesson_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["UpdateLessonRequestDTO"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["LessonResponseDTO"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    restore_lesson_lessons__lesson_id__restore_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                lesson_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["LessonResponseDTO"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_lesson_students_lessons__lesson_id__students_get: {
        parameters: {
            query?: {
                limit?: number;
                offset?: number;
            };
            header?: never;
            path: {
                lesson_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PaginationResponseDTO_LessonRecipientResponseDTO_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    add_student_to_lesson_lessons__lesson_id__students_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                lesson_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["AddStudentToLessonRequestDTO"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["LessonStudentResponseDTO"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    remove_student_from_lesson_lessons__lesson_id__students__student_user_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                lesson_id: number;
                student_user_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["LessonStudentResponseDTO"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    notifications_notifications_get: {
        parameters: {
            query?: {
                limit?: number;
                offset?: number;
                unread_only?: boolean;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PaginationResponseDTO_NotificationResponseDTO_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    unread_notifications_unread_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UnreadCountDTO"];
                };
            };
        };
    };
    mark_read_notifications__notification_id__read_patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                notification_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["NotificationResponseDTO"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    target_notifications__notification_id__target_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                notification_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["NotificationTargetDTO"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_review_queue_submissions_review_queue_get: {
        parameters: {
            query?: {
                limit?: number;
                offset?: number;
                course_id?: number | null;
                student_user_id?: number | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PaginationResponseDTO_ReviewQueueItemDTO_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_homework_submission_submissions__submission_id__get: {
        parameters: {
            query: {
                homework_id: number;
            };
            header?: never;
            path: {
                submission_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HomeworkSubmissionResponseDTO"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    delete_homework_submission_submissions__submission_id__delete: {
        parameters: {
            query: {
                homework_id: number;
            };
            header?: never;
            path: {
                submission_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HomeworkSubmissionResponseDTO"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_homework_submission_file_submissions__submission_id__files__file_id__get: {
        parameters: {
            query: {
                homework_id: number;
            };
            header?: never;
            path: {
                submission_id: number;
                file_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    replace_submission_file_submissions__submission_id__files__file_id__put: {
        parameters: {
            query: {
                homework_id: number;
            };
            header?: never;
            path: {
                submission_id: number;
                file_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "multipart/form-data": components["schemas"]["Body_replace_submission_file_submissions__submission_id__files__file_id__put"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HomeworkSubmissionResponseDTO"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    delete_submission_file_submissions__submission_id__files__file_id__delete: {
        parameters: {
            query: {
                homework_id: number;
                expected_version?: number | null;
            };
            header?: never;
            path: {
                submission_id: number;
                file_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HomeworkSubmissionResponseDTO"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    review_homework_submission_with_files_submissions__submission_id__review_patch: {
        parameters: {
            query: {
                homework_id: number;
            };
            header?: never;
            path: {
                submission_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "multipart/form-data": components["schemas"]["Body_review_homework_submission_with_files_submissions__submission_id__review_patch"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HomeworkSubmissionResponseDTO"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_homework_submission_student_submissions__submission_id__student_patch: {
        parameters: {
            query: {
                homework_id: number;
            };
            header?: never;
            path: {
                submission_id: number;
            };
            cookie?: never;
        };
        requestBody?: {
            content: {
                "multipart/form-data": components["schemas"]["Body_update_homework_submission_student_submissions__submission_id__student_patch"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HomeworkSubmissionResponseDTO"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    submit_homework_submission_submissions__submission_id__submit_post: {
        parameters: {
            query: {
                homework_id: number;
            };
            header?: never;
            path: {
                submission_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HomeworkSubmissionResponseDTO"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_homework_submission_teacher_submissions__submission_id__teacher_patch: {
        parameters: {
            query: {
                homework_id: number;
            };
            header?: never;
            path: {
                submission_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["UpdateSubmissionTeacherRequestDTO"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HomeworkSubmissionResponseDTO"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    mark_material_not_needed_teacher_planning_lessons__lesson_id__students__student_user_id__patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                lesson_id: number;
                student_user_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ReminderRequestDTO"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PaginationResponseDTO_RecipientReminderDTO_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    reminders_teacher_planning_reminders_get: {
        parameters: {
            query?: {
                lesson_id?: number | null;
                student_user_id?: number | null;
                only_missing?: boolean;
                limit?: number;
                offset?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PaginationResponseDTO_RecipientReminderDTO_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    planning_students_teacher_planning_students_get: {
        parameters: {
            query: {
                week: string;
                deficit_only?: boolean;
                student_user_id?: number | null;
                q?: string | null;
                limit?: number;
                offset?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PaginationResponseDTO_PlanningStudentDTO_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    save_norm_teacher_planning_students__student_user_id__norm_put: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                student_user_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["NormRequestDTO"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["NormRevisionDTO"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    student_price_teacher_planning_students__student_user_id__price_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                student_user_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["LessonPriceDTO"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    save_student_price_teacher_planning_students__student_user_id__price_put: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                student_user_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["UpdateLessonPriceDTO"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["LessonPriceDTO"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    weekly_earnings_teacher_planning_weekly_earnings_get: {
        parameters: {
            query: {
                week: string;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["WeeklyEarningsDTO"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_links_teacher_students_get: {
        parameters: {
            query?: {
                teacher_user_id?: number | null;
                student_user_id?: number | null;
                active?: boolean | null;
                limit?: number;
                offset?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PaginationResponseDTO_AdminTeacherStudentResponseDTO_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    link_teacher_student_teacher_students_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["LinkTeacherStudentRequestDTO"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TeacherStudentResponseDTO"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    end_link_teacher_students__teacher_user_id___student_user_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                teacher_user_id: number;
                student_user_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_me_users_me_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UserResponse"];
                };
            };
        };
    };
    get_students_users_students_get: {
        parameters: {
            query?: {
                sort?: components["schemas"]["StudentSort"];
                attention?: ("homework" | "lecture") | null;
                school_grade?: number | null;
                q?: string | null;
                limit?: number;
                offset?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PaginationResponseDTO_Union_PublicProfileResponseDTO__TeacherStudentProfileResponseDTO__MinimalProfileResponseDTO__"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_teachers_users_teachers_get: {
        parameters: {
            query?: {
                limit?: number;
                offset?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PaginationResponseDTO_Union_PublicProfileResponseDTO__MinimalProfileResponseDTO__"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_public_profile_users__user_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                user_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PublicProfileResponseDTO"] | components["schemas"]["MinimalProfileResponseDTO"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_user_users__user_id__patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                user_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["UpdateUserDataRequestDTO"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TeachersResponseDTO"] | components["schemas"]["StudentsResponseDTO"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_account_status_users__user_id__account_status_patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                user_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["AdminAccountStatusRequestDTO"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UserResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_avatar_users__user_id__avatar_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                user_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    delete_avatar_users__user_id__avatar_delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                user_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_avatar_users__user_id__avatar_patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                user_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "multipart/form-data": components["schemas"]["Body_update_avatar_users__user_id__avatar_patch"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UserAvatarResponseDTO"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_school_grade_users__user_id__school_grade_patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                user_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["UpdateSchoolGradeRequestDTO"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PublicProfileResponseDTO"] | components["schemas"]["MinimalProfileResponseDTO"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    storage_usage_users__user_id__storage_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                user_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["StorageQuotaResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
}
