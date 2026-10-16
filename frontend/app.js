const API_BASE = window.location.origin.includes('8000') 
  ? window.location.origin 
  : 'http://localhost:8000';

const elements = {
  gatewayStatus: document.getElementById('gatewayStatus'),
  apiKey: document.getElementById('apiKey'),
  providerSelect: document.getElementById('providerSelect'),
  modelInput: document.getElementById('modelInput'),
  promptInput: document.getElementById('promptInput'),
  bypassCache: document.getElementById('bypassCache'),
  sendBtn: document.getElementById('sendBtn'),
  spinner: document.getElementById('spinner'),
  resultContainer: document.getElementById('resultContainer'),
  cacheBadge: document.getElementById('cacheBadge'),
  latencyTag: document.getElementById('latencyTag'),
  tokensTag: document.getElementById('tokensTag'),
  similarityTag: document.getElementById('similarityTag'),
  responseText: document.getElementById('responseText'),
  hitRatio: document.getElementById('hitRatio'),
  totalCached: document.getElementById('totalCached'),
  storageBackend: document.getElementById('storageBackend'),
  cacheEntriesList: document.getElementById('cacheEntriesList'),
  flushCacheBtn: document.getElementById('flushCacheBtn')
};

// Quick sample buttons
document.querySelectorAll('.sample-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    elements.promptInput.value = btn.getAttribute('data-prompt');
    elements.promptInput.focus();
  });
});

// Provider changes default model hint
elements.providerSelect.addEventListener('change', (e) => {
  const provider = e.target.value;
  if (provider === 'huggingface') {
    elements.modelInput.value = 'google/flan-t5-base';
  } else if (provider === 'openai') {
    elements.modelInput.value = 'gpt-4o-mini';
  } else {
    elements.modelInput.value = 'nexus-mock-v1';
  }
});

// Check Health & Telemetry
async function checkGatewayHealth() {
  try {
    const res = await fetch(`${API_BASE}/api/v1/health`);
    if (res.ok) {
      const data = await res.json();
      elements.gatewayStatus.textContent = `Online • ${data.backend_storage.toUpperCase()}`;
      elements.storageBackend.textContent = data.backend_storage.toUpperCase();
    } else {
      elements.gatewayStatus.textContent = 'Degraded';
    }
  } catch (err) {
    elements.gatewayStatus.textContent = 'Offline (Run Server)';
    elements.storageBackend.textContent = 'DISCONNECTED';
  }
}

// Fetch Cache Stats
async function refreshCacheStats() {
  try {
    const apiKey = elements.apiKey.value.trim();
    const res = await fetch(`${API_BASE}/api/v1/cache/stats`, {
      headers: { 'X-API-Key': apiKey }
    });
    if (!res.ok) return;

    const data = await res.json();
    elements.hitRatio.textContent = `${data.hit_ratio}%`;
    elements.totalCached.textContent = data.total_entries;
    elements.storageBackend.textContent = data.storage_backend.toUpperCase();

    renderCacheEntries(data.entries);
  } catch (err) {
    console.error('Error fetching cache stats:', err);
  }
}

function renderCacheEntries(entries) {
  if (!entries || entries.length === 0) {
    elements.cacheEntriesList.innerHTML = '<div class="empty-state">No queries cached yet. Run your first inference!</div>';
    return;
  }

  elements.cacheEntriesList.innerHTML = entries.map(item => `
    <div class="cache-entry-item">
      <div class="cache-entry-prompt">"${escapeHtml(item.prompt)}"</div>
      <div class="cache-entry-meta">
        <span>TTL: ${item.expires_in_seconds}s</span>
        <span>ID: ${item.id.slice(0, 8)}...</span>
      </div>
    </div>
  `).join('');
}

function escapeHtml(str) {
  return str.replace(/[&<>"']/g, m => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;'
  }[m]));
}

// Execute Inference
elements.sendBtn.addEventListener('click', async () => {
  const prompt = elements.promptInput.value.trim();
  if (!prompt) {
    alert('Please enter a prompt.');
    return;
  }

  const apiKey = elements.apiKey.value.trim();
  const provider = elements.providerSelect.value;
  const model = elements.modelInput.value.trim();
  const bypassCache = elements.bypassCache.checked;

  elements.sendBtn.disabled = true;
  elements.spinner.classList.remove('hidden');

  try {
    const res = await fetch(`${API_BASE}/api/v1/infer`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': apiKey
      },
      body: JSON.stringify({
        prompt: prompt,
        provider: provider,
        model: model || undefined,
        bypass_cache: bypassCache
      })
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(errData.detail || 'Request failed');
    }

    const data = await res.json();
    displayResult(data);
    await refreshCacheStats();
  } catch (err) {
    alert(`Inference Error: ${err.message}`);
  } finally {
    elements.sendBtn.disabled = false;
    elements.spinner.classList.add('hidden');
  }
});

function displayResult(data) {
  elements.resultContainer.classList.remove('hidden');
  elements.responseText.textContent = data.response;

  // Latency & Tokens
  elements.latencyTag.textContent = `${data.latency_ms} ms`;
  elements.tokensTag.textContent = `${data.tokens_used} tokens`;

  // Similarity
  if (data.similarity_score !== null && data.similarity_score !== undefined) {
    elements.similarityTag.classList.remove('hidden');
    elements.similarityTag.textContent = `Sim: ${(data.similarity_score * 100).toFixed(1)}%`;
  } else {
    elements.similarityTag.classList.add('hidden');
  }

  // Badge Status
  elements.cacheBadge.className = 'badge';
  if (data.bypassed_due_to_volatility) {
    elements.cacheBadge.classList.add('bypass');
    elements.cacheBadge.textContent = 'REALTIME BYPASS';
  } else if (data.cache_hit) {
    elements.cacheBadge.classList.add('hit');
    elements.cacheBadge.textContent = 'CACHE HIT';
  } else {
    elements.cacheBadge.classList.add('miss');
    elements.cacheBadge.textContent = 'CACHE MISS';
  }
}

// Flush Cache
elements.flushCacheBtn.addEventListener('click', async () => {
  if (!confirm('Are you sure you want to clear all semantic cached vectors?')) return;
  const apiKey = elements.apiKey.value.trim();

  try {
    const res = await fetch(`${API_BASE}/api/v1/cache/clear`, {
      method: 'DELETE',
      headers: { 'X-API-Key': apiKey }
    });
    if (res.ok) {
      await refreshCacheStats();
    }
  } catch (err) {
    alert(`Clear error: ${err.message}`);
  }
});

// Periodic Telemetry Poll
checkGatewayHealth();
refreshCacheStats();
setInterval(() => {
  checkGatewayHealth();
  refreshCacheStats();
}, 6000);
