"""Pipeline conditions: single-oneshot, single-with-retry, multi-agent.

All three are configurations of the same underlying workflow.
"""

from .multi_agent import run_multi_agent
from .single_oneshot import run_single_oneshot
from .single_with_retry import run_single_with_retry

__all__ = ["run_multi_agent", "run_single_oneshot", "run_single_with_retry"]
