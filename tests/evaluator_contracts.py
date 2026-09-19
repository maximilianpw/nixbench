"""Compatibility imports for older tests; implementation lives in nixbench.contracts."""

from nixbench.contracts import (  # noqa: F401
    ContractRun,
    EvaluatorContractCase,
    RenameOperation,
    apply_contract_candidate,
    contract_result_errors,
    coverage_errors,
    load_contract_cases,
    run_contract_case,
    tree_digest,
)
