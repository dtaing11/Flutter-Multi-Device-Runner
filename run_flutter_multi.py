#!/usr/bin/env python3
"""
run_flutter_multi.py

Runs `flutter run` on multiple devices simultaneously in a single terminal,
using real pseudo-terminals (ptys) so Flutter's full interactive key command
set (r, R, s, v, w, i, o, b, q, etc.) works on every device at once.

Keystrokes you type are relayed to ALL running flutter processes.
Output from each device is prefixed with the device ID you entered, so
debug prints stay readable in one terminal.

You manually type in how many devices to run on and each device ID.
Run `flutter devices` beforehand to see available IDs.
"""

import os
import pty
import select
import subprocess
import sys
import termios
import tty


def spawn_flutter(device_id, project_dir):
    master_fd, slave_fd = pty.openpty()
    proc = subprocess.Popen(
        ["flutter", "run", "-d", device_id],
        stdin=slave_fd,
        stdout=slave_fd,
        stderr=slave_fd,
        cwd=project_dir,
        close_fds=True,
    )
    os.close(slave_fd)
    return proc, master_fd


def main():
    project_dir = os.getcwd()

    try:
        count = int(input("How many devices do you want to run on? ").strip())
    except ValueError:
        print("Please enter a valid number.")
        sys.exit(1)

    if count < 1:
        print("Need at least 1 device.")
        sys.exit(1)

    device_ids = []
    for i in range(count):
        device_id = input(f"Enter device ID #{i + 1}: ").strip()
        if not device_id:
            print("Device ID cannot be empty.")
            sys.exit(1)
        device_ids.append(device_id)

    print("\nLaunching flutter run on:")
    for d in device_ids:
        print(f"  - {d}")

    procs = {}
    fds = {}
    label_width = max(len(d) for d in device_ids)

    for device_id in device_ids:
        proc, fd = spawn_flutter(device_id, project_dir)
        label = device_id.ljust(label_width)
        procs[fd] = proc
        fds[fd] = f"[{label}] "

    old_settings = termios.tcgetattr(sys.stdin)
    tty.setcbreak(sys.stdin.fileno())

    line_buffers = {fd: b"" for fd in fds}

    try:
        while True:
            watch = [sys.stdin] + list(fds.keys())
            readable, _, _ = select.select(watch, [], [])

            if sys.stdin in readable:
                key = os.read(sys.stdin.fileno(), 1)
                if not key:
                    break
                for fd in fds:
                    try:
                        os.write(fd, key)
                    except OSError:
                        pass

            for fd in list(fds.keys()):
                if fd in readable:
                    try:
                        data = os.read(fd, 4096)
                    except OSError:
                        data = b""
                    if not data:
                        continue
                    line_buffers[fd] += data
                    while b"\n" in line_buffers[fd]:
                        line, line_buffers[fd] = line_buffers[fd].split(b"\n", 1)
                        sys.stdout.write(fds[fd] + line.decode(errors="replace") + "\n")
                        sys.stdout.flush()

            if all(p.poll() is not None for p in procs.values()):
                break

    except KeyboardInterrupt:
        pass
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        for proc in procs.values():
            if proc.poll() is None:
                proc.terminate()
        print("\nAll flutter run processes terminated.")


if __name__ == "__main__":
    main()