import logging
from datetime import timedelta

from temporalio import workflow

from temporal_worker.constants import JOB_POST_REGIONS

# pass static imports through the sandbox (recommended by Temporal)
with workflow.unsafe.imports_passed_through():
    from temporal_worker.activities.activities import FakeGreenhouseActivities
    from temporal_worker.models.io_models import (
        DeleteJobPostInput,
        DuplicateJobPostInput,
        GetBoardByNameInput,
        GetExistingJobPostsInput,
        ReplicateJobPostsInput,
        ReplicateJobPostsOutput,
        SetJobPostStatusInput,
    )

logger = logging.getLogger(__name__)


@workflow.defn
class FakeReplicateJobPostsWorkflow:
    @workflow.run
    async def run(
        self, input: ReplicateJobPostsInput
    ) -> ReplicateJobPostsOutput:
        """
        Mock replicate workflow:
        1. validate regions
        2. get target board ID
        3. delete existing replicated posts in target regions
        4. create new replicated posts for each location in regions
        """
        logger.info(
            f"Starting Fake replicate workflow: "
            f"job post {input.source_post_id} -> {input.regions}"
        )

        try:
            # validate regions
            invalid_regions = [
                r for r in input.regions if r not in JOB_POST_REGIONS
            ]
            if invalid_regions:
                raise ValueError(f"Invalid regions: {invalid_regions}")

            # collect all target locations
            target_locations = []
            for region in input.regions:
                target_locations.extend(JOB_POST_REGIONS[region])

            total_locations = len(target_locations)

            results = ReplicateJobPostsOutput(
                workflow_type="fake_replicate",
                success=False,  # will be set to True at the end if no errors
                created_posts=[],
                deleted_posts=[],
                errors=[],
                target_locations=total_locations,
            )

            logger.info("Fake workflow: Finding existing posts to delete")

            # get existing job posts for deletion
            fake_activities = FakeGreenhouseActivities()
            existing_posts = await workflow.execute_activity(
                fake_activities.get_existing_job_posts_by_location,
                GetExistingJobPostsInput(
                    job_id=input.job_id, target_locations=target_locations
                ),
                start_to_close_timeout=timedelta(minutes=2),
            )

            # delete existing posts
            deletion_count = len(existing_posts)
            logger.info(
                f"Fake workflow: Deleting {deletion_count} existing posts"
            )

            for i, post_info in enumerate(existing_posts):
                try:
                    await workflow.execute_activity(
                        fake_activities.delete_job_post,
                        DeleteJobPostInput(
                            post_id=post_info.id, job_id=input.job_id
                        ),
                        start_to_close_timeout=timedelta(minutes=1),
                    )
                    results.deleted_posts.append(
                        {
                            "id": post_info.id,
                            "location": post_info.location,
                        }
                    )

                except Exception as e:
                    error_msg = (
                        f"Failed to delete post {post_info.id}: {str(e)}"
                    )
                    logger.error(error_msg)
                    results.errors.append(error_msg)

            # get target board information
            logger.info("Fake workflow: Getting target board information")

            target_board_name = await workflow.execute_activity(
                fake_activities.get_target_board_name,
                start_to_close_timeout=timedelta(seconds=10),
            )

            target_board = await workflow.execute_activity(
                fake_activities.get_board_by_name,
                GetBoardByNameInput(board_name=target_board_name),
                start_to_close_timeout=timedelta(minutes=1),
            )

            # create new posts for each target location
            for i, location in enumerate(target_locations):
                try:
                    logger.info(
                        f"Fake workflow: Creating post for {location} "
                        f"({i + 1}/{len(target_locations)})"
                    )

                    # duplicate job post
                    result = await workflow.execute_activity(
                        fake_activities.duplicate_job_post,
                        DuplicateJobPostInput(
                            source_post_id=input.source_post_id,
                            location=location,
                            board_id=target_board["id"],
                            job_id=input.job_id,
                        ),
                        start_to_close_timeout=timedelta(minutes=2),
                    )

                    # set new post to live status
                    new_post_id = result.get("job_application_id")
                    if new_post_id:
                        await workflow.execute_activity(
                            fake_activities.set_job_post_status,
                            SetJobPostStatusInput(
                                post_id=new_post_id,
                                job_id=input.job_id,
                                status="live",
                                status_id=target_board["publish_status_id"],
                            ),
                            start_to_close_timeout=timedelta(minutes=1),
                        )

                    results.created_posts.append(
                        {
                            "location": location,
                            "post_id": new_post_id,
                            "status": "live",
                        }
                    )

                except Exception as e:
                    error_msg = (
                        f"Failed to create post for {location}: {str(e)}"
                    )
                    logger.error(error_msg)
                    results["errors"].append(error_msg)

            logger.info("Fake workflow: Replication completed")

            results.success = len(results.errors) == 0

            return results

        except Exception as e:
            logger.error(f"Fake replicate workflow failed: {str(e)}")
            raise
