# Approved plans: the project's memory

Every change starts as a short plan here. A human approves it before any code is written.
Three months later, read the plans, not the whole codebase: they are shorter, they say *why*,
and they fit in an agent's context window.

## Template

```markdown
# NNNN: <title>
Status: Proposed | Approved by <name>, <date> | Superseded by NNNN
## Goal          one paragraph: whose problem, what changes for them
## Spec          checkable statements; each becomes a test or a gate
## Files         what changes and what must not
## Tests first   the tests to write before the code
## Evaluation    how we will know it worked, beyond the tests
## Risks         what could go wrong, including security
```
