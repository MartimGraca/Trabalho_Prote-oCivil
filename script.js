// Clean frontend script — pages, occurrences, polling, upload, filters and modal
document.addEventListener('DOMContentLoaded', () => {
    const API_CANDIDATES = [window.API_BASE, 'http://127.0.0.1:8000', 'http://localhost:8000'].filter(Boolean);
    let API = null;

    async function detectApiBase() {
        const checkPath = '/metrics';
        for (const base of API_CANDIDATES) {
            try {
                const ac = new AbortController();
                const to = setTimeout(() => ac.abort(), 3000);
                const res = await fetch(base + checkPath, { method: 'GET', signal: ac.signal });
                clearTimeout(to);
                if (res.ok) { API = base; return API; }
            } catch (_) { /* ignore */ }
        }
        API = null;
        return null;
    }

    // UI elements
    const pageDashboard = document.getElementById('page-dashboard');
    const pageOccurrences = document.getElementById('page-occurrences');
    const occurrencesGrid = document.getElementById('occurrences-grid');
    const occurrencesCount = document.getElementById('occurrences-count');

    const uploadFormOcc = document.getElementById('upload-form-occ');
    const fileInputOcc = document.getElementById('excel-file-occ');
    const uploadStatusOcc = document.getElementById('upload-status-occ');
    const selectedFileName = document.getElementById('selected-file-name');

    // Filters & search helpers
    function applyFilter(filterText) {
        const cards = document.querySelectorAll('#occurrences-grid .alert-card');
        cards.forEach(card => {
            if (filterText === 'todos') { card.style.display = 'block'; return; }
            const cls = (card.className || '');
            const sevMatch = cls.match(/severity-(\w+)/);
            const sev = sevMatch ? sevMatch[1] : 'low';
            const map = { 'critical': 'crítico', 'high': 'alto', 'medium': 'médio', 'low': 'baixo' };
            card.style.display = (map[sev] === filterText) ? 'block' : 'none';
        });
    }

    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            applyFilter(btn.textContent.trim().toLowerCase());
        });
    });

    document.addEventListener('input', (e) => {
        if (!e.target.matches('.search-input')) return;
        const term = e.target.value.trim().toLowerCase();
        document.querySelectorAll('#occurrences-grid .alert-card').forEach(card => {
            const title = (card.querySelector('.alert-header div')?.textContent || '').toLowerCase();
            const loc = (card.querySelector('.alert-description')?.textContent || '').toLowerCase();
            const meta = (card.querySelector('.alert-meta')?.textContent || '').toLowerCase();
            card.style.display = (title.includes(term) || loc.includes(term) || meta.includes(term)) ? 'block' : 'none';
        });
    });

    // Page switching
    function showPage(name){
        if (name === 'dashboard') {
            if (pageDashboard) pageDashboard.style.display = '';
            if (pageOccurrences) pageOccurrences.style.display = 'none';
        } else {
            if (pageDashboard) pageDashboard.style.display = 'none';
            if (pageOccurrences) pageOccurrences.style.display = '';
            fetchOccurrences();
        }
    }

    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            document.querySelectorAll('.nav-btn').forEach(n => n.classList.remove('active'));
            btn.classList.add('active');
            const t = btn.getAttribute('data-target');
            if (t === 'dashboard') showPage('dashboard');
            else showPage('list');
        });
    });

    // Render helpers
    function severityClass(sev){
        if(!sev) return 'severity-low';
        sev = String(sev).toLowerCase();
        if (sev.includes('crit')) return 'severity-critical';
        if (sev.includes('high') || sev.includes('alto')) return 'severity-high';
        if (sev.includes('med') || sev.includes('médio')) return 'severity-medium';
        return 'severity-low';
    }

    function renderOccurrences(items){
        if (!occurrencesGrid) return;
        occurrencesGrid.innerHTML = '';
        occurrencesCount.textContent = `${items.length} ocorrência(s) encontrada(s)`;
        if (!items || items.length === 0) {
            occurrencesGrid.innerHTML = '<div class="card">Nenhuma ocorrência encontrada.</div>';
            return;
        }
        const tpl = document.getElementById('occ-actions-tpl');
        items.forEach((it) => {
            const el = document.createElement('div');
            el.className = 'alert-card ' + severityClass(it.severity);
            el.innerHTML = `
                <div class="alert-header">
                    <div style="font-weight:700">${it.type || 'Sem título'}</div>
                    <div class="alert-time">${it.timestamp ? new Date(it.timestamp).toLocaleString() : ''}</div>
                </div>
                <div class="alert-description">${it.location || ''}</div>
                <div style="display:flex;justify-content:space-between;margin-top:8px">
                    <div class="alert-meta">#${it.id || ''} ${it.status ? '• ' + it.status : ''}</div>
                    <div class="alert-severity">${it.severity ? it.severity.toUpperCase() : ''}</div>
                </div>
            `;
            if (tpl) el.appendChild(tpl.content.cloneNode(true));
            el.querySelector('.view-btn')?.addEventListener('click', ev => { ev.stopPropagation(); openOccurrenceModal(it); });
            el.querySelector('.edit-btn')?.addEventListener('click', ev => { ev.stopPropagation(); const newType = prompt('Editar título', it.type||''); if(newType!==null){ it.type = newType; renderOccurrences(items); }});
            el.querySelector('.resolve-btn')?.addEventListener('click', ev => { ev.stopPropagation(); it.status = 'Resolvida'; renderOccurrences(items); });
            el.addEventListener('click', () => openOccurrenceModal(it));
            occurrencesGrid.appendChild(el);
        });
    }

    // Network operations
    async function fetchOccurrences(){
        if (!API) return;
        try {
            const r = await fetch(`${API}/occurrences`);
            if (!r.ok) { console.error('/occurrences status', r.status); return; }
            const body = await r.json();
            renderOccurrences(body.items || []);
        } catch (err) {
            console.error('Erro de rede ao buscar ocorrências', err);
        }
    }

    async function doUpload(file, statusEl){
        if (!file) { if (statusEl) statusEl.textContent = 'Selecione um ficheiro .xls/.xlsx'; return null; }
        const allowed = ['.xls', '.xlsx'];
        if (!allowed.some(ext => file.name.toLowerCase().endsWith(ext))) { if (statusEl) statusEl.textContent = 'Ficheiro inválido (.xls/.xlsx)'; return null; }
        if (!API) { if (statusEl) statusEl.textContent = 'Backend não encontrado.'; return null; }

        const fd = new FormData(); fd.append('file', file);
        if (statusEl) { statusEl.textContent = 'A carregar…'; statusEl.classList.add('loading'); }
        try {
            const r = await fetch(`${API}/upload`, { method: 'POST', body: fd });
            const body = await r.json().catch(()=>({}));
            if (!r.ok) {
                const errText = body.detail || body.message || r.statusText || `HTTP ${r.status}`;
                if (statusEl) statusEl.textContent = 'Erro: ' + errText;
                return { ok:false, error:errText };
            }
            if (statusEl) statusEl.textContent = `Carregado — ${body.count || 0} ocorrências`;
            return { ok:true, body };
        } catch (err) {
            const msg = err.message || 'Erro de rede';
            if (statusEl) statusEl.textContent = 'Erro de rede: ' + msg;
            console.error('upload error', err);
            return { ok:false, error: msg };
        } finally {
            if (statusEl) setTimeout(()=> { statusEl.textContent = ''; statusEl.classList.remove('loading'); }, 3000);
        }
    }

    // Bind upload form
    if (uploadFormOcc) {
        uploadFormOcc.addEventListener('submit', async (ev) => {
            ev.preventDefault();
            const file = fileInputOcc?.files?.[0];
            const res = await doUpload(file, uploadStatusOcc);
            if (res && res.ok) await fetchOccurrences();
        });
    }

    fileInputOcc?.addEventListener('change', (e) => {
        const f = e.target.files && e.target.files[0];
        if (selectedFileName) selectedFileName.textContent = f ? f.name : 'Nenhum ficheiro selecionado';
    });

    // Modal helpers
    const occModal = document.getElementById('occ-modal');
    const occDetail = document.getElementById('occ-detail');
    const occClose = document.getElementById('occ-close');

    function openOccurrenceModal(item){
        if (!occModal || !occDetail) return;
        occDetail.innerHTML = `<h3>${item.type || 'Sem título'}</h3>
            <p><strong>ID:</strong> ${item.id || '-'}</p>
            <p><strong>Local:</strong> ${item.location || '-'}</p>
            <p><strong>Status:</strong> ${item.status || '-'}</p>
            <p><strong>Severidade:</strong> ${item.severity || '-'}</p>
            <p><strong>Data:</strong> ${item.timestamp ? new Date(item.timestamp).toLocaleString() : '-'}</p>`;
        occModal.style.display = 'flex';
        occModal.setAttribute('aria-hidden', 'false');
    }

    occClose?.addEventListener('click', () => { occModal.style.display = 'none'; occModal.setAttribute('aria-hidden', 'true'); });
    occModal?.addEventListener('click', (ev) => { if (ev.target === occModal) { occModal.style.display = 'none'; occModal.setAttribute('aria-hidden', 'true'); } });

    // Start: detect API then show initial page
    (async () => {
        await detectApiBase();
        if (!API) {
            if (uploadStatusOcc) uploadStatusOcc.textContent = 'Backend não encontrado.';
        } else {
            fetchOccurrences();
        }
    })();

    showPage('dashboard');
    setInterval(() => { if (pageOccurrences && pageOccurrences.style.display !== 'none' && API) fetchOccurrences(); }, 10000);
});
