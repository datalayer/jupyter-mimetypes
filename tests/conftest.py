# Copyright (c) 2023-2024 Datalayer, Inc.
#
# BSD 3-Clause License

"""Test configuration and fixtures."""

import logging
import secrets
import signal
import socket
import time
import typing as t
from contextlib import closing
from subprocess import PIPE, Popen, TimeoutExpired

import pytest
import requests

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)


def find_free_port() -> int:
    """
    Find a free port on localhost.

    Uses a socket to bind to port 0, which automatically assigns a free port,
    then returns that port number.

    Returns
    -------
    int
        An available port number.

    See Also
    --------
    jupyter_server : Fixture that uses this function.

    Examples
    --------
    >>> port = find_free_port()
    >>> isinstance(port, int)
    True
    """
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("localhost", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


def print_stream(stream: bytes) -> None:
    """
    Print a byte stream line by line.

    This utility function takes a byte stream and prints each line
    after decoding it to UTF-8.

    Parameters
    ----------
    stream : bytes
        The byte stream to print.

    See Also
    --------
    jupyter_server : Fixture that uses this for debugging output.

    Examples
    --------
    >>> print_stream(b"hello\\nworld")
    hello
    world
    """
    for line in stream.split(b"\n"):
        print(line.decode())


@pytest.fixture(scope="session")
def jupyter_server() -> t.Generator[tuple[str, str], t.Any, t.Any]:
    """
    Start a Jupyter server for testing.

    This fixture starts a Jupyter server instance for use in tests,
    providing the port and token needed to connect to it.

    Yields
    ------
    tuple[str, str]
        A tuple containing (port, token) for connecting to the server.

    See Also
    --------
    find_free_port : Function to get an available port.

    Examples
    --------
    >>> def test_example(jupyter_server):
    ...     port, token = jupyter_server
    ...     # Use port and token to connect
    """
    port = find_free_port()
    token = secrets.token_hex(20)

    jp_server = Popen(
        [
            "jupyter-server",
            "--port",
            str(port),
            "--IdentityProvider.token",
            token,
            # "--ServerApp.open_browser",
            # "False",
            # "--ServerApp.disable_check_xsrf",
            # "True",
            # "--ServerApp.allow_origin",
            # "*",
            # "--ServerApp.log_level",
            # "WARNING",
        ],
        stdout=PIPE,
        stderr=PIPE,
    )

    # Wait for server to be ready with exponential backoff
    max_attempts = 10
    attempt = 0
    starting = True

    while starting and attempt < max_attempts:
        try:
            ans = requests.get(f"http://localhost:{port}/api", timeout=2)
            print(ans.text)
            if ans.status_code == 200:
                logging.debug("Server ready at http://localhost:%s", port)
                # Give the server a moment to fully initialize
                time.sleep(0.5)
                break
        except requests.RequestException:
            attempt += 1
            # Exponential backoff: 0.1, 0.2, 0.4, 0.8, 1.6, then cap at 2.0
            wait_time = min(0.1 * (2**attempt), 2.0)
            time.sleep(wait_time)

    if attempt >= max_attempts:
        jp_server.terminate()
        raise RuntimeError(
            f"Jupyter server failed to start on port {port} after {max_attempts} attempts"
        )
    try:
        yield (str(port), token)
    finally:
        # Graceful shutdown with longer timeout
        jp_server.send_signal(signal.SIGINT)
        out, err = jp_server.communicate(timeout=100)
        failed_to_terminate = True
        try:
            out, err = jp_server.communicate(timeout=10)
            failed_to_terminate = False
            if out:
                print_stream(out)
            if err:
                print_stream(err)
        except TimeoutExpired:
            logging.warning("Server did not shutdown gracefully, force terminating")
            jp_server.terminate()
            try:
                jp_server.communicate(timeout=5)
            except TimeoutExpired:
                jp_server.kill()
                jp_server.communicate()

        if failed_to_terminate:
            if jp_server.stdout is not None:
                remaining_out = jp_server.stdout.read()
                if remaining_out:
                    print_stream(remaining_out)
            if jp_server.stderr is not None:
                remaining_err = jp_server.stderr.read()
                if remaining_err:
                    print_stream(remaining_err)
