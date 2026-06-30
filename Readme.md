# Flutter Multi-Device Runner

A small Python script that runs `flutter run` on multiple devices at once, **inside a single terminal**, while keeping every interactive Flutter key command fully functional on all devices simultaneously — hot reload, hot restart, screenshots, widget inspector, and the rest.

## Why this exists

Flutter natively supports `flutter run -d all`, but that targets *every* connected device, including desktop runtimes (e.g. macOS) you usually don't want. Running two separate `flutter run` processes side-by-side normally breaks interactivity, because:

- A plain background process or named pipe (FIFO) used as stdin isn't recognized by Flutter as a real terminal, so it silently disables hot reload, hot restart, and all other interactive key commands.
- Flutter only enables its interactive command mode when it detects a genuine TTY (pseudo-terminal) attached to stdin.

This script solves that by giving each `flutter run` process its own real pseudo-terminal (pty) via Python's `pty` module, so Flutter treats each one exactly as if it were run manually in its own terminal window — while your keystrokes are relayed to all of them from one place, and all their debug output streams back into one terminal, clearly labeled.

## Features

- Run `flutter run` on **any number of devices** at once (Android, iOS, or both).
- Full interactive key command support per device: `r` (hot reload), `R` (hot restart), `s` (screenshot), `v` (DevTools), `w`/`t`/`L`/`f`/`S`/`U` (widget/render/layer/focus/semantics tree dumps), `i` (widget inspector toggle), `o` (simulate OS), `b` (toggle brightness), `P` (performance overlay), `q` (quit), and the rest of Flutter's key command list.
- A single keystroke is relayed to **every** running device simultaneously.
- Debug output (`print`, `debugPrint`, build logs, errors) from each device is prefixed with its device ID, e.g. `[emulator-5554]` or `[31E8A918-91FB-43C5-9EDB-7E63AE04A4EB]`, so output from multiple devices stays readable in one terminal.
- No hardcoded device IDs — you're prompted for how many devices to run and their IDs each time you run the script.
- Clean shutdown: `Ctrl+C` terminates all running `flutter run` processes.

## Requirements

- Python 3 (uses only the standard library: `pty`, `select`, `subprocess`, `termios`, `tty` — no installs needed)
- macOS or Linux (the `pty`/`termios` modules used here are POSIX-only; this script does not work on native Windows, though it should work fine under WSL)
- Flutter SDK installed and devices/emulators/simulators already booted

## Usage

1. Boot the devices/emulators/simulators you want to target.
2. Run `flutter devices` to find their device IDs:

   ```
   flutter devices
   ```

3. From your Flutter project root, run the script:

   ```bash
   chmod +x run_flutter_multi.py
   python3 run_flutter_multi.py
   ```

4. Follow the prompts:

   ```
   How many devices do you want to run on? 2
   Enter device ID #1: emulator-5554
   Enter device ID #2: 31E8A918-91FB-43C5-9EDB-7E63AE04A4EB
   ```

5. The script launches `flutter run -d <id>` for each device. Once running, type any Flutter interactive key (e.g. `r`) and it's sent to all devices at once. Output from each device appears in the same terminal, prefixed by device ID.

6. Press `Ctrl+C` at any time to stop all running instances cleanly.

## How it works (brief)

- Each device gets its own pseudo-terminal pair (`pty.openpty()`), and `flutter run` is spawned with its stdin/stdout/stderr attached to the slave end of that pty. This makes Flutter believe it's running in a normal interactive terminal.
- The script's own stdin is put into cbreak mode (`tty.setcbreak`) so single keypresses are captured immediately, without waiting for Enter.
- A `select()` loop watches your real stdin and every device's pty master file descriptor at once. Keystrokes you type are written to every pty master (relaying them to all `flutter run` processes); output read from each pty master is buffered per line and printed with a `[device-id]` prefix.

## Limitations

- All devices receive the same keystroke — there's currently no way to send a command to only one device (e.g. hot reload Android only). This could be added with a per-device command prefix if needed.
- POSIX-only (macOS/Linux/WSL), since it relies on `pty` and `termios`.
- Assumes the device IDs you enter are already valid/online; if a device isn't connected, that `flutter run` process will simply fail and its pty will close.

## Credits

This script and README were built with the help of [Claude](https://claude.ai) (Anthropic), through an iterative conversation refining the approach from a basic multi-terminal idea down to a single-terminal, pty-based solution that preserves full Flutter interactivity across multiple devices.