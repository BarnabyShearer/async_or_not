Utility Repo to help chose performance trade offs.

[TL;DR](./RESULTS.txt)

Theory:

- How much trafic can 1vCPU/1GB serve with acceptable performance.
  i.e. before the HPA horizontally scales.
- App workers are significantly cheeper then DB so we assume
  we will tune our Database to slightly bottleneck on our trafic.
- These implementations need to _reasonably_ match your usage. How you
  ensure this can only be judgment.
- This is _NOT_ production code, no error handling nor anything else
  I didn't feel the need to benchmark.

Run:

    make sync async golang threading
