import asyncio

import pytest

from golden_gate.core.adapter import ActionSpec, Adapter, DeviceConfig, DeviceState, InputSpec


class EchoAdapter(Adapter):
    kind = "echo"
    link = "ble"
    actions = {"echo": ActionSpec(label="Echo", inputs=(InputSpec("text", "str"),))}

    async def connect(self):
        self.connected = True

    async def disconnect(self):
        self.connected = False

    async def status(self):
        return {"connected": getattr(self, "connected", False)}

    async def run(self, action, inputs, progress):
        await progress(1.0, "done")
        return {"text": inputs["text"]}


def test_contract_roundtrip():
    async def go():
        a = EchoAdapter(DeviceConfig(id="e1", kind="echo", name="Echo", secrets={"pin": "x"}))
        await a.connect()
        seen = []

        async def progress(f, msg):
            seen.append((f, msg))

        out = await a.run("echo", {"text": "hi"}, progress)
        assert out == {"text": "hi"}
        assert seen == [(1.0, "done")]
        assert (await a.status())["connected"] is True
        await a.disconnect()

    asyncio.run(go())


def test_secrets_not_in_repr():
    assert "x" not in repr(DeviceConfig(id="e1", kind="echo", name="Echo", secrets={"pin": "x"}))


def test_base_methods_unimplemented():
    a = Adapter(DeviceConfig(id="b", kind="base", name="Base"))
    with pytest.raises(NotImplementedError):
        asyncio.run(a.status())


def test_states():
    assert {s.value for s in DeviceState} == {"offline", "connecting", "ready", "busy", "error"}
