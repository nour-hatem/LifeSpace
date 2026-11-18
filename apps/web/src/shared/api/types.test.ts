import { describe, expectTypeOf, it } from "vitest";

import type { Settings, Task, TaskEvent, TaskPage } from "./types";

describe("generated api type aliases", () => {
  it("accepts literals that satisfy the generated schemas", () => {
    const task: Task = {
      id: "00000000-0000-0000-0000-000000000001",
      title: "Write the plan",
      description: null,
      status: "planned",
      source: "manual",
      category: null,
      priority: null,
      estimate_minutes: null,
      deadline: null,
      scheduled: null,
      completed_at: null,
      canceled_at: null,
      cancellation_reason: null,
      created_at: "2026-01-01T12:00:00Z",
      updated_at: "2026-01-01T12:00:00Z",
      version: 1,
      is_overdue: false,
    };
    const page: TaskPage = { items: [task], next_cursor: null };
    const settings: Settings = { timezone: "UTC" };
    const event: TaskEvent = {
      id: "00000000-0000-0000-0000-000000000002",
      task_id: task.id,
      from_status: "planned",
      to_status: "in_progress",
      occurred_at: "2026-01-01T12:00:00Z",
      reason: null,
      discarded_schedule: null,
    };

    expectTypeOf(task).toEqualTypeOf<Task>();
    expectTypeOf(page).toEqualTypeOf<TaskPage>();
    expectTypeOf(settings).toEqualTypeOf<Settings>();
    expectTypeOf(event).toEqualTypeOf<TaskEvent>();
  });
});
