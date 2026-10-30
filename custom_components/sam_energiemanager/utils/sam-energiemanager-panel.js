/**
 * Energiemanager Custom Sidebar Panel (Web Component)
 * Native Shadow DOM Web Component architecture for Home Assistant.
 */

const _CSS = `
:host {
  display: block;
  height: calc(100dvh - var(--safe-area-inset-top, 0px) - var(--safe-area-inset-bottom, 0px));
  overflow: hidden;
  background: var(--primary-background-color, #111318);
  color: var(--primary-text-color, #e2e8f0);
  font-family: var(--paper-font-body1_-_font-family, Roboto, system-ui, -apple-system, sans-serif);
  --em-radius-sm: 6px;
  --em-radius-md: 10px;
  --em-radius-lg: 14px;
  --em-solar: #f59e0b;
  --em-grid-export: #10b981;
  --em-grid-import: #ef4444;
  --em-battery: #3b82f6;
  --em-ac: #06b6d4;
  --em-ev: #8b5cf6;
}
.em-root {
  height: 100%;
  display: flex;
  flex-direction: column;
}
.em-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 24px;
  background: var(--app-header-background-color, var(--primary-color, #0284c7));
  color: var(--app-header-text-color, #ffffff);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25);
  z-index: 20;
  flex-shrink: 0;
}
.em-burger {
  display: none;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  color: inherit;
  cursor: pointer;
  padding: 6px;
  margin-left: -6px;
  border-radius: var(--em-radius-sm);
}
.em-burger:hover {
  background: rgba(255, 255, 255, 0.16);
}
@media (max-width: 870px) {
  .em-burger { display: inline-flex; }
}
.em-burger.em-burger--force {
  display: inline-flex;
}
.em-logo {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border-radius: 9px;
  background: rgba(255, 255, 255, 0.18);
  flex-shrink: 0;
}
.em-header h1 {
  margin: 0;
  font-size: 1.22em;
  font-weight: 600;
  letter-spacing: 0.01em;
}
.em-sub {
  font-size: 0.74em;
  opacity: 0.8;
  margin-top: 2px;
}
.em-hdr-badge {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 5px 13px;
  border-radius: 20px;
  font-size: 0.8em;
  font-weight: 600;
  background: rgba(255, 255, 255, 0.18);
  color: inherit;
  white-space: nowrap;
}
.em-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: currentColor;
  flex-shrink: 0;
}
.em-pulse {
  animation: em-pulse-kf 1.5s ease-in-out infinite;
}
@keyframes em-pulse-kf {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.35; transform: scale(0.9); }
}
.em-icon-btn {
  background: rgba(255, 255, 255, 0.12);
  border: none;
  color: inherit;
  cursor: pointer;
  padding: 7px 12px;
  border-radius: var(--em-radius-sm);
  font-size: 0.8em;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  transition: background 0.15s;
}
.em-icon-btn:hover {
  background: rgba(255, 255, 255, 0.24);
}
.em-main {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
}
.em-body {
  max-width: 1180px;
  margin: 0 auto;
  padding: 20px 18px 64px;
}
.em-nav {
  position: sticky;
  top: 0;
  z-index: 15;
  background: var(--primary-background-color, #111318);
  margin: -20px -18px 20px;
  padding: 16px 18px 0;
  border-bottom: 1px solid var(--divider-color, rgba(127, 127, 127, 0.2));
}
.em-tabs {
  display: flex;
  gap: 4px;
  overflow-x: auto;
}
.em-tab {
  padding: 10px 20px;
  border: none;
  background: transparent;
  color: var(--secondary-text-color, #94a3b8);
  font-size: 0.82em;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  cursor: pointer;
  border-bottom: 2.5px solid transparent;
  transition: color 0.15s, border-color 0.15s;
  white-space: nowrap;
}
.em-tab:hover {
  color: var(--primary-text-color);
}
.em-tab.active {
  color: var(--primary-color, #0ea5e9);
  border-bottom-color: var(--primary-color, #0ea5e9);
}
.em-card {
  background: var(--card-background-color, #1e222b);
  border-radius: var(--em-radius-lg);
  padding: 20px 22px;
  margin-bottom: 16px;
  box-shadow: var(--ha-card-box-shadow, 0 2px 8px rgba(0, 0, 0, 0.12));
  border: 1px solid var(--divider-color, rgba(127, 127, 127, 0.12));
}
.em-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 16px;
}
.em-card-title {
  margin: 0;
  font-size: 0.76em;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--secondary-text-color, #94a3b8);
  display: flex;
  align-items: center;
  gap: 8px;
}
.em-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(175px, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}
.em-stat {
  background: var(--secondary-background-color, rgba(127, 127, 127, 0.08));
  border-radius: var(--em-radius-md);
  padding: 15px 14px;
  border: 1px solid var(--divider-color, rgba(127, 127, 127, 0.12));
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.em-stat-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 0.74em;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--secondary-text-color);
}
.em-stat-val {
  font-size: 1.6em;
  font-weight: 700;
  line-height: 1.15;
  font-variant-numeric: tabular-nums;
}
.em-stat-sub {
  font-size: 0.76em;
  color: var(--secondary-text-color);
}
.em-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 11px;
  border-radius: 999px;
  font-size: 0.75em;
  font-weight: 600;
}
.em-badge-ok {
  color: #10b981;
  background: rgba(16, 185, 129, 0.14);
}
.em-badge-warn {
  color: #f59e0b;
  background: rgba(245, 158, 11, 0.15);
}
.em-badge-err {
  color: #ef4444;
  background: rgba(239, 68, 68, 0.15);
}
.em-badge-info {
  color: #3b82f6;
  background: rgba(59, 130, 246, 0.15);
}
.em-badge-muted {
  color: var(--secondary-text-color);
  background: var(--secondary-background-color);
}
.em-select {
  background: var(--card-background-color, #1e222b);
  color: var(--primary-text-color);
  border: 1px solid var(--divider-color, rgba(127, 127, 127, 0.25));
  border-radius: var(--em-radius-md);
  padding: 6px 10px;
  font-size: 0.82em;
  font-weight: 600;
  cursor: pointer;
  outline: none;
}
.em-select:focus {
  border-color: var(--primary-color, #0ea5e9);
}

/* Live Energy Flow Diagram */
.em-flow-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0;
}
.em-flow-sources {
  display: grid;
  grid-template-columns: repeat(2, minmax(200px, 340px));
  justify-content: center;
  gap: 28px;
  width: 100%;
}
.em-flow-node {
  background: var(--secondary-background-color, rgba(127, 127, 127, 0.08));
  border-radius: var(--em-radius-md);
  padding: 15px 16px;
  border: 1.5px solid var(--divider-color, rgba(127, 127, 127, 0.16));
  display: flex;
  flex-direction: column;
  gap: 8px;
  position: relative;
  transition: border-color 0.25s, box-shadow 0.25s;
}
.em-flow-node.active-solar {
  border-color: var(--em-solar);
  box-shadow: 0 0 18px rgba(245, 158, 11, 0.12);
}
.em-flow-node.active-export {
  border-color: var(--em-grid-export);
}
.em-flow-node.active-import {
  border-color: var(--em-grid-import);
}
.em-flow-node.active-battery {
  border-color: var(--em-battery);
  box-shadow: 0 0 16px rgba(59, 130, 246, 0.12);
}
.em-flow-node.locked-battery {
  border-color: #f59e0b;
}
.em-flow-node.active-ac {
  border-color: var(--em-ac);
  box-shadow: 0 0 16px rgba(6, 182, 212, 0.12);
}
.em-flow-node.active-dhw {
  border-color: #f97316;
  box-shadow: 0 0 16px rgba(249, 115, 22, 0.14);
}
.em-flow-node.active-ev {
  border-color: var(--em-ev);
  box-shadow: 0 0 18px rgba(139, 92, 246, 0.16);
}
.em-flow-svg {
  width: 100%;
  max-width: 820px;
  height: 52px;
  display: block;
  overflow: visible;
}
.em-flow-line-bg {
  fill: none;
  stroke: var(--divider-color, rgba(127, 127, 127, 0.25));
  stroke-width: 2.5;
  stroke-linecap: round;
}
.em-flow-line-anim {
  fill: none;
  stroke-width: 3;
  stroke-linecap: round;
  stroke-dasharray: 7 9;
  animation: em-dash-flow 1.1s linear infinite;
}
.em-flow-line-rev {
  animation-direction: reverse;
}
@keyframes em-dash-flow {
  from { stroke-dashoffset: 32; }
  to { stroke-dashoffset: 0; }
}
.em-flow-hub {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 10px 22px;
  border-radius: 999px;
  background: var(--card-background-color, #1e222b);
  border: 2px solid var(--primary-color, #0ea5e9);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
  font-size: 0.86em;
  font-weight: 600;
  flex-wrap: wrap;
  z-index: 2;
}
.em-flow-consumers {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  width: 100%;
}
.em-node-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.em-node-title {
  font-weight: 700;
  font-size: 0.88em;
  display: flex;
  align-items: center;
  gap: 7px;
}
.em-prio-tag {
  font-size: 0.7em;
  font-weight: 700;
  padding: 2px 7px;
  border-radius: 999px;
  background: var(--card-background-color);
  color: var(--secondary-text-color);
  border: 1px solid var(--divider-color);
}
.em-node-body {
  display: flex;
  align-items: center;
  gap: 14px;
}
.em-ring-wrap {
  position: relative;
  width: 64px;
  height: 64px;
  flex-shrink: 0;
}
.em-ring-svg {
  width: 64px;
  height: 64px;
  transform: rotate(-90deg);
}
.em-ring-bg {
  fill: none;
  stroke: var(--card-background-color, rgba(0, 0, 0, 0.25));
  stroke-width: 6;
}
.em-ring-fg {
  fill: none;
  stroke-width: 6;
  stroke-linecap: round;
  transition: stroke-dashoffset 0.4s ease;
}
.em-ring-lbl {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.85em;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}
.em-node-metrics {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
  flex: 1;
}
.em-node-big {
  font-size: 1.32em;
  font-weight: 700;
  line-height: 1.15;
  font-variant-numeric: tabular-nums;
}
.em-node-sub {
  font-size: 0.78em;
  color: var(--secondary-text-color);
  line-height: 1.35;
}
.em-node-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: auto;
  padding-top: 4px;
}
.em-pill {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 8px;
  border-radius: 6px;
  font-size: 0.73em;
  font-weight: 600;
  background: var(--card-background-color);
  color: var(--secondary-text-color);
  border: 1px solid var(--divider-color, rgba(127, 127, 127, 0.15));
}
.em-pill.ok {
  color: #10b981;
  border-color: rgba(16, 185, 129, 0.3);
  background: rgba(16, 185, 129, 0.1);
}
.em-pill.warn {
  color: #f59e0b;
  border-color: rgba(245, 158, 11, 0.35);
  background: rgba(245, 158, 11, 0.1);
}
.em-pill.info {
  color: #06b6d4;
  border-color: rgba(6, 182, 212, 0.35);
  background: rgba(6, 182, 212, 0.1);
}
.em-pill.ev {
  color: #a78bfa;
  border-color: rgba(139, 92, 246, 0.35);
  background: rgba(139, 92, 246, 0.12);
}

/* Segmented Mode Picker */
.em-seg {
  display: inline-flex;
  background: var(--secondary-background-color);
  padding: 4px;
  border-radius: var(--em-radius-md);
  border: 1px solid var(--divider-color);
  gap: 4px;
  flex-wrap: wrap;
}
.em-seg-btn {
  border: none;
  background: transparent;
  color: var(--secondary-text-color);
  font-size: 0.85em;
  font-weight: 600;
  padding: 8px 16px;
  border-radius: 7px;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}
.em-seg-btn:hover {
  color: var(--primary-text-color);
}
.em-seg-btn.active {
  background: var(--primary-color, #0ea5e9);
  color: #ffffff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.2);
}

/* Controls & Sliders Grid */
.em-ctrl-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 14px;
  margin-top: 14px;
}
.em-ctrl-box {
  background: var(--secondary-background-color);
  border-radius: var(--em-radius-md);
  padding: 14px 16px;
  border: 1px solid var(--divider-color, rgba(127, 127, 127, 0.12));
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.em-ctrl-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.em-ctrl-lbl {
  font-size: 0.82em;
  font-weight: 600;
  color: var(--primary-text-color);
  display: flex;
  align-items: center;
  gap: 6px;
}
.em-ctrl-readout {
  font-size: 0.95em;
  font-weight: 700;
  color: var(--primary-color, #0ea5e9);
  font-variant-numeric: tabular-nums;
}
.em-slider-row {
  display: flex;
  align-items: center;
  gap: 10px;
}
.em-slider-row input[type="range"] {
  flex: 1;
  accent-color: var(--primary-color, #0ea5e9);
  cursor: pointer;
}
.em-num-input {
  width: 78px;
  padding: 6px 8px;
  border-radius: var(--em-radius-sm);
  border: 1px solid var(--divider-color);
  background: var(--card-background-color);
  color: var(--primary-text-color);
  font-size: 0.88em;
  font-weight: 600;
  text-align: right;
  font-variant-numeric: tabular-nums;
}
.em-hint {
  font-size: 0.75em;
  color: var(--secondary-text-color);
  line-height: 1.4;
}

/* Switch toggle */
.em-switch-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.em-switch {
  position: relative;
  display: inline-flex;
  width: 44px;
  height: 24px;
  flex-shrink: 0;
  cursor: pointer;
}
.em-switch input {
  opacity: 0;
  width: 0;
  height: 0;
  position: absolute;
}
.em-switch-track {
  position: absolute;
  inset: 0;
  border-radius: 24px;
  background: var(--switch-unchecked-track-color, rgba(127, 127, 127, 0.45));
  transition: background 0.2s;
}
.em-switch-track::before {
  content: "";
  position: absolute;
  width: 18px;
  height: 18px;
  left: 3px;
  top: 3px;
  border-radius: 50%;
  background: #ffffff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
  transition: transform 0.2s;
}
.em-switch input:checked + .em-switch-track {
  background: var(--primary-color, #0ea5e9);
}
.em-switch input:checked + .em-switch-track::before {
  transform: translateX(20px);
}

/* Buttons */
.em-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px 15px;
  border-radius: var(--em-radius-sm);
  border: 1px solid var(--divider-color);
  background: var(--secondary-background-color);
  color: var(--primary-text-color);
  font-size: 0.83em;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
}
.em-btn:hover {
  border-color: var(--primary-color, #0ea5e9);
  color: var(--primary-color, #0ea5e9);
}
.em-btn-primary {
  background: var(--primary-color, #0ea5e9);
  color: #fff;
  border-color: var(--primary-color, #0ea5e9);
}
.em-btn-primary:hover {
  opacity: 0.9;
  color: #fff;
}

/* Split bar for Solar vs Grid */
.em-split-bar {
  height: 12px;
  border-radius: 999px;
  background: var(--card-background-color);
  overflow: hidden;
  display: flex;
  margin: 8px 0 5px;
}
.em-split-solar {
  background: linear-gradient(90deg, #f59e0b, #10b981);
  height: 100%;
  transition: width 0.4s ease;
}
.em-split-grid {
  background: #ef4444;
  height: 100%;
  transition: width 0.4s ease;
}
.em-split-legend {
  display: flex;
  justify-content: space-between;
  font-size: 0.78em;
  color: var(--secondary-text-color);
  flex-wrap: wrap;
  gap: 8px;
}

/* Table */
.em-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.86em;
}
.em-table th {
  text-align: left;
  padding: 8px 10px;
  color: var(--secondary-text-color);
  font-size: 0.74em;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  border-bottom: 1px solid var(--divider-color);
}
.em-table td {
  padding: 10px;
  border-bottom: 1px solid var(--divider-color, rgba(127, 127, 127, 0.08));
}
.em-table tr:last-child td {
  border-bottom: none;
}

/* Toast */
.em-toast {
  position: fixed;
  bottom: 22px;
  right: 22px;
  z-index: 90;
  padding: 10px 18px;
  border-radius: var(--em-radius-md);
  background: var(--primary-color, #0284c7);
  color: #fff;
  font-size: 0.86em;
  font-weight: 600;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.35);
}

/* Action Traces */
.em-trace-timeline {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.em-trace-item {
  background: var(--card-background-color, rgba(127, 127, 127, 0.05));
  border: 1px solid var(--divider-color, rgba(127, 127, 127, 0.12));
  border-radius: var(--em-radius-md);
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  transition: background 0.15s ease;
}
.em-trace-item:hover {
  background: var(--secondary-background-color, rgba(127, 127, 127, 0.1));
}
.em-trace-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  flex-wrap: wrap;
}
.em-trace-cat {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 3px 9px;
  border-radius: 999px;
  font-size: 0.72em;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.em-trace-cat-ev { color: #a78bfa; background: rgba(139, 92, 246, 0.18); }
.em-trace-cat-dhw { color: #2dd4bf; background: rgba(20, 184, 166, 0.18); }
.em-trace-cat-ac { color: #22d3ee; background: rgba(6, 182, 212, 0.18); }
.em-trace-cat-battery { color: #60a5fa; background: rgba(59, 130, 246, 0.18); }
.em-trace-cat-system { color: #94a3b8; background: rgba(148, 163, 184, 0.18); }
.em-trace-time {
  font-size: 0.78em;
  font-family: monospace;
  color: var(--secondary-text-color);
}
.em-trace-body {
  font-size: 0.95em;
  font-weight: 600;
  color: var(--primary-text-color);
}
.em-trace-reason {
  font-size: 0.83em;
  color: var(--secondary-text-color);
  background: rgba(0, 0, 0, 0.16);
  padding: 6px 10px;
  border-radius: var(--em-radius-sm);
  border-left: 3px solid var(--primary-color, #0284c7);
}
.em-trace-target {
  font-size: 0.76em;
  color: var(--secondary-text-color);
  font-family: monospace;
  opacity: 0.85;
}
.em-empty-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 48px 20px;
}

@media (max-width: 1020px) {
  .em-flow-consumers { grid-template-columns: repeat(2, 1fr); }
  .em-flow-svg { display: none; }
  .em-flow-hub { margin: 10px 0; }
}
@media (max-width: 860px) {
  .em-flow-consumers { grid-template-columns: 1fr; }
  .em-flow-sources { grid-template-columns: 1fr; gap: 12px; }
}
@media (max-width: 680px) {
  .em-header { padding: 12px 14px; }
  .em-body { padding: 14px 10px 64px; }
  .em-nav { margin: -14px -10px 14px; padding: 12px 10px 0; }
  .em-card { padding: 15px; }
  .em-stats { grid-template-columns: repeat(2, 1fr); }
}
`;

function _esc(s) {
  return String(s == null ? '' : s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function _fmtNum(v, dec = 0) {
  const n = Number(v);
  if (v == null || v === '' || !isFinite(n)) return '–';
  return n.toLocaleString('de-DE', {
    minimumFractionDigits: dec,
    maximumFractionDigits: dec,
  });
}

function _renderRingGauge(pct, color) {
  const r = 26;
  const c = 2 * Math.PI * r;
  const clamped = Math.max(0, Math.min(100, Number(pct) || 0));
  const offset = c - (clamped / 100) * c;
  const label = pct != null && isFinite(Number(pct)) ? `${Math.round(Number(pct))}%` : '–';
  return `
    <div class="em-ring-wrap">
      <svg class="em-ring-svg" viewBox="0 0 64 64">
        <circle class="em-ring-bg" cx="32" cy="32" r="${r}"/>
        <circle class="em-ring-fg" cx="32" cy="32" r="${r}" stroke="${color}" stroke-dasharray="${c.toFixed(1)}" stroke-dashoffset="${offset.toFixed(1)}"/>
      </svg>
      <div class="em-ring-lbl">${label}</div>
    </div>
  `;
}

const _THRESHOLD_SECTIONS = [
  {
    title: '1. Netzzähler & Glättung',
    intro: 'Glättet kurze Lastspitzen (z. B. Herd) und hält die Regelung ruhig.',
    fields: [
      {
        key: 'ema_alpha',
        label: 'Glättungsfaktor (EMA)',
        unit: '',
        min: 0.05,
        max: 1.0,
        step: 0.05,
        dec: 2,
        hint: '0,35 = empfohlene Glättung · 1,0 = ungefiltert.',
      },
      {
        key: 'deadband_watts',
        label: 'Ruhezone (±W)',
        unit: 'W',
        min: 0,
        max: 500,
        step: 5,
        dec: 0,
        hint: 'Innerhalb dieser Abweichung um 0 W wird nicht nachgeregelt.',
      },
    ],
  },
  {
    title: '2. Anker Solarbank & Entladesperre',
    intro: 'Füllt zuerst den Hausakku und verhindert, dass er ins Auto entladen wird.',
    fields: [
      {
        key: 'battery_reserve_soc',
        label: 'Heimspeicher Reserve-SOC',
        unit: '%',
        min: 0,
        max: 100,
        step: 5,
        dec: 0,
        hint: 'Unter diesem Wert lädt zuerst nur der Hausakku (Sommer z. B. 60 %, Winter 0 %).',
      },
      {
        key: 'battery_lock_threshold_watts',
        label: 'Entladesperre ab Auto-Leistung',
        unit: 'W',
        min: 50,
        max: 2000,
        step: 50,
        dec: 0,
        hint: 'Lädt das Auto stärker als dieser Wert, wird die Hausbatterie-Entladung gesperrt.',
      },
      {
        key: 'battery_lock_release_seconds',
        label: 'Wartezeit vor Freigabe',
        unit: 's',
        min: 0,
        max: 600,
        step: 10,
        dec: 0,
        hint: 'Wartezeit nach Ladeende, bevor die Hausbatterie wieder entladen darf.',
      },
    ],
  },
  {
    title: '3. Warmwasser-Wärmepumpe (LG)',
    intro: 'Heizt tagsüber (10–18 Uhr) bei PV-Überschuss auf Zieltemperatur und schützt im Winter vor Auskühlung.',
    fields: [
      {
        key: 'dhw_min_surplus_watts',
        label: 'Start ab PV-Überschuss',
        unit: 'W',
        min: 200,
        max: 1500,
        step: 50,
        dec: 0,
        hint: 'Ab diesem Überschuss schaltet die Warmwasser-WP in den Modus „heat_pump“ (Standard: 500 W).',
      },
      {
        key: 'dhw_target_temp',
        label: 'PV-Zieltemperatur',
        unit: '°C',
        min: 45,
        max: 60,
        step: 1,
        dec: 0,
        hint: 'Erreicht das Wasser diese Zieltemperatur, schaltet die Wärmepumpe ab (Standard: 53 °C).',
      },
      {
        key: 'dhw_stop_temp',
        label: 'Abschaltschwelle bei Netzbezug',
        unit: '°C',
        min: 40,
        max: 58,
        step: 1,
        dec: 0,
        hint: 'Oberhalb dieser Wassertemperatur wird bei > 200 W Netzbezug wieder abgeschaltet (Standard: 51 °C).',
      },
      {
        key: 'dhw_min_temp',
        label: 'Mindesttemperatur (Winter-Schutz)',
        unit: '°C',
        min: 35,
        max: 50,
        step: 1,
        dec: 0,
        hint: 'Fällt das Wasser unter diesen Wert, wird ab dem Tages-PV-Peak zwangsweise nachgeheizt (Standard: 42 °C).',
      },
    ],
  },
  {
    title: '4. Klimaanlage als Wärmepuffer',
    intro: 'Nutzt mittleren Überschuss zum Vorheizen oder Vorkühlen der Räume.',
    fields: [
      {
        key: 'ac_buffer_min_surplus_watts',
        label: 'Start ab Überschuss',
        unit: 'W',
        min: 100,
        max: 3000,
        step: 50,
        dec: 0,
        hint: 'Ab diesem Überschuss schaltet sich der Klimapuffer ein (Standard: 500 W).',
      },
      {
        key: 'ac_buffer_max_surplus_watts',
        label: 'Obergrenze bei Überschuss',
        unit: 'W',
        min: 500,
        max: 5000,
        step: 50,
        dec: 0,
        hint: 'Darüber übernimmt das E-Auto den Überschuss (Standard: 1.350 W).',
      },
      {
        key: 'ac_buffer_temp_offset',
        label: 'Temperatur-Anpassung (±°C)',
        unit: '°C',
        min: 0.5,
        max: 5.0,
        step: 0.5,
        dec: 1,
        hint: 'Hebt (Heizen) oder senkt (Kühlen) die Zieltemperatur; alter Wert wird danach wiederhergestellt.',
      },
      {
        key: 'ac_buffer_min_hold_minutes',
        label: 'Mindestlaufzeit',
        unit: 'min',
        min: 1,
        max: 120,
        step: 1,
        dec: 0,
        hint: 'Schützt den Kompressor vor ständigem Ein- und Ausschalten (Standard: 20 min).',
      },
      {
        key: 'ac_auto_heat_max_outdoor_temp',
        label: 'Auto-Heizen bis Außentemperatur',
        unit: '°C',
        min: 0.0,
        max: 20.0,
        step: 0.5,
        dec: 1,
        hint: 'Ist „Auto-Start Heizen“ aktiv und die Klimaanlage aus, wird das Gerät unterhalb dieser Außentemperatur bei Überschuss eingeschaltet (Standard: 11,0 °C).',
      },
    ],
  },
  {
    title: '5. Tesla-Ladesteuerung & Strompreis',
    intro: 'Steuert den Ladestrom von 3 bis 16 A (je 230 W) und stoppt bei längerem Netzbezug.',
    fields: [
      {
        key: 'tesla_max_current',
        label: 'Maximaler Ladestrom',
        unit: 'A',
        min: 3,
        max: 16,
        step: 1,
        dec: 0,
        hint: '13 A für Schuko-Steckdose (2.990 W), bis 16 A für CEE-Stecker (3.680 W).',
      },
      {
        key: 'tesla_target_soc',
        label: 'Schnelllade-Limit',
        unit: '%',
        min: 50,
        max: 100,
        step: 5,
        dec: 0,
        hint: 'Stoppt „Schnellladen“ bei diesem Akkustand automatisch.',
      },
      {
        key: 'ev_min_surplus_watts',
        label: 'Start-Überschuss für PV-Laden',
        unit: 'W',
        min: 600,
        max: 3680,
        step: 10,
        dec: 0,
        hint: 'Nötiger Überschuss, um die Ladung inkl. Wake-Up zu starten (Standard: 1.380 W).',
      },
      {
        key: 'ev_cloud_hysteresis_seconds',
        label: 'Wolkenpuffer / Stopp-Verzögerung',
        unit: 's',
        min: 0,
        max: 900,
        step: 15,
        dec: 0,
        hint: 'Regelt bei Wolken bis auf 3 A herunter und stoppt erst nach dieser Zeit bei < 5 A & Netzbezug (Standard: 300 s = 5 min).',
      },
      {
        key: 'ev_wakeup_delay_seconds',
        label: 'Aufwach-Wartezeit (Wake-Up)',
        unit: 's',
        min: 1,
        max: 60,
        step: 1,
        dec: 0,
        hint: 'Wartezeit nach dem Wake-Up-Befehl vor dem Senden von Ladestrom und Startbefehl (Standard: 10 s). Bei aktivem Awake-Sensor wird vorzeitig freigegeben.',
      },
      {
        key: 'electricity_price',
        label: 'Netzstrompreis',
        unit: '€/kWh',
        min: 0,
        max: 1.5,
        step: 0.01,
        dec: 2,
        hint: 'Für die Kostenberechnung des Netzanteils pro Ladesitzung.',
      },
    ],
  },
];

const _SIM_NUMBERS = [
  { id: 'input_number.sim_grid_power', label: 'Simulierter Netzzähler (- Einspeisung / + Bezug)', unit: 'W', min: -5000, max: 5000, step: 50 },
  { id: 'input_number.sim_anker_battery_soc', label: 'Simulierter Anker Speicher SOC', unit: '%', min: 0, max: 100, step: 1 },
  { id: 'input_number.sim_tesla_charging_power', label: 'Simulierte Tesla Ladeleistung', unit: 'W', min: 0, max: 3680, step: 10 },
  { id: 'input_number.sim_tesla_soc', label: 'Simulierter Tesla Akku SOC', unit: '%', min: 0, max: 100, step: 1 },
  { id: 'input_number.sim_tesla_charging_amps', label: 'Simulierter Tesla Ladestrom', unit: 'A', min: 0, max: 16, step: 1 },
  { id: 'input_number.sim_room_temperature', label: 'Simulierte Raumtemperatur', unit: '°C', min: 15, max: 30, step: 0.5 },
];

const _SIM_BOOLEANS = [
  { id: 'input_boolean.sim_tesla_plugged', label: 'Tesla Ladekabel angesteckt' },
  { id: 'input_boolean.sim_tesla_ble_connected', label: 'Tesla BLE direkt verbunden (in Reichweite)' },
  { id: 'input_boolean.sim_tesla_charger', label: 'Tesla Ladeschalter aktiv' },
  { id: 'input_boolean.sim_anker_discharge_disabled', label: 'Anker Entladesperre aktiv' },
];

class SamEnergiemanagerPanel extends HTMLElement {
  constructor() {
    super();
    this._hass = null;
    this._initialized = false;
    this._tab = 'overview';
    this._entityMap = null;
    this._toast = null;
    this._toastTimer = null;
    this._updateThrottle = null;
  }

  set hass(hass) {
    const first = !this._initialized && hass;
    this._hass = hass;
    if (first) {
      this._initialized = true;
      this._boot();
      return;
    }
    if (this._initialized && !this._updateThrottle) {
      this._updateThrottle = setTimeout(() => {
        this._updateThrottle = null;
        this._discoverEntities();
        // Avoid clobbering an active slider drag or number input focus
        const active = this.shadowRoot && this.shadowRoot.activeElement;
        if (active && (active.tagName === 'INPUT' || active.tagName === 'SELECT')) {
          return;
        }
        this._render();
      }, 350);
    }
  }

  set panel(panel) {
    this._panel = panel;
  }

  set narrow(narrow) {
    this._narrow = narrow;
  }

  connectedCallback() {
    this._onResize = () => this._syncPanelHeight();
    window.addEventListener('resize', this._onResize);
    requestAnimationFrame(() => this._syncPanelHeight());
  }

  disconnectedCallback() {
    if (this._onResize) {
      window.removeEventListener('resize', this._onResize);
      this._onResize = null;
    }
    if (this._updateThrottle) {
      clearTimeout(this._updateThrottle);
      this._updateThrottle = null;
    }
  }

  _syncPanelHeight() {
    if (!this.isConnected) return;
    const r = this.getBoundingClientRect();
    const top = r.top + (window.scrollY || document.documentElement.scrollTop || 0);
    const avail = Math.round((window.innerHeight || 0) - top);
    if (avail > 200) {
      this.style.height = `${avail}px`;
    }
  }

  _boot() {
    const shadow = this.attachShadow({ mode: 'open' });
    const style = document.createElement('style');
    style.textContent = _CSS;
    shadow.appendChild(style);
    this._container = document.createElement('div');
    this._container.className = 'em-root';
    shadow.appendChild(this._container);
    this._discoverEntities();
    this._render();
  }

  /**
   * Discover all Energiemanager entities from hass.entities or fallback slugs.
   */
  _discoverEntities() {
    if (!this._hass) return;
    const map = {};
    const ents = this._hass.entities || {};
    for (const [eid, info] of Object.entries(ents)) {
      if (info && info.platform === 'sam_energiemanager' && info.translation_key) {
        map[info.translation_key] = eid;
      }
    }
    // Fallback lookup by known suffix patterns if hass.entities is unavailable
    const fallbacks = {
      charging_mode: ['select.energiemanager_ev_charging_mode', 'select.sam_energiemanager_charging_mode'],
      priority_order: ['select.energiemanager_surplus_consumer_priority_order', 'select.energiemanager_priority_order', 'select.sam_energiemanager_priority_order'],
      battery_reserve_soc: ['number.energiemanager_battery_priority_reserve_soc', 'number.sam_energiemanager_battery_reserve_soc'],
      tesla_max_current: ['number.energiemanager_tesla_maximum_charging_current', 'number.sam_energiemanager_tesla_max_current'],
      tesla_target_soc: ['number.energiemanager_tesla_fast_charge_target_soc', 'number.sam_energiemanager_tesla_target_soc'],
      ac_buffer_enabled: ['switch.energiemanager_thermal_ac_buffer_enabled', 'switch.sam_energiemanager_ac_buffer_enabled'],
      ac_auto_heat_enabled: ['switch.energiemanager_ac_auto_start_heating_when_off', 'switch.sam_energiemanager_ac_auto_heat_enabled'],
      dhw_enabled: ['switch.energiemanager_hot_water_heat_pump_auto_control', 'switch.sam_energiemanager_dhw_enabled'],
      battery_discharge_lock_active: ['binary_sensor.energiemanager_battery_discharge_lock_active'],
      ac_buffer_active: ['binary_sensor.energiemanager_thermal_ac_buffer_active'],
      dhw_active: ['binary_sensor.energiemanager_hot_water_heat_pump_active'],
      ev_session_active: ['binary_sensor.energiemanager_ev_charging_session_active'],
      grid_power_filtered: ['sensor.energiemanager_grid_power_filtered'],
      surplus_power: ['sensor.energiemanager_pv_surplus_power'],
      home_power_watts: ['sensor.energiemanager_home_power_consumption'],
      daily_home_kwh: ['sensor.energiemanager_daily_home_energy_consumption'],
      daily_pv_kwh: ['sensor.energiemanager_daily_pv_energy_generation'],
      daily_grid_import_kwh: ['sensor.energiemanager_daily_grid_energy_import'],
      daily_grid_export_kwh: ['sensor.energiemanager_daily_grid_energy_export'],
      ev_charging_power: ['sensor.energiemanager_ev_charging_power'],
      ev_solar_power: ['sensor.energiemanager_ev_solar_charging_power'],
      ev_grid_power: ['sensor.energiemanager_ev_grid_charging_power'],
      ev_target_current: ['sensor.energiemanager_ev_target_current'],
      ev_solar_lifetime_kwh: ['sensor.energiemanager_ev_solar_lifetime_energy'],
      ev_grid_lifetime_kwh: ['sensor.energiemanager_ev_grid_lifetime_energy'],
      last_session_summary: ['sensor.energiemanager_last_ev_charging_session'],
      ema_alpha: ['number.energiemanager_ema_smoothing_factor'],
      deadband_watts: ['number.energiemanager_symmetric_deadband'],
      battery_lock_threshold_watts: ['number.energiemanager_battery_lock_power_threshold'],
      battery_lock_release_seconds: ['number.energiemanager_battery_lock_release_delay'],
      ac_buffer_min_surplus_watts: ['number.energiemanager_ac_buffer_minimum_surplus'],
      ac_buffer_max_surplus_watts: ['number.energiemanager_ac_buffer_maximum_surplus'],
      ac_buffer_temp_offset: ['number.energiemanager_ac_buffer_temperature_offset'],
      ac_buffer_min_hold_minutes: ['number.energiemanager_ac_buffer_minimum_hold_time'],
      ac_auto_heat_max_outdoor_temp: ['number.energiemanager_ac_auto_heat_maximum_outdoor_temperature'],
      dhw_min_surplus_watts: ['number.energiemanager_hot_water_minimum_surplus_power'],
      dhw_target_temp: ['number.energiemanager_hot_water_pv_target_temperature'],
      dhw_stop_temp: ['number.energiemanager_hot_water_grid_import_stop_temperature'],
      dhw_min_temp: ['number.energiemanager_hot_water_winter_minimum_temperature'],
      ev_min_surplus_watts: ['number.energiemanager_ev_minimum_surplus_power'],
      ev_cloud_hysteresis_seconds: ['number.energiemanager_ev_cloud_hysteresis_delay'],
      ev_wakeup_delay_seconds: [
        'number.energiemanager_ev_wake_up_delay',
        'number.energiemanager_ev_wakeup_delay',
        'number.energiemanager_ev_wakeup_delay_seconds',
      ],
      electricity_price: ['number.energiemanager_electricity_tariff_price'],
      action_tracing_enabled: [
        'switch.energiemanager_action_tracing',
        'switch.energiemanager_action_tracing_enabled',
        'switch.sam_energiemanager_action_tracing_enabled',
      ],
      last_action_trace: [
        'sensor.energiemanager_last_action_trace',
        'sensor.sam_energiemanager_last_action_trace',
      ],
    };
    const states = this._hass.states || {};
    for (const [key, candidates] of Object.entries(fallbacks)) {
      if (!map[key]) {
        const found = candidates.find((c) => c in states);
        if (found) map[key] = found;
      }
    }
    this._entityMap = map;
  }

  _entId(key) {
    return (this._entityMap && this._entityMap[key]) || null;
  }

  _stateObj(key) {
    const eid = this._entId(key);
    return eid && this._hass && this._hass.states ? this._hass.states[eid] : null;
  }

  _val(key, fallback = null) {
    const st = this._stateObj(key);
    if (!st || st.state === 'unavailable' || st.state === 'unknown') return fallback;
    return st.state;
  }

  _num(key, fallback = 0) {
    const v = this._val(key, null);
    if (v == null) return fallback;
    const n = Number(v);
    return isFinite(n) ? n : fallback;
  }

  _bool(key) {
    return this._val(key) === 'on';
  }

  _sourceEntities() {
    const st = this._stateObj('ev_session_active');
    return (st && st.attributes && st.attributes.source_entities) || {};
  }

  _sourceState(confKey) {
    const src = this._sourceEntities();
    const eid = src[confKey];
    if (!eid || !this._hass || !this._hass.states) return null;
    return this._hass.states[eid] || null;
  }

  _outdoorTemp() {
    const explicit = this._sourceState('outdoor_temp_sensor');
    if (explicit && isFinite(Number(explicit.state))) return Number(explicit.state);
    const states = (this._hass && this._hass.states) || {};
    const src = this._sourceEntities();
    const climId = src.climate_entity || '';
    const candidates = [];
    if (climId.startsWith('climate.')) {
      const slug = climId.split('.', 2)[1];
      candidates.push(`sensor.${slug}_outdoor`, `sensor.${slug}_outside_temperature`);
    }
    candidates.push(
      'sensor.klima_buro_outdoor',
      'sensor.klima_esszimmer_outdoor',
      'sensor.klima_schlafzimmer_outdoor',
      'sensor.tesla_ble_lrw3e7fs1rc955673_outside_temp',
      'sensor.sim_outdoor_temperature'
    );
    for (const cid of candidates) {
      const st = states[cid];
      if (st && st.state !== 'unavailable' && st.state !== 'unknown' && isFinite(Number(st.state))) {
        return Number(st.state);
      }
    }
    return null;
  }

  _hasSimulator() {
    return !!(this._hass && this._hass.states && this._hass.states['input_number.sim_grid_power']);
  }

  _showToast(msg) {
    this._toast = msg;
    if (this._toastTimer) clearTimeout(this._toastTimer);
    this._render();
    this._toastTimer = setTimeout(() => {
      this._toast = null;
      this._render();
    }, 2400);
  }

  async _setNumber(key, value) {
    const eid = this._entId(key);
    if (!eid || !this._hass) return;
    await this._hass.callService('number', 'set_value', {
      entity_id: eid,
      value: Number(value),
    });
    this._showToast(`Gespeichert: ${value}`);
  }

  async _setSelect(key, option) {
    const eid = this._entId(key);
    if (!eid || !this._hass) return;
    await this._hass.callService('select', 'select_option', {
      entity_id: eid,
      option,
    });
    const labels = {
      off: 'Aus',
      pv_surplus: 'PV-Überschuss',
      fast: 'Schnellladen',
      fast_charge: 'Schnellladen',
      dhw_ev_ac: 'Warmwasser → Auto → Klima',
      ev_dhw_ac: 'Auto → Warmwasser → Klima',
      dhw_ac_ev: 'Warmwasser → Klima → Auto',
      ev_ac_dhw: 'Auto → Klima → Warmwasser',
    };
    this._showToast(`Einstellung: ${labels[option] || option}`);
  }

  async _setSwitch(key, turnOn) {
    const eid = this._entId(key);
    if (!eid || !this._hass) return;
    await this._hass.callService('switch', turnOn ? 'turn_on' : 'turn_off', {
      entity_id: eid,
    });
    this._showToast(turnOn ? 'Schalter aktiviert' : 'Schalter deaktiviert');
  }

  _render() {
    if (!this._container) return;
    const scroller = this.shadowRoot && this.shadowRoot.querySelector('.em-main');
    const scrollTop = scroller ? scroller.scrollTop : 0;

    this._container.innerHTML = this._buildHtml();
    this._wire();

    const newScroller = this.shadowRoot && this.shadowRoot.querySelector('.em-main');
    if (newScroller && scrollTop > 0) {
      newScroller.scrollTop = scrollTop;
    }
  }

  _buildHtml() {
    const mode = this._val('charging_mode', 'pv_surplus');
    const evAmps = this._num('ev_target_current', 0);
    const acActive = this._bool('ac_buffer_active');
    const batLock = this._bool('battery_discharge_lock_active');

    let statusLabel = 'Bereit · Nulleinspeisung';
    let statusDotPulse = false;
    if (evAmps >= 3) {
      statusLabel = mode === 'fast' || mode === 'fast_charge' ? `Schnellladen (${evAmps} A)` : `PV-Überschussladen (${evAmps} A)`;
      statusDotPulse = true;
    } else if (acActive) {
      statusLabel = 'Klimapuffer aktiv';
      statusDotPulse = true;
    } else if (batLock) {
      statusLabel = 'Akku-Schutz aktiv';
    }

    const forceBurger = this._hass && this._hass.dockedSidebar === 'always_hidden' ? ' em-burger--force' : '';
    const hasSim = this._hasSimulator();

    const tabs = [
      { id: 'overview', label: '⚡ Energiefluss & Steuerung' },
      { id: 'sessions', label: '📊 Ladebilanz & Sitzungen' },
      { id: 'traces', label: '🔍 Aktions-Traces' },
      { id: 'settings', label: '🎛️ Schwellenwerte & Feintuning' },
    ];
    if (hasSim) {
      tabs.push({ id: 'simulator', label: '🧪 Test-Simulator' });
    }

    const tabBtns = tabs
      .map(
        (t) =>
          `<button class="em-tab ${this._tab === t.id ? 'active' : ''}" data-tab="${t.id}">${t.label}</button>`
      )
      .join('');

    let paneHtml = '';
    if (this._tab === 'overview') paneHtml = this._htmlOverview();
    else if (this._tab === 'sessions') paneHtml = this._htmlSessions();
    else if (this._tab === 'traces') paneHtml = this._htmlTraces();
    else if (this._tab === 'settings') paneHtml = this._htmlSettings();
    else if (this._tab === 'simulator') paneHtml = this._htmlSimulator();

    return `
      <div class="em-header">
        <button class="em-burger${forceBurger}" id="em-burger" title="Seitenleiste umschalten">
          <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
            <line x1="4" y1="7" x2="20" y2="7"/><line x1="4" y1="12" x2="20" y2="12"/><line x1="4" y1="17" x2="20" y2="17"/>
          </svg>
        </button>
        <div class="em-logo">
          <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
          </svg>
        </div>
        <div>
          <h1>Energiemanager</h1>
          <div class="em-sub">Kaskaden-Steuerung · Anker Solarbank · Multisplit-Klima · Tesla BLE</div>
        </div>
        <div class="em-hdr-badge">
          <span class="em-dot ${statusDotPulse ? 'em-pulse' : ''}"></span>
          <span>${_esc(statusLabel)}</span>
        </div>
        <span style="flex:1"></span>
        <button class="em-icon-btn" data-action="recalculate" title="Regelschleife sofort neu berechnen">
          ↻ Neu berechnen
        </button>
      </div>
      <div class="em-main">
        <div class="em-body">
          <div class="em-nav">
            <div class="em-tabs">${tabBtns}</div>
          </div>
          ${paneHtml}
        </div>
      </div>
      ${this._toast ? `<div class="em-toast">${_esc(this._toast)}</div>` : ''}
    `;
  }

  _htmlOverview() {
    const gridW = this._num('grid_power_filtered', 0);
    const surplusW = this._num('surplus_power', 0);
    const homeW = this._num('home_power_watts', 0);
    const homeSt = this._stateObj('home_power_watts');
    const homeAttrs = (homeSt && homeSt.attributes) || {};
    const pvW = isFinite(Number(homeAttrs.pv_power_watts)) ? Number(homeAttrs.pv_power_watts) : 0;
    const batW = isFinite(Number(homeAttrs.battery_power_watts)) ? Number(homeAttrs.battery_power_watts) : 0;
    const dailyHomeKwh = this._num('daily_home_kwh', Number(homeAttrs.daily_home_kwh) || 0);
    const dailyPvKwh = this._num('daily_pv_kwh', Number(homeAttrs.daily_pv_kwh) || 0);
    const dailyImportKwh = this._num('daily_grid_import_kwh', Number(homeAttrs.daily_grid_import_kwh) || 0);
    const dailyExportKwh = this._num('daily_grid_export_kwh', Number(homeAttrs.daily_grid_export_kwh) || 0);
    const dailyAutarky = isFinite(Number(homeAttrs.daily_autarky_pct)) ? Number(homeAttrs.daily_autarky_pct) : 100;

    const dhwEnabled = this._bool('dhw_enabled');
    const dhwActive = this._bool('dhw_active');
    const dhwSt = this._stateObj('dhw_active');
    const dhwAttrs = (dhwSt && dhwSt.attributes) || {};
    const waterTemp = isFinite(Number(dhwAttrs.water_temp)) ? Number(dhwAttrs.water_temp) : null;
    const dhwPowerW = isFinite(Number(dhwAttrs.dhw_power_watts)) ? Number(dhwAttrs.dhw_power_watts) : 0;
    const dhwForced = !!dhwAttrs.dhw_forced_min_temp;
    const dhwTargetTemp = this._num('dhw_target_temp', 53);
    const dhwMinTemp = this._num('dhw_min_temp', 42);

    const evW = this._num('ev_charging_power', 0);
    const evSolarW = this._num('ev_solar_power', 0);
    const evGridW = this._num('ev_grid_power', 0);
    const evAmps = this._num('ev_target_current', 0);
    const reserveSoc = this._num('battery_reserve_soc', 60);
    const maxAmps = this._num('tesla_max_current', 13);
    const targetSoc = this._num('tesla_target_soc', 80);
    const mode = this._val('charging_mode', 'pv_surplus');
    const acEnabled = this._bool('ac_buffer_enabled');
    const acAutoHeat = this._bool('ac_auto_heat_enabled');
    const acMaxOutdoor = this._num('ac_auto_heat_max_outdoor_temp', 11.0);
    const acActive = this._bool('ac_buffer_active');
    const batLock = this._bool('battery_discharge_lock_active');
    const sessionActive = this._bool('ev_session_active');

    const acStateObj = this._stateObj('ac_buffer_active');
    const savedTemp = acStateObj && acStateObj.attributes ? acStateObj.attributes.saved_temperature : null;
    const savedHvacMode = acStateObj && acStateObj.attributes ? acStateObj.attributes.saved_hvac_mode : null;

    // Live hardware states from source_entities
    const batSocSt = this._sourceState('battery_soc_sensor');
    const batSoc = batSocSt && isFinite(Number(batSocSt.state)) ? Number(batSocSt.state) : null;
    const evSocSt = this._sourceState('ev_soc_sensor');
    const evSoc = evSocSt && isFinite(Number(evSocSt.state)) ? Number(evSocSt.state) : null;
    const evPlugSt = this._sourceState('ev_plugged_binary_sensor');
    const evPlugged = evPlugSt ? evPlugSt.state === 'on' : null;
    const evBleSt = this._sourceState('ev_ble_connected_binary_sensor');
    const evHome = evBleSt ? evBleSt.state === 'on' || evBleSt.state === 'home' : null;
    const climSt = this._sourceState('climate_entity');
    const climState = climSt ? climSt.state : null;
    const climTemp = climSt && climSt.attributes ? climSt.attributes.temperature : null;
    const climCurrTemp = climSt && climSt.attributes ? climSt.attributes.current_temperature : null;
    const outdoorTemp = this._outdoorTemp();

    const batPriorityActive = batSoc != null && batSoc < reserveSoc;
    const hasSurplusFlow = surplusW > 30 || pvW > 30;
    const isExporting = gridW < -25;
    const isImporting = gridW > 25;
    const gridColor = isExporting ? 'var(--em-grid-export)' : isImporting ? 'var(--em-grid-import)' : 'var(--primary-text-color)';
    const gridSub = isExporting ? 'Netzeinspeisung (Überschuss)' : isImporting ? 'Netzbezug' : 'Ausbalanciert (Nulleinspeisung)';

    const batFlowActive = Math.abs(batW) > 15 || (hasSurplusFlow && batPriorityActive) || (!batLock && isImporting);
    const dhwFlowActive = dhwActive || dhwPowerW > 50;
    const acFlowActive = acActive;
    const evFlowActive = evAmps >= 3 || evW > 50;

    const solarSharePct = evW > 0 ? Math.round((evSolarW / evW) * 100) : 100;
    const isFastMode = mode === 'fast' || mode === 'fast_charge';
    const modeLabel = isFastMode ? '⚡ Schnellladen' : mode === 'pv_surplus' ? '☀️ PV-Überschuss' : '⏹ Aus';

    const prioOrder = this._val('priority_order', 'dhw_ev_ac');
    let dhwPrio = 'Prio 3';
    let evPrio = 'Prio 4';
    let acPrio = 'Prio 5';

    if (prioOrder === 'ev_dhw_ac') {
      evPrio = 'Prio 3';
      dhwPrio = 'Prio 4';
      acPrio = 'Prio 5';
    } else if (prioOrder === 'dhw_ac_ev') {
      dhwPrio = 'Prio 3';
      acPrio = 'Prio 4';
      evPrio = 'Prio 5';
    } else if (prioOrder === 'ev_ac_dhw') {
      evPrio = 'Prio 3';
      acPrio = 'Prio 4';
      dhwPrio = 'Prio 5';
    }

    const batPowerLabel =
      batW < -10
        ? `⚡ Lädt mit ${_fmtNum(Math.abs(batW), 0)} W`
        : batW > 10
          ? `🔋 Entlädt mit ${_fmtNum(batW, 0)} W`
          : `Reserve-Ziel: ${_fmtNum(reserveSoc, 0)} %`;

    return `
      <!-- Compact Daily Energy Overview -->
      <div class="em-stats">
        <div class="em-stat">
          <div class="em-stat-top"><span>Hausverbrauch (Heute)</span><span>🏠</span></div>
          <div class="em-stat-val">${_fmtNum(dailyHomeKwh, 2)} kWh</div>
          <div class="em-stat-sub">Aktuell: ${_fmtNum(homeW, 0)} W · Autarkie: ${_fmtNum(dailyAutarky, 0)} %</div>
        </div>
        <div class="em-stat">
          <div class="em-stat-top"><span>PV-Erzeugung (Heute)</span><span>☀️</span></div>
          <div class="em-stat-val" style="color:var(--em-solar)">${_fmtNum(dailyPvKwh, 2)} kWh</div>
          <div class="em-stat-sub">Wechselrichter aktuell: ${_fmtNum(pvW, 0)} W</div>
        </div>
        <div class="em-stat">
          <div class="em-stat-top"><span>Netzbezug (Heute)</span><span>🔌</span></div>
          <div class="em-stat-val" style="color:var(--em-grid-import)">${_fmtNum(dailyImportKwh, 2)} kWh</div>
          <div class="em-stat-sub">Aus dem öffentlichen Netz</div>
        </div>
        <div class="em-stat">
          <div class="em-stat-top"><span>Einspeisung (Heute)</span><span>⚡</span></div>
          <div class="em-stat-val" style="color:var(--em-grid-export)">${_fmtNum(dailyExportKwh, 2)} kWh</div>
          <div class="em-stat-sub">Überschuss ins Netz</div>
        </div>
      </div>

      <!-- Unified Animated Energy Flow & Priority Diagram Card -->
      <div class="em-card">
        <div class="em-card-head">
          <div class="em-card-title">⚡ Live-Energiefluss & Kaskaden-Status</div>
          <div style="display:flex;gap:8px;flex-wrap:wrap">
            <span class="em-badge ${batLock ? 'em-badge-warn' : 'em-badge-ok'}">
              ${batLock ? '🔒 Anker Entladesperre aktiv' : '🔓 Anker Entladung frei'}
            </span>
            <span class="em-badge ${dhwActive ? 'em-badge-warn' : 'em-badge-muted'}">
              ${dhwActive ? `🚿 Warmwasser heizt (${waterTemp != null ? `${_fmtNum(waterTemp, 0)} °C` : 'WP'})` : '🚿 Warmwasser bereit'}
            </span>
            <span class="em-badge ${acActive ? 'em-badge-info' : 'em-badge-muted'}">
              ${acActive
                ? `❄️ Klimapuffer aktiv (${savedHvacMode === 'off' ? 'Auto-Heizen' : savedTemp != null ? `vorher ${savedTemp} °C` : '±Temp.'})`
                : acEnabled
                  ? '❄️ Klimapuffer bereit'
                  : '❄️ Klimapuffer aus'}
            </span>
            <span class="em-badge ${sessionActive ? 'em-badge-ok' : 'em-badge-muted'}">
              ${sessionActive ? '⚡ Ladesitzung läuft' : '🔌 Keine laufende Sitzung'}
            </span>
          </div>
        </div>

        <div class="em-flow-wrap">
          <!-- Top Row: PV Surplus & Smart Meter Grid -->
          <div class="em-flow-sources">
            <div class="em-flow-node ${hasSurplusFlow ? 'active-solar' : ''}">
              <div class="em-node-head">
                <span class="em-node-title">☀️ PV-Überschuss${pvW > 0 ? ' & Erzeugung' : ''}</span>
                <span class="em-prio-tag">Quelle</span>
              </div>
              <div class="em-node-big" style="color:var(--em-solar)">${_fmtNum(surplusW, 0)} W</div>
              <div class="em-node-sub">
                ${pvW > 0 ? `Wechselrichter: <strong>${_fmtNum(pvW, 0)} W</strong> · ` : ''}
                ${surplusW > 30 ? 'Frei verfügbar am Zähler' : 'Aktuell kein freier Überschuss'}
              </div>
            </div>

            <div class="em-flow-node ${isExporting ? 'active-export' : isImporting ? 'active-import' : ''}">
              <div class="em-node-head">
                <span class="em-node-title">⚡ Netzzähler (Smart Meter)</span>
                <span class="em-prio-tag">${isExporting ? 'Einspeisung' : isImporting ? 'Netzbezug' : '0-Balance'}</span>
              </div>
              <div class="em-node-big" style="color:${gridColor}">${_fmtNum(gridW, 0)} W</div>
              <div class="em-node-sub">${gridSub}</div>
            </div>
          </div>

          <!-- Top Animated SVG Connectors (Sources -> Home Hub) -->
          <svg class="em-flow-svg" viewBox="0 0 800 52" preserveAspectRatio="none">
            <path class="em-flow-line-bg" d="M 230 0 C 230 30, 400 22, 400 52"/>
            <path class="em-flow-line-bg" d="M 570 0 C 570 30, 400 22, 400 52"/>
            ${hasSurplusFlow ? `<path class="em-flow-line-anim" stroke="#f59e0b" d="M 230 0 C 230 30, 400 22, 400 52"/>` : ''}
            ${isImporting ? `<path class="em-flow-line-anim" stroke="#ef4444" d="M 570 0 C 570 30, 400 22, 400 52"/>` : ''}
            ${isExporting ? `<path class="em-flow-line-anim em-flow-line-rev" stroke="#10b981" d="M 570 0 C 570 30, 400 22, 400 52"/>` : ''}
          </svg>

          <!-- Center Distribution Hub (Prio 1: Hausverbrauch) -->
          <div class="em-flow-hub">
            <span>🏠 <strong>Prio 1 · Hausverbrauch: ${_fmtNum(homeW, 0)} W</strong> (10s-synchronisiert)</span>
            <span style="opacity:0.4">|</span>
            <span style="color:var(--primary-color, #0ea5e9)">Modus: ${modeLabel}</span>
          </div>

          <!-- Bottom Animated SVG Connectors (Home Hub -> 4 Priority Consumers) -->
          <svg class="em-flow-svg" viewBox="0 0 800 52" preserveAspectRatio="none">
            <path class="em-flow-line-bg" d="M 400 0 C 400 26, 100 22, 100 52"/>
            <path class="em-flow-line-bg" d="M 400 0 C 400 26, 300 22, 300 52"/>
            <path class="em-flow-line-bg" d="M 400 0 C 400 26, 500 22, 500 52"/>
            <path class="em-flow-line-bg" d="M 400 0 C 400 26, 700 22, 700 52"/>
            ${batFlowActive ? `<path class="em-flow-line-anim" stroke="#3b82f6" d="M 400 0 C 400 26, 100 22, 100 52"/>` : ''}
            ${dhwFlowActive ? `<path class="em-flow-line-anim" stroke="#f97316" d="M 400 0 C 400 26, 300 22, 300 52"/>` : ''}
            ${acFlowActive ? `<path class="em-flow-line-anim" stroke="#06b6d4" d="M 400 0 C 400 26, 500 22, 500 52"/>` : ''}
            ${evFlowActive ? `<path class="em-flow-line-anim" stroke="#8b5cf6" d="M 400 0 C 400 26, 700 22, 700 52"/>` : ''}
          </svg>

          <!-- Bottom Row: 4 Priority Consumer Nodes -->
          <div class="em-flow-consumers">
            <!-- Node 1: Anker Solarbank -->
            <div class="em-flow-node ${batPriorityActive ? 'active-battery' : ''} ${batLock ? 'locked-battery' : ''}">
              <div class="em-node-head">
                <span class="em-node-title">🔋 Anker Solarbank</span>
                <span class="em-prio-tag">Prio 2</span>
              </div>
              <div class="em-node-body">
                ${_renderRingGauge(batSoc != null ? batSoc : reserveSoc, '#3b82f6')}
                <div class="em-node-metrics">
                  <div class="em-node-big" style="color:var(--em-battery)">
                    ${batSoc != null ? `${_fmtNum(batSoc, 0)} %` : '–'}
                  </div>
                  <div class="em-node-sub">
                    <strong>${batPowerLabel}</strong><br>
                    ${batPriorityActive ? `Vorrang bis ${_fmtNum(reserveSoc, 0)} %` : `Reserve (${_fmtNum(reserveSoc, 0)} %) erreicht`}
                  </div>
                </div>
              </div>
              <div class="em-node-pills">
                <span class="em-pill ${batLock ? 'warn' : 'ok'}">
                  ${batLock ? '🔒 Entladesperre aktiv' : '🔓 Entladung frei'}
                </span>
                <span class="em-pill">
                  ${batPriorityActive ? '⏳ Verbraucher warten' : '✅ Überschuss freigegeben'}
                </span>
              </div>
            </div>

            <!-- Node 2: Warmwasser-Wärmepumpe (LG) -->
            <div class="em-flow-node ${dhwActive ? 'active-dhw' : ''}">
              <div class="em-node-head">
                <span class="em-node-title">🚿 Warmwasser-WP</span>
                <span class="em-prio-tag">${dhwPrio}</span>
              </div>
              <div class="em-node-body">
                <div class="em-node-metrics">
                  <div class="em-node-big" style="color:#f97316">
                    ${waterTemp != null ? `${_fmtNum(waterTemp, 0)} °C` : dhwActive ? 'Heizt' : 'Bereit'}
                  </div>
                  <div class="em-node-sub">
                    PV-Ziel: <strong>${_fmtNum(dhwTargetTemp, 0)} °C</strong> · Min: <strong>${_fmtNum(dhwMinTemp, 0)} °C</strong><br>
                    Leistung: <strong>${_fmtNum(dhwPowerW, 0)} W</strong> · Fenster: 10–18 Uhr
                  </div>
                </div>
              </div>
              <div class="em-node-pills">
                <span class="em-pill ${dhwActive ? 'warn' : ''}">
                  ${dhwForced
                    ? '🔥 Winter-Schutz (< Min.)'
                    : dhwActive
                      ? '☀️ PV-Aufheizung (heat_pump)'
                      : dhwEnabled
                        ? `Ab ${_fmtNum(this._num('dhw_min_surplus_watts', 500), 0)} W Überschuss`
                        : '⏸ Automatik aus'}
                </span>
              </div>
            </div>

            <!-- Node 3: Multisplit-Klimaanlage -->
            <div class="em-flow-node ${acActive ? 'active-ac' : ''}">
              <div class="em-node-head">
                <span class="em-node-title">❄️ Multisplit-Klima</span>
                <span class="em-prio-tag">${acPrio}</span>
              </div>
              <div class="em-node-body">
                <div class="em-node-metrics">
                  <div class="em-node-big" style="color:var(--em-ac)">
                    ${climCurrTemp != null ? `Raum ${_fmtNum(climCurrTemp, 1)} °C` : acActive ? 'Puffer aktiv' : 'Bereit'}
                  </div>
                  <div class="em-node-sub">
                    Sollwert: <strong>${climTemp != null ? `${_fmtNum(climTemp, 1)} °C` : '–'}</strong>
                    ${savedTemp != null ? ` (vorher ${_fmtNum(savedTemp, 1)} °C)` : ''}<br>
                    Status: <strong>${_esc(climState || 'unbekannt')}</strong>
                    ${outdoorTemp != null ? ` · Außen: <strong>${_fmtNum(outdoorTemp, 1)} °C</strong>` : ''}
                  </div>
                </div>
              </div>
              <div class="em-node-pills">
                <span class="em-pill ${acActive ? 'info' : ''}">
                  ${acActive
                    ? savedHvacMode === 'off'
                      ? '🔥 Auto-Heizen aktiv'
                      : `❄️ Sollwert ±${_fmtNum(this._num('ac_buffer_temp_offset', 2.5), 1)} °C aktiv`
                    : acEnabled
                      ? `Fenster: ${_fmtNum(this._num('ac_buffer_min_surplus_watts', 500), 0)}–${_fmtNum(this._num('ac_buffer_max_surplus_watts', 1350), 0)} W`
                      : '⏸ Wärmepuffer aus'}
                </span>
                ${acAutoHeat
                  ? `<span class="em-pill ${outdoorTemp != null && outdoorTemp <= acMaxOutdoor ? 'ok' : ''}">
                      🌡️ Auto-Heizen ≤ ${_fmtNum(acMaxOutdoor, 1)} °C
                    </span>`
                  : ''}
              </div>
            </div>

            <!-- Node 4: Tesla Wallbox / BLE -->
            <div class="em-flow-node ${evFlowActive ? 'active-ev' : ''}">
              <div class="em-node-head">
                <span class="em-node-title">🚗 Tesla Ladung</span>
                <span class="em-prio-tag">${evPrio}</span>
              </div>
              <div class="em-node-body">
                ${_renderRingGauge(evSoc != null ? evSoc : 0, '#8b5cf6')}
                <div class="em-node-metrics">
                  <div class="em-node-big" style="color:var(--em-ev)">
                    ${_fmtNum(evW, 0)} W · ${_fmtNum(evAmps, 0)} A
                  </div>
                  <div class="em-node-sub">
                    Akku: <strong>${evSoc != null ? `${_fmtNum(evSoc, 0)} %` : '–'}</strong> (Limit ${_fmtNum(targetSoc, 0)} %)<br>
                    Regelbereich: 3–${_fmtNum(maxAmps, 0)} A
                  </div>
                </div>
              </div>
              <div class="em-node-pills">
                <span class="em-pill ${evHome === true ? 'ok' : evHome === false ? 'warn' : ''}">
                  ${evHome === true ? '📍 Zuhause (BLE)' : evHome === false ? '🚗 Nicht zuhause' : '📍 Status unbekannt'}
                </span>
                <span class="em-pill ${evPlugged === true ? 'ev' : ''}">
                  ${evPlugged === true ? '🔌 Angesteckt' : evPlugged === false ? '🔓 Nicht angesteckt' : '🔌 Stecker unbekannt'}
                </span>
              </div>
              ${evW > 0 ? `
                <div>
                  <div class="em-split-bar">
                    <div class="em-split-solar" style="width:${solarSharePct}%"></div>
                    <div class="em-split-grid" style="width:${100 - solarSharePct}%"></div>
                  </div>
                  <div class="em-split-legend">
                    <span>☀️ ${_fmtNum(evSolarW, 0)} W (${solarSharePct}%)</span>
                    <span>🔌 ${_fmtNum(evGridW, 0)} W (${100 - solarSharePct}%)</span>
                  </div>
                </div>
              ` : ''}
            </div>
          </div>
        </div>
      </div>

      <!-- Direct Interactive Control Panel -->
      <div class="em-card">
        <div class="em-card-head">
          <div class="em-card-title">🎛️ Schnellsteuerung & Betriebsmodi</div>
          <div style="display:flex;gap:12px;align-items:center;flex-wrap:wrap">
            <div style="display:flex;align-items:center;gap:6px">
              <span style="font-size:0.75em;font-weight:700;color:var(--secondary-text-color);text-transform:uppercase">Kaskaden-Prio:</span>
              <select class="em-select" data-select="priority_order">
                <option value="dhw_ev_ac" ${prioOrder === 'dhw_ev_ac' ? 'selected' : ''}>🚿 Warmwasser → 🚗 Auto → ❄️ Klima</option>
                <option value="ev_dhw_ac" ${prioOrder === 'ev_dhw_ac' ? 'selected' : ''}>🚗 Auto → 🚿 Warmwasser → ❄️ Klima</option>
                <option value="dhw_ac_ev" ${prioOrder === 'dhw_ac_ev' ? 'selected' : ''}>🚿 Warmwasser → ❄️ Klima → 🚗 Auto</option>
                <option value="ev_ac_dhw" ${prioOrder === 'ev_ac_dhw' ? 'selected' : ''}>🚗 Auto → ❄️ Klima → 🚿 Warmwasser</option>
              </select>
            </div>
            <div class="em-seg" role="group" aria-label="Tesla Lademodus">
              <button class="em-seg-btn ${mode === 'off' ? 'active' : ''}" data-mode="off">⏹ Aus</button>
              <button class="em-seg-btn ${mode === 'pv_surplus' ? 'active' : ''}" data-mode="pv_surplus">☀️ PV-Überschuss</button>
              <button class="em-seg-btn ${isFastMode ? 'active' : ''}" data-mode="fast">⚡ Schnellladen</button>
            </div>
          </div>
        </div>

        <div class="em-ctrl-grid">
          <!-- Reserve SOC -->
          <div class="em-ctrl-box">
            <div class="em-ctrl-top">
              <span class="em-ctrl-lbl">🔋 Heimspeicher Reserve-SOC</span>
              <span class="em-ctrl-readout" id="lbl-battery_reserve_soc">${_fmtNum(reserveSoc, 0)} %</span>
            </div>
            <div class="em-slider-row">
              <input type="range" min="0" max="100" step="5" value="${reserveSoc}" data-num-slider="battery_reserve_soc">
              <input type="number" class="em-num-input" min="0" max="100" step="5" value="${reserveSoc}" data-num-input="battery_reserve_soc">
            </div>
            <div class="em-hint">Sommer z. B. 60 % (Speicher zuerst füllen), Winter 0 % (Überschuss direkt nutzen).</div>
          </div>

          <!-- Tesla Max Current -->
          <div class="em-ctrl-box">
            <div class="em-ctrl-top">
              <span class="em-ctrl-lbl">🔌 Max. Ladestrom</span>
              <span class="em-ctrl-readout" id="lbl-tesla_max_current">${_fmtNum(maxAmps, 0)} A (${_fmtNum(maxAmps * 230, 0)} W)</span>
            </div>
            <div class="em-slider-row">
              <input type="range" min="3" max="16" step="1" value="${maxAmps}" data-num-slider="tesla_max_current">
              <input type="number" class="em-num-input" min="3" max="16" step="1" value="${maxAmps}" data-num-input="tesla_max_current">
            </div>
            <div class="em-hint">13 A = Schuko-Steckdose · 16 A = blauer CEE-Stecker.</div>
          </div>

          <!-- Tesla Target SOC -->
          <div class="em-ctrl-box">
            <div class="em-ctrl-top">
              <span class="em-ctrl-lbl">🎯 Schnelllade-Limit</span>
              <span class="em-ctrl-readout" id="lbl-tesla_target_soc">${_fmtNum(targetSoc, 0)} %</span>
            </div>
            <div class="em-slider-row">
              <input type="range" min="50" max="100" step="5" value="${targetSoc}" data-num-slider="tesla_target_soc">
              <input type="number" class="em-num-input" min="50" max="100" step="5" value="${targetSoc}" data-num-input="tesla_target_soc">
            </div>
            <div class="em-hint">Stoppt „Schnellladen“ bei diesem Akkustand automatisch.</div>
          </div>

          <!-- DHW & AC Buffer Switches & Quick Actions -->
          <div class="em-ctrl-box" style="justify-content:space-between">
            <div class="em-switch-row">
              <div>
                <div class="em-ctrl-lbl">🚿 Warmwasser-WP Automatik</div>
                <div class="em-hint">PV-Aufheizung bis ${_fmtNum(dhwTargetTemp, 0)} °C & Winter-Schutz (&lt; ${_fmtNum(dhwMinTemp, 0)} °C).</div>
              </div>
              <label class="em-switch">
                <input type="checkbox" data-switch="dhw_enabled" ${dhwEnabled ? 'checked' : ''}>
                <span class="em-switch-track"></span>
              </label>
            </div>
            <div class="em-switch-row" style="padding-top:6px;border-top:1px solid var(--divider-color, rgba(127,127,127,0.12))">
              <div>
                <div class="em-ctrl-lbl">❄️ Klimaanlage als Wärmepuffer</div>
                <div class="em-hint">Sollwert um ±${_fmtNum(this._num('ac_buffer_temp_offset', 2.5), 1)} °C bei Überschuss anpassen.</div>
              </div>
              <label class="em-switch">
                <input type="checkbox" data-switch="ac_buffer_enabled" ${acEnabled ? 'checked' : ''}>
                <span class="em-switch-track"></span>
              </label>
            </div>
            <div class="em-switch-row" style="padding-top:6px;border-top:1px solid var(--divider-color, rgba(127,127,127,0.12))">
              <div>
                <div class="em-ctrl-lbl">🔥 Auto-Heizen wenn Klima aus</div>
                <div class="em-hint">Schaltet Klima bei ≤ ${_fmtNum(acMaxOutdoor, 1)} °C außen zum Heizen ein.</div>
              </div>
              <label class="em-switch">
                <input type="checkbox" data-switch="ac_auto_heat_enabled" ${acAutoHeat ? 'checked' : ''}>
                <span class="em-switch-track"></span>
              </label>
            </div>
            <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:6px">
              <button class="em-btn" data-action="wakeup-tesla">⚡ Tesla aufwecken</button>
              <button class="em-btn" data-tab="settings">⚙️ Schwellenwerte</button>
            </div>
          </div>
        </div>
      </div>
    `;
  }

  _htmlSessions() {
    const solarKwh = this._num('ev_solar_lifetime_kwh', 0);
    const gridKwh = this._num('ev_grid_lifetime_kwh', 0);
    const totalKwh = solarKwh + gridKwh;
    const solarPct = totalKwh > 0 ? Math.round((solarKwh / totalKwh) * 100) : 100;
    const sessionActive = this._bool('ev_session_active');

    const sumSt = this._stateObj('last_session_summary');
    const summaryText = sumSt && sumSt.state && sumSt.state !== 'unknown' ? sumSt.state : 'Noch keine abgeschlossene Ladesitzung';
    const attrs = (sumSt && sumSt.attributes) || {};

    return `
      <div class="em-stats">
        <div class="em-stat">
          <div class="em-stat-top"><span>Geladen über Solar</span><span>☀️</span></div>
          <div class="em-stat-val" style="color:#10b981">${_fmtNum(solarKwh, 2)} kWh</div>
          <div class="em-stat-sub">Eigener PV-Strom insgesamt</div>
        </div>
        <div class="em-stat">
          <div class="em-stat-top"><span>Geladen über Netz</span><span>🔌</span></div>
          <div class="em-stat-val" style="color:#ef4444">${_fmtNum(gridKwh, 2)} kWh</div>
          <div class="em-stat-sub">Netzstrom insgesamt</div>
        </div>
        <div class="em-stat">
          <div class="em-stat-top"><span>Solar-Anteil</span><span>📊</span></div>
          <div class="em-stat-val" style="color:var(--em-solar)">${_fmtNum(solarPct, 0)} %</div>
          <div class="em-stat-sub">Gesamt: ${_fmtNum(totalKwh, 2)} kWh</div>
        </div>
        <div class="em-stat">
          <div class="em-stat-top"><span>Aktuelle Sitzung</span><span>🚗</span></div>
          <div class="em-stat-val" style="font-size:1.25em">${sessionActive ? '🟢 Lädt gerade' : '⚪ Keine Ladung'}</div>
          <div class="em-stat-sub">Wird automatisch aufgezeichnet</div>
        </div>
      </div>

      <div class="em-card">
        <div class="em-card-head">
          <div class="em-card-title">☀️ Lebenszeit Solar- vs. Netzanteil (Gesamtbilanz)</div>
        </div>
        <div class="em-split-bar" style="height:18px">
          <div class="em-split-solar" style="width:${solarPct}%"></div>
          <div class="em-split-grid" style="width:${100 - solarPct}%"></div>
        </div>
        <div class="em-split-legend">
          <span>☀️ <strong>${_fmtNum(solarKwh, 3)} kWh (${solarPct} %)</strong> aus eigenem PV-Überschuss</span>
          <span>🔌 <strong>${_fmtNum(gridKwh, 3)} kWh (${100 - solarPct} %)</strong> aus dem Stromnetz</span>
        </div>
      </div>

      <div class="em-card">
        <div class="em-card-head">
          <div class="em-card-title">📋 Letzte abgeschlossene Ladesitzung</div>
          <span class="em-badge em-badge-info">${_esc(summaryText)}</span>
        </div>
        <table class="em-table">
          <thead>
            <tr>
              <th>Kennzahl</th>
              <th>Wert</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>Gesamtenergie der Sitzung</strong></td>
              <td>${attrs.energy_total_kwh != null ? `${_fmtNum(attrs.energy_total_kwh, 2)} kWh` : '–'}</td>
            </tr>
            <tr>
              <td><strong>Davon Solarstrom (PV-Überschuss)</strong></td>
              <td>${attrs.energy_solar_kwh != null ? `${_fmtNum(attrs.energy_solar_kwh, 2)} kWh (${_fmtNum(attrs.solar_percentage, 1)} %)` : '–'}</td>
            </tr>
            <tr>
              <td><strong>Davon Netzstrom</strong></td>
              <td>${attrs.energy_grid_kwh != null ? `${_fmtNum(attrs.energy_grid_kwh, 2)} kWh (${_fmtNum(attrs.grid_percentage, 1)} %)` : '–'}</td>
            </tr>
            <tr>
              <td><strong>Ladedauer</strong></td>
              <td>${attrs.duration_minutes != null ? `${_fmtNum(attrs.duration_minutes, 1)} min` : '–'}</td>
            </tr>
            <tr>
              <td><strong>Fahrzeug-SOC (Start → Ziel)</strong></td>
              <td>${attrs.start_soc != null || attrs.end_soc != null ? `${_fmtNum(attrs.start_soc, 0)} % → ${_fmtNum(attrs.end_soc, 0)} %` : '–'}</td>
            </tr>
            <tr>
              <td><strong>Berechnete Netzkosten (${_fmtNum(this._num('electricity_price', 0.3), 2)} €/kWh)</strong></td>
              <td>${attrs.cost_eur != null ? `${_fmtNum(attrs.cost_eur, 2)} €` : '–'}</td>
            </tr>
          </tbody>
        </table>
      </div>
    `;
  }

  _htmlTraces() {
    const traceSt = this._stateObj('last_action_trace');
    const attrs = (traceSt && traceSt.attributes) || {};
    const tracingEnabled = this._bool('action_tracing_enabled') || !!attrs.tracing_enabled;
    const rawTraces = Array.isArray(attrs.recent_traces) ? attrs.recent_traces : [];
    const traces = [...rawTraces].reverse();
    const traceCount = traces.length;

    const filter = this._traceFilter || 'all';

    const filtered = filter === 'all'
      ? traces
      : traces.filter((t) => t.category === filter);

    const filterBtns = [
      { id: 'all', label: 'Alle' },
      { id: 'ev', label: '🚗 Tesla EV' },
      { id: 'dhw', label: '💧 Warmwasser' },
      { id: 'ac', label: '❄️ Klima' },
      { id: 'battery', label: '🔋 Speicher' },
      { id: 'system', label: '⚙️ System' },
    ]
      .map(
        (f) => `
        <button class="em-btn ${filter === f.id ? 'em-btn-primary' : ''}" data-trace-filter="${f.id}">
          ${f.label}
        </button>
      `
      )
      .join('');

    let listHtml = '';
    if (filtered.length === 0) {
      listHtml = `
        <div class="em-empty-box">
          <div style="font-size:2.2em;margin-bottom:8px">🔍</div>
          <div style="font-weight:600;font-size:1.05em">Keine Aktions-Traces vorhanden</div>
          <div style="font-size:0.85em;color:var(--secondary-text-color);margin-top:6px;max-width:500px;line-height:1.45">
            ${
              tracingEnabled
                ? 'Die Aufzeichnung ist aktiv. Sobald der Energiemanager einen Steuerbefehl ausführt (z. B. Ladestrom regelt, Wärmepumpe umschaltet oder Klima anpasst), erscheint dieser sofort hier.'
                : 'Aktiviere oben <strong>Aktionen aufzeichnen</strong>, um alle Steuerbefehle und Entscheidungen live zu protokollieren.'
            }
          </div>
        </div>
      `;
    } else {
      const itemsHtml = filtered
        .map((t) => {
          const cat = _esc(t.category || 'system');
          const catLabels = {
            ev: 'Tesla EV',
            dhw: 'Warmwasser',
            ac: 'Klima',
            battery: 'Speicher',
            system: 'System',
          };
          const catIcons = {
            ev: '🚗',
            dhw: '💧',
            ac: '❄️',
            battery: '🔋',
            system: '⚙️',
          };
          const catLabel = catLabels[cat] || cat.toUpperCase();
          const catIcon = catIcons[cat] || '📋';
          const action = _esc(t.action || '–');
          const reason = _esc(t.reason || '');
          const target = t.target ? `<span class="em-trace-target">${_esc(t.target)}</span>` : '';
          const time = _esc(t.time || (t.timestamp ? t.timestamp.split('T')[1].split('.')[0] : '–'));

          return `
            <div class="em-trace-item">
              <div class="em-trace-head">
                <span class="em-trace-cat em-trace-cat-${cat}">
                  <span>${catIcon}</span>
                  <span>${catLabel}</span>
                </span>
                ${target}
                <span style="flex:1"></span>
                <span class="em-trace-time">⏱️ ${time}</span>
              </div>
              <div class="em-trace-body">${action}</div>
              ${reason ? `<div class="em-trace-reason"><strong>Grund:</strong> ${reason}</div>` : ''}
            </div>
          `;
        })
        .join('');

      listHtml = `<div class="em-trace-timeline">${itemsHtml}</div>`;
    }

    return `
      <div class="em-card" style="margin-bottom:16px">
        <div class="em-card-head" style="flex-wrap:wrap;gap:12px">
          <div>
            <div class="em-card-title">🔍 Live Action-Traces & Regelungs-Protokoll</div>
            <div class="em-card-sub" style="font-size:0.8em;color:var(--secondary-text-color);margin-top:2px">
              Protokolliert alle Steuerbefehle (Ladestrom, Schalter, Wärmepumpe, Klima) und Begründungen
            </div>
          </div>
          <span style="flex:1"></span>
          <div style="display:flex;align-items:center;gap:14px;flex-wrap:wrap">
            <label style="display:inline-flex;align-items:center;gap:8px;cursor:pointer;font-weight:600;font-size:0.9em">
              <input type="checkbox" data-switch="action_tracing_enabled" ${tracingEnabled ? 'checked' : ''}>
              <span>Aktionen aufzeichnen</span>
            </label>
            <button class="em-btn" data-action="clear-traces" title="Alle aufgezeichneten Traces löschen" ${traceCount === 0 ? 'disabled' : ''}>
              🗑️ Traces leeren
            </button>
            <button class="em-btn" data-action="recalculate" title="Neu auslesen">
              ↻ Aktualisieren
            </button>
          </div>
        </div>

        <div style="display:flex;align-items:center;justify-content:space-between;margin-top:14px;padding-top:12px;border-top:1px solid var(--divider-color, rgba(127,127,127,0.12));flex-wrap:wrap;gap:10px">
          <div style="display:flex;align-items:center;gap:8px;font-size:0.85em">
            <span class="em-dot ${tracingEnabled ? 'em-pulse' : ''}" style="background:${tracingEnabled ? '#10b981' : '#94a3b8'}"></span>
            <span>${tracingEnabled ? `<strong>Aufzeichnung aktiv</strong> (${traceCount} Aktionen)` : 'Aufzeichnung inaktiv'}</span>
          </div>
          <div style="display:flex;gap:6px;flex-wrap:wrap">
            ${filterBtns}
          </div>
        </div>
      </div>

      <div class="em-card">
        ${listHtml}
      </div>
    `;
  }

  _htmlSettings() {
    const sectionsHtml = _THRESHOLD_SECTIONS
      .map((sec) => {
        const fieldsHtml = sec.fields
          .map((f) => {
            const val = this._num(f.key, 0);
            return `
              <div class="em-ctrl-box">
                <div class="em-ctrl-top">
                  <span class="em-ctrl-lbl">${_esc(f.label)}</span>
                  <span class="em-ctrl-readout" id="lbl-${f.key}">${_fmtNum(val, f.dec)}${f.unit ? ' ' + _esc(f.unit) : ''}</span>
                </div>
                <div class="em-slider-row">
                  <input type="range" min="${f.min}" max="${f.max}" step="${f.step}" value="${val}" data-num-slider="${f.key}" data-dec="${f.dec}" data-unit="${_esc(f.unit)}">
                  <input type="number" class="em-num-input" min="${f.min}" max="${f.max}" step="${f.step}" value="${val}" data-num-input="${f.key}">
                </div>
                <div class="em-hint">${_esc(f.hint)}</div>
              </div>
            `;
          })
          .join('');

        return `
          <div class="em-card">
            <div class="em-card-head" style="margin-bottom:6px">
              <div class="em-card-title">${_esc(sec.title)}</div>
            </div>
            <p class="em-hint" style="margin:0 0 14px">${_esc(sec.intro)}</p>
            <div class="em-ctrl-grid">${fieldsHtml}</div>
          </div>
        `;
      })
      .join('');

    const src = this._sourceEntities();
    const srcRows = Object.entries(src)
      .filter(([, eid]) => !!eid)
      .map(([k, eid]) => {
        const st = this._hass && this._hass.states ? this._hass.states[eid] : null;
        const unit = st && st.attributes && st.attributes.unit_of_measurement ? ` ${st.attributes.unit_of_measurement}` : '';
        const val = st ? `${st.state}${unit}` : 'nicht gefunden';
        return `<tr><td><code>${_esc(k)}</code></td><td><code>${_esc(eid)}</code></td><td><strong>${_esc(val)}</strong></td></tr>`;
      })
      .join('');

    return `
      ${sectionsHtml}
      <div class="em-card">
        <div class="em-card-head">
          <div class="em-card-title">🔗 Verknüpfte Hardware-Quellentitäten (Config Entry)</div>
        </div>
        ${srcRows
        ? `<table class="em-table"><thead><tr><th>Zuordnung</th><th>Entity-ID</th><th>Live-Zustand</th></tr></thead><tbody>${srcRows}</tbody></table>`
        : `<p class="em-hint">Keine Quellentitäten geladen.</p>`}
      </div>
    `;
  }

  _htmlSimulator() {
    const states = (this._hass && this._hass.states) || {};
    const numBoxes = _SIM_NUMBERS
      .filter((s) => s.id in states)
      .map((s) => {
        const st = states[s.id];
        const val = st && isFinite(Number(st.state)) ? Number(st.state) : 0;
        return `
          <div class="em-ctrl-box">
            <div class="em-ctrl-top">
              <span class="em-ctrl-lbl">${_esc(s.label)}</span>
              <span class="em-ctrl-readout" id="sim-lbl-${_esc(s.id)}">${_fmtNum(val, s.step < 1 ? 1 : 0)} ${_esc(s.unit)}</span>
            </div>
            <div class="em-slider-row">
              <input type="range" min="${s.min}" max="${s.max}" step="${s.step}" value="${val}" data-sim-slider="${_esc(s.id)}" data-unit="${_esc(s.unit)}">
              <input type="number" class="em-num-input" min="${s.min}" max="${s.max}" step="${s.step}" value="${val}" data-sim-input="${_esc(s.id)}">
            </div>
            <div class="em-hint"><code>${_esc(s.id)}</code></div>
          </div>
        `;
      })
      .join('');

    const boolBoxes = _SIM_BOOLEANS
      .filter((b) => b.id in states)
      .map((b) => {
        const st = states[b.id];
        const on = st && st.state === 'on';
        return `
          <div class="em-ctrl-box">
            <div class="em-switch-row">
              <div>
                <div class="em-ctrl-lbl">${_esc(b.label)}</div>
                <div class="em-hint"><code>${_esc(b.id)}</code></div>
              </div>
              <label class="em-switch">
                <input type="checkbox" data-sim-bool="${_esc(b.id)}" ${on ? 'checked' : ''}>
                <span class="em-switch-track"></span>
              </label>
            </div>
          </div>
        `;
      })
      .join('');

    return `
      <div class="em-card">
        <div class="em-card-head">
          <div class="em-card-title">🧪 Test-Simulator (Szenarien live durchspielen)</div>
          <div style="display:flex;gap:8px;flex-wrap:wrap">
            <button class="em-btn" data-preset="idle">🏠 Normalbetrieb (-50 W)</button>
            <button class="em-btn" data-preset="ac">❄️ Mittlerer Überschuss (-950 W → Klima)</button>
            <button class="em-btn em-btn-primary" data-preset="ev">🚗 Hoher PV-Überschuss (-2.600 W → Tesla)</button>
          </div>
        </div>
        <p class="em-hint" style="margin:0 0 14px">
          Verändere hier die simulierten Sensoren oder wähle ein Schnell-Szenario oben rechts, um die Reaktion der Kaskade sofort zu beobachten.
        </p>
        <div class="em-ctrl-grid">${numBoxes}${boolBoxes}</div>
      </div>
    `;
  }

  _wire() {
    const sr = this.shadowRoot;
    if (!sr) return;

    const burger = sr.getElementById('em-burger');
    if (burger) {
      burger.addEventListener('click', () => {
        this.dispatchEvent(new CustomEvent('hass-toggle-menu', { bubbles: true, composed: true }));
      });
    }

    sr.querySelectorAll('[data-tab]').forEach((btn) => {
      btn.addEventListener('click', () => {
        this._tab = btn.dataset.tab;
        this._render();
      });
    });

    sr.querySelectorAll('[data-mode]').forEach((btn) => {
      btn.addEventListener('click', () => {
        this._setSelect('charging_mode', btn.dataset.mode);
      });
    });

    sr.querySelectorAll('[data-select]').forEach((sel) => {
      sel.addEventListener('change', () => {
        this._setSelect(sel.dataset.select, sel.value);
      });
    });

    sr.querySelectorAll('[data-switch]').forEach((chk) => {
      chk.addEventListener('change', () => {
        this._setSwitch(chk.dataset.switch, chk.checked);
      });
    });

    sr.querySelectorAll('[data-num-slider]').forEach((slider) => {
      const key = slider.dataset.numSlider;
      slider.addEventListener('input', () => {
        const numInp = sr.querySelector(`[data-num-input="${key}"]`);
        if (numInp) numInp.value = slider.value;
        const lbl = sr.getElementById(`lbl-${key}`);
        if (lbl) {
          const unit = slider.dataset.unit || (key.includes('soc') ? '%' : key.includes('current') ? 'A' : '');
          lbl.textContent = `${slider.value}${unit ? ' ' + unit : ''}`;
        }
      });
      slider.addEventListener('change', () => {
        this._setNumber(key, slider.value);
      });
    });

    sr.querySelectorAll('[data-num-input]').forEach((inp) => {
      const key = inp.dataset.numInput;
      inp.addEventListener('change', () => {
        this._setNumber(key, inp.value);
      });
    });

    sr.querySelectorAll('[data-sim-slider]').forEach((slider) => {
      const simId = slider.dataset.simSlider;
      slider.addEventListener('input', () => {
        const inp = sr.querySelector(`[data-sim-input="${simId}"]`);
        if (inp) inp.value = slider.value;
        const lbl = sr.getElementById(`sim-lbl-${simId}`);
        if (lbl) lbl.textContent = `${slider.value} ${slider.dataset.unit || ''}`;
      });
      slider.addEventListener('change', async () => {
        await this._hass.callService('input_number', 'set_value', {
          entity_id: simId,
          value: Number(slider.value),
        });
        const refreshEid = this._entId('grid_power_filtered') || 'sensor.energiemanager_grid_power_filtered';
        await this._hass.callService('homeassistant', 'update_entity', { entity_id: refreshEid });
      });
    });

    sr.querySelectorAll('[data-sim-input]').forEach((inp) => {
      const simId = inp.dataset.simInput;
      inp.addEventListener('change', async () => {
        await this._hass.callService('input_number', 'set_value', {
          entity_id: simId,
          value: Number(inp.value),
        });
        const refreshEid = this._entId('grid_power_filtered') || 'sensor.energiemanager_grid_power_filtered';
        await this._hass.callService('homeassistant', 'update_entity', { entity_id: refreshEid });
      });
    });

    sr.querySelectorAll('[data-sim-bool]').forEach((chk) => {
      const simId = chk.dataset.simBool;
      chk.addEventListener('change', async () => {
        await this._hass.callService('input_boolean', chk.checked ? 'turn_on' : 'turn_off', {
          entity_id: simId,
        });
        const refreshEid = this._entId('grid_power_filtered') || 'sensor.energiemanager_grid_power_filtered';
        await this._hass.callService('homeassistant', 'update_entity', { entity_id: refreshEid });
      });
    });

    sr.querySelectorAll('[data-preset]').forEach((btn) => {
      btn.addEventListener('click', async () => {
        const p = btn.dataset.preset;
        if (p === 'idle') {
          await this._hass.callService('input_number', 'set_value', { entity_id: 'input_number.sim_grid_power', value: -50 });
          await this._hass.callService('input_number', 'set_value', { entity_id: 'input_number.sim_tesla_charging_power', value: 0 });
        } else if (p === 'ac') {
          await this._hass.callService('input_number', 'set_value', { entity_id: 'input_number.sim_anker_battery_soc', value: 80 });
          await this._hass.callService('input_number', 'set_value', { entity_id: 'input_number.sim_grid_power', value: -950 });
          await this._hass.callService('input_number', 'set_value', { entity_id: 'input_number.sim_tesla_charging_power', value: 0 });
        } else if (p === 'ev') {
          await this._hass.callService('input_number', 'set_value', { entity_id: 'input_number.sim_anker_battery_soc', value: 85 });
          await this._hass.callService('input_number', 'set_value', { entity_id: 'input_number.sim_grid_power', value: -2600 });
          await this._hass.callService('input_boolean', 'turn_on', { entity_id: 'input_boolean.sim_tesla_plugged' });
          await this._hass.callService('input_boolean', 'turn_on', { entity_id: 'input_boolean.sim_tesla_ble_connected' });
        }
        const refreshEid = this._entId('grid_power_filtered') || 'sensor.energiemanager_grid_power_filtered';
        await this._hass.callService('homeassistant', 'update_entity', { entity_id: refreshEid });
        this._showToast('Szenario aktiviert & neu berechnet');
      });
    });

    sr.querySelectorAll('[data-trace-filter]').forEach((btn) => {
      btn.addEventListener('click', () => {
        this._traceFilter = btn.dataset.traceFilter;
        this._render();
      });
    });

    sr.querySelectorAll('[data-action]').forEach((btn) => {
      btn.addEventListener('click', async () => {
        const act = btn.dataset.action;
        if (act === 'clear-traces') {
          await this._hass.callService('sam_energiemanager', 'clear_traces', {});
          this._showToast('Traces geleert');
        } else if (act === 'recalculate') {
          const refreshEid = this._entId('grid_power_filtered') || 'sensor.energiemanager_grid_power_filtered';
          await this._hass.callService('homeassistant', 'update_entity', { entity_id: refreshEid });
          this._showToast('Regelschleife neu berechnet');
        } else if (act === 'wakeup-tesla') {
          const src = this._sourceEntities();
          const wakeBtn = src.ev_wakeup_button;
          if (wakeBtn) {
            await this._hass.callService('button', 'press', { entity_id: wakeBtn });
            this._showToast('Wake-Up gesendet');
          } else {
            this._showToast('Kein Wake-Up-Button konfiguriert');
          }
        }
      });
    });
  }
}

if (!customElements.get('sam-energiemanager-panel')) {
  customElements.define('sam-energiemanager-panel', SamEnergiemanagerPanel);
}
