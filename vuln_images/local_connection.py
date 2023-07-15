from typing import Optional, Tuple
import asyncio

import aioshutil
from asyncssh import SSHCompletedProcess, ProcessError


class LocalConnection:
    """
    This class is "monkey-patching" replacement for asyncssh.create_connection().
    Instead of creating remote SSH connection it runs command on the local machine.
    It supports only one method: run().

    Syntax is the same as with asyncssh.create_connection(), look:

    async with asyncssh.create_connection() as connection:
        await connection.ssh("rm -rf /", check=True)

    async with LocalConnection() as connection:
        await connection.run("rm -rf /", check=True)
    """
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return

    async def run(self, *args: str, check: bool = False,
                  timeout: Optional[float] = None,
                  **kwargs: object) -> SSHCompletedProcess:
        if len(args) != 1:
            raise ValueError("LocalConnection supports only one-line command")

        command = args[0]
        process = await asyncio.create_subprocess_shell(
            command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        await process.wait()

        stdout_data = await process.stdout.read()
        stderr_data = await process.stderr.read()

        stdout_data = stdout_data.decode()
        stderr_data = stderr_data.decode()

        if check and process.returncode:
            raise ProcessError(None, command, None,
                               None, None,
                               process.returncode, stdout_data, stderr_data)
        else:
            return SSHCompletedProcess(None, command, None,
                                       None, None,
                                       process.returncode, stdout_data,
                                       stderr_data)


async def local_copy(source: str, destination: Tuple[object, str], preserve: Optional[bool] = True):
    """
    local_copy() is drop-in replacement for asyncssh.scp, which makes local copy.

    asyncssh.scp(source, (ssh, destination)) vs
    local_copy(source, (ssh, destination))
    """
    full_destination = destination[1]
    await aioshutil.copy(source, full_destination)


async def main():
    async with LocalConnection() as connection:
        process = await connection.run("echo 'Hello world'")
        print(process.stdout)


if __name__ == "__main__":
    asyncio.run(main())
