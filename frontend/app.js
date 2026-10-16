/* ═══════════════════════════════════════════════════════
   NexusAI — Frontend Application
   Playground + Observability Dashboard
═══════════════════════════════════════════════════════ */

const API_BASE = window.location.origin.includes('8000')
  ? window.location.origin
  : 'http://localhost:8000';

/* ── DOM refs ── */
const el = {
  // Header
  statusDot:       document.getElementById('statusDot'),
  gatewayStatus:   document.getElementById('gatewayStatus'),
  // Playground
  apiKey:          document.getElementById('apiKey'),
  providerSelect:  document.getElementById('providerSelect'),
  modelInput:      document.getElementById('modelInput'),
  promptInput:     document.getElementById('promptInput'),
  bypassCache:     document.getElementById('bypassCache'),
  sendBtn:         document.getElementById('sendBtn'),
  spinner:         document.getElementById('spinner'),
  resultContainer: document.getElementById('resultContainer'),
  cacheBadge:      document.getElementById('cacheBadge'),
  latencyTag:      document.getElementById('latencyTag'),
  tokensTag:       document.getElementById('tokensTag'),
  similarityTag:   document.getElementById('similarityTag'),
  responseText:    document.getElementById('responseText'),
  hitRatio:        document.getElementById('hitRatio'),
  totalCached:     document.getElementById('totalCached'),
  storageBackend:  document.getElementById('storageBackend'),
  cacheEntriesList:document.getElementById('cacheEntriesList'),
  flushCacheBtn:   document.getElementById('flushCacheBtn'),
  // Monitoring
  lastRefreshLabel:   document.getElementById('lastRefreshLabel'),
  refreshMetricsBtn:  document.getElementById('refreshMetricsBtn'),
  rawMetrics:         document.getElementById('rawMetrics'),
  metricsFilter:      document.getElementById('metricsFilter'),
  // Embedder KPIs
  embedBackend:    document.getElementById('embedBackend'),
  embedTotal:      document.getElementById('embedTotal'),
  embedP50:        document.getElementById('embedP50'),
  // Gateway KPIs
  monStorageBackend: document.getElementById('monStorageBackend'),
  monTotalRequests:  document.getElementById('monTotalRequests'),
  monErrorRate:      document.getElementById('monErrorRate'),
  // Throughput cards
  monHits:    document.getElementById('monHits'),
  monHitPct:  document.getElementById('monHitPct'),
  monMisses:  document.getElementById('monMisses'),
  monMissPct: document.getElementById('monMissPct'),
  monVolatile:document.getElementById('monVolatile'),
  monTokens:  document.getElementById('monTokens'),
  // Latency bars
  latHitP50:    document.getElementById('latHitP50'),
  latHitP90:    document.getElementById('latHitP90'),
  latHitP99:    document.getElementById('latHitP99'),
  latHitP50Bar: document.getElementById('latHitP50Bar'),
  latHitP90Bar: document.getElementById('latHitP90Bar'),
  latHitP99Bar: document.getElementById('latHitP99Bar'),
  latMissP50:    document.getElementById('latMissP50'),
  latMissP90:    document.getElementById('latMissP90'),
  latMissP99:    document.getElementById('latMissP99'),
  latMissP50Bar: document.getElementById('latMissP50Bar'),
  latMissP90Bar: document.getElementById('latMissP90Bar'),
  latMissP99Bar: document.getElementById('latMissP99Bar'),
  latEmbedP50:    document.getElementById('latEmbedP50'),
  latEmbedP90:    document.getElementById('latEmbedP90'),
  latEmbedP99:    document.getElementById('latEmbedP99'),
  latEmbedP50Bar: document.getElementById('latEmbedP50Bar'),
  latEmbedP90Bar: document.getElementById('latEmbedP90Bar'),
  latEmbedP99Bar: document.getElementById('latEmbedP99Bar'),
  // Similarity histogram
  simHistogram:  document.getElementById('simHistogram'),
  // Rate limiter
  rateLimitAllowed:  document.getElementById('rateLimitAllowed'),
  rateLimitRejected: document.getElementById('rateLimitRejected'),
  rateLimitPct:      document.getElementById('rateLimitPct'),
  rateLimitFill:     document.getElementById('rateLimitFill'),
  // Cache gauge
  cacheEntriesGauge: document.getElementById('cacheEntriesGauge'),
  // Admin Panel
  adminApiKey:       document.getElementById('adminApiKey'),
  adminTotalKeys:    document.getElementById('adminTotalKeys'),
  adminTotalTenants: document.getElementById('adminTotalTenants'),
  adminAuditEvents:  document.getElementById('adminAuditEvents'),
  newKeyName:        document.getElementById('newKeyName'),
  newKeyRole:        document.getElementById('newKeyRole'),
  newKeyTenant:      document.getElementById('newKeyTenant'),
  newKeyQuotaReq:    document.getElementById('newKeyQuotaReq'),
  newKeyQuotaToken:  document.getElementById('newKeyQuotaToken'),
  newKeyDesc:        document.getElementById('newKeyDesc'),
  createKeyBtn:      document.getElementById('createKeyBtn'),
  createKeyResult:   document.getElementById('createKeyResult'),
  adminKeysList:     document.getElementById('adminKeysList'),
  refreshAdminBtn:   document.getElementById('refreshAdminBtn'),
  auditFilterTenant: document.getElementById('auditFilterTenant'),
  auditFilterEvent:  document.getElementById('auditFilterEvent'),
  applyAuditFilters: document.getElementById('applyAuditFilters'),
  adminAuditList:    document.getElementById('adminAuditList'),
  clearAuditBtn:     document.getElementById('clearAuditBtn'),
};

/* ════════════════════════════════════════════
   Tab navigation
════════════════════════════════════════════ */
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById('tab-' + btn.dataset.tab).classList.add('active');
    if (btn.dataset.tab === 'monitoring') refreshMonitoring();
    if (btn.dataset.tab === 'admin') refreshAdminPanel();
  });
});

/* ════════════════════════════════════════════
   Playground helpers
════════════════════════════════════════════ */
document.querySelectorAll('.sample-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    el.promptInput.value = btn.getAttribute('data-prompt');
    el.promptInput.focus();
  });
});

el.providerSelect.addEventListener('change', e => {
  const p = e.target.value;
  el.modelInput.value = p === 'huggingface' ? 'google/flan-t5-base'
                      : p === 'openai'      ? 'gpt-4o-mini'
                      :                       'nexus-mock-v1';
});

/* ════════════════════════════════════════════
   Health check
════════════════════════════════════════════ */
async function checkGatewayHealth() {
  try {
    const res = await fetch(`${API_BASE}/api/v1/health`);
    if (res.ok) {
      const data = await res.json();
      const be = (data.backend_storage || 'unknown').toUpperCase();
      el.gatewayStatus.textContent = `Online • ${be}`;
      el.storageBackend.textContent = be;
      el.statusDot.className = 'status-indicator online';
    } else {
      el.gatewayStatus.textContent = 'Degraded';
      el.statusDot.className = 'status-indicator offline';
    }
  } catch {
    el.gatewayStatus.textContent = 'Offline (Run Server)';
    el.storageBackend.textContent = 'DISCONNECTED';
    el.statusDot.className = 'status-indicator offline';
  }
}

/* ════════════════════════════════════════════
   Cache stats (playground tab)
════════════════════════════════════════════ */
async function refreshCacheStats() {
  try {
    const res = await fetch(`${API_BASE}/api/v1/cache/stats`, {
      headers: { 'X-API-Key': el.apiKey.value.trim() },
    });
    if (!res.ok) return;
    const data = await res.json();
    el.hitRatio.textContent     = `${data.hit_ratio}%`;
    el.totalCached.textContent  = data.total_entries;
    el.storageBackend.textContent = (data.storage_backend || '').toUpperCase();
    renderCacheEntries(data.entries);
  } catch (err) {
    console.error('Cache stats error:', err);
  }
}

function renderCacheEntries(entries) {
  if (!entries || entries.length === 0) {
    el.cacheEntriesList.innerHTML = '<div class="empty-state">No queries cached yet. Run your first inference!</div>';
    return;
  }
  el.cacheEntriesList.innerHTML = entries.map(item => {
    const cat = item.ttl_category || 'general';
    const catColor = cat === 'factual' ? '#10b981' : cat === 'technical' ? '#6366f1' : '#9ca3af';
    return `
    <div class="cache-entry-item">
      <div class="cache-entry-prompt">"${esc(item.prompt)}"</div>
      <div class="cache-entry-meta">
        <span>TTL: ${item.expires_in_seconds}s</span>
        <span style="color:${catColor}">● ${cat}</span>
        <span>Hits: ${item.access_count || 0}</span>
        <span>ID: ${item.id.slice(0, 8)}…</span>
      </div>
    </div>`;
  }).join('');
}

function esc(str) {
  return str.replace(/[&<>"']/g, m => ({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }[m]));
}

/* ════════════════════════════════════════════
   Execute Inference
════════════════════════════════════════════ */
el.sendBtn.addEventListener('click', async () => {
  const prompt = el.promptInput.value.trim();
  if (!prompt) { alert('Please enter a prompt.'); return; }

  el.sendBtn.disabled = true;
  el.spinner.classList.remove('hidden');

  try {
    const res = await fetch(`${API_BASE}/api/v1/infer`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-API-Key': el.apiKey.value.trim() },
      body: JSON.stringify({
        prompt,
        provider: el.providerSelect.value,
        model: el.modelInput.value.trim() || undefined,
        bypass_cache: el.bypassCache.checked,
      }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'Request failed');
    }

    const data = await res.json();
    displayResult(data);
    await refreshCacheStats();
  } catch (err) {
    alert(`Inference Error: ${err.message}`);
  } finally {
    el.sendBtn.disabled = false;
    el.spinner.classList.add('hidden');
  }
});

function displayResult(data) {
  el.resultContainer.classList.remove('hidden');
  el.responseText.textContent = data.response;
  el.latencyTag.textContent   = `${data.latency_ms} ms`;
  el.tokensTag.textContent    = `${data.tokens_used} tokens`;

  if (data.similarity_score != null) {
    el.similarityTag.classList.remove('hidden');
    el.similarityTag.textContent = `Sim: ${(data.similarity_score * 100).toFixed(1)}%`;
  } else {
    el.similarityTag.classList.add('hidden');
  }

  el.cacheBadge.className = 'badge';
  if (data.bypassed_due_to_volatility) {
    el.cacheBadge.classList.add('bypass');
    el.cacheBadge.textContent = 'REALTIME BYPASS';
  } else if (data.cache_hit) {
    el.cacheBadge.classList.add('hit');
    el.cacheBadge.textContent = 'CACHE HIT';
  } else {
    el.cacheBadge.classList.add('miss');
    const cat = data.ttl_category || 'general';
    el.cacheBadge.textContent = `CACHE MISS · ${cat.toUpperCase()} TTL`;
  }
}

/* ════════════════════════════════════════════
   Flush cache
════════════════════════════════════════════ */
el.flushCacheBtn.addEventListener('click', async () => {
  if (!confirm('Clear all semantic cached vectors?')) return;
  try {
    const res = await fetch(`${API_BASE}/api/v1/cache/clear`, {
      method: 'DELETE',
      headers: { 'X-API-Key': el.apiKey.value.trim() },
    });
    if (res.ok) await refreshCacheStats();
  } catch (err) {
    alert(`Clear error: ${err.message}`);
  }
});

/* ════════════════════════════════════════════
   ───────── MONITORING DASHBOARD ──────────
════════════════════════════════════════════ */

/* Prometheus text parser — returns { metricName: [{labels, value}] } */
function parsePrometheus(text) {
  const result = {};
  for (const line of text.split('\n')) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;
    const braceOpen = trimmed.indexOf('{');
    const braceClose = trimmed.lastIndexOf('}');
    let name, labelsStr, valueStr;

    if (braceOpen !== -1 && braceClose !== -1) {
      name      = trimmed.slice(0, braceOpen);
      labelsStr = trimmed.slice(braceOpen + 1, braceClose);
      valueStr  = trimmed.slice(braceClose + 2).split(' ')[0];
    } else {
      const parts = trimmed.split(' ');
      name      = parts[0];
      labelsStr = '';
      valueStr  = parts[1];
    }

    const value  = parseFloat(valueStr);
    if (isNaN(value)) continue;

    // Parse label pairs
    const labels = {};
    if (labelsStr) {
      const labelRe = /(\w+)="([^"]*)"/g;
      let m;
      while ((m = labelRe.exec(labelsStr)) !== null) labels[m[1]] = m[2];
    }

    if (!result[name]) result[name] = [];
    result[name].push({ labels, value });
  }
  return result;
}

/* Helper: sum all series entries for a metric name */
function sumMetric(parsed, name) {
  return (parsed[name] || []).reduce((acc, e) => acc + e.value, 0);
}

/* Helper: sum entries filtered by a label match */
function sumMetricLabel(parsed, name, labelKey, labelVal) {
  return (parsed[name] || [])
    .filter(e => e.labels[labelKey] === labelVal)
    .reduce((acc, e) => acc + e.value, 0);
}

/* Helper: estimate percentile from a Prometheus histogram
   buckets = [{labels:{le}, value}, ...] plus _count/_sum */
function estimatePercentile(parsed, baseName, labelFilters, p) {
  const bucketName = `${baseName}_bucket`;
  const countName  = `${baseName}_count`;

  const allBuckets = (parsed[bucketName] || []).filter(e => {
    for (const [k, v] of Object.entries(labelFilters)) {
      if (e.labels[k] !== v) return false;
    }
    return e.labels.le !== undefined;
  });

  const totalCount = (parsed[countName] || [])
    .filter(e => Object.entries(labelFilters).every(([k, v]) => e.labels[k] === v))
    .reduce((a, e) => a + e.value, 0);

  if (!allBuckets.length || totalCount === 0) return null;

  // Sort by le ascending
  const sorted = allBuckets
    .map(e => ({ le: e.labels.le === '+Inf' ? Infinity : parseFloat(e.labels.le), count: e.value }))
    .sort((a, b) => a.le - b.le);

  const target = p * totalCount;
  for (let i = 0; i < sorted.length; i++) {
    if (sorted[i].count >= target) {
      // Linear interpolation between previous and current bucket boundary
      const lower     = i === 0 ? 0 : sorted[i - 1].le;
      const lowerCnt  = i === 0 ? 0 : sorted[i - 1].count;
      const upper     = sorted[i].le === Infinity ? sorted[i - 1]?.le * 2 || 10 : sorted[i].le;
      const upperCnt  = sorted[i].count;
      const fraction  = upperCnt === lowerCnt ? 0 : (target - lowerCnt) / (upperCnt - lowerCnt);
      return lower + fraction * (upper - lower);
    }
  }
  return sorted[sorted.length - 1].le;
}

function fmtSeconds(s) {
  if (s === null || s === undefined) return '—';
  if (s < 0.001) return `${(s * 1e6).toFixed(0)} µs`;
  if (s < 1)     return `${(s * 1000).toFixed(1)} ms`;
  return `${s.toFixed(2)} s`;
}

function fmtNum(n) {
  if (n === null || n === undefined || isNaN(n)) return '—';
  if (n >= 1e6) return (n / 1e6).toFixed(1) + 'M';
  if (n >= 1e3) return (n / 1e3).toFixed(1) + 'k';
  return String(Math.round(n));
}

/* Bar width helper — caps at 100%, relative to a max value */
function barWidth(value, maxMs) {
  if (!value || !maxMs) return '2%';
  return Math.min(100, (value / maxMs) * 100).toFixed(1) + '%';
}

/* Render the similarity score distribution histogram */
function renderSimHistogram(parsed) {
  const bucketName = 'nexusai_cache_similarity_score_bucket';
  const buckets = (parsed[bucketName] || [])
    .filter(e => e.labels.le !== undefined && e.labels.le !== '+Inf')
    .map(e => ({ le: parseFloat(e.labels.le), count: e.value }))
    .sort((a, b) => a.le - b.le);

  if (!buckets.length) {
    el.simHistogram.innerHTML = '<div class="empty-state" style="height:80px;display:flex;align-items:center;justify-content:center">No similarity data yet.</div>';
    return;
  }

  // Convert cumulative counts → per-bucket frequencies
  const bars = buckets.map((b, i) => ({
    le: b.le,
    freq: i === 0 ? b.count : b.count - buckets[i - 1].count,
  }));

  const maxFreq = Math.max(...bars.map(b => b.freq), 1);
  const gradient = ['#6366f1','#8b5cf6','#a78bfa','#06b6d4','#10b981'];

  el.simHistogram.innerHTML = bars.map((b, i) => {
    const pct = Math.max(4, Math.round((b.freq / maxFreq) * 100));
    const color = gradient[i % gradient.length];
    return `
      <div class="sim-bar-col" title="≤${b.le}: ${Math.round(b.freq)} lookups">
        <div class="sim-bar-inner" style="height:${pct}%;background:${color};margin-top:auto"></div>
        <div class="sim-bar-lbl">${b.le}</div>
      </div>`;
  }).join('');
}

/* ── Main monitoring refresh ── */
let _rawPrometheusText = '';

async function refreshMonitoring() {
  try {
    const res = await fetch(`${API_BASE}/api/v1/metrics`);
    if (!res.ok) {
      el.rawMetrics.textContent = `Error fetching metrics: HTTP ${res.status}`;
      return;
    }

    const text = await res.text();
    _rawPrometheusText = text;
    applyMetricsFilter();  // render raw panel

    const parsed = parsePrometheus(text);

    /* ── Embedder card ── */
    const embedTotalVal = sumMetric(parsed, 'nexusai_embed_requests_total');
    // Determine active backend by which has the highest count
    const stEntries = sumMetricLabel(parsed, 'nexusai_embed_requests_total', 'backend', 'sentence_transformers');
    const hashEntries = sumMetricLabel(parsed, 'nexusai_embed_requests_total', 'backend', 'hash_fallback');
    const backendLabel = stEntries > 0 ? 'sentence-transformers' : hashEntries > 0 ? 'hash-fallback' : '—';
    const activeBackend = stEntries > 0 ? 'sentence_transformers' : 'hash_fallback';
    const embedP50val = estimatePercentile(parsed, 'nexusai_embed_latency_seconds', { backend: activeBackend }, 0.50);

    el.embedBackend.textContent = backendLabel;
    el.embedTotal.textContent   = fmtNum(embedTotalVal);
    el.embedP50.textContent     = fmtSeconds(embedP50val);

    /* ── Gateway health (read from cache stats) ── */
    // (handled in Option 3 block below with full stats fetch)

    /* ── Total requests & errors ── */
    const totalReqs  = sumMetric(parsed, 'nexusai_inference_requests_total');
    const totalErrors = sumMetric(parsed, 'nexusai_inference_errors_total');
    el.monTotalRequests.textContent = fmtNum(totalReqs);
    el.monErrorRate.textContent     = fmtNum(totalErrors);

    /* ── Throughput cards ── */
    const hits     = sumMetricLabel(parsed, 'nexusai_inference_requests_total', 'cache_result', 'hit');
    const misses   = sumMetricLabel(parsed, 'nexusai_inference_requests_total', 'cache_result', 'miss');
    const volatile = sumMetricLabel(parsed, 'nexusai_inference_requests_total', 'cache_result', 'volatile_bypass');
    const tokens   = sumMetric(parsed, 'nexusai_inference_tokens_total');

    el.monHits.textContent    = fmtNum(hits);
    el.monMisses.textContent  = fmtNum(misses);
    el.monVolatile.textContent= fmtNum(volatile);
    el.monTokens.textContent  = fmtNum(tokens);

    const total = hits + misses + volatile || 1;
    el.monHitPct.textContent  = `${((hits   / total) * 100).toFixed(1)}% of requests`;
    el.monMissPct.textContent = `${((misses  / total) * 100).toFixed(1)}% of requests`;

    /* ── Latency percentiles ── */
    const MAX_HIT_MS   = 100;   // reference scale for hit bars
    const MAX_MISS_MS  = 5000;  // reference scale for miss bars
    const MAX_EMBED_MS = 500;

    // Hit latency
    const hitP50 = estimatePercentile(parsed, 'nexusai_inference_latency_seconds', { cache_result: 'hit' }, 0.50);
    const hitP90 = estimatePercentile(parsed, 'nexusai_inference_latency_seconds', { cache_result: 'hit' }, 0.90);
    const hitP99 = estimatePercentile(parsed, 'nexusai_inference_latency_seconds', { cache_result: 'hit' }, 0.99);
    el.latHitP50.textContent = fmtSeconds(hitP50); el.latHitP50Bar.style.width = barWidth(hitP50 && hitP50 * 1000, MAX_HIT_MS);
    el.latHitP90.textContent = fmtSeconds(hitP90); el.latHitP90Bar.style.width = barWidth(hitP90 && hitP90 * 1000, MAX_HIT_MS);
    el.latHitP99.textContent = fmtSeconds(hitP99); el.latHitP99Bar.style.width = barWidth(hitP99 && hitP99 * 1000, MAX_HIT_MS);

    // Miss latency
    const missP50 = estimatePercentile(parsed, 'nexusai_inference_latency_seconds', { cache_result: 'miss' }, 0.50);
    const missP90 = estimatePercentile(parsed, 'nexusai_inference_latency_seconds', { cache_result: 'miss' }, 0.90);
    const missP99 = estimatePercentile(parsed, 'nexusai_inference_latency_seconds', { cache_result: 'miss' }, 0.99);
    el.latMissP50.textContent = fmtSeconds(missP50); el.latMissP50Bar.style.width = barWidth(missP50 && missP50 * 1000, MAX_MISS_MS);
    el.latMissP90.textContent = fmtSeconds(missP90); el.latMissP90Bar.style.width = barWidth(missP90 && missP90 * 1000, MAX_MISS_MS);
    el.latMissP99.textContent = fmtSeconds(missP99); el.latMissP99Bar.style.width = barWidth(missP99 && missP99 * 1000, MAX_MISS_MS);

    // Embed latency
    const embedP50 = estimatePercentile(parsed, 'nexusai_embed_latency_seconds', { backend: activeBackend }, 0.50);
    const embedP90 = estimatePercentile(parsed, 'nexusai_embed_latency_seconds', { backend: activeBackend }, 0.90);
    const embedP99 = estimatePercentile(parsed, 'nexusai_embed_latency_seconds', { backend: activeBackend }, 0.99);
    el.latEmbedP50.textContent = fmtSeconds(embedP50); el.latEmbedP50Bar.style.width = barWidth(embedP50 && embedP50 * 1000, MAX_EMBED_MS);
    el.latEmbedP90.textContent = fmtSeconds(embedP90); el.latEmbedP90Bar.style.width = barWidth(embedP90 && embedP90 * 1000, MAX_EMBED_MS);
    el.latEmbedP99.textContent = fmtSeconds(embedP99); el.latEmbedP99Bar.style.width = barWidth(embedP99 && embedP99 * 1000, MAX_EMBED_MS);

    /* ── Similarity histogram ── */
    renderSimHistogram(parsed);

    /* ── Rate limiter ── */
    const allowed  = sumMetric(parsed, 'nexusai_rate_limit_allowed_total');
    const rejected = sumMetric(parsed, 'nexusai_rate_limit_rejected_total');
    const rlTotal  = allowed + rejected || 1;
    const passPct  = ((allowed / rlTotal) * 100).toFixed(1);
    el.rateLimitAllowed.textContent  = fmtNum(allowed);
    el.rateLimitRejected.textContent = fmtNum(rejected);
    el.rateLimitPct.textContent      = `${passPct}%`;
    el.rateLimitFill.style.width     = `${passPct}%`;

    /* ── Option 3: Advanced Cache Management metrics ── */
    const evictions    = sumMetric(parsed, 'nexusai_cache_evictions_total');
    const warmupEntries = sumMetric(parsed, 'nexusai_cache_warmup_entries_total');
    const warmupRuns   = sumMetric(parsed, 'nexusai_cache_warmup_runs_total');

    const monEvictions     = document.getElementById('monEvictions');
    const monWarmupEntries = document.getElementById('monWarmupEntries');
    const monWarmupRuns    = document.getElementById('monWarmupRuns');
    const monCapacityPct   = document.getElementById('monCapacityPct');
    const monCapacitySub   = document.getElementById('monCapacitySub');

    if (monEvictions)     monEvictions.textContent     = fmtNum(evictions);
    if (monWarmupEntries) monWarmupEntries.textContent  = fmtNum(warmupEntries);
    if (monWarmupRuns)    monWarmupRuns.textContent     = `${fmtNum(warmupRuns)} runs total`;

    // Capacity gauge from cache stats
    try {
      const statsRes = await fetch(`${API_BASE}/api/v1/cache/stats`, {
        headers: { 'X-API-Key': el.apiKey.value.trim() },
      });
      if (statsRes.ok) {
        const stats = await statsRes.json();
        el.monStorageBackend.textContent = (stats.storage_backend || '—').toUpperCase();
        el.cacheEntriesGauge.textContent = stats.total_entries;

        const maxEntries = stats.max_entries || 500;
        const pct = maxEntries > 0 ? ((stats.total_entries / maxEntries) * 100).toFixed(1) : 0;
        if (monCapacityPct)  monCapacityPct.textContent  = `${pct}%`;
        if (monCapacitySub)  monCapacitySub.textContent  = `${stats.total_entries} of ${maxEntries} max`;

        // TTL category breakdown
        renderTTLBreakdown(stats.ttl_category_counts || {}, stats.total_entries);

        // Top accessed entries
        renderTopEntries((stats.entries || []).slice(0, 5));
      }
    } catch { /* non-critical */ }

    /* ── Timestamp ── */
    el.lastRefreshLabel.textContent = `Last refresh: ${new Date().toLocaleTimeString()}`;

  } catch (err) {
    el.rawMetrics.textContent = `Could not reach /api/v1/metrics — is the server running?\n\n${err}`;
  }
}

/* Raw metrics filter */
function applyMetricsFilter() {
  const q = (el.metricsFilter?.value || '').toLowerCase().trim();
  if (!_rawPrometheusText) return;
  const lines = _rawPrometheusText.split('\n');
  const filtered = q
    ? lines.filter(l => l.toLowerCase().includes(q))
    : lines;
  el.rawMetrics.textContent = filtered.join('\n') || '(no matching metrics)';
}

el.metricsFilter?.addEventListener('input', applyMetricsFilter);
el.refreshMetricsBtn?.addEventListener('click', refreshMonitoring);

/* ════════════════════════════════════════════
   Option 3: TTL breakdown + Top entries renderers
════════════════════════════════════════════ */

const TTL_COLORS = { factual: '#10b981', technical: '#6366f1', general: '#9ca3af' };
const TTL_LABELS = { factual: 'Factual (24h)', technical: 'Technical (6h)', general: 'General (1h)' };

function renderTTLBreakdown(counts, total) {
  const el2 = document.getElementById('ttlBreakdown');
  if (!el2) return;
  if (!total || Object.keys(counts).length === 0) {
    el2.innerHTML = '<div class="empty-state">No entries cached yet.</div>';
    return;
  }
  el2.innerHTML = Object.entries(TTL_LABELS).map(([key, label]) => {
    const count = counts[key] || 0;
    const pct   = total > 0 ? ((count / total) * 100).toFixed(1) : 0;
    const color = TTL_COLORS[key];
    return `
      <div class="ttl-row">
        <div class="ttl-row-header">
          <span class="ttl-dot" style="background:${color}"></span>
          <span class="ttl-name">${label}</span>
          <span class="ttl-count">${count}</span>
        </div>
        <div class="ttl-bar-track">
          <div class="ttl-bar-fill" style="width:${pct}%;background:${color}"></div>
        </div>
      </div>`;
  }).join('');
}

function renderTopEntries(entries) {
  const el2 = document.getElementById('topEntriesList');
  if (!el2) return;
  if (!entries || entries.length === 0) {
    el2.innerHTML = '<div class="empty-state">No entries cached yet.</div>';
    return;
  }
  el2.innerHTML = entries.map((item, i) => {
    const cat   = item.ttl_category || 'general';
    const color = TTL_COLORS[cat] || '#9ca3af';
    return `
      <div class="top-entry-item">
        <div class="top-entry-rank">#${i + 1}</div>
        <div class="top-entry-body">
          <div class="top-entry-prompt">"${esc(item.prompt)}"</div>
          <div class="top-entry-meta">
            <span style="color:${color}">● ${cat}</span>
            <span class="top-entry-hits">⚡ ${item.access_count} hits</span>
            <span>TTL ${item.expires_in_seconds}s left</span>
          </div>
        </div>
      </div>`;
  }).join('');
}

/* ── Warm-up button ── */
const warmBtn = document.getElementById('warmCacheBtn');
const warmStatus = document.getElementById('warmStatus');

warmBtn?.addEventListener('click', async () => {
  warmBtn.disabled = true;
  warmBtn.textContent = '⏳ Warming…';
  if (warmStatus) warmStatus.textContent = '';
  try {
    const res = await fetch(`${API_BASE}/api/v1/cache/warm`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-API-Key': el.apiKey.value.trim() },
      body: JSON.stringify({ provider: 'mock', model: 'nexus-mock-v1' }),
    });
    const data = await res.json();
    if (warmStatus) {
      warmStatus.textContent = res.ok
        ? `✓ Stored ${data.stored} entries in ${data.elapsed_ms} ms`
        : `✗ ${data.detail || 'Warm-up failed'}`;
      warmStatus.style.color = res.ok ? '#10b981' : '#ef4444';
    }
    if (res.ok) {
      await refreshCacheStats();
      await refreshMonitoring();
    }
  } catch (err) {
    if (warmStatus) { warmStatus.textContent = `✗ ${err.message}`; warmStatus.style.color = '#ef4444'; }
  } finally {
    warmBtn.disabled = false;
    warmBtn.textContent = '⚡ Run Warm-up';
  }
});

/* ════════════════════════════════════════════
   ───────── ADMIN PANEL ──────────
════════════════════════════════════════════ */

/* ── Refresh admin dashboard ── */
async function refreshAdminPanel() {
  const adminKey = el.adminApiKey.value.trim();
  if (!adminKey) {
    alert('Please enter an admin API key.');
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/api/v1/admin/stats`, {
      headers: { 'X-API-Key': adminKey },
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'Failed to load admin stats');
    }
    const data = await res.json();

    // Update dashboard stats
    el.adminTotalKeys.textContent    = data.total_active_keys || 0;
    el.adminTotalTenants.textContent = data.total_tenants || 0;
    el.adminAuditEvents.textContent  = data.audit_events_today || 0;

    // Render keys list
    renderAdminKeys(data.keys || []);

    // Load audit log
    await refreshAuditLog();
  } catch (err) {
    alert(`Admin panel error: ${err.message}`);
  }
}

/* ── Render API keys table ── */
function renderAdminKeys(keys) {
  if (!keys || keys.length === 0) {
    el.adminKeysList.innerHTML = '<div class="empty-state">No API keys found.</div>';
    return;
  }

  el.adminKeysList.innerHTML = keys.map(key => {
    const reqPct = key.quota_pct_requests || 0;
    const tokPct = key.quota_pct_tokens || 0;
    const statusColor = key.is_active ? '#10b981' : '#ef4444';
    const statusLabel = key.is_active ? 'Active' : 'Revoked';

    return `
      <div class="admin-key-card">
        <div class="admin-key-header">
          <div class="admin-key-name">${esc(key.name)}</div>
          <div class="admin-key-status" style="color:${statusColor}">● ${statusLabel}</div>
        </div>
        <div class="admin-key-meta">
          <span>Key: <code>${esc(key.key_preview)}</code></span>
          <span>Role: <strong>${esc(key.role)}</strong></span>
          <span>Tenant: ${esc(key.tenant_id || 'default')}</span>
        </div>
        <div class="admin-quota-section">
          <div class="admin-quota-item">
            <div class="admin-quota-label">Requests: ${key.requests_used} / ${key.requests_limit || '∞'}</div>
            <div class="admin-quota-bar-track">
              <div class="admin-quota-bar-fill admin-quota-bar-requests" style="width:${Math.min(100, reqPct)}%"></div>
            </div>
            <div class="admin-quota-pct">${reqPct.toFixed(1)}%</div>
          </div>
          <div class="admin-quota-item">
            <div class="admin-quota-label">Tokens: ${key.tokens_used} / ${key.tokens_limit || '∞'}</div>
            <div class="admin-quota-bar-track">
              <div class="admin-quota-bar-fill admin-quota-bar-tokens" style="width:${Math.min(100, tokPct)}%"></div>
            </div>
            <div class="admin-quota-pct">${tokPct.toFixed(1)}%</div>
          </div>
        </div>
        <div class="admin-key-actions">
          <button class="btn btn-sm btn-outline admin-usage-btn" data-key="${esc(key.key_preview.split('…')[0])}">📊 Usage</button>
          ${key.is_active ? `<button class="btn btn-sm btn-danger admin-revoke-btn" data-key="${esc(key.key_preview.split('…')[0])}">🔒 Revoke</button>` : ''}
        </div>
      </div>`;
  }).join('');

  // Attach event listeners
  document.querySelectorAll('.admin-revoke-btn').forEach(btn => {
    btn.addEventListener('click', () => revokeKey(btn.dataset.key));
  });
  document.querySelectorAll('.admin-usage-btn').forEach(btn => {
    btn.addEventListener('click', () => showKeyUsage(btn.dataset.key));
  });
}

/* ── Create new API key ── */
el.createKeyBtn.addEventListener('click', async () => {
  const adminKey = el.adminApiKey.value.trim();
  if (!adminKey) {
    alert('Please enter an admin API key first.');
    return;
  }

  const name = el.newKeyName.value.trim();
  if (!name) {
    alert('Key name is required.');
    return;
  }

  const body = {
    name,
    role: el.newKeyRole.value,
    tenant_id: el.newKeyTenant.value.trim() || 'default',
    quota_requests: parseInt(el.newKeyQuotaReq.value) || null,
    quota_tokens: parseInt(el.newKeyQuotaToken.value) || null,
    description: el.newKeyDesc.value.trim() || null,
  };

  el.createKeyBtn.disabled = true;
  el.createKeyBtn.textContent = '⏳ Creating…';

  try {
    const res = await fetch(`${API_BASE}/api/v1/admin/keys`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-API-Key': adminKey },
      body: JSON.stringify(body),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'Failed to create key');
    }

    const data = await res.json();
    el.createKeyResult.classList.remove('hidden');
    el.createKeyResult.innerHTML = `
      <div class="admin-success-box">
        <div class="admin-success-title">✅ API Key Created Successfully</div>
        <div class="admin-success-key">
          <strong>Key:</strong> <code>${esc(data.key)}</code>
          <button class="btn btn-sm btn-outline admin-copy-btn" data-text="${esc(data.key)}">📋 Copy</button>
        </div>
        <div class="admin-success-warning">⚠️ Save this key securely — it won't be shown again!</div>
      </div>`;

    // Attach copy button listener
    document.querySelector('.admin-copy-btn').addEventListener('click', function() {
      navigator.clipboard.writeText(this.dataset.text);
      this.textContent = '✓ Copied';
      setTimeout(() => { this.textContent = '📋 Copy'; }, 2000);
    });

    // Clear form
    el.newKeyName.value = '';
    el.newKeyTenant.value = '';
    el.newKeyQuotaReq.value = '';
    el.newKeyQuotaToken.value = '';
    el.newKeyDesc.value = '';

    // Refresh keys list
    await refreshAdminPanel();
  } catch (err) {
    alert(`Create key error: ${err.message}`);
  } finally {
    el.createKeyBtn.disabled = false;
    el.createKeyBtn.textContent = '🔑 Create API Key';
  }
});

/* ── Revoke key ── */
async function revokeKey(keyId) {
  const adminKey = el.adminApiKey.value.trim();
  if (!confirm(`Revoke key "${keyId}…"? This action cannot be undone.`)) return;

  try {
    const res = await fetch(`${API_BASE}/api/v1/admin/keys/${keyId}`, {
      method: 'DELETE',
      headers: { 'X-API-Key': adminKey },
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'Failed to revoke key');
    }

    await refreshAdminPanel();
  } catch (err) {
    alert(`Revoke error: ${err.message}`);
  }
}

/* ── Show key usage detail ── */
async function showKeyUsage(keyId) {
  const adminKey = el.adminApiKey.value.trim();
  try {
    const res = await fetch(`${API_BASE}/api/v1/admin/keys/${keyId}/usage`, {
      headers: { 'X-API-Key': adminKey },
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'Failed to load usage');
    }

    const data = await res.json();
    alert(`Usage for ${data.name}:\n\n` +
          `Requests: ${data.requests_used} / ${data.requests_limit || '∞'} (${data.quota_pct_requests}%)\n` +
          `Tokens: ${data.tokens_used} / ${data.tokens_limit || '∞'} (${data.quota_pct_tokens}%)\n` +
          `Role: ${data.role}\n` +
          `Tenant: ${data.tenant_id}\n` +
          `Status: ${data.is_active ? 'Active' : 'Revoked'}`);
  } catch (err) {
    alert(`Usage error: ${err.message}`);
  }
}

/* ── Refresh audit log ── */
async function refreshAuditLog() {
  const adminKey = el.adminApiKey.value.trim();
  if (!adminKey) return;

  const tenantFilter = el.auditFilterTenant?.value.trim() || null;
  const eventFilter = el.auditFilterEvent?.value.trim() || null;

  try {
    const params = new URLSearchParams({ limit: '50' });
    if (tenantFilter) params.append('tenant_id', tenantFilter);
    if (eventFilter) params.append('event_type', eventFilter);

    const res = await fetch(`${API_BASE}/api/v1/admin/audit?${params}`, {
      headers: { 'X-API-Key': adminKey },
    });

    if (!res.ok) return;

    const data = await res.json();
    renderAuditLog(data.entries || []);
  } catch (err) {
    console.error('Audit log error:', err);
  }
}

/* ── Render audit log entries ── */
function renderAuditLog(entries) {
  if (!entries || entries.length === 0) {
    el.adminAuditList.innerHTML = '<div class="empty-state">No audit entries found.</div>';
    return;
  }

  el.adminAuditList.innerHTML = entries.map(entry => {
    const ts = new Date(entry.timestamp * 1000).toLocaleString();
    const eventColor = entry.event_type === 'key_created' ? '#10b981'
                     : entry.event_type === 'key_revoked' ? '#ef4444'
                     : entry.event_type === 'quota_exceeded' ? '#f59e0b'
                     : '#6366f1';
    return `
      <div class="admin-audit-entry">
        <div class="admin-audit-header">
          <span class="admin-audit-event" style="color:${eventColor}">● ${esc(entry.event_type)}</span>
          <span class="admin-audit-time">${ts}</span>
        </div>
        <div class="admin-audit-detail">${esc(entry.detail || '—')}</div>
        <div class="admin-audit-meta">
          <span>Tenant: ${esc(entry.tenant_id || 'n/a')}</span>
          <span>Key: ${esc(entry.api_key_preview || 'n/a')}</span>
          <span>${esc(entry.method || '')} ${esc(entry.endpoint || '')}</span>
        </div>
      </div>`;
  }).join('');
}

/* ── Clear audit log ── */
el.clearAuditBtn?.addEventListener('click', async () => {
  const adminKey = el.adminApiKey.value.trim();
  if (!adminKey) {
    alert('Please enter an admin API key.');
    return;
  }
  if (!confirm('Clear all audit log entries? This cannot be undone.')) return;

  try {
    const res = await fetch(`${API_BASE}/api/v1/admin/audit`, {
      method: 'DELETE',
      headers: { 'X-API-Key': adminKey },
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'Failed to clear audit log');
    }

    await refreshAuditLog();
    alert('Audit log cleared.');
  } catch (err) {
    alert(`Clear audit error: ${err.message}`);
  }
});

/* ── Admin panel event listeners ── */
el.refreshAdminBtn?.addEventListener('click', refreshAdminPanel);
el.applyAuditFilters?.addEventListener('click', refreshAuditLog);

/* ════════════════════════════════════════════
   Polling — every 6 s
════════════════════════════════════════════ */
checkGatewayHealth();
refreshCacheStats();

setInterval(() => {
  checkGatewayHealth();
  refreshCacheStats();
  // Only auto-refresh monitoring data when its tab is active
  const monTab = document.getElementById('tab-monitoring');
  if (monTab && monTab.classList.contains('active')) refreshMonitoring();
}, 6000);
