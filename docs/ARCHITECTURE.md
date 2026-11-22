# golden-gate architecture

## Goal
One small box on the lab LAN that talks to devices which only offer their own Wi-Fi AP or a Bluetooth link, and re-exposes them as a web UI and HTTP API on the LAN. Adding a device means writing an adapter, not a new server.

## Hardware
- **Raspberry Pi 3**, hostname `golden-gate`, Pi OS Lite 64-bit, user `chris`.
- **eth0**: lab LAN. The only interface with a default route. The UI and API are served here.
- **wlan1**: TP-Link Archer TX10UB Nano (RTL8851BU, `rtw89`; DKMS on kernels < 6.17). Joins device APs (for example `INSTAX-xxxx`). **No default route**: device networks are isolated and never bridged to the LAN.
- **wlan0**: onboard Wi-Fi. Spare. Can serve as a second device-AP radio later.
- **hci0**: onboard Bluetooth (BCM43438, BT 4.1 / BLE), driven by BlueZ over D-Bus.

## Software layout
```
golden-gate/
  core/        # service: device registry, job queue, HTTP API, web UI host
  adapters/
    instax_sp2/   # adapter #1 + its mock device
  links/
    wifi_ap.py    # join/leave a device AP on wlan1 (NetworkManager), no default route
    ble.py        # BlueZ scan/connect/GATT helpers
  ui/          # web UI: device list + per-device panels
  deploy/      # Pi setup script, systemd units, env template
```

### Core
- **Registry**: loads the enabled adapters from config (`/etc/golden-gate/devices.toml`) and holds each device's state (`offline | connecting | ready | busy | error`).
- **Job queue**: one job at a time per device. A job is an adapter action call with its inputs.
- **Link arbitration**: `wlan1` can join only one AP at a time. Core serialises Wi-Fi-AP devices on that radio and reconnects on drop.
- **HTTP API** (LAN only):
  - `GET /api/devices` lists devices with state and their declared actions.
  - `GET /api/devices/{id}` returns status (adapter-specific fields, e.g. battery, prints left).
  - `POST /api/devices/{id}/actions/{action}` queues a job and returns a job id.
  - `GET /api/jobs/{id}` returns job state.
  - `POST /api/uploads` stores a file for use as a job input.
- **Secrets** (device PINs, pairing keys) live in `/etc/golden-gate/secrets.env` (root:chris 0640), never in source or the repo.

### Adapter interface
Each adapter is a Python package exposing one class:
```python
class Adapter:
    kind: str                   # "instax_sp2"
    link: str                   # "wifi_ap" | "ble"
    actions: dict[str, ActionSpec]  # name -> input schema + confirm flag
    async def connect(self) -> None
    async def disconnect(self) -> None
    async def status(self) -> dict
    async def run(self, action: str, inputs: dict, progress) -> dict
```
- An `ActionSpec` with `confirm=True` makes the UI ask before running. Use it for anything that consumes material (film) or changes the device's settings.
- Every adapter ships a **mock device** speaking the same protocol, so the agents and CI never need hardware or network.

### UI
A device list. Each device's panel is generated from its status fields and actions, and an adapter can supply a custom panel (the Instax panel adds image upload, crop preview at 600×800, rotate and brightness).

## Adapter #1: Instax SHARE SP-2
- Link: `wifi_ap` (SSID `INSTAX-xxxx`, PIN from secrets, default 1111).
- Status: battery, prints remaining, connection.
- Actions: `print` (image input, `confirm=True`; uses film).
- Image prep: fit/crop to 600×800, rotate, brightness. Credit the open-source SP-2/SP-3 protocol library it builds on.

## Security
- LAN only, no internet exposure, no auth in v1 (same trust model as other lab services). Revisit before adding any device that can actuate hardware.
- Device networks are never routed. `wlan1` and Bluetooth carry device traffic only.
- Agents develop against mocks. **Richard** deploys to the Pi from onyx-ops (agents can't reach the LAN).

## Human gates
- First real action on any physical device (first print, first actuation) is Christopher's.
- Consumables: every film-using action needs confirmation in the UI.

## Adding a device
1. Write `adapters/<kind>/` with the adapter and a mock device.
2. Tests against the mock (no network).
3. Add an entry to `devices.toml` on the Pi; secrets go in `secrets.env`.
