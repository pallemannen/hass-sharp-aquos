"""Minimal async client for Sharp's AQUOS IP/serial control protocol.

The protocol is a simple four-letter-command scheme over a plaintext TCP
connection (default port 10002): connect, authenticate with a username and
password (each terminated by \\r, blank if unset on the TV), then send a
four-character command code followed by a value left-padded to four
characters and terminated by \\r. The TV replies with "OK", "ERR", or the
requested value, also \\r-terminated. The TV does not keep the connection
open between commands well, so - matching Sharp's own documentation - a new
connection is opened for every command.
"""

from __future__ import annotations

import asyncio
import logging

_LOGGER = logging.getLogger(__name__)

# Commands that only make sense while the TV is on. Querying these while off
# either times out or returns garbage, so callers should skip them then.
STATUS_ONLY_WHEN_ON = frozenset(
    {"VOLM", "MUTE", "IAVD", "WIDE", "ACHN", "AVMD", "OPGD", "CHTR", "IFGS"}
)


class AquosError(Exception):
    """Base error talking to the TV."""


class AquosConnectionError(AquosError):
    """Could not open/authenticate a connection to the TV."""


class AquosCommandError(AquosError):
    """The TV rejected a command (ERR) or returned something unparseable."""


class AquosTV:
    """Thin async wrapper around the AQUOS four-letter-command protocol."""

    def __init__(
        self,
        host: str,
        port: int,
        username: str = "",
        password: str = "",
        timeout: float = 3.0,
        retries: int = 2,
    ) -> None:
        self._host = host
        self._port = port
        self._auth = f"{username}\r{password}\r".encode()
        self._timeout = timeout
        self._retries = retries

    async def _send_once(self, code: str, value: str | int) -> str:
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self._host, self._port), timeout=self._timeout
            )
        except (OSError, asyncio.TimeoutError) as err:
            raise AquosConnectionError(f"Could not connect to {self._host}:{self._port}") from err

        try:
            writer.write(self._auth)
            await writer.drain()
            # The TV echoes/acknowledges the username and password separately.
            await asyncio.wait_for(reader.read(1024), timeout=self._timeout)
            await asyncio.wait_for(reader.read(1024), timeout=self._timeout)

            command = f"{code}{str(value).ljust(4)}\r"
            writer.write(command.encode())
            await writer.drain()
            raw = await asyncio.wait_for(reader.read(1024), timeout=self._timeout)
        except (OSError, asyncio.TimeoutError) as err:
            raise AquosConnectionError(f"Lost connection to {self._host}:{self._port}") from err
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except OSError:
                pass

        return raw.decode(errors="ignore").strip()

    async def _send(self, code: str, value: str | int = "?") -> str | int | bool:
        """Send a command, retrying transient connection failures."""
        last_err: Exception | None = None
        for attempt in range(self._retries + 1):
            try:
                status = await self._send_once(code, value)
                break
            except AquosConnectionError as err:
                last_err = err
                if attempt < self._retries:
                    await asyncio.sleep(0.2)
        else:
            assert last_err is not None
            raise last_err

        if status == "OK":
            return True
        if status == "ERR":
            raise AquosCommandError(f"{code}{value} rejected by TV")
        try:
            return int(status)
        except ValueError:
            return status

    # --- Power / system -------------------------------------------------

    async def power(self, on: bool | None = None) -> bool:
        """Get or set power state."""
        if on is None:
            return await self._send("POWR") == 1
        await self._send("POWR", 1 if on else 0)
        return on

    async def set_power_on_command_settings(self, tcp_wake_enabled: bool) -> None:
        """Enable/disable accepting a power-on command over TCP/IP (RSPW)."""
        await self._send("RSPW", 2 if tcp_wake_enabled else 0)

    async def model(self) -> str:
        return str(await self._send("MNRD"))

    # --- Audio / video ----------------------------------------------------

    async def volume(self, level: int | None = None) -> int:
        """Get or set volume, 0-60."""
        if level is None:
            return int(await self._send("VOLM"))
        await self._send("VOLM", max(0, min(60, int(level))))
        return level

    async def mute(self, muted: bool | None = None) -> bool:
        """Get or set mute state. MUTE1 = muted, MUTE2 = unmuted (deterministic)."""
        if muted is None:
            return int(await self._send("MUTE")) == 1
        await self._send("MUTE", 1 if muted else 2)
        return muted

    async def input_source(self, source_code: int | None = None) -> int:
        """Get or set the input (0=TV/Antenna via ITVD, 1-5 via IAVD)."""
        if source_code is None:
            return int(await self._send("IAVD"))
        if source_code == 0:
            await self._send("ITVD", 0)
        else:
            await self._send("IAVD", source_code)
        return source_code

    async def aspect_ratio(self) -> int:
        return int(await self._send("WIDE"))

    async def audio_selection(self) -> int:
        return int(await self._send("ACHN"))

    async def av_mode(self) -> int:
        return int(await self._send("AVMD"))

    async def backlight(self) -> int:
        return int(await self._send("OPGD"))

    # --- Tuner ------------------------------------------------------------

    async def channel(self, number: int | None = None) -> int:
        """Get the current channel, or direct-tune to one (CHTR)."""
        if number is None:
            return int(await self._send("CHTR"))
        await self._send("CHTR", number)
        return number

    async def channel_up(self) -> None:
        await self._send("CHUP", 1)

    async def channel_down(self) -> None:
        await self._send("CHDN", 1)

    async def signal_strength(self) -> int:
        return int(await self._send("IFGS"))
