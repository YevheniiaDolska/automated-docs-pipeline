---
title: Workflow execution model
description: The workflow engine processes workflows by executing nodes sequentially, passing data as
  arrays of JSON objects between each node in the chain.
content_type: concept
product: both
app_component: workflow-engine
tags:
- Concept
- Nodes
- Cloud
- Self-hosted
last_reviewed: '2026-02-16'
original_author: JaneDo
---


## Workflow execution model overview

The execution model determines how data flows from one node to the next within a workflow. The engine executes nodes sequentially and passes data as arrays of JSON objects. This model explains why node behavior is predictable across branches, retries, and failures.

## Data structure between nodes

Every node receives and outputs data in the same format: an array of items, where each item is a JSON object wrapped in a `json` key (for example, user records and event payloads).

When a node receives 5 items, it processes each item independently. The Slack node, for example, sends 5 separate messages—one per item.

## Execution flow

The engine follows these rules during execution:

1. The **trigger node** starts the workflow and produces the initial items.
1. Each subsequent node receives all output items from the previous node.
1. A node processes items either **once for all items** or **once per item**, depending on the node type and configuration.
1. **Branch nodes** (IF, Switch) route items to different paths based on conditions.
1. Execution stops when all branches reach their final nodes.

## Execution modes

The platform supports two execution modes that affect error handling and performance.

=== "Regular mode (default)"

 Nodes execute one at a time. If a node fails, execution stops and the workflow reports an error. This mode is predictable and easier to debug.

 Typical setting: `EXECUTIONS_MODE=regular`

=== "Queue mode (production)"

 Workflow executions are distributed across worker processes. This mode handles high-volume workloads (hundreds of concurrent executions) and requires a Redis instance for coordination.

 Typical setting: `EXECUTIONS_MODE=queue`

## Error handling

When a node fails, behavior depends on the node's error handling setting:

- **Stop execution** (default): The workflow stops. The error appears in the execution log.
- **Continue on fail**: The node outputs an error object, and the next node receives it. Use this for non-critical steps like logging.
- **Error Trigger workflow**: A separate workflow handles the error path. This pattern is common for alerting and retry logic.

## Key implications for documentation writers

The execution model means that every node reference page should document what input format the node expects, what output format it produces (how many items, what structure), and how the node behaves with multiple items (once for all vs. once per item).

## Related

- [Build your first workflow](../getting-started/quickstart.md)
- [Webhook node reference](../reference/nodes/webhook.md)

## Next steps

- [Documentation index](index.md)
