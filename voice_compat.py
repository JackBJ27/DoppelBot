"""
Runtime compatibility patches for Discord voice protocol changes.
"""
from __future__ import annotations
import asyncio
import logging
import os
import struct
from typing import Any, Dict, Tuple
import aiohttp
import discord
from discord import utils
from discord.enums import SpeakingState
from discord.errors import ConnectionClosed
from discord.gateway import DiscordVoiceWebSocket, VoiceKeepAliveHandler
from discord.sinks.core import RawData
from discord.voice_client import VoiceClient

try:
    import davey  # type: ignore
    _HAS_DAVEY = True
except Exception: 
    davey = None  # type: ignore[assignment]
    _HAS_DAVEY = False

logger = logging.getLogger(__name__)

_PATCH_APPLIED = False
_ORIGINALS: dict[Tuple[int, str], tuple[Any, str, bool, Any]] = {}

def _remember_attribute(target: Any, name: str) -> None:
    key = (id(target), name)
    if key in _ORIGINALS: return
    had_attr = hasattr(target, name)
    value = getattr(target, name) if had_attr else None
    _ORIGINALS[key] = (target, name, had_attr, value)

def _set_attribute(target: Any, name: str, value: Any) -> None:
    _remember_attribute(target, name)
    setattr(target, name, value)

def _resolve_max_dave_protocol_version() -> int:
    raw = os.getenv("VOICE_MAX_DAVE_PROTOCOL_VERSION")
    if raw is not None:
        raw = raw.strip()
        try: return max(0, int(raw))
        except ValueError: pass
    if _HAS_DAVEY: return max(0, int(getattr(davey, "DAVE_PROTOCOL_VERSION", 0)))
    return 0

def _ensure_voice_client_state(client: VoiceClient) -> None:
    if not hasattr(client, "dave_session"): client.dave_session = None
    if not hasattr(client, "dave_protocol_version"): client.dave_protocol_version = 0
    if not hasattr(client, "dave_pending_transitions"): client.dave_pending_transitions = {}
    if not hasattr(client, "dave_downgraded"): client.dave_downgraded = False
    if not hasattr(client, "_voicecompat_active_ws"): client._voicecompat_active_ws = None

def _voiceclient_can_encrypt(self: VoiceClient) -> bool:
    session = getattr(self, "dave_session", None)
    protocol = int(getattr(self, "dave_protocol_version", 0) or 0)
    return bool(protocol > 0 and session is not None and getattr(session, "ready", False))

async def _voiceclient_reinit_dave_session(self: VoiceClient) -> None:
    _ensure_voice_client_state(self)
    version = int(getattr(self, "dave_protocol_version", 0) or 0)
    if version > 0:
        if not _HAS_DAVEY: raise RuntimeError("davey library is required")
        if self.dave_session is not None: self.dave_session.reinit(version, int(self.user.id), int(self.channel.id))
        else: self.dave_session = davey.DaveSession(version, int(self.user.id), int(self.channel.id))
        ws = getattr(self, "ws", None)
        if ws in (None, utils.MISSING): ws = getattr(self, "_voicecompat_active_ws", None)
        if ws in (None, utils.MISSING): return
        await ws.send_binary(DiscordVoiceWebSocket.MLS_KEY_PACKAGE, self.dave_session.get_serialized_key_package())
    elif self.dave_session is not None:
        self.dave_session.reset()
        self.dave_session.set_passthrough_mode(True, 10)

async def _voiceclient_recover_from_invalid_commit(self: VoiceClient, transition_id: int) -> None:
    payload = {"op": DiscordVoiceWebSocket.MLS_INVALID_COMMIT_WELCOME, "d": {"transition_id": int(transition_id)}}
    await self.ws.send_as_json(payload)
    await self.reinit_dave_session()

async def _voiceclient_execute_transition(self: VoiceClient, transition_id: int) -> None:
    _ensure_voice_client_state(self)
    if transition_id not in self.dave_pending_transitions: return
    old_version = int(getattr(self, "dave_protocol_version", 0) or 0)
    self.dave_protocol_version = int(self.dave_pending_transitions.pop(transition_id))
    if old_version != self.dave_protocol_version and self.dave_protocol_version == 0: self.dave_downgraded = True
    elif transition_id > 0 and self.dave_downgraded:
        self.dave_downgraded = False
        if self.dave_session is not None: self.dave_session.set_passthrough_mode(True, 10)

async def _patched_identify(self: DiscordVoiceWebSocket) -> None:
    state = self._connection
    payload = {"op": self.IDENTIFY, "d": {"server_id": str(state.server_id), "user_id": str(state.user.id), "session_id": state.session_id, "token": state.token, "max_dave_protocol_version": int(getattr(state, "max_dave_protocol_version", 0))}}
    await self.send_as_json(payload)

async def _patched_speak(self: DiscordVoiceWebSocket, state: SpeakingState = SpeakingState.voice) -> None:
    payload = {"op": self.SPEAKING, "d": {"speaking": int(state), "delay": 0}}
    ssrc = getattr(self._connection, "ssrc", None)
    if ssrc not in (None, utils.MISSING): payload["d"]["ssrc"] = int(ssrc)
    await self.send_as_json(payload)

async def _patched_send_binary(self: DiscordVoiceWebSocket, opcode: int, data: bytes) -> None:
    await self.ws.send_bytes(bytes([int(opcode)]) + data)

async def _patched_send_transition_ready(self: DiscordVoiceWebSocket, transition_id: int) -> None:
    payload = {"op": self.DAVE_TRANSITION_READY, "d": {"transition_id": int(transition_id)}}
    await self.send_as_json(payload)

async def _patched_load_secret_key(self: DiscordVoiceWebSocket, data: Dict[str, Any]) -> None:
    self.secret_key = self._connection.secret_key = data.get("secret_key")
    await self.speak(SpeakingState.none)

async def _patched_received_binary_message(self: DiscordVoiceWebSocket, msg: bytes) -> None:
    if len(msg) < 3: return
    self.seq_ack = struct.unpack_from(">H", msg, 0)[0]
    op = msg[2]
    state: VoiceClient = self._connection
    _ensure_voice_client_state(state)
    session = state.dave_session
    if session is None or not _HAS_DAVEY: return
    if op == self.MLS_EXTERNAL_SENDER: session.set_external_sender(msg[3:])
    elif op == self.MLS_PROPOSALS:
        if len(msg) < 4: return
        optype = msg[3]
        result = session.process_proposals(davey.ProposalsOperationType.append if optype == 0 else davey.ProposalsOperationType.revoke, msg[4:])
        if isinstance(result, davey.CommitWelcome):
            await self.send_binary(self.MLS_COMMIT_WELCOME, result.commit + (result.welcome if result.welcome else b""))
    elif op == self.MLS_ANNOUNCE_COMMIT_TRANSITION:
        if len(msg) < 5: return
        transition_id = struct.unpack_from(">H", msg, 3)[0]
        try:
            session.process_commit(msg[5:])
            if transition_id != 0:
                state.dave_pending_transitions[transition_id] = int(getattr(state, "dave_protocol_version", 0) or 0)
                await self.send_transition_ready(transition_id)
        except: await state._recover_from_invalid_commit(transition_id)
    elif op == self.MLS_WELCOME:
        if len(msg) < 5: return
        transition_id = struct.unpack_from(">H", msg, 3)[0]
        try:
            session.process_welcome(msg[5:])
            if transition_id != 0:
                state.dave_pending_transitions[transition_id] = int(getattr(state, "dave_protocol_version", 0) or 0)
                await self.send_transition_ready(transition_id)
        except: await state._recover_from_invalid_commit(transition_id)

async def _patched_received_message(self: DiscordVoiceWebSocket, msg: Dict[str, Any]) -> None:
    op = msg.get("op")
    data = msg.get("d") or {}
    self.seq_ack = msg.get("seq", self.seq_ack)
    self._connection._voicecompat_active_ws = self

    if op == self.READY: await self.initial_connection(data)
    elif op == self.HEARTBEAT_ACK:
        if self._keep_alive: self._keep_alive.ack()
    elif op == self.SESSION_DESCRIPTION:
        self._connection.mode = data["mode"]
        await self.load_secret_key(data)
        state: VoiceClient = self._connection
        _ensure_voice_client_state(state)
        state.dave_protocol_version = int(data.get("dave_protocol_version", 0) or 0)
        await state.reinit_dave_session()
    elif op == self.HELLO:
        interval = data["heartbeat_interval"] / 1000.0
        self._keep_alive = VoiceKeepAliveHandler(ws=self, interval=min(interval, 5.0))
        self._keep_alive.start()
    elif op == self.SPEAKING:
        ssrc = data["ssrc"]
        if ssrc in self.ssrc_map: self.ssrc_map[ssrc]["speaking"] = data["speaking"]
        else: self.ssrc_map.update({ssrc: {"user_id": int(data["user_id"]), "speaking": data["speaking"]}})
    elif op == self.DAVE_PREPARE_TRANSITION:
        state = self._connection
        _ensure_voice_client_state(state)
        transition_id = int(data["transition_id"])
        protocol_version = int(data["protocol_version"])
        state.dave_pending_transitions[transition_id] = protocol_version
        if transition_id == 0: await state._execute_transition(transition_id)
        else:
            if protocol_version == 0 and state.dave_session is not None: state.dave_session.set_passthrough_mode(True, 120)
            await self.send_transition_ready(transition_id)
    elif op == self.DAVE_EXECUTE_TRANSITION:
        await self._connection._execute_transition(int(data["transition_id"]))
    elif op == self.DAVE_PREPARE_EPOCH:
        if int(data["epoch"]) == 1:
            state = self._connection
            _ensure_voice_client_state(state)
            state.dave_protocol_version = int(data["protocol_version"])
            await state.reinit_dave_session()
    await self._hook(self, msg)

async def _patched_poll_event(self: DiscordVoiceWebSocket) -> None:
    msg = await asyncio.wait_for(self.ws.receive(), timeout=30.0)
    if msg.type is aiohttp.WSMsgType.TEXT: await self.received_message(utils._from_json(msg.data))
    elif msg.type is aiohttp.WSMsgType.BINARY: await self.received_binary_message(msg.data)
    elif msg.type is aiohttp.WSMsgType.ERROR: raise ConnectionClosed(self.ws, shard_id=None) from msg.data
    elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.CLOSE, aiohttp.WSMsgType.CLOSING):
        close_code = self._close_code if self._close_code is not None else self.ws.close_code
        raise ConnectionClosed(self.ws, shard_id=None, code=close_code)

def _patched_unpack_audio(self: VoiceClient, data: bytes) -> None:
    if data[1] & 0x78 != 0x78: return
    if self.paused: return
    frame = RawData(data, self)
    if frame.decrypted_data == b"\xf8\xff\xfe": return
    _ensure_voice_client_state(self)
    session = getattr(self, "dave_session", None)
    if session is not None and getattr(self, "can_encrypt", False):
        ws = getattr(self, "ws", None)
        if ws in (None, utils.MISSING): return
        user_id = ws.ssrc_map.get(frame.ssrc, {}).get("user_id")
        if user_id is None: return
        try: frame.decrypted_data = session.decrypt(int(user_id), davey.MediaType.audio, bytes(frame.decrypted_data))
        except: return
    self.decoder.decode(frame)

def apply_voice_protocol_compat_patches() -> None:
    global _PATCH_APPLIED
    if _PATCH_APPLIED: return
    max_dave_protocol_version = _resolve_max_dave_protocol_version()
    dave_constants = {"DAVE_PREPARE_TRANSITION": 21, "DAVE_EXECUTE_TRANSITION": 22, "DAVE_TRANSITION_READY": 23, "DAVE_PREPARE_EPOCH": 24, "MLS_EXTERNAL_SENDER": 25, "MLS_KEY_PACKAGE": 26, "MLS_PROPOSALS": 27, "MLS_COMMIT_WELCOME": 28, "MLS_ANNOUNCE_COMMIT_TRANSITION": 29, "MLS_WELCOME": 30, "MLS_INVALID_COMMIT_WELCOME": 31}
    for name, value in dave_constants.items(): _set_attribute(DiscordVoiceWebSocket, name, value)
    if not hasattr(VoiceClient, "max_dave_protocol_version"):
        @property
        def max_dave_protocol_version_prop(self: VoiceClient) -> int: return max_dave_protocol_version
        _set_attribute(VoiceClient, "max_dave_protocol_version", max_dave_protocol_version_prop)
    if not hasattr(VoiceClient, "can_encrypt"): _set_attribute(VoiceClient, "can_encrypt", property(_voiceclient_can_encrypt))
    if not hasattr(VoiceClient, "reinit_dave_session"): _set_attribute(VoiceClient, "reinit_dave_session", _voiceclient_reinit_dave_session)
    if not hasattr(VoiceClient, "_recover_from_invalid_commit"): _set_attribute(VoiceClient, "_recover_from_invalid_commit", _voiceclient_recover_from_invalid_commit)
    if not hasattr(VoiceClient, "_execute_transition"): _set_attribute(VoiceClient, "_execute_transition", _voiceclient_execute_transition)
    original_init = VoiceClient.__init__
    def patched_voice_client_init(self: VoiceClient, *args: Any, **kwargs: Any) -> None:
        original_init(self, *args, **kwargs)
        _ensure_voice_client_state(self)
    _set_attribute(VoiceClient, "__init__", patched_voice_client_init)
    original_get_voice_packet = VoiceClient._get_voice_packet
    def patched_get_voice_packet(self: VoiceClient, data: bytes) -> bytes:
        _ensure_voice_client_state(self)
        packet = data
        session = getattr(self, "dave_session", None)
        if session is not None and getattr(self, "can_encrypt", False):
            try: packet = session.encrypt_opus(data)
            except: pass
        return original_get_voice_packet(self, packet)
    _set_attribute(VoiceClient, "_get_voice_packet", patched_get_voice_packet)
    _set_attribute(VoiceClient, "unpack_audio", _patched_unpack_audio)
    _set_attribute(DiscordVoiceWebSocket, "identify", _patched_identify)
    _set_attribute(DiscordVoiceWebSocket, "speak", _patched_speak)
    _set_attribute(DiscordVoiceWebSocket, "send_binary", _patched_send_binary)
    _set_attribute(DiscordVoiceWebSocket, "send_transition_ready", _patched_send_transition_ready)
    _set_attribute(DiscordVoiceWebSocket, "load_secret_key", _patched_load_secret_key)
    _set_attribute(DiscordVoiceWebSocket, "received_binary_message", _patched_received_binary_message)
    _set_attribute(DiscordVoiceWebSocket, "received_message", _patched_received_message)
    _set_attribute(DiscordVoiceWebSocket, "poll_event", _patched_poll_event)
    _PATCH_APPLIED = True