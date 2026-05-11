/**
 * LRU Cache for expensive data slices
 */
class LRUDataCache {
    constructor(limit = 50) {
        this.limit = limit;
        this.cache = new Map();
    }

    get(key) {
        if (!this.cache.has(key)) return null;
        const value = this.cache.get(key);
        this.cache.delete(key);
        this.cache.set(key, value);
        return value;
    }

    set(key, value) {
        if (this.cache.has(key)) this.cache.delete(key);
        else if (this.cache.size >= this.limit) {
            // Prune oldest (first in Map)
            const oldestKey = this.cache.keys().next().value;
            this.cache.delete(oldestKey);
        }
        this.cache.set(key, value);
    }
}

/**
 * Persists app state to localStorage
 */
class StatePersistence {
    constructor(key = 'era5_dashboard_state') {
        this.key = key;
    }

    save(state) {
        try {
            localStorage.setItem(this.key, JSON.stringify(state));
        } catch (e) { console.error('Persistence failed', e); }
    }

    load() {
        try {
            const saved = localStorage.getItem(this.key);
            return saved ? JSON.parse(saved) : null;
        } catch (e) { return null; }
    }
}

class Era5Viewer {
    constructor() {
        this.map = null;
        this.dataLayer = null;
        this.currentData = null;
        this.currentMetadata = null;
        
        this.selectedFile = null;
        this.selectedVariable = null;
        this.granularity = 'original';
        this.startDate = '';
        this.endDate = '';
        this.currentTimeIdx = 0;
        
        this.isPlaying = false;
        this.playInterval = null;
        this.fps = 5;

        this.cache = new LRUDataCache();
        this.persistence = new StatePersistence();

        this.initMap();
        this.initEventListeners();
        this.startSequence();
        
        setTimeout(() => this.map.invalidateSize(), 500);
    }

    async startSequence() {
        await this.loadLayers();
        this.restoreState();
    }

    initMap() {
        this.map = L.map('map', { 
            zoomControl: false,
            zoomSnap: 0.1,      // Unlock fractional zoom
            zoomDelta: 0.1,     // Smooth increment
            wheelPxPerZoomLevel: 120, // Lower sensitivity
            zoomAnimation: true
        }).setView([23.5, -98.0], 8);
        
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(this.map);
        L.control.zoom({ position: 'topright' }).addTo(this.map);
    }

    saveCurrentState() {
        this.persistence.save({
            selectedFile: this.selectedFile,
            selectedVariable: this.selectedVariable,
            granularity: this.granularity,
            startDate: this.startDate,
            endDate: this.endDate,
            currentTimeIdx: this.currentTimeIdx
        });
    }

    async restoreState() {
        const saved = this.persistence.load();
        if (!saved) return;

        if (saved.selectedFile) {
            this.granularity = saved.granularity || 'original';
            this.startDate = saved.startDate || '';
            this.endDate = saved.endDate || '';
            this.currentTimeIdx = saved.currentTimeIdx || 0;
            
            document.getElementById('dataset-select').value = saved.selectedFile;
            document.getElementById('granularity-select').value = this.granularity;
            document.getElementById('start-date').value = this.startDate;
            document.getElementById('end-date').value = this.endDate;

            // Trigger file load sequence
            await this.onFileChange(saved.selectedFile, saved.selectedVariable);
            
            // Set slider and time after metadata loads
            if (this.currentMetadata) {
                this.currentTimeIdx = Math.min(saved.currentTimeIdx, this.currentMetadata.times.length - 1);
                document.getElementById('time-slider').value = this.currentTimeIdx;
                this.updateTimeDisplay();
                this.fetchData();
            }
        }
    }

    showError(msg) {
        console.error(msg);
        const container = document.getElementById('analytics-content');
        if (container) {
            container.innerHTML = `<div class="placeholder" style="color: #ef4444; padding: 20px; border: 1px solid #ef4444; border-radius: 8px;">
                <strong>Data Access Error</strong><br>${msg}
            </div>`;
        }
    }

    initEventListeners() {
        document.getElementById('dataset-select').addEventListener('change', (e) => this.onFileChange(e.target.value));
        document.getElementById('variable-select').addEventListener('change', (e) => this.onVariableChange(e.target.value));
        document.getElementById('granularity-select').addEventListener('change', (e) => this.onFilterUpdate('granularity', e.target.value));
        document.getElementById('start-date').addEventListener('change', (e) => this.onFilterUpdate('start', e.target.value));
        document.getElementById('end-date').addEventListener('change', (e) => this.onFilterUpdate('end', e.target.value));
        document.getElementById('time-slider').addEventListener('input', (e) => this.onTimeSliderChange(parseInt(e.target.value)));
        
        document.getElementById('generate-btn').addEventListener('click', () => this.onGenerateClick());
        
        document.getElementById('play-btn').addEventListener('click', () => this.togglePlayback());
        document.getElementById('stop-btn').addEventListener('click', () => this.stopPlayback());
        document.getElementById('fps-select').addEventListener('change', (e) => {
            this.fps = parseInt(e.target.value);
            if (this.isPlaying) { this.stopPlayback(); this.startPlayback(); }
        });
    }

    async loadLayers() {
        try {
            const resp = await fetch('/api/layers');
            if (!resp.ok) throw new Error('Failed to load dataset list.');
            const layers = await resp.json();
            const select = document.getElementById('dataset-select');
            layers.forEach(l => {
                const opt = document.createElement('option');
                opt.value = l.id; opt.textContent = l.name;
                select.appendChild(opt);
            });
        } catch (err) { this.showError(err.message); }
    }

    async onFileChange(fileId, restoreVariable = null) {
        this.stopPlayback();
        const previousVariable = restoreVariable || this.selectedVariable;
        this.selectedFile = fileId;
        const varSelect = document.getElementById('variable-select');
        varSelect.innerHTML = '<option value="">Select Variable...</option>';
        varSelect.disabled = true;
        document.getElementById('generate-btn').disabled = true;

        if (!fileId) return;

        try {
            const params = new URLSearchParams({ granularity: this.granularity, start: this.startDate, end: this.endDate });
            const resp = await fetch(`/api/metadata/${fileId}?${params.toString()}`);
            if (!resp.ok) throw new Error('Failed to load metadata.');
            
            this.currentMetadata = await resp.json();
            Object.entries(this.currentMetadata.variables).forEach(([val, info]) => {
                const opt = document.createElement('option');
                opt.value = val; opt.textContent = info.label;
                varSelect.appendChild(opt);
            });
            varSelect.disabled = false;

            if (!this.startDate) {
                this.startDate = this.currentMetadata.range.start;
                document.getElementById('start-date').value = this.startDate;
            }
            if (!this.endDate) {
                this.endDate = this.currentMetadata.range.end;
                document.getElementById('end-date').value = this.endDate;
            }

            if (previousVariable && this.currentMetadata.variables[previousVariable]) {
                varSelect.value = previousVariable;
                this.selectedVariable = previousVariable;
                document.getElementById('variable-description').textContent = this.currentMetadata.variables[previousVariable].description;
                document.getElementById('generate-btn').disabled = false;
            } else {
                this.selectedVariable = null;
            }

            const slider = document.getElementById('time-slider');
            const total = this.currentMetadata.times.length;
            slider.max = Math.max(0, total - 1);
            slider.disabled = total === 0;

            if (this.currentTimeIdx >= total) {
                this.currentTimeIdx = Math.max(0, total - 1);
            }
            slider.value = this.currentTimeIdx;
            
            document.getElementById('step-counter').textContent = `${this.currentTimeIdx + 1} / ${total}`;
            this.updateTimeDisplay();
            this.saveCurrentState();
        } catch (err) { this.showError(err.message); this.currentMetadata = null; }
    }

    onVariableChange(variable) {
        this.stopPlayback();
        this.selectedVariable = variable;
        document.getElementById('generate-btn').disabled = !variable;
        this.saveCurrentState();
        if (variable && this.currentMetadata) {
            const desc = this.currentMetadata.variables[variable].description;
            document.getElementById('variable-description').textContent = desc;
            document.getElementById('variable-brief').textContent = desc;
        } else {
            this.clearLayer(); this.clearStats();
            document.getElementById('variable-brief').textContent = "";
        }
    }

    onFilterUpdate(type, val) {
        this.stopPlayback();
        if (type === 'granularity') this.granularity = val;
        else if (type === 'start') this.startDate = val;
        else if (type === 'end') this.endDate = val;
        
        this.saveCurrentState();
    }


    async onGenerateClick() {
        this.stopPlayback();
        if (this.selectedFile) {
            await this.onFileChange(this.selectedFile, this.selectedVariable);
            if (this.selectedVariable) {
                this.fetchData();
                this.fetchAnalytics();
                this.fetchTimelineData();
            }
        }
    }

    async fetchTimelineData() {
        if (!this.selectedFile || !this.selectedVariable) return;
        try {
            const params = new URLSearchParams({ granularity: this.granularity, start: this.startDate, end: this.endDate });
            const resp = await fetch(`/api/timeline/${this.selectedFile}/${this.selectedVariable}?${params.toString()}`);
            if (!resp.ok) return;
            const data = await resp.json();
            this.drawWaveform(data.means);
            this.timelineData = data;
        } catch (err) { console.error('Timeline fetch failed', err); }
    }

    drawWaveform(means) {
        const canvas = document.getElementById('timeline-canvas');
        if (!canvas || !means.length) return;
        const ctx = canvas.getContext('2d');
        const w = canvas.width = canvas.offsetWidth;
        const h = canvas.height = canvas.offsetHeight;
        
        ctx.clearRect(0, 0, w, h);
        
        // Draw Ticks (Data markers)
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)';
        ctx.lineWidth = 1;
        const step = w / (means.length - 1);
        for (let i = 0; i < means.length; i += Math.max(1, Math.floor(means.length / 50))) {
            ctx.beginPath();
            ctx.moveTo(i * step, 0);
            ctx.lineTo(i * step, h);
            ctx.stroke();
        }

        // Draw Waveform
        ctx.beginPath();
        ctx.moveTo(0, h);
        for (let i = 0; i < means.length; i++) {
            const x = i * step;
            const y = h - (means[i] * h * 0.8) - (h * 0.1);
            ctx.lineTo(x, y);
        }
        ctx.lineTo(w, h);
        ctx.closePath();
        
        const grad = ctx.createLinearGradient(0, 0, 0, h);
        grad.addColorStop(0, '#38bdf8');
        grad.addColorStop(1, 'rgba(56, 189, 248, 0)');
        ctx.fillStyle = grad;
        ctx.fill();
        
        ctx.strokeStyle = '#38bdf8';
        ctx.lineWidth = 2;
        ctx.stroke();
    }

    onTimeSliderChange(idx) { 
        this.currentTimeIdx = idx; 
        this.saveCurrentState(); 
        this.updateTimeDisplay(); 
        this.fetchData(); 
        
        if (this.timelineData && this.timelineData.actual_means) {
            const val = this.timelineData.actual_means[idx];
            document.getElementById('timeline-stat').textContent = `Mean: ${this.formatValue(val)} ${this.timelineData.units}`;
        }
    }

    updateTimeDisplay() {
        if (!this.currentMetadata?.times?.length) return;
        let timeStr = this.currentMetadata.times[this.currentTimeIdx];
        const date = new Date(timeStr);
        if (this.granularity === 'yearly') timeStr = date.getFullYear();
        else if (this.granularity === 'monthly') timeStr = date.toLocaleString('default', { month: 'long', year: 'numeric' });
        else if (this.granularity === 'daily') timeStr = date.toLocaleDateString();
        
        document.getElementById('current-time').textContent = timeStr;
        document.getElementById('step-counter').textContent = `${this.currentTimeIdx + 1} / ${this.currentMetadata.times.length}`;
    }

    async fetchData() {
        if (!this.selectedFile || !this.selectedVariable) return;
        
        const cacheKey = `data_${this.selectedFile}_${this.selectedVariable}_${this.currentTimeIdx}_${this.granularity}`;
        const cached = this.cache.get(cacheKey);
        if (cached) {
            this.currentData = cached;
            this.renderData(); this.updateStats();
            return;
        }

        try {
            const params = new URLSearchParams({ granularity: this.granularity, start: this.startDate, end: this.endDate });
            const resp = await fetch(`/api/data/${this.selectedFile}/${this.selectedVariable}/${this.currentTimeIdx}?${params.toString()}`);
            if (!resp.ok) throw new Error('Data fetch failed.');
            this.currentData = await resp.json();
            this.cache.set(cacheKey, this.currentData);
            this.renderData(); this.updateStats();
        } catch (err) { this.showError(err.message); }
    }

    renderData() {
        if (!this.currentData || !this.currentMetadata || !this.selectedVariable) return;
        this.clearLayer();
        const { data, units } = this.currentData;
        const variableInfo = this.currentMetadata.variables[this.selectedVariable];
        const { min, max } = variableInfo;
        const b = this.currentMetadata.bounds;
        const shape = this.currentMetadata.shape;
        const latStep = (b.lat[1] - b.lat[0]) / (shape.lat - 1);
        const lonStep = (b.lon[1] - b.lon[0]) / (shape.lon - 1);
        const layerGroup = L.layerGroup();
        for (let i = 0; i < shape.lat; i++) {
            for (let j = 0; j < shape.lon; j++) {
                const val = data[i][j]; if (val === null) continue;
                const lat = b.lat[1] - (i * latStep);
                const lon = b.lon[0] + (j * lonStep);
                L.rectangle([[lat - latStep/2, lon - lonStep/2], [lat + latStep/2, lon + lonStep/2]], {
                    color: 'transparent', fillColor: this.getColor(val, min, max), fillOpacity: 0.7, weight: 0
                }).bindPopup(`Value: ${this.formatValue(val)} ${units}`).addTo(layerGroup);
            }
        }
        this.dataLayer = layerGroup; this.dataLayer.addTo(this.map);
        this.updateLegend(min, max, units);
    }

    formatUnits(u) { return u ? u.replace(/\*\*(-?\d+)/g, '<sup>$1</sup>') : ''; }
    formatValue(v) { if (v === null || v === undefined) return '--'; return Math.abs(v) < 0.001 ? v.toExponential(3) : v.toFixed(3); }

    getColor(val, min, max) {
        const r = (max === min) ? 0.5 : (val - min) / (max - min);
        if (this.selectedVariable === 't2m') { const hue = (1 - r) * 240; return `hsl(${hue}, 80%, 50%)`; }
        const colors = [[203,51,77],[233,92,71],[249,142,82],[253,191,111],[254,229,147],[255,255,190],[234,247,158],[191,229,160],[134,207,165],[84,174,173],[58,126,184]];
        const i = Math.min(Math.floor(r * 10), 9);
        const [r1,g1,b1] = colors[i]; const [r2,g2,b2] = colors[i+1];
        const sub = (r * 10) - i; return `rgb(${Math.floor(r1+(r2-r1)*sub)},${Math.floor(g1+(g2-g1)*sub)},${Math.floor(b1+(b2-b1)*sub)})`;
    }

    updateLegend(min, max, units) {
        const legend = document.getElementById('legend');
        const grad = this.selectedVariable === 't2m' ? 'linear-gradient(to right, hsl(240, 80%, 50%), hsl(0, 80%, 50%))' : 'linear-gradient(to right, #cb334d, #ffffbe, #3a7eb8)';
        legend.innerHTML = `<div style="font-weight:700;font-size:0.8rem;">${this.currentMetadata.variables[this.selectedVariable].label}</div>
            <div style="font-size:0.7rem;color:#94a3b8;">Units: ${this.formatUnits(units)}</div>
            <div style="display:flex;align-items:center;gap:10px;margin-top:5px;">
                <span>${this.formatValue(min)}</span>
                <div style="flex:1;height:8px;background:${grad};border-radius:4px;"></div>
                <span>${this.formatValue(max)}</span>
            </div>`;
    }

    updateStats() {
        if (!this.currentMetadata || !this.selectedVariable || !this.currentData) return;
        const info = this.currentMetadata.variables[this.selectedVariable];
        const flat = this.currentData.data.flat().filter(v => v !== null);
        const mean = flat.length ? flat.reduce((a, b) => a + b, 0) / flat.length : 0;
        document.getElementById('global-range-val').innerHTML = `${this.formatValue(info.min)} to ${this.formatValue(info.max)} <small>${this.formatUnits(info.units)}</small>`;
        document.getElementById('step-mean-val').innerHTML = `${this.formatValue(mean)} <small>${this.formatUnits(info.units)}</small>`;
        document.getElementById('step-range-val').innerHTML = `${this.formatValue(this.currentData.min)} to ${this.formatValue(this.currentData.max)} <small>${this.formatUnits(info.units)}</small>`;
    }

    clearStats() { document.querySelectorAll('.f-stat span').forEach(s => s.innerHTML = '--'); document.getElementById('legend').innerHTML = ''; }

    async fetchAnalytics() {
        const key = `analytics_${this.selectedFile}_${this.selectedVariable}_${this.granularity}_${this.startDate}_${this.endDate}`;
        const cached = this.cache.get(key);
        const container = document.getElementById('analytics-content');
        if (cached) { container.innerHTML = `<img src="${cached}" alt="Plot">`; return; }

        container.innerHTML = '<div class="loader"><div class="spinner"></div><p>Calculating Analytics...</p></div>';
        try {
            const params = new URLSearchParams({ granularity: this.granularity, start: this.startDate, end: this.endDate });
            const resp = await fetch(`/api/analytics/${this.selectedFile}/${this.selectedVariable}?${params.toString()}`);
            if (!resp.ok) throw new Error('Analytics failed.');
            const blob = await resp.blob();
            const url = URL.createObjectURL(blob);
            this.cache.set(key, url);
            container.innerHTML = `<img src="${url}" alt="Plot">`;
        } catch (err) { container.innerHTML = `<p class="placeholder">Analytics Error: ${err.message}</p>`; }
    }

    clearLayer() { if (this.dataLayer) { this.map.removeLayer(this.dataLayer); this.dataLayer = null; } }

    togglePlayback() {
        if (this.isPlaying) this.stopPlayback();
        else this.startPlayback();
    }

    startPlayback() {
        if (!this.currentMetadata || this.currentMetadata.times.length === 0) return;
        this.isPlaying = true;
        
        const playBtn = document.getElementById('play-btn');
        const icon = playBtn.querySelector('i');
        icon.className = 'fas fa-pause';
        playBtn.classList.add('active');
        document.getElementById('stop-btn').disabled = false;
        
        if (this.playInterval) clearInterval(this.playInterval);
        
        let isFetching = false;
        this.playInterval = setInterval(async () => {
            if (isFetching) return;
            
            const total = this.currentMetadata.times.length;
            this.currentTimeIdx = (this.currentTimeIdx + 1) % total;
            
            const slider = document.getElementById('time-slider');
            slider.value = this.currentTimeIdx;
            
            this.updateTimeDisplay();
            
            if (this.timelineData && this.timelineData.actual_means) {
                const val = this.timelineData.actual_means[this.currentTimeIdx];
                document.getElementById('timeline-stat').textContent = `Mean: ${this.formatValue(val)} ${this.timelineData.units}`;
            }

            isFetching = true;
            try { await this.fetchData(); } finally { isFetching = false; }
        }, 1000 / this.fps);
    }

    stopPlayback() {
        this.isPlaying = false;
        if (this.playInterval) {
            clearInterval(this.playInterval);
            this.playInterval = null;
        }
        
        const playBtn = document.getElementById('play-btn');
        const icon = playBtn.querySelector('i');
        icon.className = 'fas fa-play';
        playBtn.classList.remove('active');
        playBtn.disabled = false;
        
        document.getElementById('stop-btn').disabled = true;
        this.saveCurrentState();
    }
}
window.addEventListener('load', () => { window._viewer = new Era5Viewer(); });
