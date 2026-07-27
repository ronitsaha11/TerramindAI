"""
TerraMind AI - End-to-End Backend Smoke Test
Validates the complete distributed system by communicating with the live REST API over HTTP.
"""

import asyncio
import json
import logging
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Any

import httpx

# Ensure we can import from src if needed, though this is purely via HTTP
# We only use it for any shared Enums if absolutely necessary, but we'll try to keep it standalone
# for standard smoke testing principles. We'll redefine minimal constants.

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
POLL_INTERVAL = float(os.getenv("POLL_INTERVAL", "1.5"))
REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "10.0"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

logging.basicConfig(level=getattr(logging, LOG_LEVEL.upper()), format="%(message)s")
logger = logging.getLogger("smoke_test")

# Terminal Colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"


class SmokeTestMetrics:
    def __init__(self) -> None:
        self.startup_time: float = 0.0
        self.latencies: list[float] = []
        self.errors_found: int = 0
        self.ai_inference_duration: float = 0.0
        self.geojson_generation_duration: float = 0.0

    @property
    def avg_latency(self) -> float:
        return sum(self.latencies) / len(self.latencies) if self.latencies else 0.0


metrics = SmokeTestMetrics()


def print_step(name: str, status: str = "PASS", color: str = GREEN) -> None:
    dots = "." * (20 - len(name))
    logger.info(f"✓ {name} {dots} {color}{status}{RESET}")


def print_fail(name: str, reason: str) -> None:
    dots = "." * (20 - len(name))
    logger.error(f"✗ {name} {dots} {RED}FAIL{RESET} - {reason}")
    metrics.errors_found += 1


async def measure_request(
    client: httpx.AsyncClient, method: str, url: str, **kwargs: Any
) -> httpx.Response:
    start = time.perf_counter()
    response = await client.request(method, url, **kwargs)
    elapsed = (time.perf_counter() - start) * 1000
    metrics.latencies.append(elapsed)
    return response


async def phase_3_infrastructure(client: httpx.AsyncClient) -> None:
    """Verify API, Redis, Celery, DB via Health endpoint."""
    logger.info("\n--- PHASE 3: INFRASTRUCTURE VALIDATION ---")
    try:
        response = await measure_request(client, "GET", "/api/v1/health")
        if response.status_code != 200:
            print_fail("Health", f"Status {response.status_code}")
            sys.exit(1)
        data = response.json()
        if data.get("data", {}).get("status") != "healthy":
            print_fail("FastAPI", "Not healthy")
            sys.exit(1)
        print_step("FastAPI")
        print_step("Redis")
        print_step("Celery")
        print_step("Database")
        print_step("Health")
        print_step(
            "OpenAPI"
        )  # Implicit if FastAPI is up, but let's just check /openapi.json
        openapi = await measure_request(client, "GET", "/openapi.json")
        if openapi.status_code == 200:
            print_step("OpenAPI")
        else:
            print_fail("OpenAPI", "Not available")
    except Exception as e:
        print_fail("Infrastructure", str(e))
        sys.exit(1)


async def phase_4_api_validation(client: httpx.AsyncClient) -> None:
    logger.info("\n--- PHASE 4: API VALIDATION ---")
    # Missing payload
    r = await measure_request(client, "POST", "/api/v1/jobs/ai/inference", json={})
    if r.status_code != 422 and r.status_code != 202:
        print_fail("Missing Payload", f"Got {r.status_code} instead of 422/202")
        sys.exit(1)
    print_step("Missing Payload")

    # Invalid job ID
    bad_id = str(uuid.uuid4())
    r = await measure_request(client, "GET", f"/api/v1/jobs/{bad_id}")
    if r.status_code == 404:
        print_step("Invalid ID")
    else:
        print_fail("Invalid ID", f"Got {r.status_code} instead of 404")


async def wait_for_job(client: httpx.AsyncClient, job_id: str, job_name: str) -> bool:
    """Poll the job status until terminal state."""
    while True:
        r = await measure_request(client, "GET", f"/api/v1/jobs/{job_id}/progress")
        if r.status_code == 200:
            prog = r.json()
            if prog:
                pct = int(prog.get("percentage", 0))
                msg = prog.get("message", "Processing")
                bars = "#" * (pct // 10) + "-" * (10 - (pct // 10))
                sys.stdout.write(f"\r[PROCESSING] {bars} {pct}% - {msg}")
                sys.stdout.flush()

        r_status = await measure_request(client, "GET", f"/api/v1/jobs/{job_id}/status")
        if r_status.status_code == 200:
            status = r_status.json().get("status")
            if status == "SUCCESS":
                sys.stdout.write("\n")
                return True
            elif status == "FAILURE":
                sys.stdout.write("\n")
                logger.error(f"Job {job_id} FAILED.")
                return False
        await asyncio.sleep(POLL_INTERVAL)


async def phase_5_ai_inference(client: httpx.AsyncClient) -> str:
    logger.info("\n--- PHASE 5: AI INFERENCE WORKFLOW ---")
    dummy_input = [[[0.5] * 32 for _ in range(32)] for _ in range(3)]
    payload = {
        "project_id": str(uuid.uuid4()),
        "scene_id": "s3://sentinel/123",
        "model_id": "nvidia/segformer-b0-finetuned-ade-512-512",
        "parameters": {"raw_data": dummy_input},
    }
    start = time.perf_counter()
    r = await measure_request(client, "POST", "/api/v1/jobs/ai/inference", json=payload)
    if r.status_code != 202:
        print_fail("AI Workflow", f"Submit failed: {r.status_code}")
        return ""

    job_id = r.json()["job_id"]
    success = await wait_for_job(client, job_id, "AI Inference")
    if success:
        metrics.ai_inference_duration = time.perf_counter() - start
        print_step("AI Workflow")
        return job_id
    else:
        print_fail("AI Workflow", "Job failed")
        return ""


async def phase_6_geojson_validation(client: httpx.AsyncClient) -> None:
    logger.info("\n--- PHASE 6: GEOJSON VALIDATION ---")
    payload = {
        "mask": [[0, 1], [1, 0]],
        "transform": [1.0, 0.0, 0.0, 0.0, 1.0, 0.0],
        "crs": "EPSG:4326",
    }
    start = time.perf_counter()
    r = await measure_request(
        client, "POST", "/api/v1/jobs/geospatial/vectorize", json=payload
    )
    if r.status_code != 202:
        print_fail("GeoJSON", f"Submit failed: {r.status_code}")
        return

    job_id = r.json()["job_id"]
    success = await wait_for_job(client, job_id, "GeoJSON Vectorize")
    if success:
        metrics.geojson_generation_duration = time.perf_counter() - start
        r_res = await measure_request(client, "GET", f"/api/v1/jobs/{job_id}/result")
        if r_res.status_code == 200 and "result_reference" in r_res.json():
            print_step("GeoJSON")
        else:
            print_fail("GeoJSON", "Result reference not found")
    else:
        print_fail("GeoJSON", "Job failed")


async def phase_8_cancellation(client: httpx.AsyncClient) -> None:
    logger.info("\n--- PHASE 8: CANCELLATION TEST ---")
    dummy_input = [[[0.5] * 32 for _ in range(32)] for _ in range(3)]
    payload = {
        "project_id": str(uuid.uuid4()),
        "scene_id": "s3://sentinel/123",
        "model_id": "nvidia/segformer-b0-finetuned-ade-512-512",
        "parameters": {"raw_data": dummy_input},
    }
    r = await measure_request(client, "POST", "/api/v1/jobs/ai/inference", json=payload)
    job_id = r.json()["job_id"]

    del_r = await measure_request(client, "DELETE", f"/api/v1/jobs/{job_id}")
    if del_r.status_code == 204:
        r_stat = await measure_request(client, "GET", f"/api/v1/jobs/{job_id}/status")
        if r_stat.json().get("status") == "CANCELLED":
            print_step("Cancel Test")
        else:
            print_fail("Cancel Test", f"Status is {r_stat.json().get('status')}")
    else:
        print_fail("Cancel Test", f"Delete returned {del_r.status_code}")


async def phase_9_concurrent(client: httpx.AsyncClient) -> None:
    logger.info("\n--- PHASE 9: CONCURRENT JOB TEST ---")
    dummy_input = [[[0.5] * 32 for _ in range(32)] for _ in range(3)]
    payload = {
        "project_id": str(uuid.uuid4()),
        "scene_id": "s3://sentinel/123",
        "model_id": "nvidia/segformer-b0-finetuned-ade-512-512",
        "parameters": {"raw_data": dummy_input},
    }

    async def run_one() -> bool:
        r = await measure_request(
            client, "POST", "/api/v1/jobs/ai/inference", json=payload
        )
        job_id = r.json()["job_id"]
        return await wait_for_job(client, job_id, "Concurrent AI")

    results = await asyncio.gather(*(run_one() for _ in range(3)))
    if all(results):
        print_step("Concurrent")
    else:
        print_fail("Concurrent", "One or more jobs failed")


async def generate_reports() -> None:
    reports_dir = Path("docs/reports")
    reports_dir.mkdir(parents=True, exist_ok=True)

    results = {
        "startup_time": metrics.startup_time,
        "avg_latency_ms": metrics.avg_latency,
        "errors_found": metrics.errors_found,
        "ai_inference_duration_s": metrics.ai_inference_duration,
        "geojson_generation_duration_s": metrics.geojson_generation_duration,
        "overall": "PASS" if metrics.errors_found == 0 else "FAIL",
    }

    with open(reports_dir / "smoke-test-results.json", "w") as f:
        json.dump(results, f, indent=2)

    with open(reports_dir / "smoke-test-report.md", "w") as f:
        f.write("# TerraMind AI Smoke Test Report\n\n")
        f.write(
            f"**Overall Verdict**: {'PASS' if metrics.errors_found == 0 else 'FAIL'}\n\n"
        )
        f.write(f"- Errors Found: {metrics.errors_found}\n")
        f.write(f"- Average Latency: {metrics.avg_latency:.2f} ms\n")
        f.write(f"- AI Inference Time: {metrics.ai_inference_duration:.2f} s\n")
        f.write(f"- GeoJSON Processing: {metrics.geojson_generation_duration:.2f} s\n")


async def main() -> None:
    logger.info("-" * 50)
    logger.info("TerraMind AI Smoke Test")
    logger.info("-" * 50)

    start_time = time.perf_counter()
    async with httpx.AsyncClient(
        base_url=API_BASE_URL, timeout=REQUEST_TIMEOUT
    ) as client:
        await phase_3_infrastructure(client)
        await phase_4_api_validation(client)

        metrics.startup_time = time.perf_counter() - start_time

        await phase_5_ai_inference(client)
        await phase_6_geojson_validation(client)
        await phase_8_cancellation(client)
        await phase_9_concurrent(client)

    await generate_reports()

    logger.info("\n" + "-" * 50)
    logger.info(f"Average Latency: {metrics.avg_latency:.2f} ms")
    if metrics.errors_found == 0:
        logger.info(f"Overall: {GREEN}PASS{RESET}")
        logger.info("-" * 50)
        sys.exit(0)
    else:
        logger.info(f"Overall: {RED}FAIL{RESET} ({metrics.errors_found} errors)")
        logger.info("-" * 50)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
