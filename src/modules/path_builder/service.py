from pathlib import Path

from src.core.config import Config


class PathBuilder:
    def __init__(self, config: Config):
        self.config = config

    @staticmethod
    def _prepare_directory(directory: Path) -> Path:
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    # --- avatar ---

    def get_avatar_user(self, user_id: int) -> Path:
        root_dir = self._prepare_directory(
            self.config.paths.avatars_users / str(user_id)
        )

        return root_dir / "avatar.webp"

    def get_avatar_course(self, course_id: int) -> Path:
        root_dir = self._prepare_directory(
            self.config.paths.avatars_courses / str(course_id)
        )

        return root_dir / "avatar.webp"

    # --- lecture ---

    def get_lecture_original(
        self,
        lecture_id: int,
        file_name: str,
        file_type: str,
    ) -> Path:
        root_dir = self._prepare_directory(
            self.config.paths.lectures
            / str(lecture_id)
            / "original"
        )

        return root_dir / f"{file_name}.{file_type}"

    def get_lecture_pdf(
        self,
        lecture_id: int,
        file_name: str,
    ) -> Path:
        root_dir = self._prepare_directory(
            self.config.paths.lectures / str(lecture_id)
        )

        return root_dir / f"{file_name}.pdf"

    # --- homework ---

    def get_homework_original(
        self,
        homework_id: int,
        file_name: str,
        file_type: str,
    ) -> Path:
        root_dir = self._prepare_directory(
            self.config.paths.homework
            / str(homework_id)
            / "original"
        )

        return root_dir / f"{file_name}.{file_type}"

    def get_homework_pdf(
        self,
        homework_id: int,
        file_name: str,
    ) -> Path:
        root_dir = self._prepare_directory(
            self.config.paths.homework / str(homework_id)
        )

        return root_dir / f"{file_name}.pdf"

    # --- homework submission ---

    def get_homework_submission_original(
        self,
        homework_submission_id: int,
        file_name: str,
        file_type: str,
    ) -> Path:
        root_dir = self._prepare_directory(
            self.config.paths.homework_submissions
            / str(homework_submission_id)
            / "original"
        )

        return root_dir / f"{file_name}.{file_type}"

    def get_homework_submission_pdf(
        self,
        homework_submission_id: int,
        file_name: str,
    ) -> Path:
        root_dir = self._prepare_directory(
            self.config.paths.homework_submissions
            / str(homework_submission_id)
        )

        return root_dir / f"{file_name}.pdf"

    # --- temp ---

    def get_temp(self) -> Path:
        return self._prepare_directory(
            self.config.paths.temp
        )