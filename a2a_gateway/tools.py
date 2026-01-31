"""Coding tools integration for A2A Coding Gateway"""

import asyncio
import pty
import os
import subprocess
import structlog
import re
from typing import Any, Dict, List

from a2a_gateway.config import settings
from a2a_gateway.tasks import task_store, task_semaphore

# Configure logger
logger = structlog.get_logger(__name__)

# Log sanitization patterns
SANITIZATION_PATTERNS = [
    (re.compile(r"X-API-Key:\s*\S+"), "X-API-Key: ***REDACTED***"),
    (re.compile(r'password["\s:]+\S+'), "password: ***REDACTED***"),
    (re.compile(r'token["\s:]+\S+'), "token: ***REDACTED***"),
]


def sanitize_log(message: str) -> str:
    """Sanitize sensitive information in log messages"""
    for pattern, replacement in SANITIZATION_PATTERNS:
        message = pattern.sub(replacement, message)
    return message


async def execute_task_with_tool(task_id: str, message: Dict[str, Any], skill: str):
    """Execute task with appropriate coding tool"""
    logger.info("Starting task execution", task_id=task_id, skill=skill)
    try:
        async with task_semaphore:
            logger.debug("Task acquired semaphore", task_id=task_id)
            if skill == "fix_bug":
                result = await run_droid_task(task_id, message)
            elif skill == "refactor_code":
                result = await run_claude_task(task_id, message)
            elif skill == "review_pr":
                result = await run_claude_task(task_id, message)
            else:
                result = {"artifacts": [], "error": f"Unsupported skill: {skill}"}

        if "error" in result:
            logger.error(
                "Task execution failed", task_id=task_id, error=result["error"]
            )
            await task_store.update_task_status(task_id, "failed")
        else:
            logger.info("Task execution completed", task_id=task_id)
            await task_store.update_task_status(task_id, "completed")
        await task_store.update_task_result(task_id, result)

    except Exception as e:
        logger.error("Task execution exception", task_id=task_id, error=str(e))
        await task_store.update_task_status(task_id, "failed")
        await task_store.update_task_result(task_id, {"artifacts": [], "error": str(e)})


async def run_droid_task(task_id: str, message: Dict[str, Any]) -> Dict[str, Any]:
    """Run droid tool task"""
    logger.debug("Running droid task", task_id=task_id)
    bug_description = message.get("bug_description", "")
    workdir = message.get("workdir", ".")
    context_files = message.get("context_files", [])

    # Create command
    command = [settings.droid_command, "fix", bug_description]
    if workdir != ".":
        command.extend(["--workdir", workdir])
    if context_files:
        command.extend(["--context", ",".join(context_files)])

    logger.debug("Droid command created", task_id=task_id, command=command)
    result = await run_pty_command(task_id, command, workdir)
    logger.debug("Droid task completed", task_id=task_id, result=result)
    return result


async def run_claude_task(task_id: str, message: Dict[str, Any]) -> Dict[str, Any]:
    """Run Claude Code tool task"""
    logger.debug("Running Claude Code task", task_id=task_id)
    task_type = message.get("task_type", "fix_bug")
    task_description = message.get("description", "")
    workdir = message.get("workdir", ".")
    context_files = message.get("context_files", [])

    # Create command
    command = [settings.claude_command, "task", task_type, task_description]
    if workdir != ".":
        command.extend(["--workdir", workdir])
    if context_files:
        command.extend(["--context", ",".join(context_files)])

    logger.debug("Claude Code command created", task_id=task_id, command=command)
    result = await run_pty_command(task_id, command, workdir)
    logger.debug("Claude Code task completed", task_id=task_id, result=result)
    return result


async def run_pty_command(task_id: str, command: List[str], cwd: str) -> Dict[str, Any]:
    """Run command in PTY mode"""
    logger.debug("Executing PTY command", task_id=task_id, command=command, cwd=cwd)
    loop = asyncio.get_event_loop()
    try:
        return await asyncio.wait_for(
            loop.run_in_executor(
                None, _run_pty_command_blocking, task_id, command, cwd
            ),
            timeout=settings.task_timeout,
        )
    except asyncio.TimeoutError:
        error_msg = f"Command timed out after {settings.task_timeout} seconds"
        logger.error("PTY command timeout", task_id=task_id, error=error_msg)
        return {"artifacts": [], "error": error_msg}


async def generate_dockerfile_task(task_id: str, message: Dict[str, Any]) -> Dict[str, Any]:
    """Generate Dockerfile using Claude Code"""
    logger.info("Starting Dockerfile generation task", task_id=task_id)
    try:
        async with task_semaphore:
            logger.debug("Task acquired semaphore", task_id=task_id)
            
            # Extract parameters
            project_description = message.get("project_description", "")
            workdir = message.get("workdir", ".")
            project_type = message.get("project_type", "python")
            
            # Prepare task for Claude Code
            task_message = {
                "task_type": "generate_dockerfile",
                "description": f"Generate a production-ready Dockerfile for {project_type or 'Python'} project",
                "workdir": workdir,
                "project_context": project_description
            }
            
            # Run Claude Code task
            logger.debug("Running Claude Code to generate Dockerfile", task_id=task_id)
            result = await run_claude_task(task_id, task_message)
            
            if "error" in result:
                logger.error("Dockerfile generation failed", task_id=task_id, error=result["error"])
                await task_store.update_task_status(task_id, "failed")
                await task_store.update_task_result(task_id, result)
            else:
                logger.info("Dockerfile generation completed", task_id=task_id)
                await task_store.update_task_status(task_id, "completed")
                await task_store.update_task_result(task_id, result)

    except Exception as e:
        logger.error("Dockerfile generation task exception", task_id=task_id, error=str(e))
        await task_store.update_task_status(task_id, "failed")
        await task_store.update_task_result(task_id, {"artifacts": [], "error": str(e)})


def _run_pty_command_blocking(
    task_id: str, command: List[str], cwd: str
) -> Dict[str, Any]:
    """Run command in PTY mode (blocking version)"""
    logger.debug("PTY command started (blocking)", task_id=task_id)
    master = None
    process = None
    try:
        # Create PTY process
        master, slave = pty.openpty()
        process = subprocess.Popen(
            command,
            stdin=slave,
            stdout=slave,
            stderr=slave,
            cwd=cwd,
            universal_newlines=True,
            close_fds=True,
        )
        os.close(slave)

        # Read output with non-blocking mode
        os.set_blocking(master, False)
        output = []

        while process.poll() is None:
            try:
                data = os.read(master, 1024).decode()
                if data:
                    output.append(data)
            except (OSError, BlockingIOError):
                # No data available, continue
                import time

                time.sleep(0.1)
                continue
            except Exception:
                break

        # Read any remaining output
        try:
            while True:
                data = os.read(master, 1024).decode()
                if not data:
                    break
                output.append(data)
        except (OSError, BlockingIOError):
            pass

        # Wait for process to complete
        return_code = process.wait()
        logger.debug(
            "PTY command completed",
            task_id=task_id,
            return_code=return_code,
            output="".join(output),
        )

        if return_code != 0:
            error_msg = f"Command failed with return code {return_code}"
            logger.error(
                "PTY command failed",
                task_id=task_id,
                return_code=return_code,
                error=error_msg,
                output="".join(output),
            )
            return {"artifacts": [], "error": error_msg}

        return {"artifacts": [{"type": "text", "data": {"output": "".join(output)}}]}

    except Exception as e:
        logger.error("PTY command exception", task_id=task_id, error=str(e))
        return {"artifacts": [], "error": str(e)}
    finally:
        if master is not None:
            try:
                os.close(master)
            except Exception:
                pass
        if process is not None and process.poll() is None:
            try:
                process.terminate()
                process.wait(timeout=1)
            except Exception:
                try:
                    process.kill()
                except Exception:
                    pass
