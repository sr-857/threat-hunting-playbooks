"""Command line client for Threat Hunting Playbooks."""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any

import click
import httpx
from rich.console import Console
from rich.table import Table

DEFAULT_API_URL = os.getenv("THREAT_API_URL", "http://localhost:8000")

console = Console()


class Client:
    """Lightweight HTTP client for the Threat Hunting API."""

    def __init__(self, base_url: str = DEFAULT_API_URL) -> None:
        self.base_url = base_url.rstrip("/")
        self._client = httpx.Client(base_url=self.base_url, timeout=30.0)

    def list_playbooks(self) -> list[dict[str, Any]]:
        response = self._client.get("/api/playbooks/")
        response.raise_for_status()
        return response.json()

    def run_playbook(self, playbook_id: str) -> dict[str, Any]:
        response = self._client.post(f"/api/playbooks/{playbook_id}/run")
        response.raise_for_status()
        return response.json()

    def list_schedules(self) -> list[dict[str, Any]]:
        response = self._client.get("/api/schedules/")
        response.raise_for_status()
        return response.json()

    def create_schedule(self, payload: dict[str, Any]) -> dict[str, Any]:
        response = self._client.post("/api/schedules/", json=payload)
        response.raise_for_status()
        return response.json()

    def update_schedule(self, schedule_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        response = self._client.put(f"/api/schedules/{schedule_id}", json=payload)
        response.raise_for_status()
        return response.json()

    def delete_schedule(self, schedule_id: str) -> None:
        response = self._client.delete(f"/api/schedules/{schedule_id}")
        response.raise_for_status()

    def run_schedule(self, schedule_id: str) -> dict[str, Any]:
        response = self._client.post(f"/api/schedules/{schedule_id}/run")
        response.raise_for_status()
        return response.json()


def _format_timestamp(value: Any) -> str:
    if not value:
        return "—"
    if isinstance(value, str):
        candidate = value.replace("Z", "+00:00")
        try:
            dt_value = datetime.fromisoformat(candidate)
            return dt_value.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            return value
    return str(value)


def _render_schedule_table(schedules: list[dict[str, Any]]) -> Table:
    table = Table(title="Hunt Schedules")
    table.add_column("ID", style="cyan", overflow="fold")
    table.add_column("Name", style="white")
    table.add_column("Playbook", style="magenta")
    table.add_column("Cron", style="green")
    table.add_column("Enabled", style="yellow")
    table.add_column("Next Run", style="blue")
    table.add_column("Last Run", style="blue")

    for schedule in schedules:
        table.add_row(
            schedule.get("id", ""),
            schedule.get("name", ""),
            schedule.get("playbook_id", ""),
            schedule.get("cron_expression", ""),
            "Yes" if schedule.get("enabled", True) else "No",
            _format_timestamp(schedule.get("next_run_at")),
            _format_timestamp(schedule.get("last_run_at")),
        )

    return table


def _get_client(base_url: str | None) -> Client:
    if base_url:
        return Client(base_url)
    return Client()


@click.group()
@click.option(
    "--api-url",
    envvar="THREAT_API_URL",
    default=DEFAULT_API_URL,
    show_default=True,
    help="Threat Hunting API base URL.",
)
@click.pass_context
def app(ctx: click.Context, api_url: str) -> None:
    """Threat Hunting Playbooks CLI."""

    ctx.obj = {
        "client": _get_client(api_url),
    }


@app.command("list")
@click.pass_context
def list_playbooks(ctx: click.Context) -> None:
    """List available playbooks."""

    client: Client = ctx.obj["client"]
    try:
        playbooks = client.list_playbooks()
    except httpx.HTTPError as exc:
        console.print(f"[red]Failed to fetch playbooks:[/red] {exc}")
        raise SystemExit(1) from exc

    if not playbooks:
        console.print("[yellow]No playbooks found. Seed the database to get started.[/yellow]")
        return

    table = Table(title="Threat Hunting Playbooks")
    table.add_column("ID", style="cyan", overflow="fold")
    table.add_column("Name", style="white")
    table.add_column("Tags", style="green")
    table.add_column("Sample Data", style="magenta")

    for playbook in playbooks:
        tags = ", ".join(playbook.get("tags", [])) or "—"
        table.add_row(
            playbook.get("id", ""),
            playbook.get("name", ""),
            tags,
            playbook.get("data_path", ""),
        )

    console.print(table)


@app.group("schedules")
@click.pass_context
def schedules_group(ctx: click.Context) -> None:
    """Manage scheduled hunts."""

    ctx.obj = ctx.obj or {}
    ctx.obj.setdefault("client", _get_client(None))


@schedules_group.command("list")
@click.pass_context
def list_schedules(ctx: click.Context) -> None:
    """List configured hunt schedules."""

    client: Client = ctx.obj["client"]
    try:
        schedules = client.list_schedules()
    except httpx.HTTPError as exc:
        console.print(f"[red]Failed to fetch schedules:[/red] {exc}")
        raise SystemExit(1) from exc

    if not schedules:
        console.print("[yellow]No schedules defined. Use 'schedules create' to add one.[/yellow]")
        return

    table = _render_schedule_table(schedules)
    console.print(table)


@schedules_group.command("create")
@click.option("--name", required=True, help="Human friendly schedule name.")
@click.option("--playbook", "playbook_id", required=True, help="Target playbook ID.")
@click.option("--cron", "cron_expression", required=True, help="Cron expression (e.g. '0 * * * *').")
@click.option("--description", default="", help="Optional description or analyst notes.")
@click.option("--disabled", is_flag=True, help="Create the schedule in a disabled state.")
@click.pass_context
def create_schedule(
    ctx: click.Context,
    name: str,
    playbook_id: str,
    cron_expression: str,
    description: str,
    disabled: bool,
) -> None:
    """Create a new hunt schedule."""

    client: Client = ctx.obj["client"]
    payload = {
        "name": name,
        "playbook_id": playbook_id,
        "cron_expression": cron_expression,
        "description": description or None,
        "enabled": not disabled,
    }

    try:
        schedule = client.create_schedule(payload)
    except httpx.HTTPStatusError as exc:
        console.print(f"[red]API error:[/red] {exc.response.status_code} {exc.response.text}")
        raise SystemExit(1) from exc
    except httpx.HTTPError as exc:
        console.print(f"[red]Failed to create schedule:[/red] {exc}")
        raise SystemExit(1) from exc

    console.print("[green]Schedule created successfully.[/green]")
    console.print_json(data=schedule)


@schedules_group.command("update")
@click.argument("schedule_id")
@click.option("--name", help="New name for the schedule.")
@click.option("--cron", "cron_expression", help="Updated cron expression.")
@click.option("--description", help="Updated description text.")
@click.option("--enable/--disable", "enabled", default=None, help="Enable or disable the schedule.")
@click.pass_context
def update_schedule_command(
    ctx: click.Context,
    schedule_id: str,
    name: str | None,
    cron_expression: str | None,
    description: str | None,
    enabled: bool | None,
) -> None:
    """Update an existing hunt schedule."""

    if not any([name, cron_expression, description, enabled is not None]):
        console.print("[yellow]No updates provided. Use --name/--cron/--description/--enable/--disable.[/yellow]")
        raise SystemExit(1)

    payload: dict[str, Any] = {}
    if name is not None:
        payload["name"] = name
    if cron_expression is not None:
        payload["cron_expression"] = cron_expression
    if description is not None:
        payload["description"] = description
    if enabled is not None:
        payload["enabled"] = enabled

    client: Client = ctx.obj["client"]
    try:
        schedule = client.update_schedule(schedule_id, payload)
    except httpx.HTTPStatusError as exc:
        console.print(f"[red]API error:[/red] {exc.response.status_code} {exc.response.text}")
        raise SystemExit(1) from exc
    except httpx.HTTPError as exc:
        console.print(f"[red]Failed to update schedule:[/red] {exc}")
        raise SystemExit(1) from exc

    console.print("[green]Schedule updated successfully.[/green]")
    console.print_json(data=schedule)


@schedules_group.command("delete")
@click.argument("schedule_id")
@click.option("--force", is_flag=True, help="Skip confirmation prompt.")
@click.pass_context
def delete_schedule_command(ctx: click.Context, schedule_id: str, force: bool) -> None:
    """Delete a schedule permanently."""

    if not force:
        confirmed = click.confirm("Delete this schedule?", default=False)
        if not confirmed:
            console.print("[yellow]Deletion cancelled.[/yellow]")
            return

    client: Client = ctx.obj["client"]
    try:
        client.delete_schedule(schedule_id)
    except httpx.HTTPStatusError as exc:
        console.print(f"[red]API error:[/red] {exc.response.status_code} {exc.response.text}")
        raise SystemExit(1) from exc
    except httpx.HTTPError as exc:
        console.print(f"[red]Failed to delete schedule:[/red] {exc}")
        raise SystemExit(1) from exc

    console.print("[green]Schedule deleted successfully.[/green]")


@schedules_group.command("run")
@click.argument("schedule_id")
@click.option("--json-output", is_flag=True, help="Print raw JSON response from the API.")
@click.pass_context
def run_schedule_command(ctx: click.Context, schedule_id: str, json_output: bool) -> None:
    """Trigger a schedule immediately via Celery."""

    client: Client = ctx.obj["client"]
    try:
        response = client.run_schedule(schedule_id)
    except httpx.HTTPStatusError as exc:
        console.print(f"[red]API error:[/red] {exc.response.status_code} {exc.response.text}")
        raise SystemExit(1) from exc
    except httpx.HTTPError as exc:
        console.print(f"[red]Failed to trigger schedule:[/red] {exc}")
        raise SystemExit(1) from exc

    if json_output:
        console.print_json(data=response)
        return

    console.print(f"[green]Run dispatched for schedule {schedule_id}.[/green]")
