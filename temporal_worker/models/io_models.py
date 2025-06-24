from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class ReplicateJobPostsInput:
    source_post_id: int
    regions: List[str]
    job_id: int
    user_email: str


@dataclass
class ReplicateJobPostsOutput:
    workflow_type: str
    success: bool
    created_posts: List[Dict[str, Any]]
    deleted_posts: List[Dict[str, Any]]
    errors: List[str]
    target_locations: int
    new_post_id: Optional[int] = None


@dataclass
class JobPostLocation:
    id: int
    location: str


@dataclass
class GetExistingJobPostsInput:
    job_id: int
    target_locations: List[str]


@dataclass
class DeleteJobPostInput:
    post_id: int
    job_id: int


@dataclass
class DuplicateJobPostInput:
    source_post_id: int
    location: str
    board_id: int
    job_id: int


@dataclass
class GetBoardByNameInput:
    board_name: str


@dataclass
class SetJobPostStatusInput:
    post_id: int
    job_id: int
    status: str
    status_id: int
