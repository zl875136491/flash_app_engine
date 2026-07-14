"""Docker CLI 封装（subprocess）。"""

from __future__ import annotations

import logging
import shutil
import subprocess
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CommandResult:
    ok: bool
    returncode: int
    stdout: str
    stderr: str

    @property
    def output(self) -> str:
        return (self.stdout or "") + ("\n" + self.stderr if self.stderr else "")


def docker_available() -> bool:
    return shutil.which("docker") is not None


def run_docker(args: list[str], *, timeout: int = 300) -> CommandResult:
    cmd = ["docker", *args]
    logger.info("docker %s", " ".join(args))
    try:
        completed = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as exc:
        return CommandResult(ok=False, returncode=127, stdout="", stderr=str(exc))
    except subprocess.TimeoutExpired as exc:
        return CommandResult(
            ok=False,
            returncode=124,
            stdout=exc.stdout or "",
            stderr=(exc.stderr or "") + "\ntimeout",
        )
    return CommandResult(
        ok=completed.returncode == 0,
        returncode=completed.returncode,
        stdout=completed.stdout or "",
        stderr=completed.stderr or "",
    )


def container_logs(name: str, *, tail: int = 50) -> str:
    result = run_docker(["logs", "--tail", str(tail), name], timeout=60)
    return result.output[-8000:]
