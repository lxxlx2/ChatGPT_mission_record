# Proposed classes and unresolved guard

- EXPECTED_EXECUTOR_SELF_BOUND_DIRECTORY_FD: exactly one observed DIR matches recorded live PID/start/FD/device/inode and currently active managed token.
- APPROVED_SERVICE_EXACT_REFERENCE: separately approved PID/start/FD/device/inode and current matching observed reference.
- UNEXPECTED_CONSUMER: every other descriptor/process; hard-blocking even same UID/executable or same executor.
- UNRESOLVED: missing proof, closed token, changed identity, incomplete OS inventory.

This definition is insufficient to distinguish unmanaged close/reopen of the same inode on the same descriptor. Therefore final acceptance MUST remain UNRESOLVED; do not use the prototype PASS branch for production.

Executed counterexample:
```python
os.close(bound.proof.fd)
new = os.open(synthetic_root, os.O_RDONLY | os.O_DIRECTORY)
# new == old FD on actual Darwin run
# old proof incorrectly accepted despite recycled descriptor
```
