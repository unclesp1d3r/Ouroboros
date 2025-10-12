from typing import Annotated

# Third-party imports
from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    Path,
    Response,
    status,
)
from fastapi.responses import JSONResponse, PlainTextResponse
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InvalidAgentTokenError
from app.core.services.agent_service import (
    submit_cracked_hash_service,
    submit_task_status_service,
    update_task_progress_service,
)
from app.core.services.client_service import (
    AgentNotAssignedError,
    TaskNotRunningError,
)
from app.core.services.task_service import (
    NoPendingTasksError,
    TaskAlreadyAbandonedError,
    TaskAlreadyCompletedError,
    TaskAlreadyExhaustedError,
    TaskNotFoundError,
    abandon_task_service,
    accept_task_service,
    assign_task_service,
    exhaust_task_service,
    get_task_by_id_service,
    get_task_zaps_service,
)

# Local imports
from app.db.session import get_db
from app.schemas.task import (
    HashcatResult,
    TaskOutV1,
    TaskProgressUpdate,
    TaskStatusUpdate,
)

router = APIRouter(prefix="/client/tasks")


@router.post(
    "/{id}/progress",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Update task progress (v1 compatibility)",
    description="Agents send progress updates for a task. Compatibility layer for v1 API.",
)
@router.post(
    "/tasks/{id}/progress",
    status_code=status.HTTP_204_NO_CONTENT,
    include_in_schema=False,
)
async def update_task_progress_v1(
    id: Annotated[int, Path()],  # noqa: A002
    data: TaskProgressUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[str, Header(alias="Authorization")],
) -> Response:
    try:
        await update_task_progress_service(id, data, db, authorization)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except InvalidAgentTokenError as e:
        raise HTTPException(status_code=401, detail="Not authorized") from e
    except (TaskNotFoundError, AgentNotAssignedError):
        raise HTTPException(
            status_code=404, detail={"error": "Record not found"}
        ) from None
    except PermissionError as e:
        raise HTTPException(status_code=403, detail="Forbidden") from e
    except TaskNotRunningError as e:
        raise HTTPException(status_code=409, detail="Task not running") from e
    except TaskAlreadyExhaustedError as e:
        raise HTTPException(status_code=422, detail="Task already completed") from e
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e


@router.post(
    "/{id}/submit_status",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Submit a status update for a task (v1 agent API)",
    description="Submit a status update for a running task. This is the main status heartbeat endpoint for agents.",
    responses={
        status.HTTP_204_NO_CONTENT: {"description": "status received successfully"},
        status.HTTP_202_ACCEPTED: {
            "description": "status received successfully, but stale"
        },
        status.HTTP_410_GONE: {
            "description": "status received successfully, but task paused"
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "malformed status data"},
        status.HTTP_404_NOT_FOUND: {"description": "Task not found"},
        status.HTTP_401_UNAUTHORIZED: {"description": "Unauthorized"},
        status.HTTP_403_FORBIDDEN: {"description": "Forbidden"},
        status.HTTP_409_CONFLICT: {"description": "Task not running"},
    },
)
@router.post(
    "/tasks/{id}/submit_status",
    status_code=status.HTTP_204_NO_CONTENT,
    include_in_schema=False,
)
async def submit_task_status_v1(
    id: Annotated[int, Path()],  # noqa: A002
    data: TaskStatusUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[str, Header(alias="Authorization")],
) -> Response:
    try:
        status_code = await submit_task_status_service(id, data, db, authorization)
        return Response(status_code=status_code)
    except InvalidAgentTokenError as e:
        raise HTTPException(status_code=401, detail="Not authorized") from e
    except AgentNotAssignedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "Agent not assigned to this task"},
        ) from None
    except TaskNotRunningError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "Task is not running"},
        ) from None
    except TaskNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail={"error": "Task not found"}
        ) from None
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"error": str(e)}
        ) from None


@router.get(
    "/new",
    status_code=status.HTTP_200_OK,
    summary="Request a new task from server (v1 compatibility)",
    description="Request a new task from the server, if available. Compatibility layer for v1 API.",
)
@router.get(
    "/tasks/new",
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def get_new_task_v1(
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[str, Header(alias="Authorization")],
) -> Response:
    try:
        task = await assign_task_service(db, authorization, "Ouroboros-Agent/1.0.0")
        if task is None:
            return Response(status_code=status.HTTP_204_NO_CONTENT)
        return JSONResponse(
            content=TaskOutV1.model_validate(task, from_attributes=True).model_dump(
                mode="json"
            ),
            status_code=status.HTTP_200_OK,
        )
    except NoPendingTasksError:
        # Expected when no tasks are available or agent has no benchmark data
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except InvalidAgentTokenError as e:
        raise HTTPException(status_code=401, detail="Not authorized") from e


@router.get(
    "/{id}",
    summary="Request the task information (v1 agent API)",
    description="Request the task information from the server. Requires agent authentication and assignment.",
    responses={
        status.HTTP_200_OK: {"content": {"application/json": {}}},
        status.HTTP_404_NOT_FOUND: {"description": "Task not found"},
        status.HTTP_401_UNAUTHORIZED: {"description": "Unauthorized"},
        status.HTTP_403_FORBIDDEN: {"description": "Forbidden"},
    },
)
@router.get(
    "/tasks/{id}",
    include_in_schema=False,
)
async def get_task_v1(
    id: Annotated[int, Path()],  # noqa: A002
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[str, Header(alias="Authorization")],
) -> TaskOutV1:
    try:
        return await get_task_by_id_service(id, db, authorization)
    except (TaskNotFoundError, AgentNotAssignedError):
        raise HTTPException(
            status_code=404, detail={"error": "Record not found"}
        ) from None
    except PermissionError as e:
        raise HTTPException(status_code=403, detail="Forbidden") from e
    except InvalidAgentTokenError as e:
        raise HTTPException(status_code=401, detail="Not authorized") from e


@router.post(
    "/{id}/accept_task",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Accept Task (v1 agent API)",
    description="Accept an offered task from the server. Sets the task status to running and assigns it to the agent.",
    responses={
        status.HTTP_204_NO_CONTENT: {"description": "task accepted successfully"},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "task already completed"},
        status.HTTP_404_NOT_FOUND: {"description": "task not found for agent"},
        status.HTTP_401_UNAUTHORIZED: {"description": "Unauthorized"},
        status.HTTP_403_FORBIDDEN: {"description": "Forbidden"},
    },
)
@router.post(
    "/tasks/{id}/accept_task",
    status_code=status.HTTP_204_NO_CONTENT,
    include_in_schema=False,
)
async def accept_task_v1(
    id: Annotated[int, Path()],  # noqa: A002
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[str, Header(alias="Authorization")],
) -> None:
    try:
        await accept_task_service(id, db, authorization)
    except InvalidAgentTokenError as e:
        raise HTTPException(status_code=401, detail="Not authorized") from e
    except (TaskNotFoundError, AgentNotAssignedError):
        raise HTTPException(
            status_code=404, detail={"error": "Record not found"}
        ) from None
    except PermissionError as e:
        raise HTTPException(status_code=403, detail="Forbidden") from e
    except TaskAlreadyCompletedError as e:
        raise HTTPException(status_code=422, detail="Task already completed") from e
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e


@router.post(
    "/{id}/exhausted",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Notify of Exhausted Task (v1 agent API)",
    description="Notify the server that the task is exhausted. This will mark the task as completed.",
    responses={
        status.HTTP_204_NO_CONTENT: {"description": "successful"},
        status.HTTP_404_NOT_FOUND: {"description": "Task not found"},
        status.HTTP_401_UNAUTHORIZED: {"description": "Unauthorized"},
        status.HTTP_403_FORBIDDEN: {"description": "Forbidden"},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "description": "Task already completed or exhausted"
        },
    },
)
@router.post(
    "/tasks/{id}/exhausted",
    status_code=status.HTTP_204_NO_CONTENT,
    include_in_schema=False,
)
async def exhaust_task_v1(
    id: Annotated[int, Path()],  # noqa: A002
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[str, Header(alias="Authorization")],
) -> None:
    try:
        await exhaust_task_service(id, db, authorization)
    except InvalidAgentTokenError as e:
        raise HTTPException(status_code=401, detail="Not authorized") from e
    except (TaskNotFoundError, AgentNotAssignedError):
        raise HTTPException(
            status_code=404, detail={"error": "Record not found"}
        ) from None
    except PermissionError as e:
        raise HTTPException(status_code=403, detail="Forbidden") from e
    except TaskAlreadyExhaustedError as e:
        raise HTTPException(status_code=422, detail="Task already completed") from e
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e


@router.post(
    "/{id}/abandon",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Abandon Task (v1 agent API)",
    description="Abandon a task. This will mark the task as abandoned. Usually used when the client is unable to complete the task.",
    responses={
        status.HTTP_204_NO_CONTENT: {"description": "successful"},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "description": "already completed",
            "content": {"application/json": {}},
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Task not found",
            "content": {"application/json": {}},
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Unauthorized",
            "content": {"application/json": {}},
        },
        status.HTTP_403_FORBIDDEN: {"description": "Forbidden"},
    },
)
@router.post(
    "/tasks/{id}/abandon",
    status_code=status.HTTP_204_NO_CONTENT,
    include_in_schema=False,
)
async def abandon_task_v1(
    id: Annotated[int, Path()],  # noqa: A002
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[str, Header(alias="Authorization")],
) -> None:
    try:
        await abandon_task_service(id, db, authorization)
    except InvalidAgentTokenError as e:
        raise HTTPException(status_code=401, detail="Not authorized") from e
    except (TaskNotFoundError, AgentNotAssignedError):
        raise HTTPException(
            status_code=404, detail={"error": "Record not found"}
        ) from None
    except PermissionError as e:
        raise HTTPException(status_code=403, detail="Forbidden") from e
    except TaskAlreadyAbandonedError as e:
        raise HTTPException(status_code=422, detail="Task already abandoned") from e
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e


@router.get(
    "/{id}/get_zaps",
    summary="Get Completed Hashes (v1 agent API)",
    description="Gets the completed hashes for a task. This is a text file that should be added to the monitored directory to remove the hashes from the list during runtime.",
    response_class=PlainTextResponse,
    responses={
        status.HTTP_200_OK: {"content": {"text/plain": {}}},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "already completed"},
        status.HTTP_404_NOT_FOUND: {"description": "Task not found"},
        status.HTTP_401_UNAUTHORIZED: {"description": "Unauthorized"},
        status.HTTP_403_FORBIDDEN: {"description": "Forbidden"},
    },
)
@router.get(
    "/tasks/{id}/get_zaps",
    include_in_schema=False,
)
async def get_task_zaps_v1(
    id: Annotated[int, Path()],  # noqa: A002
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> Response:
    if authorization is None:
        raise HTTPException(status_code=401, detail="Not authorized")
    try:
        zaps = await get_task_zaps_service(id, db, authorization)
        return PlainTextResponse("\n".join(zaps), status_code=status.HTTP_200_OK)
    except (TaskNotFoundError, AgentNotAssignedError):
        raise HTTPException(
            status_code=404, detail={"error": "Record not found"}
        ) from None
    except InvalidAgentTokenError as e:
        raise HTTPException(status_code=401, detail="Not authorized") from e
    except PermissionError as e:
        raise HTTPException(status_code=403, detail="Forbidden") from e
    except TaskAlreadyCompletedError as e:
        raise HTTPException(status_code=422, detail="Task already completed") from e


@router.post(
    "/{id}/submit_crack",
    status_code=status.HTTP_200_OK,
    summary="Submit a cracked hash result for a task (v1 compatibility)",
    description="Submit a cracked hash result for a task. Compatibility layer for v1 API.",
)
@router.post(
    "/tasks/{id}/submit_crack",
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def submit_cracked_hash_v1(
    id: Annotated[int, Path(alias="id")],  # noqa: A002
    data: HashcatResult,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[str, Header(alias="Authorization")],
) -> JSONResponse:
    try:
        await submit_cracked_hash_service(
            task_id=id,
            hash_value=data.hash,
            plain_text=data.plain_text,
            db=db,
            authorization=authorization,
        )
        return JSONResponse(
            content={"message": "Cracked hash submitted"},
            status_code=status.HTTP_200_OK,
        )
    except InvalidAgentTokenError as e:
        raise HTTPException(status_code=401, detail="Not authorized") from e
    except (TaskNotFoundError, AgentNotAssignedError):
        raise HTTPException(
            status_code=404, detail={"error": "Record not found"}
        ) from None
    except TaskNotRunningError as e:
        raise HTTPException(status_code=409, detail="Task not running") from e
    except ValueError as e:
        # For Agent API v1, hash not found should return 404 with error format per `contracts/v1_api_swagger.json`
        if "Hash not found in hash list" in str(e):
            raise HTTPException(
                status_code=404, detail={"error": "Hash not found"}
            ) from e
        raise HTTPException(status_code=422, detail=str(e)) from e
    except Exception as e:
        logger.exception("Unexpected error in submit_cracked_hash_v1")
        raise HTTPException(status_code=500, detail="Internal server error") from e
