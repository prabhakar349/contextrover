# Estimation and Capacity Model

How Stage 4 turns Slice sizes into a defensible forecast. Terminology per `09-glossary.md`.

---

## 1. The governing claim

> **Review capacity is the binding constraint, not authoring capacity.**

If agents produce twenty pull requests a day and three reviewers each review three, throughput is nine. The model's speed is irrelevant past that point. Every estimate this tool produces must make that visible, because it is the single most actionable fact leadership will receive: *adding one reviewer usually moves the date more than adding three engineers.*

This is the same argument as the rest of the framework. The bottleneck is review; objective gates are how you widen it.

---

## 2. Three input sources — only one is a question

### 2.1 Computed from Discovery and Solution Outline (never asked)

Per Slice, from `size.json`:

| Input | Why it matters |
|---|---|
| Behavior count | Primary scope driver |
| Failure-path Behavior count | Costs materially more than happy-path; tracked separately |
| Interface count, split sync / async | Async interfaces carry ordering and delivery semantics — higher cost per interface |
| Divergence count requiring adjudication | Each is a human decision with calendar latency, not effort |
| Affected consumer count | Drives Consumer Migration Stream effort |
| Data migration required | The largest single multiplier. If true, the Slice is a different kind of animal |
| Inter-pass agreement rate | Not a size input — a **confidence** input (§5) |

### 2.2 Asked at Intake — new Section F, Delivery Capacity

Organization-specific and unknowable from code. Added to `06-intake.md`.

| # | Question | Default if unknown |
|---|---|---|
| F1 | Engineers actually available to this engagement (not headcount) | — |
| F2 | **Qualified reviewers** for this codebase | — |
| F3 | Maximum PR size policy, including tests | 500 lines |
| F4 | PRs a reviewer completes per day | 3 |
| F5 | CI cycle time, and flake rate | — |
| F6 | Deploys to production per week | — |
| F7 | Change-approval lead time per production change | 0 days |
| F8 | Test environment availability and contention | — |
| F9 | Walking Skeleton duration — infra, data stores, pipeline, observability, security | 2 weeks |
| F10 | Freeze windows and holidays in the horizon | — |
| F11 | Onboarding ramp for anyone not already on the codebase | — |

F2, F4 and F7 are the ones that actually determine the date. F1 rarely does.

### 2.3 Calibrated from actuals

After Increment 0 completes, replace assumed rates with measured ones and re-forecast. The tool does not claim absolute estimates — it builds a capacity model and corrects it once real throughput exists.

Measured after Increment 0: actual Behaviors per PR, actual review turnaround, actual CI cycle time and rework rate, actual approval latency.

---

## 3. The model

```
work_units       = Σ per Slice:  behaviors
                                + failure_path_behaviors × f_failure
                                + interfaces_sync
                                + interfaces_async × f_async

estimated_prs    = work_units / behaviors_per_pr        # seeded, then calibrated

authoring_rate   = effectively unbounded (agent-assisted)
review_rate      = reviewers × prs_per_reviewer_per_day
integration_rate = deploys_per_week / 5 ÷ change_lead_time_factor

throughput       = min(authoring_rate, review_rate, integration_rate)

duration_days    = walking_skeleton_days
                 + estimated_prs / throughput
                 + adjudication_latency
                 + freeze_days
```

**Seed values** (replaced by calibration after Increment 0): `behaviors_per_pr = 4`, `f_failure = 1.5`, `f_async = 2.0`.

`adjudication_latency` is calendar time waiting for human decisions on Divergences — it is not effort, and it does not shrink by adding engineers. Model it separately or it silently inflates everyone's velocity estimate.

---

## 4. Required outputs

Stage 4 must produce, in the roadmap and the HTML report:

1. **The binding constraint, named.** "Throughput is review-limited at 9 PRs/day" — not a story-point total.
2. **Sensitivity table.** Effect on the end date of: +1 reviewer, +1 engineer, +1 deploy per week, −1 day of approval latency. This is what makes the estimate actionable rather than decorative.
3. **Confidence band**, per §5.
4. **Re-forecast trigger.** The date after which this forecast is stale — always the completion of Increment 0.
5. **What was assumed.** Every default used because the answer was unknown, listed explicitly. An estimate built on six defaults should look different from one built on measured data.

---

## 5. Confidence from agreement

The Stage 1 inter-pass agreement rate is the honest proxy for how well scope is understood:

| Agreement rate | Band | Reading |
|---|---|---|
| ≥ 0.90 | ±20% | Passes converged; scope well understood |
| 0.75 – 0.90 | ±40% | Material disagreement; expect discovered work |
| < 0.75 | ±80%, and say so | Scope is not understood. A date here is theatre |

Below 0.75 the tool must recommend extending Discovery rather than producing a forecast. Reporting a narrow band on poorly understood scope is the most damaging thing an estimation feature can do.

---

## 6. What this model deliberately will not do

- **No story points, no velocity.** Both are team-relative and meaningless across engagements.
- **No effort estimates per Behavior in hours.** Behaviors vary enormously; the aggregate calibrates, the individual does not.
- **No single-number date without a band.** Ever.

**Below 0.75 agreement** (§5): produce the ±80% band **and** a prominent recommendation to extend Discovery before committing. Do not suppress the forecast — leadership will produce a worse number themselves if given none — but the band must be wide enough to be honest and the recommendation must be unmissable.

Definitions used above: `change_lead_time_factor = 1 + (change_approval_lead_time_days / 5)`. `adjudication_latency = unresolved_divergence_count × median_decision_turnaround_days`, where the turnaround is measured from `gates.jsonl` once data exists and defaults to 3 days before that.
