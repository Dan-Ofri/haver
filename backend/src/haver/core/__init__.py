"""Domain-agnostic core: agent loop, plugin registry, retrieval, memory and safety.

Nothing in this package may import from `haver.plugins`. Domains plug into the core,
never the other way round. This rule is checked by tests/test_architecture.py.
"""
