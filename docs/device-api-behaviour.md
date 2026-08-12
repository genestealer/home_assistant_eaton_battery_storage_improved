# Observed device API behaviour

Recorded on 2026-08-12 by probing a live inverter, because these responses are
not described in the [xStorage Home API
documentation](https://github.com/genestealer/eaton-xstorage-home-api-doc) and
the integration previously guessed at them.

| Field | Value |
| --- | --- |
| Model | `XSTH1P036P048V01` (3.6 kW) |
| Bundle version | `v1.17` |
| Device firmware | `00.01.0017-0-g72006700` |
| Inverter firmware | `00.06.0069` |
| BMS firmware | `4004` |

Behaviour may still differ on the 4.6 kW and 6 kW models, and on units left on
an older bundle version. It will not change on this one: the xStorage Home is
discontinued and no further firmware is expected, so what is recorded here is
fixed for this build rather than a snapshot. Add findings from other models
below rather than replacing these.

## Write endpoints answer in three different shapes

| Endpoint | Status | Content-Type | Body |
| --- | --- | --- | --- |
| `POST /api/device/power` | `200` | `application/json` | `""` |
| `POST /api/device/command` | `200` | `application/json` | `{"successful": true, "result": {…}}` |
| `PUT /api/settings` | `307` → `/api/settings/` → `200` | `application/json` | `{"successful": true, "result": {…}}` |

`POST /api/device/power` returns a bare JSON empty string rather than a result
object, so it cannot be checked for success. `api.set_device_power` therefore
does not call `_require_success`, and `make_request` treats a 2xx with no usable
body as success. The other two return a normal result object and are checked.

`PUT /api/settings` redirects to the trailing-slash path. aiohttp follows a 307
while preserving the method, so the client sees the final `200` and no special
handling is needed. It does cost two round trips per settings write. Note that
`GET /api/settings` does **not** redirect.

## The inverter power rating can be zero

`technical_status.inverterPowerRating` reads `0` on this unit, while
`device.inverterVaRating` reads `3600` and matches the model number. The
xStorage Home range spans 3.6 kW to 6 kW, so the percentage to watt conversion
for the charge and discharge helpers cannot assume 3600.

`number._full_scale_power` therefore prefers `inverterPowerRating` only when it
is greater than zero, then falls back to `inverterVaRating`, then to
`DEFAULT_INVERTER_POWER_RATING`. Removing the greater-than-zero guard would
collapse the watt entities to a 0 W scale on this hardware.

## Sign-in errors

Still unverified. `_classify_auth_error` maps the documented `errCode` `10`
(account locked) and the two synthetic codes the client raises itself, then
falls back to matching the English `description` for wrong credentials and an
invalid inverter serial. Capturing the real codes needs deliberately failed
logins, which risk a ten minute account lockout.

Because the firmware is frozen, that prose fallback cannot be broken by an
update, which makes this low priority. The remaining risk is a device set to a
non-English language returning a localised `description`, which would fall
through to the generic `invalid_auth` message.

## Reproducing

`temp/probe_device.py` in this repository performs these probes. It reads the
credentials from a local Home Assistant config entry so no password is typed or
stored, and it redacts the access token from its output. The command probe
replays whatever mode the device is already running rather than forcing a new
one, but it still replaces the running session, so avoid it mid-charge.
