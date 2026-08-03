# Language Pack — Java

```
discovery_method: pattern
```

Sections per `packs/PACK-INTERFACE.md`. Framework and tooling conventions only — no organization-specific content (Constitution C4).

## 1. Sync route discovery

Look for Spring MVC / Spring WebFlux annotations (`@RestController`, `@RequestMapping`, `@GetMapping`/`@PostMapping`/`@PutMapping`/`@DeleteMapping`/`@PatchMapping`) for HTTP, and for JAX-RS annotations (`@Path`, `@GET`, `@POST`, etc.) where Spring is not in use. For gRPC, look for `.proto` service definitions and their generated `*Grpc.*ImplBase` classes. Request/response shapes usually come from the annotated method's parameter and return types (Spring) or the `.proto` message definitions (gRPC); prefer the `.proto` file as the source of truth when both a proto and generated code are present, since the proto is hand-authored and the generated code is derived.

## 2. Async binding discovery

For Kafka: look for `@KafkaListener` (Spring Kafka) for consumers and `KafkaTemplate.send(...)` / `@KafkaHandler` publishing calls for producers; consumer group is usually the `groupId` attribute on the listener, partition key is whatever is passed as the `key` argument to `send`. For JMS/SQS: look for `@JmsListener` / `@SqsListener` and the corresponding client `send`/`sendMessage` calls. Application configuration (`application.yml`/`application.properties`) frequently names topics, groups, and retry/DLQ configuration explicitly — read it alongside the code.

## 3. Behavior-extraction hints

Business logic in idiomatic layered Spring applications tends to live in `@Service`-annotated classes, not in `@RestController` or `@Repository` classes — controllers should be thin, and a controller doing validation or calculation itself is often exactly the anaemic-model-inverted case worth flagging. Validation frequently uses Bean Validation annotations (`@NotNull`, `@Valid`, etc.) or explicit checks that throw a custom exception; error-mapping usually lives in an `@ExceptionHandler` or `@ControllerAdvice` class — read those specifically for the failure-path behaviors they encode, since those are exactly the behaviors under-represented by default.

## 4. Arch-fitness tooling

[ArchUnit](https://www.archunit.org/) — a JUnit-integrated library for asserting architectural rules directly against compiled bytecode (package dependency direction, layering, naming conventions). See `fitness.json` in this directory for the invocation contract `scripts/run-fitness.py` uses.

## 5. Characterization harness conventions

JUnit 5, invoked via the project's existing Maven (`mvn test`) or Gradle (`./gradlew test`) wrapper — do not introduce a second test runner. Characterization tests belong in a distinct source set (e.g. `src/characterizationTest/java`) so they are never confused with or accidentally merged into pre-existing unit tests that pin internals (the exact failure mode this framework's tests avoid — DR1). Use an HTTP client (`RestAssured`, `WebTestClient`, or the project's existing integration-test client) to exercise the protocol boundary; use Testcontainers where the target system's dependencies (databases, brokers) need to be stood up for a realistic comparison.

**Masking conventions.** Common volatile fields in this ecosystem and how to mask them before comparison: `UUID.randomUUID()` output and JPA/Hibernate auto-generated `@Id` values (`GenerationType.IDENTITY`/`SEQUENCE`) — replace with a fixed placeholder or match against a shape regex rather than an exact value. `Instant.now()`/`LocalDateTime.now()`-derived timestamps (commonly serialized by Jackson's default `ObjectMapper`) — strip or replace with a placeholder. Jackson preserves declared field/getter order by default (no `@JsonPropertyOrder` needed for stability), so key order is not itself a volatility concern unless the project has customized serialization. A field is a masking candidate only when it varies between two calls with identical business input — a field that is part of the business response (e.g. a status that legitimately changes over an entity's lifecycle) is not volatility in this sense, even though it varies over time.

## 6. Build/CI integration

Maven (`mvn verify`) or Gradle (`./gradlew check`) — whichever the target repository already uses. Wire `fitness.json`'s ArchUnit rule into the same test phase so a fitness violation fails the build the same way a failing test would, rather than living as a separate, skippable step.
