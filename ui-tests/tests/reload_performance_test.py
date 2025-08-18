import statistics
from playwright.sync_api import sync_playwright
import time

MAX_TIME_MS       = 4800
MAX_TIME_P95_MS   = 5200
MAX_DELTA_MB      = 10.0
MAX_NET_GROWTH_MB = 20.0
RUNS      = 5
WARMUP    = 1
CANVAS_PATH = ("ui-tests", "tests", "LargeCanvas.xircuits")
STABLE_WINDOW_MS  = 2000
STABLE_SAMPLES    = 4
STABLE_EPSILON_MB = 5.0

def get_js_heap_used(page) -> int:
    client = page.context.new_cdp_session(page)
    client.send("Performance.enable")
    metrics = client.send("Performance.getMetrics")["metrics"]
    for m in metrics:
        if m.get("name") == "JSHeapUsedSize":
            return int(m.get("value") or 0)
    return 0

def get_dom_counters(page):
    client = page.context.new_cdp_session(page)
    try:
        return client.send("Memory.getDOMCounters")
    except Exception:
        return None

def collect_gc(page):
    client = page.context.new_cdp_session(page)
    try:
        client.send("HeapProfiler.enable")
        client.send("HeapProfiler.collectGarbage")
    except Exception:
        pass

def wait_for_heap_stable(page, window_ms=STABLE_WINDOW_MS, samples=STABLE_SAMPLES, epsilon_mb=STABLE_EPSILON_MB):
    values = []
    per_sample = max(250, window_ms // samples)
    for _ in range(samples):
        h = get_js_heap_used(page)
        values.append(h)
        page.wait_for_timeout(per_sample)
    span_mb = (max(values) - min(values)) / (1024 * 1024)
    return span_mb <= epsilon_mb

def wait_reload_settled(page, timeout_ms=60000):
    locator = page.get_by_text("Reloading all nodes...", exact=False)
    try:
        locator.wait_for(state="visible", timeout=10_000)
    except Exception:
        pass
    try:
        locator.wait_for(state="detached", timeout=timeout_ms)
    except Exception:
        pass
    assert wait_for_heap_stable(page), "Heap not stable after overlay detached"

def measure_reload_duration(page) -> float:
    t0 = time.perf_counter()
    page.locator('jp-button[title="Reload all nodes"] >>> button').click()
    wait_reload_settled(page)
    t1 = time.perf_counter()
    return (t1 - t0) * 1000.0

def open_canvas_file(page, path_tuple):
    page.wait_for_selector('#jupyterlab-splash', state='detached')
    for segment in path_tuple[:-1]:
        page.get_by_text(segment, exact=True).dblclick()
        page.wait_for_timeout(200)
    page.get_by_text(path_tuple[-1], exact=True).dblclick()
    page.wait_for_selector('#jupyterlab-splash', state='detached')
    page.wait_for_timeout(800)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    page.goto("http://localhost:8888")
    page.wait_for_selector('#jupyterlab-splash', state='detached')
    open_canvas_file(page, CANVAS_PATH)

    times, deltas = [], []

    dom_before = get_dom_counters(page)
    if dom_before:
        print(f"DOM before: {dom_before}")

    heap0 = get_js_heap_used(page)

    for i in range(RUNS):
        heap_before = get_js_heap_used(page)
        dur_ms = measure_reload_duration(page)
        collect_gc(page)
        page.wait_for_timeout(200)
        heap_after = get_js_heap_used(page)

        delta_mb = (heap_after - heap_before) / (1024 * 1024)
        label = "Warm-up" if i < WARMUP else f"Run {i - WARMUP + 1}"
        print(f"[{label}] time={dur_ms:.0f} ms, Δheap={delta_mb:.1f} MB")

        if i >= WARMUP:
            times.append(dur_ms)
            deltas.append(delta_mb)

    dom_after = get_dom_counters(page)
    if dom_after:
        print(f"DOM after:  {dom_after}")

    med = statistics.median(times)
    p95 = sorted(times)[min(len(times) - 1, int(round(0.95 * len(times) - 1)))]
    net_growth_mb = (get_js_heap_used(page) - heap0) / (1024 * 1024)

    print("\n=== Reload Perf Summary ===")
    print(f"times (ms): {', '.join(f'{t:.0f}' for t in times)}")
    print(f"median: {med:.0f} ms | p95: {p95:.0f} ms")
    print(f"Δheap (MB): {', '.join(f'{d:.1f}' for d in deltas)}")
    print(f"net growth across runs: {net_growth_mb:.1f} MB")

    assert med <= MAX_TIME_MS, f"Median time {med:.0f}ms > {MAX_TIME_MS}ms"
    assert p95 <= MAX_TIME_P95_MS, f"P95 time {p95:.0f}ms > {MAX_TIME_P95_MS}ms"
    for i, d in enumerate(deltas, 1):
        assert d <= MAX_DELTA_MB, f"Run {i}: Δheap {d:.1f}MB > {MAX_DELTA_MB}MB"
    assert net_growth_mb <= MAX_NET_GROWTH_MB, \
        f"Net heap growth {net_growth_mb:.1f}MB > {MAX_NET_GROWTH_MB}MB"

    if dom_before and dom_after:
        nb = dom_before.get("nodes", 0)
        na = dom_after.get("nodes", 0)
        if nb and na:
            grow_pct = 100.0 * (na - nb) / nb
            print(f"DOM nodes growth: {grow_pct:.1f}%")

    context.close()
    browser.close()
