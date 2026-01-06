from enum import StrEnum


class UserRole(StrEnum):
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"


class BlockType(StrEnum):
    TEXT = "text"
    VIDEO = "video"
    EXTERNAL_LINK = "external_link"
    CODE = "code"


class AssessmentType(StrEnum):
    TEST = "test"
    PROJECT = "project"
    CODE = "code"
    ESSAY = "essay"
