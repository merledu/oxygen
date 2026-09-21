// Oxygen RISC-V Simulator Frontend Engine
// Full Support for RISC-V IMFCDV Extensions (Spike & Custom Engines)

// 1. Global State
let currentSimulator = 'spike'; // 'spike' or 'custom'
let isHexNotation = true;
let floatViewMode = 'double'; // 'double', 'single', 'hex'
let currentSEW = 32; // 8, 16, 32, 64, or 'raw'
let activeInspectorTab = 'integer';

let isPlaying = false;
let playTimer = null;
let breakpoints = new Set();

let prevIntRegisters = new Array(32).fill(0);
let currentIntRegisters = new Array(32).fill(0);

let currentFRegisters = new Array(32).fill(0.0);
let currentDRegisters = new Array(32).fill(0.0);
let currentFHex = new Array(32).fill('0x0000000000000000');
let prevFRegisters = new Array(32).fill(0.0);
let prevDRegisters = new Array(32).fill(0.0);
let prevFHex = new Array(32).fill('0x0000000000000000');

let currentVRegisters = Array.from({ length: 32 }, () => [0, 0]);
let currentVElements = { '8': [], '16': [], '32': [], '64': [] };
let prevVRegisters = Array.from({ length: 32 }, () => [0, 0]);
let prevVElements = { '8': [], '16': [], '32': [], '64': [] };
let vectorStatus = { vl: 0, sew: 32, lmul: 'm1' };

let memoryDict = {};
let currentMemoryBase = 0x80000000;
let currentPC = 0;
let decoderInstructions = [];

const ABI_INT_NAMES = [
  "zero", "ra", "sp", "gp", "tp", "t0", "t1", "t2",
  "s0/fp", "s1", "a0", "a1", "a2", "a3", "a4", "a5",
  "a6", "a7", "s2", "s3", "s4", "s5", "s6", "s7",
  "s8", "s9", "s10", "s11", "t3", "t4", "t5", "t6"
];

const ABI_FLOAT_NAMES = [
  "ft0", "ft1", "ft2", "ft3", "ft4", "ft5", "ft6", "ft7",
  "fs0", "fs1", "fa0", "fa1", "fa2", "fa3", "fa4", "fa5",
  "fa6", "fa7", "fs2", "fs3", "fs4", "fs5", "fs6", "fs7",
  "fs8", "fs9", "fs10", "fs11", "ft8", "ft9", "ft10", "ft11"
];

// Toast Notification System (Non-blocking replacement for window.alert)
function showToast(message, type = 'error') {
  const container = document.getElementById('toast-container');
  if (!container) {
    alert(message);
    return;
  }
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  const icon = type === 'error' ? '❌' : (type === 'success' ? '✅' : 'ℹ️');
  toast.innerHTML = `<span style="font-size: 14px;">${icon}</span><span style="flex: 1; word-break: break-word;">${message}</span>`;
  toast.addEventListener('click', () => {
    toast.classList.add('toast-closing');
    setTimeout(() => toast.remove(), 200);
  });
  container.appendChild(toast);
  setTimeout(() => {
    if (toast.parentNode) {
      toast.classList.add('toast-closing');
      setTimeout(() => toast.remove(), 200);
    }
  }, 4000);
}

// 2. Initialization on Load
document.addEventListener('DOMContentLoaded', () => {
  // Initialize register tables once
  initIntegerRegisterTable();
  initFloatRegisterTable();
  initVectorRegisterTable();
  initMemoryTable();

  // Restore saved editor code if present
  try {
    const savedCode = localStorage.getItem('oxygen_editor_code');
    if (savedCode) {
      const editor = document.getElementById('editor-text-box');
      if (editor) {
        editor.value = savedCode;
      }
    }
  } catch (e) {}

  // Save editor code on input
  const editorBox = document.getElementById('editor-text-box');
  if (editorBox) {
    editorBox.addEventListener('input', () => {
      try {
        localStorage.setItem('oxygen_editor_code', editorBox.value);
      } catch (e) {}
    });
  }

  // Preserve 1.8s splash screen smoothly (user requested)
  const splash = document.getElementById('splash_screen');
  if (splash) {
    setTimeout(() => {
      splash.classList.add('hidden');
    }, 1800);
    splash.addEventListener('click', () => splash.classList.add('hidden'));
  }

  // Universal Keyboard Shortcuts (F5, Alt+R, Ctrl+R, F10, F9, Ctrl+Enter)
  function handleGlobalShortcuts(e) {
    // 1. Run shortcuts: F5, Alt+R, Ctrl+R, Ctrl+Shift+Enter, Shift+Enter
    const isRun = (
      e.key === 'F5' ||
      (e.altKey && (e.key === 'r' || e.key === 'R')) ||
      ((e.ctrlKey || e.metaKey) && (e.key === 'r' || e.key === 'R')) ||
      ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'Enter')
    );

    if (isRun) {
      e.preventDefault();
      e.stopPropagation();
      run_Code();
      return;
    }

    // 2. Assemble shortcut: Ctrl+Enter / Cmd+Enter (without Shift)
    if ((e.ctrlKey || e.metaKey) && !e.shiftKey && e.key === 'Enter') {
      e.preventDefault();
      e.stopPropagation();
      assemble_code();
      return;
    }

    // 3. Step shortcut: F10 or Alt+S
    if (e.key === 'F10' || (e.altKey && (e.key === 's' || e.key === 'S'))) {
      e.preventDefault();
      e.stopPropagation();
      stepInstruction();
      return;
    }

    // 4. Reset shortcut: Alt+X
    if (e.altKey && (e.key === 'x' || e.key === 'X')) {
      e.preventDefault();
      e.stopPropagation();
      reset_Registers();
      return;
    }

    // 5. Toggle breakpoint on selected row: F9
    if (e.key === 'F9') {
      e.preventDefault();
      e.stopPropagation();
      const activeRow = document.querySelector('#decoderTableBody tr.highlight');
      if (activeRow && activeRow.dataset.pc) {
        toggleBreakpoint(activeRow.dataset.pc);
      }
      return;
    }
  }

  // Use capture phase so shortcuts work inside textareas and before browser defaults
  window.addEventListener('keydown', handleGlobalShortcuts, true);

  // Memory scroll buttons
  const upBtn = document.getElementById('scrollUpBtn');
  const downBtn = document.getElementById('scrollDownBtn');
  if (upBtn) {
    upBtn.addEventListener('click', () => {
      currentMemoryBase = Math.max(0, currentMemoryBase - 16) >>> 0;
      updateMemoryTable();
    });
  }
  if (downBtn) {
    downBtn.addEventListener('click', () => {
      currentMemoryBase = (currentMemoryBase + 16) >>> 0;
      updateMemoryTable();
    });
  }

  // Initialize UI Features: Theme, Splitters, Gutter, Autocomplete
  initTheme();
  initSplitters();
  initEditorGutter();
  initAutocomplete();
});

// 3. Simulator & Extension Controls
function setSimulator(sim) {
  currentSimulator = sim;
  const spikeBtn = document.getElementById('sim-spike-btn');
  const customBtn = document.getElementById('sim-custom-btn');

  if (sim === 'spike') {
    spikeBtn.classList.add('active');
    customBtn.classList.remove('active');
    currentMemoryBase = 0x80000000;
  } else {
    customBtn.classList.add('active');
    spikeBtn.classList.remove('active');
    currentMemoryBase = 0x00000000;
  }
  reset_Registers();
}

function toggleExtension(ext) {
  const checkbox = document.getElementById(`${ext}-type`);
  const badge = document.getElementById(`badge-${ext}`);
  if (!checkbox || !badge) return;

  checkbox.checked = !checkbox.checked;
  if (checkbox.checked) {
    badge.classList.add('active');
    if (ext === 'D') {
      // D requires F
      const fCheck = document.getElementById('F-type');
      const fBadge = document.getElementById('badge-F');
      if (fCheck && !fCheck.checked) {
        fCheck.checked = true;
        fBadge.classList.add('active');
      }
    }
  } else {
    badge.classList.remove('active');
    if (ext === 'F') {
      // Unchecking F disables D
      const dCheck = document.getElementById('D-type');
      const dBadge = document.getElementById('badge-D');
      if (dCheck && dCheck.checked) {
        dCheck.checked = false;
        dBadge.classList.remove('active');
      }
    }
  }
}

// 4. Sample Code Loader
const SAMPLES = {
  arithmetic: `# Basic Integer Arithmetic (RV32I)
addi x1, x0, 10
addi x2, x0, 20
add  x3, x1, x2
sub  x4, x3, x1
slli x5, x4, 2
xor  x6, x1, x2
and  x7, x3, x4
`,
  float_double: `# Double-Precision Floating-Point (RV32IFD)
addi x1, x0, 5
addi x2, x0, 8
fcvt.d.w f1, x1
fcvt.d.w f2, x2
fadd.d   f3, f1, f2
fmul.d   f4, f1, f2
fsub.d   f5, f4, f3
`,
  vector: `# Vector Operations (RV32IV)
vsetvli t0, x0, e32, m1
vmv.v.i v1, 7
vmv.v.i v2, 3
vadd.vv v3, v1, v2
vmul.vv v4, v1, v2
`,
  memory: `# Sub-Word Memory Stores (sb, sh, sw)
lui  x1, 0x80001
addi x2, x0, 0x5a
sb   x2, 1(x1)
addi x3, x0, 0x123
sh   x3, 4(x1)
addi x4, x0, 0x789
sw   x4, 8(x1)
`,
  loop: `# Branch Loop Counter (RV32I)
addi x1, x0, 5
addi x2, x0, 0
loop:
addi x2, x2, 10
addi x1, x1, -1
bne  x1, x0, loop
`
};

function loadSampleCode(key) {
  const code = SAMPLES[key];
  if (!code) return;
  const editor = document.getElementById('editor-text-box');
  if (editor) {
    editor.value = code;
    updateLineNumbers();
  }

  // Auto-enable extensions based on sample
  if (key === 'float_double') {
    enableExt('F');
    enableExt('D');
  } else if (key === 'vector') {
    enableExt('V');
  }
}

function enableExt(ext) {
  const checkbox = document.getElementById(`${ext}-type`);
  const badge = document.getElementById(`badge-${ext}`);
  if (checkbox && badge && !checkbox.checked) {
    checkbox.checked = true;
    badge.classList.add('active');
  }
}

// 5. Inspector Tabs & View Mode
function switchInspectorTab(tabId) {
  activeInspectorTab = tabId;
  document.querySelectorAll('.tab-nav-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.tab === tabId);
  });
  document.querySelectorAll('.tab-pane').forEach(pane => {
    pane.classList.toggle('active', pane.id === `tab-${tabId}`);
  });
  updateAllInspectors();
}

function changeNotation(val) {
  isHexNotation = (val === 'hex');
  updateIntegerRegisters();
  updateFloatRegisters();
  updateVectorRegisters();
  updateMemoryTable();
}

function setFloatViewMode(mode) {
  floatViewMode = mode;
  document.getElementById('fview-double-btn').classList.toggle('active', mode === 'double');
  document.getElementById('fview-single-btn').classList.toggle('active', mode === 'single');
  document.getElementById('fview-hex-btn').classList.toggle('active', mode === 'hex');
  updateFloatRegisters();
}

function setVectorSEW(sew) {
  currentSEW = sew;
  [8, 16, 32, 64, 'raw'].forEach(s => {
    const btn = document.getElementById(`sew-${s}-btn`);
    if (btn) btn.classList.toggle('active', s === sew);
  });
  initVectorRegisterTable();
}

// 6. Persistent DOM Register & Memory Tables with Targeted Diffing
function initIntegerRegisterTable() {
  const tbody = document.getElementById('integer-reg-tbody');
  if (!tbody) return;
  tbody.innerHTML = '';
  for (let i = 0; i < 32; i++) {
    const tr = document.createElement('tr');
    tr.id = `int-row-${i}`;
    tr.innerHTML = `
      <td class="reg-name">x${i}</td>
      <td class="reg-abi">${ABI_INT_NAMES[i]}</td>
      <td class="reg-val" id="reg-${i}">0x00000000</td>
    `;
    tbody.appendChild(tr);
  }
}

function updateIntegerRegisters() {
  if (!document.getElementById('reg-0')) {
    initIntegerRegisterTable();
  }
  for (let i = 0; i < 32; i++) {
    const val = currentIntRegisters[i] || 0;
    const isChanged = (val !== prevIntRegisters[i]);
    const cell = document.getElementById(`reg-${i}`);
    if (cell) {
      const formatted = isHexNotation
        ? `0x${(val >>> 0).toString(16).padStart(8, '0')}`
        : (val | 0).toString(10);
      if (cell.textContent !== formatted) {
        cell.textContent = formatted;
      }
      cell.classList.toggle('changed', isChanged);
    }
  }
}

function initFloatRegisterTable() {
  const tbody = document.getElementById('float-reg-tbody');
  if (!tbody) return;
  tbody.innerHTML = '';
  for (let i = 0; i < 32; i++) {
    const tr = document.createElement('tr');
    tr.id = `float-row-${i}`;
    tr.innerHTML = `
      <td class="reg-name">f${i}</td>
      <td class="reg-abi">${ABI_FLOAT_NAMES[i]}</td>
      <td class="reg-val" id="freg-${i}">0.0</td>
    `;
    tbody.appendChild(tr);
  }
}

function updateFloatRegisters() {
  if (!document.getElementById('freg-0')) {
    initFloatRegisterTable();
  }
  for (let i = 0; i < 32; i++) {
    let displayVal = '0.0';
    let isChanged = false;
    if (floatViewMode === 'double') {
      const val = (currentDRegisters[i] !== undefined) ? currentDRegisters[i] : (currentFRegisters[i] || 0.0);
      const prev = (prevDRegisters[i] !== undefined) ? prevDRegisters[i] : (prevFRegisters[i] || 0.0);
      isChanged = (val !== prev);
      displayVal = val;
    } else if (floatViewMode === 'single') {
      const val = (currentFRegisters[i] !== undefined) ? currentFRegisters[i] : 0.0;
      const prev = (prevFRegisters[i] !== undefined) ? prevFRegisters[i] : 0.0;
      isChanged = (val !== prev);
      displayVal = val;
    } else if (floatViewMode === 'hex') {
      const val = currentFHex[i] || '0x0000000000000000';
      const prev = prevFHex[i] || '0x0000000000000000';
      isChanged = (val !== prev);
      displayVal = val;
    }

    const cell = document.getElementById(`freg-${i}`);
    if (cell) {
      if (cell.textContent !== String(displayVal)) {
        cell.textContent = displayVal;
      }
      cell.classList.toggle('changed', isChanged);
    }
  }
}

function initVectorRegisterTable() {
  const container = document.getElementById('vector-reg-tbody');
  if (!container) return;

  const vlEl = document.getElementById('v-status-vl');
  const sewEl = document.getElementById('v-status-sew');
  const lmulEl = document.getElementById('v-status-lmul');
  if (vlEl) vlEl.innerText = vectorStatus.vl;
  if (sewEl) sewEl.innerText = vectorStatus.sew;
  if (lmulEl) lmulEl.innerText = vectorStatus.lmul;

  container.innerHTML = '';
  for (let i = 0; i < 32; i++) {
    const row = document.createElement('div');
    row.className = 'v-reg-row';
    row.id = `v-row-${i}`;

    let contentHTML = `<div class="v-reg-header"><span>v${i}</span>`;

    if (currentSEW === 'raw') {
      contentHTML += `<span style="color: var(--text-muted); font-size: 10px;">[1]:[0]</span></div>`;
      contentHTML += `
        <div class="v-elements-grid" style="grid-template-columns: 1fr 1fr;">
          <div class="v-element-cell" id="v-cell-${i}-1">0x0000000000000000</div>
          <div class="v-element-cell" id="v-cell-${i}-0">0x0000000000000000</div>
        </div>
      `;
    } else {
      const numElems = (currentSEW === 8 ? 16 : (currentSEW === 16 ? 8 : (currentSEW === 32 ? 4 : 2)));
      const cols = currentSEW === 8 ? 8 : (currentSEW === 16 ? 4 : (currentSEW === 32 ? 4 : 2));

      contentHTML += `<span style="color: var(--text-muted); font-size: 10px;">${numElems} elements</span></div>`;
      contentHTML += `<div class="v-elements-grid" style="grid-template-columns: repeat(${cols}, 1fr);">`;

      for (let e = 0; e < numElems; e++) {
        contentHTML += `<div class="v-element-cell" id="v-cell-${i}-${e}" title="Elem [${e}]">0</div>`;
      }
      contentHTML += `</div>`;
    }

    row.innerHTML = contentHTML;
    container.appendChild(row);
  }
  updateVectorRegisters();
}

function updateVectorRegisters() {
  if (!document.getElementById('v-cell-0-0')) {
    initVectorRegisterTable();
    return;
  }
  const vlEl = document.getElementById('v-status-vl');
  const sewEl = document.getElementById('v-status-sew');
  const lmulEl = document.getElementById('v-status-lmul');
  if (vlEl) vlEl.innerText = vectorStatus.vl;
  if (sewEl) sewEl.innerText = vectorStatus.sew;
  if (lmulEl) lmulEl.innerText = vectorStatus.lmul;

  for (let i = 0; i < 32; i++) {
    if (currentSEW === 'raw') {
      const pair = currentVRegisters[i] || [0, 0];
      const prevPair = (prevVRegisters && prevVRegisters[i]) ? prevVRegisters[i] : [0, 0];
      const isChanged0 = pair[0] !== prevPair[0];
      const isChanged1 = pair[1] !== prevPair[1];

      const h0 = `0x${(BigInt(pair[0]) & 0xFFFFFFFFFFFFFFFFn).toString(16).padStart(16, '0')}`;
      const h1 = `0x${(BigInt(pair[1]) & 0xFFFFFFFFFFFFFFFFn).toString(16).padStart(16, '0')}`;

      const cell0 = document.getElementById(`v-cell-${i}-0`);
      const cell1 = document.getElementById(`v-cell-${i}-1`);
      if (cell0) {
        if (cell0.textContent !== h0) cell0.textContent = h0;
        cell0.classList.toggle('changed', isChanged0);
      }
      if (cell1) {
        if (cell1.textContent !== h1) cell1.textContent = h1;
        cell1.classList.toggle('changed', isChanged1);
      }
    } else {
      const sewKey = String(currentSEW);
      const elems = (currentVElements[sewKey] && currentVElements[sewKey][i]) ? currentVElements[sewKey][i] : [];
      const prevElems = (prevVElements && prevVElements[sewKey] && prevVElements[sewKey][i]) ? prevVElements[sewKey][i] : [];
      const numElems = (currentSEW === 8 ? 16 : (currentSEW === 16 ? 8 : (currentSEW === 32 ? 4 : 2)));

      for (let e = 0; e < numElems; e++) {
        const val = elems[e] || 0;
        const prevVal = prevElems[e] !== undefined ? prevElems[e] : 0;
        const isChanged = (val !== prevVal);
        const hexChars = currentSEW / 4;
        const formatted = isHexNotation
          ? `0x${(val >>> 0).toString(16).padStart(hexChars, '0')}`
          : val.toString(10);

        const cell = document.getElementById(`v-cell-${i}-${e}`);
        if (cell) {
          if (cell.textContent !== formatted) cell.textContent = formatted;
          cell.classList.toggle('changed', isChanged);
        }
      }
    }
  }
}

function initMemoryTable() {
  const tbody = document.getElementById('memoryTableBody');
  if (!tbody) return;
  tbody.innerHTML = '';
  for (let i = 0; i < 8; i++) {
    const tr = document.createElement('tr');
    tr.id = `mem-row-${i}`;
    let rowHTML = `<td id="mem-addr-${i}" style="color: var(--color-primary); font-weight: 600;">0x00000000</td>`;
    for (let col = 0; col < 4; col++) {
      rowHTML += `<td id="mem-cell-${i}-${col}" style="text-align: center;">00 00 00 00</td>`;
    }
    tr.innerHTML = rowHTML;
    tbody.appendChild(tr);
  }
  updateMemoryTable();
}

function updateMemoryTable() {
  // If memory has written addresses that are outside visible view, auto-snap currentMemoryBase
  const writtenAddrs = Object.keys(memoryDict).map(a => parseInt(a, 16)).filter(a => !isNaN(a));
  if (writtenAddrs.length > 0) {
    const lastAddr = writtenAddrs[writtenAddrs.length - 1];
    if (lastAddr < currentMemoryBase || lastAddr >= ((currentMemoryBase + 128) >>> 0)) {
      currentMemoryBase = ((lastAddr & ~0xF) >>> 0);
      const input = document.getElementById('mem-jump-input');
      if (input && !input.matches(':focus')) {
        input.value = `0x${currentMemoryBase.toString(16).padStart(8, '0')}`;
      }
    }
  }

  for (let i = 0; i < 8; i++) {
    const rowAddr = ((currentMemoryBase + (i * 16)) >>> 0);
    const addrCell = document.getElementById(`mem-addr-${i}`);
    if (addrCell) {
      addrCell.textContent = `0x${rowAddr.toString(16).padStart(8, '0')}`;
    }

    for (let col = 0; col < 4; col++) {
      const wordAddr = ((rowAddr + (col * 4)) >>> 0);
      let isWritten = false;
      const byteStrs = [];

      for (let b = 0; b < 4; b++) {
        const byteAddr = ((wordAddr + b) >>> 0);
        const bHex = `0x${byteAddr.toString(16)}`;
        if (memoryDict[bHex] !== undefined) {
          isWritten = true;
          byteStrs.push(memoryDict[bHex].padStart(2, '0'));
        } else {
          byteStrs.push('00');
        }
      }

      const cellText = byteStrs.join(' ');
      const cell = document.getElementById(`mem-cell-${i}-${col}`);
      if (cell) {
        if (cell.textContent !== cellText) {
          cell.textContent = cellText;
        }
        cell.className = isWritten ? 'mem-cell-written' : '';
      }
    }
  }
}

function updateAllInspectors() {
  if (activeInspectorTab === 'integer') {
    updateIntegerRegisters();
  } else if (activeInspectorTab === 'float') {
    updateFloatRegisters();
  } else if (activeInspectorTab === 'vector') {
    updateVectorRegisters();
  } else if (activeInspectorTab === 'memory') {
    updateMemoryTable();
  }
}

function jumpToMemoryAddress() {
  const input = document.getElementById('mem-jump-input');
  if (!input || !input.value) return;
  let parsed = parseInt(input.value.trim(), 16);
  if (isNaN(parsed)) parsed = parseInt(input.value.trim(), 10);
  if (!isNaN(parsed)) {
    currentMemoryBase = ((parsed & ~0xF) >>> 0); // 16-byte align as unsigned 32-bit!
    updateMemoryTable();
  }
}

// 7. Auto-Step Playback & Breakpoint Management
function togglePlay() {
  if (isPlaying) {
    stopPlay();
  } else {
    startPlay();
  }
}

function startPlay() {
  const stepBtn = document.getElementById('step-btn');
  if (!stepBtn || stepBtn.disabled) return;

  isPlaying = true;
  const playBtn = document.getElementById('play-btn');
  const playText = document.getElementById('play-btn-text');
  const playIcon = document.getElementById('play-icon');
  if (playBtn) playBtn.classList.add('btn-warning');
  if (playText) playText.innerText = 'Pause';
  if (playIcon) playIcon.innerHTML = '<rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/>';

  const speedSelect = document.getElementById('play-speed-select');
  const intervalMs = speedSelect ? parseInt(speedSelect.value, 10) : 200;

  function autoStep() {
    if (!isPlaying) return;
    const btn = document.getElementById('step-btn');
    if (!btn || btn.disabled) {
      stopPlay();
      return;
    }
    stepInstruction(true).then(shouldContinue => {
      if (shouldContinue && isPlaying) {
        // Check if next PC hit a breakpoint
        const nextPCHex = `0x${(currentPC >>> 0).toString(16).padStart(8, '0')}`.toLowerCase();
        if (breakpoints.has(nextPCHex)) {
          showToast(`Breakpoint hit at ${nextPCHex}`, 'info');
          stopPlay();
          return;
        }
        playTimer = setTimeout(autoStep, intervalMs);
      } else {
        stopPlay();
      }
    }).catch(() => stopPlay());
  }
  autoStep();
}

function stopPlay() {
  isPlaying = false;
  if (playTimer) {
    clearTimeout(playTimer);
    playTimer = null;
  }
  const playBtn = document.getElementById('play-btn');
  const playText = document.getElementById('play-btn-text');
  const playIcon = document.getElementById('play-icon');
  if (playBtn) playBtn.classList.remove('btn-warning');
  if (playText) playText.innerText = 'Play';
  if (playIcon) playIcon.innerHTML = '<polygon points="5 3 19 12 5 21 5 3"/>';
}

function toggleBreakpoint(pcHex) {
  const clean = pcHex.toLowerCase();
  if (breakpoints.has(clean)) {
    breakpoints.delete(clean);
    showToast(`Breakpoint removed at ${clean}`, 'info');
  } else {
    breakpoints.add(clean);
    showToast(`Breakpoint set at ${clean}`, 'info');
  }
  document.querySelectorAll(`#dec-row-${clean}`).forEach(row => {
    row.classList.toggle('has-breakpoint', breakpoints.has(clean));
  });
}

// 8. Core Simulator Actions
function assemble_code() {
  const code = document.getElementById('editor-text-box').value;
  const mtype = document.getElementById('M-type').checked ? 'm' : '';
  const ctype = document.getElementById('C-type').checked ? 'c' : '';
  const ftype = document.getElementById('F-type').checked ? 'f' : '';
  const dtype = document.getElementById('D-type').checked ? 'd' : '';
  const vtype = document.getElementById('V-type').checked ? 'v' : '';
  const rvtype = document.getElementById('varient-drop').value.toLowerCase();

  const assembleUrl = (currentSimulator === 'spike') ? 'gen-hex/assemble-code' : 'assemble-code';

  return axios.all([
    axios.post(assembleUrl, { code, mtype, ctype, ftype, dtype, vtype, rvtype }),
    axios.post('gen-stats/assemble-code', { code })
  ])
    .then(axios.spread((data1, data2) => {
      if (data1 && data1.data && data1.data.success === false) {
        showToast(`${data1.data.error_message} (line ${data1.data.error_line})`, 'error');
        return false;
      }
      if (data1 && data1.data) {
        const hex = data1.data.hex || '';
        const baseins = data1.data.is_sudo || [];
        const instructions = data1.data.instructions || [];
        populate_Decoder_Table(code, hex, baseins, instructions);
        document.getElementById('dump-box').value = hex;

        // Enable buttons
        document.getElementById('run-btn').disabled = false;
        document.getElementById('step-btn').disabled = false;
        const playBtn = document.getElementById('play-btn');
        if (playBtn) playBtn.disabled = false;
        document.getElementById('assemble-btn').disabled = true;

        if (instructions.length > 0) {
          currentPC = parseInt(instructions[0].pc, 16);
          highlightDecoderRow(currentPC);
        }

        showToast('Assembled successfully', 'success');
        return true;
      }
      if (data2 && data2.data) {
        populate_Stats(data2.data);
      }
      return true;
    }))
    .catch(error => {
      if (error.response && error.response.data) {
        const d = error.response.data;
        showToast(d.error_message || d.error || 'Assembly error', 'error');
      } else {
        showToast(error.message || String(error), 'error');
      }
      return false;
    });
}

function populate_Decoder_Table(code, hex, baseins, instructions = []) {
  const tbody = document.getElementById('decoderTableBody');
  tbody.innerHTML = '';
  decoderInstructions = [];

  const userLines = code.split('\n')
    .map(line => line.trim())
    .filter(line => line !== '' && !line.startsWith('#') && !line.includes(':'));

  if (instructions && instructions.length > 0) {
    instructions.forEach((inst, idx) => {
      const pcHex = inst.pc.toLowerCase();
      const machineCode = inst.hex;
      const disasm = inst.disasm;
      const orig = userLines[idx] || inst.disasm;

      decoderInstructions.push({ pc: inst.pc, machineCode, disasm, orig });

      const tr = document.createElement('tr');
      tr.id = `dec-row-${pcHex}`;
      tr.setAttribute('data-pc', pcHex);
      if (breakpoints.has(pcHex)) tr.classList.add('has-breakpoint');
      tr.innerHTML = `
        <td class="pc-cell" style="color: var(--color-primary); font-weight: 600; cursor: pointer;" title="Click to toggle Breakpoint">${inst.pc}</td>
        <td style="color: var(--color-accent);">${machineCode}</td>
        <td>${disasm}</td>
        <td style="color: var(--text-primary); font-weight: 500;">${orig}</td>
      `;
      const pcCell = tr.querySelector('.pc-cell');
      if (pcCell) {
        pcCell.addEventListener('click', (e) => {
          e.stopPropagation();
          toggleBreakpoint(pcHex);
        });
      }
      tbody.appendChild(tr);
    });
  } else {
    // Fallback if instructions not provided
    const hexLines = hex.split('\n').filter(line => line.trim() !== '');
    const startPC = (currentSimulator === 'spike') ? 0x80000000 : 0x00000000;
    userLines.forEach((instruction, idx) => {
      const pcVal = startPC + (idx * 4);
      const pcHex = `0x${pcVal.toString(16).padStart(8, '0')}`.toLowerCase();
      const machineCode = hexLines[idx] || '00000000';
      const disasm = (baseins && baseins[idx]) ? baseins[idx] : instruction;

      decoderInstructions.push({ pc: pcHex, machineCode, disasm, orig: instruction });

      const tr = document.createElement('tr');
      tr.id = `dec-row-${pcHex}`;
      tr.setAttribute('data-pc', pcHex);
      if (breakpoints.has(pcHex)) tr.classList.add('has-breakpoint');
      tr.innerHTML = `
        <td class="pc-cell" style="color: var(--color-primary); font-weight: 600; cursor: pointer;" title="Click to toggle Breakpoint">${pcHex}</td>
        <td style="color: var(--color-accent);">${machineCode}</td>
        <td>${disasm}</td>
        <td style="color: var(--text-primary); font-weight: 500;">${instruction}</td>
      `;
      const pcCell = tr.querySelector('.pc-cell');
      if (pcCell) {
        pcCell.addEventListener('click', (e) => {
          e.stopPropagation();
          toggleBreakpoint(pcHex);
        });
      }
      tbody.appendChild(tr);
    });
  }

  document.getElementById('instruction-count-badge').innerText = `${decoderInstructions.length} Instructions`;
}

function disableExecutionControls(completed = false) {
  stopPlay();
  document.getElementById('step-btn').disabled = true;
  // Keep run-btn enabled so user can re-run directly without friction!
  const runBtn = document.getElementById('run-btn');
  if (runBtn) runBtn.disabled = false;
  const playBtn = document.getElementById('play-btn');
  if (playBtn) playBtn.disabled = true;
  document.getElementById('assemble-btn').disabled = false;
  document.getElementById('reset-btn').disabled = false;

  const countBadge = document.getElementById('instruction-count-badge');
  if (countBadge && completed) {
    countBadge.innerText = 'Completed ✓';
    countBadge.style.background = 'rgba(34, 197, 94, 0.2)';
    countBadge.style.color = '#4ade80';
    countBadge.style.borderColor = 'rgba(34, 197, 94, 0.4)';
  }
}

function stepInstruction(isAuto = false) {
  const stepUrl = (currentSimulator === 'spike') ? 'gen-hex/step' : 'step';

  let currentInstHex = '';
  if (currentSimulator !== 'spike') {
    const activeRow = document.querySelector('#decoderTableBody tr.highlight');
    if (activeRow && activeRow.cells && activeRow.cells[1]) {
      currentInstHex = activeRow.cells[1].textContent.trim();
    } else {
      const firstRow = document.querySelector('#decoderTableBody tr');
      if (firstRow && firstRow.cells && firstRow.cells[1]) {
        currentInstHex = firstRow.cells[1].textContent.trim();
      }
    }
  }

  return axios.post(stepUrl, {
    pc: currentPC,
    instruction: currentInstHex,
    memory: memoryDict,
    register: currentIntRegisters,
    f_register: currentFRegisters
  })
    .then(response => {
      const d = response.data;
      if (!d || d.success === false) {
        const errMsg = d?.error || 'Simulation step ended.';
        showToast(errMsg, 'info');
        if (d && d.ended) {
          disableExecutionControls(true);
        }
        return false;
      }

      // Save previous registers to detect delta
      prevIntRegisters = [...currentIntRegisters];
      currentIntRegisters = d.register || d.registers || currentIntRegisters;

      prevFRegisters = [...currentFRegisters];
      prevDRegisters = [...currentDRegisters];
      prevFHex = [...currentFHex];
      currentFRegisters = d.f_reg || d.fregister || currentFRegisters;
      if (d.d_reg) currentDRegisters = d.d_reg;
      if (d.f_hex) currentFHex = d.f_hex;

      prevVRegisters = currentVRegisters.map(r => [...r]);
      prevVElements = JSON.parse(JSON.stringify(currentVElements));
      if (d.vreg) currentVRegisters = d.vreg;
      if (d.vreg_elements) currentVElements = d.vreg_elements;
      if (d.vector_status) vectorStatus = d.vector_status;

      if (d.memory) memoryDict = d.memory;
      currentPC = d.pc;

      // Highlight active instruction row
      highlightDecoderRow(currentPC, isAuto);

      // Render updated values only for active tab
      updateAllInspectors();

      if (d.ended) {
        disableExecutionControls(true);
        return false;
      }
      return true;
    })
    .catch(error => {
      console.error(error);
      const errMsg = error.response?.data?.error || error.message;
      showToast('Error during step: ' + errMsg, 'error');
      return false;
    });
}

async function run_Code() {
  const runBtn = document.getElementById('run-btn');

  // If not assembled yet or previous execution completed, auto-assemble first!
  const countBadge = document.getElementById('instruction-count-badge');
  const isCompleted = countBadge && countBadge.innerText.includes('Completed');
  if (decoderInstructions.length === 0 || isCompleted) {
    const asmSuccess = await assemble_code();
    if (!asmSuccess) return;
  }

  const code = document.getElementById('editor-text-box').value;
  const mtype = document.getElementById('M-type').checked ? 'm' : '';
  const ctype = document.getElementById('C-type').checked ? 'c' : '';
  const ftype = document.getElementById('F-type').checked ? 'f' : '';
  const dtype = document.getElementById('D-type').checked ? 'd' : '';
  const vtype = document.getElementById('V-type').checked ? 'v' : '';
  const rvtype = document.getElementById('varient-drop').value.toLowerCase();

  // Find nearest breakpoint ahead of currentPC
  let targetBreakpoint = null;
  if (breakpoints.size > 0) {
    const sortedBps = Array.from(breakpoints)
      .map(bp => parseInt(bp, 16))
      .filter(bp => !isNaN(bp) && bp > currentPC)
      .sort((a, b) => a - b);
    if (sortedBps.length > 0) {
      targetBreakpoint = `0x${sortedBps[0].toString(16)}`;
    }
  }

  const runUrl = (currentSimulator === 'spike') ? 'gen-hex/run-code' : 'run-code';

  if (runBtn) {
    runBtn.disabled = true;
    if (!runBtn.dataset.origHtml) runBtn.dataset.origHtml = runBtn.innerHTML;
    runBtn.innerHTML = `
      <svg class="spinner" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
      </svg>
      Running...
    `;
  }

  axios.post(runUrl, {
    code, mtype, ctype, ftype, dtype, vtype, rvtype,
    breakpoint_pc: targetBreakpoint
  })
    .then(response => {
      const d = response.data;
      if (!d || d.success === false) {
        showToast(d?.error || 'Simulation failed to run.', 'error');
        if (runBtn) {
          runBtn.disabled = false;
          if (runBtn.dataset.origHtml) runBtn.innerHTML = runBtn.dataset.origHtml;
        }
        return;
      }

      prevIntRegisters = [...currentIntRegisters];
      currentIntRegisters = d.register || d.registers || currentIntRegisters;

      prevFRegisters = [...currentFRegisters];
      prevDRegisters = [...currentDRegisters];
      prevFHex = [...currentFHex];
      currentFRegisters = d.f_reg || d.fregister || currentFRegisters;
      if (d.d_reg) currentDRegisters = d.d_reg;
      if (d.f_hex) currentFHex = d.f_hex;

      prevVRegisters = currentVRegisters.map(r => [...r]);
      prevVElements = JSON.parse(JSON.stringify(currentVElements));
      if (d.vreg) currentVRegisters = d.vreg;
      if (d.vreg_elements) currentVElements = d.vreg_elements;
      if (d.vector_status) vectorStatus = d.vector_status;

      if (d.memory) memoryDict = d.memory;
      currentPC = d.pc;

      highlightDecoderRow(currentPC, true);
      updateAllInspectors();

      if (runBtn) {
        runBtn.disabled = false;
        if (runBtn.dataset.origHtml) runBtn.innerHTML = runBtn.dataset.origHtml;
      }

      if (targetBreakpoint && currentPC === parseInt(targetBreakpoint, 16)) {
        showToast(`Stopped at Breakpoint: ${targetBreakpoint}`, 'info');
      } else if (d.ended) {
        disableExecutionControls(true);
        showToast('Program execution completed.', 'success');
      }
    })
    .catch(error => {
      console.error(error);
      if (runBtn) {
        runBtn.disabled = false;
        if (runBtn.dataset.origHtml) runBtn.innerHTML = runBtn.dataset.origHtml;
      }
      showToast('Error during run: ' + (error.response?.data?.error || error.message), 'error');
    });
}

function reset_Registers() {
  stopPlay();
  const resetUrl = (currentSimulator === 'spike') ? 'gen-hex/reset' : 'reset';

  axios.post(resetUrl, {})
    .then(response => {
      const d = response.data;
      currentIntRegisters = d.register || new Array(32).fill(0);
      prevIntRegisters = [...currentIntRegisters];

      currentFRegisters = d.fregister || new Array(32).fill(0.0);
      currentDRegisters = d.d_reg || new Array(32).fill(0.0);
      currentFHex = d.f_hex || new Array(32).fill('0x0000000000000000');
      prevFRegisters = [...currentFRegisters];
      prevDRegisters = [...currentDRegisters];
      prevFHex = [...currentFHex];

      currentVRegisters = d.vreg || Array.from({ length: 32 }, () => [0, 0]);
      currentVElements = { '8': [], '16': [], '32': [], '64': [] };
      prevVRegisters = currentVRegisters.map(r => [...r]);
      prevVElements = { '8': [], '16': [], '32': [], '64': [] };
      vectorStatus = { vl: 0, sew: 32, lmul: 'm1' };

      memoryDict = d.memory || {};
      currentPC = d.pc || ((currentSimulator === 'spike') ? 0x80000000 : 0);

      // Remove row highlights
      document.querySelectorAll('#decoderTableBody tr').forEach(r => r.classList.remove('highlight'));

      const countBadge = document.getElementById('instruction-count-badge');
      if (countBadge) {
        countBadge.innerText = `${decoderInstructions.length} Instructions`;
        countBadge.style.background = '';
        countBadge.style.color = '';
        countBadge.style.borderColor = '';
      }

      updateIntegerRegisters();
      updateFloatRegisters();
      updateVectorRegisters();
      updateMemoryTable();

      document.getElementById('assemble-btn').disabled = false;
      document.getElementById('step-btn').disabled = true;
      document.getElementById('run-btn').disabled = true;
      const playBtn = document.getElementById('play-btn');
      if (playBtn) playBtn.disabled = true;
      document.getElementById('reset-btn').disabled = false;
      showToast('Registers reset', 'info');
    })
    .catch(error => {
      console.error(error);
    });
}

function highlightDecoderRow(pc, isAuto = false) {
  document.querySelectorAll('#decoderTableBody tr').forEach(r => r.classList.remove('highlight'));
  if (pc === undefined || pc === null) return;
  let pcNum = (typeof pc === 'string') ? parseInt(pc, 16) : Number(pc);
  if (isNaN(pcNum)) return;
  const pcHex = `0x${pcNum.toString(16).padStart(8, '0')}`.toLowerCase();
  const row = document.getElementById(`dec-row-${pcHex}`) || document.querySelector(`[data-pc="${pcHex}"]`);
  if (row) {
    row.classList.add('highlight');
    row.scrollIntoView({ behavior: isAuto ? 'auto' : 'smooth', block: 'nearest' });
  }
}

function populate_Stats(data) {
  document.getElementById('total_instructions').innerText = data.total_ins || 0;
  document.getElementById('Total_cycles').innerText = data.total_cycles || 0;
  document.getElementById('ALU_instructions').innerText = data.alu_ins || 0;
  document.getElementById('Jump_instructions').innerText = data.jump_ins || 0;
  document.getElementById('Data_transfer').innerText = data.data_transfer_ins || 0;
  document.getElementById('I_ins').innerText = data.i_ins || 0;
  document.getElementById('M_ins').innerText = data.m_ins || 0;
  document.getElementById('F_ins').innerText = data.f_ins || 0;
  document.getElementById('C_ins').innerText = data.c_ins || 0;
  document.getElementById('s_ins').innerText = data.s_ins || 0;
}

// 8. Clipboard & Utilities
function copy_hex() {
  const dump = document.getElementById('dump-box').value;
  if (!dump) return;
  navigator.clipboard.writeText(dump).then(() => {
    alert('Machine code hex copied to clipboard!');
  });
}

function download_hex() {
  const dump = document.getElementById('dump-box').value;
  if (!dump) return;
  const blob = new Blob([dump], { type: 'text/plain' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'machine_code_hex.txt';
  a.click();
}

function clear_hex() {
  document.getElementById('dump-box').value = '';
}

function reset_editor() {
  const editor = document.getElementById('editor-text-box');
  if (editor) {
    editor.value = '';
    updateLineNumbers();
  }
}

// 9. Editor Line Numbers Gutter
function updateLineNumbers() {
  const editor = document.getElementById('editor-text-box');
  const gutter = document.getElementById('editor-line-numbers');
  if (!editor || !gutter) return;

  const lines = editor.value.split('\n').length;
  let numStr = '';
  for (let i = 1; i <= lines; i++) {
    numStr += i + '\n';
  }
  gutter.innerText = numStr;
}

function initEditorGutter() {
  const editor = document.getElementById('editor-text-box');
  const gutter = document.getElementById('editor-line-numbers');
  if (!editor || !gutter) return;

  editor.addEventListener('input', updateLineNumbers);
  editor.addEventListener('keyup', updateLineNumbers);
  editor.addEventListener('scroll', () => {
    gutter.scrollTop = editor.scrollTop;
  });

  updateLineNumbers();
}

// 10. RISC-V Autocomplete Suggestions
const RISCV_SUGGESTIONS = [
  // Base RV32I
  { name: 'addi', tag: 'RV32I', desc: 'Add immediate: rd = rs1 + imm' },
  { name: 'add', tag: 'RV32I', desc: 'Add: rd = rs1 + rs2' },
  { name: 'sub', tag: 'RV32I', desc: 'Subtract: rd = rs1 - rs2' },
  { name: 'sll', tag: 'RV32I', desc: 'Shift left logical: rd = rs1 << rs2' },
  { name: 'slli', tag: 'RV32I', desc: 'Shift left logical imm: rd = rs1 << shamt' },
  { name: 'slt', tag: 'RV32I', desc: 'Set less than: rd = (rs1 < rs2) ? 1 : 0' },
  { name: 'slti', tag: 'RV32I', desc: 'Set less than imm: rd = (rs1 < imm) ? 1 : 0' },
  { name: 'sltu', tag: 'RV32I', desc: 'Set less than unsigned: rd = (rs1 < rs2)' },
  { name: 'sltiu', tag: 'RV32I', desc: 'Set less than imm unsigned' },
  { name: 'xor', tag: 'RV32I', desc: 'Bitwise XOR: rd = rs1 ^ rs2' },
  { name: 'xori', tag: 'RV32I', desc: 'Bitwise XOR imm: rd = rs1 ^ imm' },
  { name: 'srl', tag: 'RV32I', desc: 'Shift right logical: rd = rs1 >> rs2' },
  { name: 'srli', tag: 'RV32I', desc: 'Shift right logical imm' },
  { name: 'sra', tag: 'RV32I', desc: 'Shift right arithmetic: rd = rs1 >> rs2' },
  { name: 'srai', tag: 'RV32I', desc: 'Shift right arithmetic imm' },
  { name: 'or', tag: 'RV32I', desc: 'Bitwise OR: rd = rs1 | rs2' },
  { name: 'ori', tag: 'RV32I', desc: 'Bitwise OR imm: rd = rs1 | imm' },
  { name: 'and', tag: 'RV32I', desc: 'Bitwise AND: rd = rs1 & rs2' },
  { name: 'andi', tag: 'RV32I', desc: 'Bitwise AND imm: rd = rs1 & imm' },
  { name: 'lui', tag: 'RV32I', desc: 'Load upper immediate: rd = imm << 12' },
  { name: 'auipc', tag: 'RV32I', desc: 'Add upper immediate to PC: rd = PC + (imm << 12)' },
  { name: 'jal', tag: 'RV32I', desc: 'Jump and link: rd = PC+4, PC += offset' },
  { name: 'jalr', tag: 'RV32I', desc: 'Jump and link register: rd = PC+4, PC = rs1 + imm' },
  { name: 'beq', tag: 'RV32I', desc: 'Branch if equal: if (rs1 == rs2) PC += offset' },
  { name: 'bne', tag: 'RV32I', desc: 'Branch if not equal: if (rs1 != rs2) PC += offset' },
  { name: 'blt', tag: 'RV32I', desc: 'Branch if less than: if (rs1 < rs2) PC += offset' },
  { name: 'bge', tag: 'RV32I', desc: 'Branch if greater or equal: if (rs1 >= rs2)' },
  { name: 'bltu', tag: 'RV32I', desc: 'Branch if less than unsigned' },
  { name: 'bgeu', tag: 'RV32I', desc: 'Branch if greater or equal unsigned' },
  { name: 'lb', tag: 'RV32I', desc: 'Load byte: rd = M[rs1 + imm][7:0]' },
  { name: 'lh', tag: 'RV32I', desc: 'Load halfword: rd = M[rs1 + imm][15:0]' },
  { name: 'lw', tag: 'RV32I', desc: 'Load word: rd = M[rs1 + imm][31:0]' },
  { name: 'lbu', tag: 'RV32I', desc: 'Load byte unsigned' },
  { name: 'lhu', tag: 'RV32I', desc: 'Load halfword unsigned' },
  { name: 'sb', tag: 'RV32I', desc: 'Store byte: M[rs1 + imm][7:0] = rs2[7:0]' },
  { name: 'sh', tag: 'RV32I', desc: 'Store halfword: M[rs1 + imm][15:0] = rs2[15:0]' },
  { name: 'sw', tag: 'RV32I', desc: 'Store word: M[rs1 + imm][31:0] = rs2[31:0]' },
  { name: 'fence', tag: 'RV32I', desc: 'Memory fence ordering' },
  { name: 'ecall', tag: 'RV32I', desc: 'Environment call / syscall' },
  { name: 'ebreak', tag: 'RV32I', desc: 'Environment breakpoint' },
  // Pseudo-ops
  { name: 'nop', tag: 'Pseudo', desc: 'No operation (addi x0, x0, 0)' },
  { name: 'li', tag: 'Pseudo', desc: 'Load immediate: rd, imm' },
  { name: 'mv', tag: 'Pseudo', desc: 'Move register: rd = rs' },
  { name: 'not', tag: 'Pseudo', desc: 'Bitwise NOT: rd = ~rs' },
  { name: 'neg', tag: 'Pseudo', desc: 'Two\'s complement negate: rd = -rs' },
  { name: 'j', tag: 'Pseudo', desc: 'Unconditional jump: j target' },
  { name: 'jr', tag: 'Pseudo', desc: 'Jump register: jr rs1' },
  { name: 'ret', tag: 'Pseudo', desc: 'Return from subroutine (jalr x0, x1, 0)' },
  { name: 'call', tag: 'Pseudo', desc: 'Call subroutine: call target' },
  // RV32M
  { name: 'mul', tag: 'M-Ext', desc: 'Multiply lower 32-bit' },
  { name: 'mulh', tag: 'M-Ext', desc: 'Multiply high signed' },
  { name: 'mulhsu', tag: 'M-Ext', desc: 'Multiply high signed * unsigned' },
  { name: 'mulhu', tag: 'M-Ext', desc: 'Multiply high unsigned' },
  { name: 'div', tag: 'M-Ext', desc: 'Divide signed: rd = rs1 / rs2' },
  { name: 'divu', tag: 'M-Ext', desc: 'Divide unsigned' },
  { name: 'rem', tag: 'M-Ext', desc: 'Remainder signed: rd = rs1 % rs2' },
  { name: 'remu', tag: 'M-Ext', desc: 'Remainder unsigned' },
  // RV32F & D
  { name: 'flw', tag: 'F-Ext', desc: 'Load float word (32-bit)' },
  { name: 'fsw', tag: 'F-Ext', desc: 'Store float word (32-bit)' },
  { name: 'fadd.s', tag: 'F-Ext', desc: 'Float add single-precision' },
  { name: 'fsub.s', tag: 'F-Ext', desc: 'Float subtract single' },
  { name: 'fmul.s', tag: 'F-Ext', desc: 'Float multiply single' },
  { name: 'fdiv.s', tag: 'F-Ext', desc: 'Float divide single' },
  { name: 'fsqrt.s', tag: 'F-Ext', desc: 'Float square root single' },
  { name: 'fcvt.w.s', tag: 'F-Ext', desc: 'Convert float single to int' },
  { name: 'fcvt.s.w', tag: 'F-Ext', desc: 'Convert int to float single' },
  { name: 'fld', tag: 'D-Ext', desc: 'Load float double (64-bit)' },
  { name: 'fsd', tag: 'D-Ext', desc: 'Store float double (64-bit)' },
  { name: 'fadd.d', tag: 'D-Ext', desc: 'Float add double-precision' },
  { name: 'fsub.d', tag: 'D-Ext', desc: 'Float subtract double' },
  { name: 'fmul.d', tag: 'D-Ext', desc: 'Float multiply double' },
  { name: 'fdiv.d', tag: 'D-Ext', desc: 'Float divide double' },
  { name: 'fsqrt.d', tag: 'D-Ext', desc: 'Float square root double' },
  { name: 'fcvt.d.w', tag: 'D-Ext', desc: 'Convert int to float double' },
  { name: 'fcvt.d.s', tag: 'D-Ext', desc: 'Convert float single to double' },
  // RV32V
  { name: 'vsetvli', tag: 'V-Ext', desc: 'Set vector length and config' },
  { name: 'vsetivli', tag: 'V-Ext', desc: 'Set vector length immediate' },
  { name: 'vsetvl', tag: 'V-Ext', desc: 'Set vector length from registers' },
  { name: 'vadd.vv', tag: 'V-Ext', desc: 'Vector add vectors: vd = vs2 + vs1' },
  { name: 'vadd.vx', tag: 'V-Ext', desc: 'Vector add scalar: vd = vs2 + rs1' },
  { name: 'vadd.vi', tag: 'V-Ext', desc: 'Vector add immediate' },
  { name: 'vsub.vv', tag: 'V-Ext', desc: 'Vector subtract vectors' },
  { name: 'vmul.vv', tag: 'V-Ext', desc: 'Vector multiply vectors' },
  { name: 'vmv.v.i', tag: 'V-Ext', desc: 'Vector move immediate: vd = imm' },
  { name: 'vmv.v.v', tag: 'V-Ext', desc: 'Vector move vector: vd = vs1' },
  { name: 'vle32.v', tag: 'V-Ext', desc: 'Vector load 32-bit elements' },
  { name: 'vse32.v', tag: 'V-Ext', desc: 'Vector store 32-bit elements' },
  // Registers
  { name: 'zero', tag: 'Reg', desc: 'x0: Hardwired zero' },
  { name: 'ra', tag: 'Reg', desc: 'x1: Return address' },
  { name: 'sp', tag: 'Reg', desc: 'x2: Stack pointer' },
  { name: 'gp', tag: 'Reg', desc: 'x3: Global pointer' },
  { name: 'tp', tag: 'Reg', desc: 'x4: Thread pointer' },
  { name: 't0', tag: 'Reg', desc: 'x5: Temporary 0' },
  { name: 't1', tag: 'Reg', desc: 'x6: Temporary 1' },
  { name: 't2', tag: 'Reg', desc: 'x7: Temporary 2' },
  { name: 's0', tag: 'Reg', desc: 'x8: Saved register 0 / frame pointer' },
  { name: 's1', tag: 'Reg', desc: 'x9: Saved register 1' },
  { name: 'a0', tag: 'Reg', desc: 'x10: Function argument 0 / return value' },
  { name: 'a1', tag: 'Reg', desc: 'x11: Function argument 1 / return value' },
  { name: 'a2', tag: 'Reg', desc: 'x12: Function argument 2' },
  { name: 'a3', tag: 'Reg', desc: 'x13: Function argument 3' },
  { name: 'a4', tag: 'Reg', desc: 'x14: Function argument 4' },
  { name: 'a5', tag: 'Reg', desc: 'x15: Function argument 5' },
  { name: 'a6', tag: 'Reg', desc: 'x16: Function argument 6' },
  { name: 'a7', tag: 'Reg', desc: 'x17: Function argument 7' },
  { name: 's2', tag: 'Reg', desc: 'x18: Saved register 2' },
  { name: 's3', tag: 'Reg', desc: 'x19: Saved register 3' },
  { name: 's4', tag: 'Reg', desc: 'x20: Saved register 4' },
  { name: 's5', tag: 'Reg', desc: 'x21: Saved register 5' },
  { name: 's6', tag: 'Reg', desc: 'x22: Saved register 6' },
  { name: 's7', tag: 'Reg', desc: 'x23: Saved register 7' },
  { name: 's8', tag: 'Reg', desc: 'x24: Saved register 8' },
  { name: 's9', tag: 'Reg', desc: 'x25: Saved register 9' },
  { name: 's10', tag: 'Reg', desc: 'x26: Saved register 10' },
  { name: 's11', tag: 'Reg', desc: 'x27: Saved register 11' },
  { name: 't3', tag: 'Reg', desc: 'x28: Temporary 3' },
  { name: 't4', tag: 'Reg', desc: 'x29: Temporary 4' },
  { name: 't5', tag: 'Reg', desc: 'x30: Temporary 5' },
  { name: 't6', tag: 'Reg', desc: 'x31: Temporary 6' },
];

let activeSuggestionIdx = -1;
let currentSuggestions = [];

function initAutocomplete() {
  const editor = document.getElementById('editor-text-box');
  const popup = document.getElementById('editor-suggestions');
  if (!editor || !popup) return;

  function getCurrentWord() {
    const pos = editor.selectionStart;
    const text = editor.value.substring(0, pos);
    const match = text.match(/([a-zA-Z0-9_\.]+)$/);
    return match ? { word: match[1], start: pos - match[1].length, end: pos } : null;
  }

  function showSuggestions(list, wordInfo) {
    currentSuggestions = list;
    activeSuggestionIdx = 0;
    popup.innerHTML = '';

    list.slice(0, 8).forEach((item, idx) => {
      const el = document.createElement('div');
      el.className = `suggestion-item ${idx === 0 ? 'active' : ''}`;
      el.innerHTML = `
        <span class="suggestion-mnemonic">${item.name}</span>
        <span style="display: flex; align-items: center;">
          <span class="suggestion-desc">${item.desc}</span>
          <span class="suggestion-tag" style="margin-left: 6px;">${item.tag}</span>
        </span>
      `;
      el.addEventListener('mousedown', (e) => {
        e.preventDefault();
        applySuggestion(item.name, wordInfo);
      });
      popup.appendChild(el);
    });

    // Position popup near cursor line
    const textBefore = editor.value.substring(0, wordInfo.start);
    const lineIndex = textBefore.split('\n').length - 1;
    const topPos = Math.min(Math.max(14 + (lineIndex * 23.5) - editor.scrollTop + 24, 10), editor.offsetHeight - 230);
    popup.style.top = `${topPos}px`;
    popup.style.left = '58px';
    popup.style.display = 'block';
  }

  function hideSuggestions() {
    popup.style.display = 'none';
    currentSuggestions = [];
    activeSuggestionIdx = -1;
  }

  function applySuggestion(suggestionText, wordInfo) {
    if (!wordInfo) wordInfo = getCurrentWord();
    if (!wordInfo) return;

    const before = editor.value.substring(0, wordInfo.start);
    const after = editor.value.substring(wordInfo.end);
    editor.value = before + suggestionText + ' ' + after;
    const newPos = wordInfo.start + suggestionText.length + 1;
    editor.setSelectionRange(newPos, newPos);
    editor.focus();
    hideSuggestions();
    updateLineNumbers();
  }

  editor.addEventListener('input', () => {
    const wordInfo = getCurrentWord();
    if (!wordInfo || wordInfo.word.length < 1) {
      hideSuggestions();
      return;
    }

    const query = wordInfo.word.toLowerCase();
    const matches = RISCV_SUGGESTIONS.filter(item => item.name.toLowerCase().startsWith(query));
    if (matches.length > 0) {
      showSuggestions(matches, wordInfo);
    } else {
      hideSuggestions();
    }
  });

  editor.addEventListener('keydown', (e) => {
    if (popup.style.display === 'block' && currentSuggestions.length > 0) {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        activeSuggestionIdx = (activeSuggestionIdx + 1) % Math.min(currentSuggestions.length, 8);
        updateActiveSuggestion();
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        activeSuggestionIdx = (activeSuggestionIdx - 1 + Math.min(currentSuggestions.length, 8)) % Math.min(currentSuggestions.length, 8);
        updateActiveSuggestion();
      } else if (e.key === 'Tab' || e.key === 'Enter') {
        e.preventDefault();
        const selected = currentSuggestions[activeSuggestionIdx];
        if (selected) {
          applySuggestion(selected.name);
        }
      } else if (e.key === 'Escape') {
        hideSuggestions();
      }
    }
  });

  function updateActiveSuggestion() {
    const items = popup.querySelectorAll('.suggestion-item');
    items.forEach((item, idx) => {
      item.classList.toggle('active', idx === activeSuggestionIdx);
      if (idx === activeSuggestionIdx) item.scrollIntoView({ block: 'nearest' });
    });
  }

  document.addEventListener('click', (e) => {
    if (!popup.contains(e.target) && e.target !== editor) {
      hideSuggestions();
    }
  });
}

// 11. Resizable Panels (Splitters)
function initSplitters() {
  const colEditor = document.getElementById('col-editor');
  const colDecoder = document.getElementById('col-decoder');
  const colInspector = document.getElementById('col-inspector');
  const gutterCol1 = document.getElementById('gutter-col-1');
  const gutterCol2 = document.getElementById('gutter-col-2');
  const gutterRow = document.getElementById('gutter-row-editor');
  const hexDump = document.getElementById('hex-dump-section');

  if (!colEditor || !gutterCol1 || !gutterCol2) return;

  // Restore saved widths from localStorage
  try {
    const saved = JSON.parse(localStorage.getItem('oxygen_layout') || '{}');
    if (saved.col1) colEditor.style.width = `${saved.col1}px`;
    if (saved.col3 && colInspector) colInspector.style.width = `${saved.col3}px`;
    if (saved.hexHeight && hexDump) hexDump.style.height = `${saved.hexHeight}px`;
  } catch (e) {}

  function saveLayout() {
    try {
      const layout = {
        col1: colEditor.offsetWidth,
        col3: colInspector ? colInspector.offsetWidth : 440,
        hexHeight: hexDump ? hexDump.offsetHeight : 180
      };
      localStorage.setItem('oxygen_layout', JSON.stringify(layout));
    } catch (e) {}
  }

  // Splitter 1: Between Editor & Decoder
  gutterCol1.addEventListener('mousedown', (e) => {
    e.preventDefault();
    gutterCol1.classList.add('dragging');
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';

    const startX = e.clientX;
    const startWidth = colEditor.offsetWidth;

    function onMouseMove(ev) {
      const deltaX = ev.clientX - startX;
      const newWidth = Math.min(Math.max(startWidth + deltaX, 260), 750);
      colEditor.style.width = `${newWidth}px`;
    }

    function onMouseUp() {
      gutterCol1.classList.remove('dragging');
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
      saveLayout();
    }

    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
  });

  // Splitter 2: Between Decoder & Inspector
  gutterCol2.addEventListener('mousedown', (e) => {
    e.preventDefault();
    gutterCol2.classList.add('dragging');
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';

    const startX = e.clientX;
    const startWidth = colInspector.offsetWidth;

    function onMouseMove(ev) {
      const deltaX = startX - ev.clientX;
      const newWidth = Math.min(Math.max(startWidth + deltaX, 280), 800);
      colInspector.style.width = `${newWidth}px`;
    }

    function onMouseUp() {
      gutterCol2.classList.remove('dragging');
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
      saveLayout();
    }

    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
  });

  // Splitter Row: Between Editor and Hex Dump
  if (gutterRow && hexDump) {
    gutterRow.addEventListener('mousedown', (e) => {
      e.preventDefault();
      gutterRow.classList.add('dragging');
      document.body.style.cursor = 'row-resize';
      document.body.style.userSelect = 'none';

      const startY = e.clientY;
      const startHeight = hexDump.offsetHeight;

      function onMouseMove(ev) {
        const deltaY = startY - ev.clientY;
        const newHeight = Math.min(Math.max(startHeight + deltaY, 80), 500);
        hexDump.style.height = `${newHeight}px`;
      }

      function onMouseUp() {
        gutterRow.classList.remove('dragging');
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
        window.removeEventListener('mousemove', onMouseMove);
        window.removeEventListener('mouseup', onMouseUp);
        saveLayout();
      }

      window.addEventListener('mousemove', onMouseMove);
      window.addEventListener('mouseup', onMouseUp);
    });
  }
}

// 12. Light / Dark Theme Management
function initTheme() {
  const saved = localStorage.getItem('oxygen-theme') ||
    (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark');
  setTheme(saved);
}

function setTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('oxygen-theme', theme);
  const icon = document.getElementById('theme-icon');
  if (icon) {
    icon.innerText = (theme === 'light') ? '☀️' : '🌙';
  }
}

function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme') || 'dark';
  setTheme(current === 'light' ? 'dark' : 'light');
}

