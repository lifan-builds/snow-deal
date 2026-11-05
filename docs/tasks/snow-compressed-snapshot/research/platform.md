# Platform evidence — November 5, 2026 UTC

Actual deployment `dpl_Fq3akbwNenNoKqebgrK94U4brZMP` rejects the optimized function at 225.49 MB against a 225 MB limit. The downloaded 179,462,144-byte public database compacts to 147,640,320 bytes without dropping observations. Prior successful deployments remain live with the 04:19 snapshot; the failed scheduled run expected 13:40.

Official [Python runtime documentation](https://vercel.com/docs/functions/runtimes/python) describes includeFiles/excludeFiles controlling packaged files. Official [runtime documentation](https://vercel.com/docs/functions/runtimes) describes writable /tmp scratch space. Broad published bundle limits differ from this project's observed enforced limit; use the actual deployment result, not a speculative plan-limit change. The repair keeps all rows, compresses the artifact and verifies exact local reconstruction. No paid-plan or deployment-setting change.
