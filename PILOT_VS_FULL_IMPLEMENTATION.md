# Pilot vs full implementation

This file compares current commercial and technical scope.

## Scope matrix

| Aspect | Pilot | Full implementation | Full + RAG |
| --- | --- | --- | --- |
| Duration | 21 days | One-time rollout project | One-time rollout + RAG |
| Price | `$5,000` | `$15,000` | `$25,000` total (`$15,000` + `$10,000`) |
| Repository scope | One repo | Production scope | Production scope |
| API protocols | Core validation in pilot scope | Full API-first coverage | Full API-first coverage |
| Docs operations | Baseline setup | Full docs operations | Full docs operations |
| RAG prep | Optional limited checks | Included prep | Included prep |
| Retrieval-time RAG | No | No | Yes |
| Weekly operations | Pilot cadence | Full cadence | Full cadence |
| Commercial objective | Prove value | Production rollout | Production rollout + AI Q&A |

## Decision guidance

Choose pilot when:

1. Client needs low-risk validation on one repository.
1. Internal stakeholders require evidence before full approval.

Choose full when:

1. Client is ready for production docs operations.
1. Team needs full automation without RAG runtime.

Choose full + RAG when:

1. Client needs retrieval-time AI answers on top of prepared knowledge.
1. Client accepts the additional implementation scope.

## Plan boundaries reminder

- Community/degraded mode keeps only free lint defaults by design.
- Full keeps advanced docs/API capabilities except retrieval-time RAG.
- Full + RAG includes the complete stack.
