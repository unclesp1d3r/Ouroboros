"""
Follow these rules for all endpoints in this file:
1. Must return Pydantic models as JSON (no TemplateResponse or render()).
2. Must use FastAPI parameter types: Query, Path, Body, Depends, etc.
3. Must not parse inputs manually -- let FastAPI validate and raise 422s.
4. Must use dependency-injected context for auth/user/project state.
5. Must not include database logic -- delegate to a service layer (e.g. campaign_service).
6. Must not contain HTMX, Jinja, or fragment-rendering logic.
7. Must annotate live-update triggers with: # WS_TRIGGER: <event description>
"""

from typing import Annotated

from fastapi import (
    APIRouter,
    Body,
    Depends,
    HTTPException,
    Path,
    Query,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.datastructures import FormData

from app.core.authz import user_can
from app.core.deps import get_current_user
from app.core.exceptions import AgentNotFoundError
from app.core.services.agent_service import (
    get_agent_benchmark_summary_service,
    get_agent_by_id_service,
    get_agent_capabilities_service,
    get_agent_device_performance_timeseries,
    get_agent_error_log_service,
    list_agents_service,
    register_agent_full_service,
    toggle_agent_enabled_service,
    trigger_agent_benchmark_service,
    update_agent_config_service,
    update_agent_devices_service,
    update_agent_hardware_service,
    validate_presigned_url_service,
)
from app.db.session import get_db
from app.models.agent import OperatingSystemEnum
from app.models.user import User
from app.schemas.agent import (
    AdvancedAgentConfiguration,
    AgentBenchmarkSummaryOut,
    AgentCapabilitiesOut,
    AgentErrorLogOut,
    AgentListOut,
    AgentOut,
    AgentPerformanceSeriesOut,
    AgentPresignedUrlTestRequest,
    AgentPresignedUrlTestResponse,
    AgentRegisterModalContext,
    AgentToggleEnabledOut,
    AgentUpdateConfigOut,
    AgentUpdateDevicesOut,
    AgentUpdateHardwareOut,
    DevicePerformanceSeries,
)
from app.schemas.agent_error import AgentErrorOut

router = APIRouter(prefix="/agents", tags=["Agents"])


@router.get("", summary="List/filter agents")
async def list_agents(
    db: Annotated[AsyncSession, Depends(get_db)],
    search: Annotated[str | None, Query(description="Search by host name")] = None,
    state: Annotated[str | None, Query(description="Filter by agent state")] = None,
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Page size")] = 20,
) -> AgentListOut:
    """Return a paginated, filterable list of agents."""
    agents, total = await list_agents_service(db, search, state, page, page_size)
    agents_out = [AgentOut.model_validate(a, from_attributes=True) for a in agents]
    return AgentListOut(
        items=agents_out,
        page=page,
        page_size=page_size,
        total=total,
        search=search,
        state=state,
    )


@router.get("/{agent_id}", summary="Agent detail")
async def agent_detail(
    agent_id: Annotated[int, Path(description="Agent ID")],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AgentOut:
    agent = await get_agent_by_id_service(agent_id, db)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return AgentOut.model_validate(agent, from_attributes=True)


@router.patch(
    "/{agent_id}",
    summary="Toggle agent enabled/disabled",
)
async def toggle_agent_enabled(
    agent_id: Annotated[int, Path(description="Agent ID")],
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> AgentToggleEnabledOut:
    try:
        agent = await toggle_agent_enabled_service(agent_id, user, db)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except AgentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return AgentToggleEnabledOut(
        agent=AgentOut.model_validate(agent, from_attributes=True)
    )


@router.get(
    "/{agent_id}/benchmarks",
    summary="Agent benchmark summary",
)
async def agent_benchmark_summary(
    agent_id: Annotated[int, Path(description="Agent ID")],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AgentBenchmarkSummaryOut:
    try:
        benchmarks_by_hash_type = await get_agent_benchmark_summary_service(
            agent_id, db
        )
    except AgentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found"
        ) from e
    # Convert int keys to str for OpenAPI compatibility
    str_benchmarks = {str(k): v for k, v in benchmarks_by_hash_type.items()}
    return AgentBenchmarkSummaryOut(benchmarks_by_hash_type=str_benchmarks)


@router.post(
    "/{agent_id}/benchmark",
    summary="Trigger agent benchmark run (set to pending)",
)
# WS_TRIGGER: Notify agent benchmark status update
async def trigger_agent_benchmark(
    agent_id: Annotated[int, Path(description="Agent ID")],
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> AgentOut:
    try:
        agent = await trigger_agent_benchmark_service(agent_id, user, db)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except AgentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return AgentOut.model_validate(agent, from_attributes=True)


@router.post(
    "/{agent_id}/test_presigned",
    summary="Validate presigned S3/MinIO URL for agent resource",
)
async def test_agent_presigned_url(
    agent_id: Annotated[int, Path(description="Agent ID")],
    payload: Annotated[AgentPresignedUrlTestRequest, Body(embed=True)],
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> AgentPresignedUrlTestResponse:
    # Only admins can use this endpoint
    if (
        not user_can(user, "system", "create_users")
        and getattr(user, "role", None) != "admin"
    ):
        raise HTTPException(status_code=403, detail="Admin only")
    agent = await get_agent_by_id_service(agent_id, db)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    valid = await validate_presigned_url_service(str(payload.url))
    return AgentPresignedUrlTestResponse(valid=valid)


def _parse_agent_config_form(
    form: FormData,
) -> dict[str, int | str | None | bool | object]:
    data = {k: v for k, v in form.items() if not hasattr(v, "filename")}
    if "agent_update_interval" in data:
        try:
            data["agent_update_interval"] = str(int(str(data["agent_update_interval"])))
        except ValueError:
            data["agent_update_interval"] = "30"
    for key in ["use_native_hashcat", "enable_additional_hash_types"]:
        if key in data:
            v = str(data[key])
            data[key] = "true" if v == "true" else "false"
    for key in ["backend_device", "opencl_devices"]:
        if key in data and str(data[key]) == "":
            data[key] = ""
    return {
        "agent_update_interval": int(str(data.get("agent_update_interval", "30"))),
        "use_native_hashcat": str(data.get("use_native_hashcat", "false")) == "true",
        "backend_device": str(data.get("backend_device")) or None,
        "opencl_devices": str(data.get("opencl_devices")) or None,
        "enable_additional_hash_types": str(
            data.get("enable_additional_hash_types", "false")
        )
        == "true",
    }


@router.patch(
    "/{agent_id}/config",
    summary="Update agent advanced configuration",
)
async def update_agent_config(
    agent_id: Annotated[int, Path(description="Agent ID")],
    config: Annotated[AdvancedAgentConfiguration, Body(embed=True)],
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> AgentUpdateConfigOut:
    try:
        await get_agent_by_id_service(agent_id, db)
    except AgentNotFoundError:
        raise HTTPException(status_code=404, detail="Agent not found") from None
    if not (
        getattr(user, "is_superuser", False)
        or user_can(user, "system", "update_agents")
    ):
        raise HTTPException(
            status_code=403, detail="Not authorized to update agent config"
        )
    try:
        updated_agent = await update_agent_config_service(agent_id, config, db)
    except AgentNotFoundError:
        raise HTTPException(status_code=404, detail="Agent not found") from None
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Update failed: {e}") from e
    return AgentUpdateConfigOut(
        agent=AgentOut.model_validate(updated_agent, from_attributes=True)
    )


@router.get("/{agent_id}/errors", summary="Agent error log")
async def agent_error_log(
    agent_id: Annotated[int, Path(description="Agent ID")],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AgentErrorLogOut:
    errors = await get_agent_error_log_service(agent_id, db)
    errors_out = [AgentErrorOut.model_validate(e, from_attributes=True) for e in errors]
    return AgentErrorLogOut(errors=errors_out)


@router.patch(
    "/{agent_id}/devices",
    summary="Toggle enabled backend devices for agent",
)
async def toggle_agent_devices(
    agent_id: Annotated[int, Path(description="Agent ID")],
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    enabled_indices: Annotated[
        list[int], Body(embed=True, description="List of enabled device indices")
    ],
) -> AgentUpdateDevicesOut:
    try:
        await update_agent_devices_service(agent_id, enabled_indices, user, db)
        agent = await get_agent_by_id_service(agent_id, db)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except AgentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return AgentUpdateDevicesOut(
        agent=AgentOut.model_validate(agent, from_attributes=True)
    )


@router.get(
    "/{agent_id}/performance",
    summary="Agent performance time series",
)
async def agent_performance(
    agent_id: Annotated[int, Path(description="Agent ID")],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AgentPerformanceSeriesOut:
    agent = await get_agent_by_id_service(agent_id, db)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    series: list[
        DevicePerformanceSeries
    ] = await get_agent_device_performance_timeseries(agent_id, db)
    return AgentPerformanceSeriesOut(series=series)


@router.post(
    "",
    summary="Register new agent and return token",
    description="Register a new agent from the web UI. Only admins can register agents. Returns agent and token.",
)
async def register_agent(
    host_name: Annotated[str, Body(..., description="Agent host name")],
    operating_system: Annotated[
        OperatingSystemEnum, Body(..., description="Operating system")
    ],
    client_signature: Annotated[str, Body(..., description="Client signature")],
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    custom_label: Annotated[str | None, Body(description="Custom label")] = None,
    devices: Annotated[
        str | None, Body(description="Comma-separated device list")
    ] = None,
    agent_update_interval: Annotated[
        int, Body(description="Agent update interval (seconds)")
    ] = 30,
    use_native_hashcat: Annotated[bool, Body(description="Use native hashcat")] = False,
    backend_device: Annotated[str | None, Body(description="Backend device")] = None,
    opencl_devices: Annotated[str | None, Body(description="OpenCL devices")] = None,
    enable_additional_hash_types: Annotated[
        bool, Body(description="Enable additional hash types")
    ] = False,
) -> AgentRegisterModalContext:
    if not (
        getattr(user, "is_superuser", False) or getattr(user, "role", None) == "admin"
    ):
        raise HTTPException(status_code=403, detail="Not authorized to register agents")
    agent_out, token = await register_agent_full_service(
        host_name=host_name,
        operating_system=operating_system,
        client_signature=client_signature,
        custom_label=custom_label,
        devices=devices,
        agent_update_interval=agent_update_interval,
        use_native_hashcat=use_native_hashcat,
        backend_device=backend_device,
        opencl_devices=opencl_devices,
        enable_additional_hash_types=enable_additional_hash_types,
        db=db,
    )
    return AgentRegisterModalContext(agent=agent_out, token=token)


@router.get("/{agent_id}/hardware", summary="Agent hardware detail")
async def agent_hardware(
    agent_id: Annotated[int, Path(description="Agent ID")],
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> AgentOut:
    agent = await get_agent_by_id_service(agent_id, db)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    resource = f"agent:{agent.id}"
    if not user_can(user, resource, "view_agent"):
        raise HTTPException(
            status_code=403, detail="Not authorized to view agent hardware"
        )
    return AgentOut.model_validate(agent, from_attributes=True)


async def _check_agent_update_permission(user: User, resource: str) -> None:
    if not user_can(user, resource, "update_agent") and not getattr(
        user, "is_superuser", False
    ):
        raise HTTPException(status_code=403, detail="Not authorized to update agent")


@router.patch(
    "/{agent_id}/hardware",
    summary="Update agent hardware limits and platform toggles",
    description="Update hardware-related advanced configuration fields for an agent. Only project admins or superusers may update.",
)
async def update_agent_hardware(
    agent_id: Annotated[int, Path(description="Agent ID")],
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    hwmon_temp_abort: Annotated[
        int | None,
        Body(
            description="Temperature abort threshold in Celsius for hashcat (--hwmon-temp-abort)"
        ),
    ] = None,
    opencl_devices: Annotated[
        str | None,
        Body(
            description="The OpenCL device types to use for hashcat, separated by commas"
        ),
    ] = None,
    backend_ignore_cuda: Annotated[
        bool | None, Body(description="Ignore CUDA backend (--backend-ignore-cuda)")
    ] = None,
    backend_ignore_opencl: Annotated[
        bool | None, Body(description="Ignore OpenCL backend (--backend-ignore-opencl)")
    ] = None,
    backend_ignore_hip: Annotated[
        bool | None, Body(description="Ignore HIP backend (--backend-ignore-hip)")
    ] = None,
    backend_ignore_metal: Annotated[
        bool | None, Body(description="Ignore Metal backend (--backend-ignore-metal)")
    ] = None,
) -> AgentUpdateHardwareOut:
    agent = await get_agent_by_id_service(agent_id, db)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    resource = f"agent:{agent.id}"
    await _check_agent_update_permission(user, resource)
    try:
        updated_agent = await update_agent_hardware_service(
            agent_id=agent_id,
            db=db,
            hwmon_temp_abort=hwmon_temp_abort,
            opencl_devices=opencl_devices,
            backend_ignore_cuda=backend_ignore_cuda,
            backend_ignore_opencl=backend_ignore_opencl,
            backend_ignore_hip=backend_ignore_hip,
            backend_ignore_metal=backend_ignore_metal,
        )
    except AgentNotFoundError as err:
        raise HTTPException(status_code=404, detail="Agent not found") from err
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err)) from err
    return AgentUpdateHardwareOut(
        agent=AgentOut.model_validate(updated_agent, from_attributes=True)
    )


@router.get(
    "/{agent_id}/capabilities",
    summary="Show agent benchmark capabilities (table + graph)",
    responses={
        status.HTTP_200_OK: {
            "model": AgentCapabilitiesOut,
            "description": "Agent capabilities",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Agent not found",
        },
    },
)
async def agent_capabilities(
    agent_id: Annotated[int, Path(description="Agent ID")],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AgentCapabilitiesOut:
    agent = await get_agent_by_id_service(agent_id, db)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found"
        )
    return await get_agent_capabilities_service(agent_id, db)
