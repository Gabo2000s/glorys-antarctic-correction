# Contributing

Thank you for your interest. This repository holds the code and data of a
published study; version 1.x reproduces the article's results.

## Reporting problems

Open an issue with the implementation and version you used, what you ran,
what you expected and what happened.

## Proposing changes

The MATLAB and Python implementations must stay equivalent. A change to the
method goes into both, in the same pull request.

1. Fork the repository and create a branch.
2. Make the change in `matlab/` and in `python/`, and update `docs/method.md`
   if the method changes.
3. Run both test suites: `run tests/run_tests.m` in `matlab/`, and `pytest`
   in `python/`.
4. Run both implementations and compare them:
   `python scripts/compare_implementations.py outputs/matlab outputs/python`.
5. Open a pull request describing the change.

Changes that alter the corrected profiles or the metrics change published
results. They go into a new major version, with an entry in `CHANGELOG.md`
that states the effect on the metrics and regenerated files in `results/`.
