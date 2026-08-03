# Language Pack — Python

```
discovery_method: pattern
```

Sections per `packs/PACK-INTERFACE.md`. Framework and tooling conventions only — no organization-specific content (Constitution C4).

## 1. Sync route discovery

Look for Flask (`@app.route`, `@blueprint.route`), FastAPI (`@app.get`/`@app.post`/etc., or `APIRouter` decorators), or Django (`urls.py` `path(...)`/`re_path(...)` entries mapped to views) route declarations. FastAPI's Pydantic request/response models are usually the clearest source of a request/response schema of any of the three frameworks — prefer them when present. For gRPC, look for `.proto` service definitions and the generated servicer base class, same as any other language.

## 2. Async binding discovery

For Kafka: look for `confluent-kafka-python` or `kafka-python` consumer construction (`group_id` parameter) and producer `produce`/`send` calls, where the partition key is typically an explicit `key=` argument. For Celery-based systems, task definitions (`@app.task`) and their `apply_async`/`delay` call sites are the closest analogue to publish/consume bindings even though Celery is not a pure event broker. For SQS/SNS or Pub/Sub, look for the relevant boto3/`google-cloud-pubsub` client calls. Configuration is often read from environment variables or a settings module (`settings.py`, `config.py`) — check there for topic and group names, not only the handler code.

## 3. Behavior-extraction hints

In Flask/Django apps without a deliberate domain layer, business logic is commonly found directly in view functions/methods — treat a view doing validation or calculation inline as the Behavior's location. In FastAPI apps using Pydantic, validation is frequently declarative (via Pydantic validators or `Field` constraints) rather than imperative code — read the model definitions themselves as behavior evidence, not just the endpoint function body. Error-mapping typically shows up as custom exception classes plus a registered exception handler (FastAPI `@app.exception_handler`, Flask `@app.errorhandler`, Django middleware) — read those specifically for failure-path behaviors.

## 4. Arch-fitness tooling

[import-linter](https://import-linter.readthedocs.io/) — a `setup.cfg`/`.importlinter`-configured tool that enforces import contracts between Python packages (layering, independence). See `fitness.json` in this directory for the invocation contract `scripts/run-fitness.py` uses.

## 5. Characterization harness conventions

pytest, using the target framework's test client (FastAPI's `TestClient`/`httpx.AsyncClient`, Flask's `test_client()`, Django's `Client`) to exercise the protocol boundary through real request handling rather than calling view functions directly. Keep characterization tests in their own directory (e.g. `tests/characterization/`) with a distinct pytest marker so they are never conflated with pre-existing unit tests that pin internals. Use `pytest-docker` or Testcontainers-Python where dependencies need to be stood up for realistic comparison.

## 6. Build/CI integration

`pytest` for tests, `ruff`/`flake8` for linting (whichever the project already uses), and `lint-imports` (import-linter's CLI) wired into the same CI step so an architecture violation fails the same way a test failure would.
