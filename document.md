# Address Integration Review Findings — v0.3.0

**Labels:** `enhancement`, `bug`, `code-quality`

---

## Summary

An in-depth review of the integration (v0.2.1) identified 25+ issues across several categories. This issue tracks implementing all non-test fixes in a single PR. Test coverage will be added separately.

## Problems Identified

### Critical — Async / Deprecated Patterns
- [ ] `datetime.utcnow()` used in `api.py` (deprecated since Python 3.12) — should be `datetime.now(timezone.utc)`
- [ ] Fire-and-forget `asyncio.create_task()` sync wrappers in `switch.py` (4 instances) and `select.py` (1 instance) — exceptions silently lost, violates HA async guidelines

### Medium — Config Flow
- [ ] Error keys contain spaces/special characters (e.g. `"Error during authentication: 10"`, `"Authentication failed: non-JSON response"`) — should be slug-format keys
- [ ] `_test_connection()` duplicated between `ConfigFlow` and `OptionsFlow` — ConfigFlow version also missing `return serial`
- [ ] No reauth flow (`async_step_reauth`) for credential refresh when tokens expire
- [ ] Hardcoded `"tech"` / `"customer"` strings throughout instead of using existing `ACCOUNT_TYPE_TECHNICIAN` / `ACCOUNT_TYPE_CUSTOMER` constants

### Medium — Code Duplication
- [ ] Settings GET→PUT transform logic (country/city/timezone dict-to-primitive conversion) duplicated 5 times across `switch.py`, `select.py`, and `number.py`

### Low — Code Quality
- [ ] `coordinator.py`: redundant `self.config_entry = config_entry` (parent already stores it)
- [ ] `coordinator.py`: unused `battery_level` property (never referenced anywhere)
- [ ] `coordinator.py`: missing `ConfigEntry` type annotation on `__init__` parameter
- [ ] `__init__.py`: bare `except Exception` catch-all in setup — should be narrowed to recoverable types
- [ ] `quality_scale.yaml`: `runtime-data` marked as `todo` but is actually implemented correctly

### Missing Files
- [ ] No `diagnostics.py` — needed for debug data download in HA UI
- [ ] No `system_health.py` — recommended for integration health reporting
- [ ] No `strings.json` — base translation source file (HA convention)
- [ ] No entity translations in `translations/en.json` for `binary_sensor` and `event` platforms

### CI/CD
- [ ] No linting in GitHub Actions workflow — should add `ruff check` and `ruff format --check`

## Proposed Changes

1. **api.py** — Replace `datetime.utcnow()` with `datetime.now(timezone.utc)`
2. **switch.py** — Remove sync `turn_on`/`turn_off` wrappers using `asyncio.create_task()`; deduplicate settings transform
3. **select.py** — Remove sync `select_option` wrapper; deduplicate settings transform
4. **number.py** — Deduplicate settings transform
5. **helpers.py** *(new)* — Shared `transform_settings_for_put()` function
6. **config_flow.py** — Extract shared `_async_test_connection()` + `_map_auth_error()`; add reauth flow; fix error keys to slugs; use `ACCOUNT_TYPE_*` constants
7. **coordinator.py** — Remove redundant `self.config_entry`, unused `battery_level`; add type annotation; use constants
8. **__init__.py** — Narrow `except Exception` to `except (OSError, TimeoutError)`; use constants
9. **sensor.py** — Use `ACCOUNT_TYPE_TECHNICIAN` constant
10. **diagnostics.py** *(new)* — Debug data download with sensitive field redaction
11. **system_health.py** *(new)* — Report device reachability, API host, last update time
12. **strings.json** *(new)* — Base translation source file
13. **translations/en.json** — Add `reauth_confirm` step, `reauth_successful` abort, entity translations, fix error keys
14. **manifest.json** — Add `system_health` dependency, bump version to `0.3.0`
15. **quality_scale.yaml** — Update `runtime-data` to `done`
16. **.github/workflows/main.yml** — Add lint job with ruff

## Branch & Commit

**Branch:** `fix/integration-review-v0.3.0`

**Commit message:**
```
fix: address integration review findings for v0.3.0

- Replace deprecated datetime.utcnow() with datetime.now(timezone.utc)
- Remove fire-and-forget asyncio.create_task() sync wrappers
- Extract shared _async_test_connection() and _map_auth_error() helpers
- Add reauth flow (async_step_reauth / async_step_reauth_confirm)
- Fix error keys to use slug format (no spaces/special chars)
- Replace hardcoded "tech"/"customer" with ACCOUNT_TYPE constants
- Deduplicate settings transform logic into helpers.py
- Remove redundant self.config_entry and unused battery_level in coordinator
- Narrow bare except Exception to (OSError, TimeoutError) in setup
- Add diagnostics.py, system_health.py, strings.json
- Add entity translations for binary_sensor and event platforms
- Add CI lint job (ruff check + format)
- Bump version to 0.3.0
```

## Out of Scope

- **Tests** — Will be tracked in a separate issue due to complexity
- **Splitting `sensor.py`** — Deferred to a future PR
- **Quality scale upgrade** — Keeping `bronze` until tests are added

## References

- [HA Developer Docs: AsyncIO Working with Async](https://developers.home-assistant.io/docs/asyncio_working_with_async)
- [HA Developer Docs: Config Flow Handler](https://developers.home-assistant.io/docs/config_entries_config_flow_handler)
- [HA Developer Docs: Integration Fetching Data](https://developers.home-assistant.io/docs/integration_fetching_data)
- [Python 3.12: datetime.utcnow() deprecation](https://docs.python.org/3/library/datetime.html#datetime.datetime.utcnow)
