# Language Pack — Go

```
discovery_method: pattern
```

Sections per `packs/PACK-INTERFACE.md`. Framework and tooling conventions only — no organization-specific content (Constitution C4).

## 1. Sync route discovery

Look for `net/http` `HandleFunc`/`Handle` registrations, or the equivalent router-registration calls for whichever router the project uses (`chi`, `gorilla/mux`, `gin`, `echo`) — each has its own idiomatic registration call (`router.Get(...)`, `r.GET(...)`, etc.) but all associate a method+path with a handler function in one place, which is where to start. For gRPC, look for `.proto` service definitions and the generated `*Server` interface implementation; prefer the `.proto` as source of truth over generated code for the same reason as any language — it is hand-authored, the generated code is derived.

## 2. Async binding discovery

For Kafka: look for consumer-group construction (`sarama.NewConsumerGroup`, `kafka-go`'s `Reader` with a `GroupID`, or similar) for consumers, and `Writer`/`Producer` construction plus `WriteMessages`/`SendMessage` calls for producers; the partition key is typically the `Message.Key` field. For SQS/SNS or Pub/Sub: look for the relevant client SDK's publish/subscribe calls. Configuration is often environment-variable or flag-driven in Go services rather than a central config file — check `main.go`/`cmd/` entry points for where topic and group names are wired in, not just the handler code itself.

## 3. Behavior-extraction hints

Idiomatic Go tends to keep HTTP handlers thin and push logic into plain functions or small structs in an internal package (`internal/`) — a handler function longer than a few lines doing validation or calculation inline is a signal worth extracting as a Behavior directly from the handler if no separate domain layer exists yet, which is common in Go services that predate a deliberate domain model. Error handling is idiomatically explicit (`if err != nil`) rather than exception-based — error-mapping behaviors show up as the translation from an internal `error` value to an HTTP status code or a published error event, often in one central place (a middleware or a response-writing helper).

## 4. Arch-fitness tooling

[go-arch-lint](https://github.com/fe3dback/go-arch-lint) — a YAML-configured architecture linter for Go that checks package-import rules against a declared architecture. See `fitness.json` in this directory for the invocation contract `scripts/run-fitness.py` uses.

## 5. Characterization harness conventions

The standard library's `testing` package, invoked via `go test`, using `net/http/httptest` to exercise the protocol boundary through real HTTP handling rather than calling handler functions directly with hand-built structs. Keep characterization tests in their own package or build-tagged file set (e.g. a `characterization` build tag) so `go test ./...` does not silently conflate them with pre-existing unit tests. Use `dockertest` or Testcontainers-go where dependencies need to be stood up for realistic comparison.

**Masking conventions.** Common volatile fields in this ecosystem and how to mask them before comparison: `github.com/google/uuid` output and database auto-increment IDs — replace with a fixed placeholder or match against a shape regex rather than an exact value. `time.Now()`-derived timestamps (commonly serialized via `encoding/json`'s default RFC3339 handling for `time.Time` fields) — strip or replace with a placeholder. `encoding/json`'s `Encode`/`Marshal` preserves struct-field declaration order, so key order is not itself a volatility concern. A field is a masking candidate only when it varies between two calls with identical business input — a field that is part of the business response (e.g. a status that legitimately changes over an entity's lifecycle) is not volatility in this sense, even though it varies over time.

## 6. Build/CI integration

`go build ./...` and `go test ./...` (or `go vet` for static checks), plus `go-arch-lint check` wired into the same CI step so an architecture violation fails the same way a test failure would.
