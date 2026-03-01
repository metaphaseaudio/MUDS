from pathlib import Path
import subprocess as sp
import shutil
import threading

def run(args: list[str], cwd=Path.cwd()) -> sp.CompletedProcess:
    """Run a subprocess, streaming output in real time while also capturing it."""
    # Resolve the command to its full path so Windows can find .cmd/.bat files
    # when shell=False (e.g., npm -> C:\...\npm.cmd)
    resolved = shutil.which(args[0])
    if resolved:
        args = [resolved] + args[1:]

    stdout_lines = []
    stderr_lines = []

    process = sp.Popen(
        args,
        stdout=sp.PIPE,
        stderr=sp.PIPE,
        text=True,
        cwd=cwd,
    )

    # Stream both stdout and stderr concurrently using threads.
    # selectors/select() only works with sockets on Windows, not pipes.
    def drain(stream, lines):
        for line in stream:
            print(line, end="")
            lines.append(line)

    t_out = threading.Thread(target=drain, args=(process.stdout, stdout_lines))
    t_err = threading.Thread(target=drain, args=(process.stderr, stderr_lines))
    t_out.start()
    t_err.start()
    t_out.join()
    t_err.join()

    process.wait()

    if process.returncode != 0:
        raise sp.CalledProcessError(
            process.returncode, args,
            "".join(stdout_lines),
            "".join(stderr_lines),
        )

    return sp.CompletedProcess(
        args, process.returncode,
        "".join(stdout_lines),
        "".join(stderr_lines),
    )
