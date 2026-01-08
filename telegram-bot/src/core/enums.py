from enum import StrEnum


class UserRole(StrEnum):
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"


class TaskStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class BlockType(StrEnum):
    TEXT = "text"
    VIDEO = "video"
    EXTERNAL_LINK = "external_link"
    CODE = "code"
    CODE_EXAMPLE = "code_example"
    INTERACTIVE = "interactive"
    READING = "reading"


class AssessmentType(StrEnum):
    TEST = "test"
    PROJECT = "project"
    CODE = "code"
    ESSAY = "essay"


class DifficultyLevel(StrEnum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"
