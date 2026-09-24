# API Performance and Latency

## Common symptoms

High latency is usually caused by slow database queries, upstream API delays, network packet loss, or overloaded background jobs. The first step is to confirm whether the issue is isolated to one endpoint or affects all requests.

## Basic checks

Check recent deployments, region health, error rates, queue depth, and database pool saturation. If the issue started after a deployment, compare the current release to the previous version.

## Response time guidelines

The target latency depends on the service tier. For customer-facing APIs, the team should investigate if p95 response time exceeds the expected threshold for more than 15 minutes.

## Escalation conditions

Escalate if there is persistent latency across multiple regions, a major dependency outage, or a production incident affecting user sign-ins or purchases.
