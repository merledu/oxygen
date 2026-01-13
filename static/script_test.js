let timer;
let reg_value = new Array(32).fill(0);
let f_reg_value = [];
let memorydic = {};
let pc = 0;
let memoryAddress = 0;
let memoryValues = {};
let isHex = 'true';
const tabs = document.querySelectorAll('[data-tab-target]');
const tabContents = document.querySelectorAll('[data-tab-content]');


tabs.forEach(tab => {
    tab.addEventListener('click', () => {
        const target = document.querySelector(tab.dataset.tabTarget);
        tabContents.forEach(tabContent => {
            tabContent.classList.remove('active');
        })
        tabs.forEach(tab => {
            tab.classList.remove('active');
        })
        tab.classList.add('active');
        target.classList.add('active');
    })
})


document.addEventListener('input', e => {
    const el = e.target;

    if (el.matches('[data-color]')) {
        clearTimeout(timer);
        timer = setTimeout(() => {
            document.documentElement.style.setProperty(`--color-${el.dataset.color}`, el.value);
        }, 100)
    }
})

var c = document.getElementById('c');
var w = c.width = window.innerWidth,
    h = c.height = window.innerHeight,
    ctx = c.getContext('2d'),

    minDist = 10,
    maxDist = 30,
    initialWidth = 10,
    maxLines = 80,
    initialLines = 10,
    speed = 5,

    lines = [],
    frame = 0,
    timeSinceLast = 0,

    dirs = [
        [0, 1], [1, 0], [0, -1], [-1, 0],
        [0.7, 0.7], [0.7, -0.7], [-0.7, 0.7], [-0.7, -0.7]
    ],
    starter = {
        x: w / 2,
        y: h / 2,
        vx: 0,
        vy: 0,
        width: initialWidth
    };

function init() {
    lines.length = 0;

    for (var i = 0; i < initialLines; ++i)
        lines.push(new Line(starter));

    ctx.fillStyle = '#222';
    ctx.fillRect(0, 0, w, h);
}

function getColor(x) {
    return 'hsl(hue, 50%, 50%)'.replace('hue', x / w * 360 + frame);
}

function anim() {
    window.requestAnimationFrame(anim);

    ++frame;

    ctx.shadowBlur = 0;
    ctx.fillStyle = 'rgba(0,0,0,.02)';
    ctx.fillRect(0, 0, w, h);
    ctx.shadowBlur = .5;

    for (var i = 0; i < lines.length; ++i)
        if (lines[i].step()) {
            lines.splice(i, 1);
            --i;
        }

    ++timeSinceLast;

    if (lines.length < maxLines && timeSinceLast > 10 && Math.random() < .5) {
        timeSinceLast = 0;
        lines.push(new Line(starter));

        ctx.fillStyle = ctx.shadowColor = getColor(starter.x);
        ctx.beginPath();
        ctx.arc(starter.x, starter.y, initialWidth, 0, Math.PI * 2);
        ctx.fill();
    }
}

function Line(parent) {
    this.x = parent.x | 0;
    this.y = parent.y | 0;
    this.width = parent.width / 1.25;

    do {
        var dir = dirs[(Math.random() * dirs.length) | 0];
        this.vx = dir[0];
        this.vy = dir[1];
    } while (
        (this.vx === -parent.vx && this.vy === -parent.vy) || (this.vx === parent.vx && this.vy === parent.vy)
    );

    this.vx *= speed;
    this.vy *= speed;
    this.dist = (Math.random() * (maxDist - minDist) + minDist);
}

Line.prototype.step = function () {
    var dead = false;
    var prevX = this.x,
        prevY = this.y;

    this.x += this.vx;
    this.y += this.vy;

    --this.dist;

    if (this.x < 0 || this.x > w || this.y < 0 || this.y > h)
        dead = true;

    if (this.dist <= 0 && this.width > 1) {
        this.dist = Math.random() * (maxDist - minDist) + minDist;

        if (lines.length < maxLines) lines.push(new Line(this));
        if (lines.length < maxLines && Math.random() < .5) lines.push(new Line(this));

        if (Math.random() < .2) dead = true;
    }

    ctx.strokeStyle = ctx.shadowColor = getColor(this.x);
    ctx.beginPath();
    ctx.lineWidth = this.width;
    ctx.moveTo(this.x, this.y);
    ctx.lineTo(prevX, prevY);
    ctx.stroke();

    if (dead) return true;
}


init();
anim();


window.addEventListener('resize', function () {
    w = c.width = window.innerWidth;
    h = c.height = window.innerHeight;
    starter.x = w / 2;
    starter.y = h / 2;
    init();
});


function showRestText() {
    var restText = document.getElementById('rest-text');
    restText.classList.add('show');
}


setTimeout(showRestText, 1000); // Show the rest of the text after 1 second


function hideSplashScreen() {
    var splashScreen = document.getElementById('splash_screen');
    splashScreen.classList.add('fade-out');
    splashScreen.addEventListener('animationend', removeSplashScreen); // Remove splash screen after fade-out animation ends
}


function removeSplashScreen() {
    var splashScreen = document.getElementById('splash_screen');
    splashScreen.remove();
    showMainContent();
}


function showMainContent() {
    var mainContent = document.getElementById('main-content');
    mainContent.classList.add('show');
}

setTimeout(hideSplashScreen, 3000);



// Simulator Switch Logic
let useCustomSimulator = true;
let memoryStartAddr = 0;

function createSimulatorSwitch() {
    const switchContainer = document.createElement('div');
    switchContainer.style.position = 'fixed';
    switchContainer.style.top = '10px';
    switchContainer.style.right = '10px';
    switchContainer.style.zIndex = '1000';
    switchContainer.style.backgroundColor = 'rgba(0, 0, 0, 0.7)';
    switchContainer.style.padding = '10px';
    switchContainer.style.borderRadius = '5px';
    switchContainer.style.color = 'white';
    switchContainer.style.display = 'flex';
    switchContainer.style.alignItems = 'center';
    switchContainer.style.gap = '10px';

    const label = document.createElement('label');
    label.innerText = 'Simulator: ';
    label.style.marginRight = '5px';

    const select = document.createElement('select');
    select.id = 'simulator-select';
    select.style.padding = '5px';
    select.style.borderRadius = '3px';
    select.style.backgroundColor = '#333';
    select.style.color = 'white';
    select.style.border = '1px solid #555';

    const optionSpike = document.createElement('option');
    optionSpike.value = 'spike';
    optionSpike.innerText = 'Spike (Standard)';
    select.appendChild(optionSpike);

    const optionCustom = document.createElement('option');
    optionCustom.value = 'custom';
    optionCustom.innerText = 'Custom Interpreter';
    select.appendChild(optionCustom);

    // Set default to custom
    select.value = 'custom';

    select.addEventListener('change', (e) => {
        useCustomSimulator = e.target.value === 'custom';
        memoryStartAddr = useCustomSimulator ? 0 : 0x80000000;
        console.log(`Simulator switched to: ${e.target.value}. Memory Start: 0x${memoryStartAddr.toString(16)}`);
        // Reset UI or state if needed
        reset_Registers();
    });

    switchContainer.appendChild(label);
    switchContainer.appendChild(select);
    document.body.appendChild(switchContainer);
}

// Initialize switch on load
window.addEventListener('load', createSimulatorSwitch);


function assemble_code() {
    // timeline()
    // const code = document.getElementById('editor-container').value;
    code = document.getElementById('editor-text-box').value
    mtype = document.getElementById('M-type').checked ? 'm' : '';
    ctype = document.getElementById('C-type').checked ? 'c' : '';
    ftype = document.getElementById('F-type').checked ? 'f' : '';
    dtype = document.getElementById('D-type').checked ? 'd' : '';
    vtype = document.getElementById('V-type').checked ? 'v' : '';
    rvtype = document.getElementById('varient-drop').value.toLowerCase()
    // if(document.getElementById('F-type').checked){
    //     ftype = true
    //     console.log("ftype is true")
    // console.log(m_type)
    // console.log(code)

    const assembleUrl = useCustomSimulator ? 'assemble-code' : 'gen-hex/assemble-code';

    axios.all([
        axios.post(assembleUrl, { code: code, mtype: mtype, ctype: ctype, ftype: ftype, dtype: dtype, vtype: vtype, rvtype: rvtype }),
        axios.post('gen-stats/assemble-code', { code: code }),
        // axios.post('timeline-update', { code: code })

    ])
        .then(axios.spread((data1, data2) => {
            if (data1 && data1.data && data1.data.success === false) {
                alert(data1.data.error_message + " at line " + data1.data.error_line); // <-- display Wrong_input_Error message
                return; // stop further handling
            }
            if (data1) {
                const hex = data1.data.hex;
                const baseins = data1.data.is_sudo
                populate_Decoder_Table(code, hex, baseins);
                document.getElementById('dump-box').value = hex;
            } else {
                alert("Error: " + data1.error);
            }
            if (data2) {
                const total_ins = data2.data.total_ins;
                const alu_ins = data2.data.alu_ins;
                const jump_ins = data2.data.jump_ins;
                const data_transfer_ins = data2.data.data_transfer_ins;
                const i_ins = data2.data.i_ins
                const m_ins = data2.data.m_ins
                const f_ins = data2.data.f_ins
                const c_ins = data2.data.c_ins
                const s_ins = data2.data.s_ins
                populate_Stats(total_ins, alu_ins, jump_ins, data_transfer_ins, i_ins, m_ins, f_ins, c_ins, s_ins);
            }
        }))
        .catch(error => {
            if (error.response && error.response.data) {
                const data = error.response.data;
                if (data.error_line) {
                    alert(`Error at line ${data.error_line}\n${data.error_message}`);
                } else if (data.error) {
                    alert(data.error);
                } else {
                    alert("Unknown error occurred");
                }
            } else {
                alert(error);
            }
        })
    const assemblebtn = document.getElementsByClassName('button-glow-button')[0];
    assemblebtn.disabled = true;

    const runbtn = document.getElementsByClassName('run-run-button')[1];
    runbtn.disabled = false;

    const stepbtn = document.getElementsByClassName('step-button')[0];
    stepbtn.disabled = false;
}

function populate_Memory_Table(data, isHex = true) {
    const tableBody = document.getElementById('memoryTableBody');
    tableBody.innerHTML = ''; // Clear existing rows

    const startAddress = memoryAddress + memoryStartAddr; // Use dynamic start address
    const memoryValues = data;

    for (let i = 0; i < 10; i++) {
        const addr1 = startAddress + (i * 4);
        const value = memoryValues[addr1] || 0;
        const row = document.createElement('tr');
        const formatValue = (value) => isHex ? `0x${value.toString(16)}` : value.toString(10);

        row.innerHTML = `
            <td>${formatValue(addr1)}</td>
            <td>${formatValue(memoryValues[addr1] || 0)}</td>
            <td>${formatValue(memoryValues[addr1 + 1] || 0)}</td>
            <td>${formatValue(memoryValues[addr1 + 2] || 0)}</td>
            <td>${formatValue(memoryValues[addr1 + 3] || 0)}</td>
        `;
        tableBody.appendChild(row);
    }
}

function reset_Registers() {
    const resetUrl = useCustomSimulator ? 'reset' : 'gen-hex/reset';
    axios.post(resetUrl, {
    })
        .then(response => {
            const currentInstructionRow = document.getElementById('decoderTableBody').rows[pc / 4];
            if (currentInstructionRow) {
                currentInstructionRow.classList.remove('highlight'); // Add highlight class
            }
            const newPc = response.data.pc;
            memorydic = response.data.memory
            reg_value = response.data.register
            f_reg_value = useCustomSimulator ? response.data.fregister : response.data.fregister // Check key name consistency?
            // Itype reset returns 'fregister', hex_dump reset returns 'fregister'. Consistent.
            // Wait, Itype reset returns 'vreg', hex_dump reset doesn't seem to return vreg?
            // hex_dump reset returns: register, memory, pc, fregister.
            // So vreg reset might be missing in hex_dump reset.

            pc = newPc;
            populate_Memory_Table(memorydic, isHex)
            update_Register_Values(reg_value, isHex)
            // update_FRegister_Values(f_reg_value,isHex) // Variable name issue?
            // response.data.fregister is assigned to f_reg_value local var.
            // But update_FRegister_Values uses f_reg_value global?
            // The code above: const f_reg_value = ... (shadows global?)
            // Let's fix variable usage.

            update_FRegister_Values(response.data.fregister, isHex);

            if (response.data.vreg) {
                update_VRegister_Values(response.data.vreg, isHex);
            }
        })
    const assemblebtn = document.getElementsByClassName('button-glow-button')[0];
    assemblebtn.disabled = false

    const stepbtn = document.getElementsByClassName('step-button')[0];
    stepbtn.disabled = true

    const runbtn = document.getElementsByClassName('run-run-button')[1];
    runbtn.disabled = true
    // assemble_code();
}


function stepInstruction() {
    const currentInstruction = document.getElementById('decoderTableBody').rows[pc / 4].cells[1].textContent;
    console.log(currentInstruction)
    const currentInstructionRow = document.getElementById('decoderTableBody').rows[pc / 4];
    if (currentInstructionRow) {
        currentInstructionRow.classList.add('highlight'); // Add highlight class
    }

    const stepUrl = useCustomSimulator ? 'step' : 'gen-hex/step';

    axios.post(stepUrl, {
        instruction: currentInstruction,
        pc: pc,
        memory: memorydic,
        register: reg_value,
        f_register: f_reg_value
    })
        .then(response => {
            const newPc = response.data.pc;
            memorydic = response.data.memory
            reg_value = response.data.register
            f_reg_value = response.data.f_reg
            v_reg_value = response.data.vreg // Itype returns vreg, hex_dump returns vreg.

            console.log("returned reg val", reg_value)
            console.log("returned reg val", v_reg_value)
            pc = newPc;
            console.log(pc)
            if (currentInstructionRow) {
                currentInstructionRow.classList.remove('highlight');
            }
            const newInstructionRow = document.getElementById('decoderTableBody').rows[pc / 4];
            if (newInstructionRow) {
                newInstructionRow.classList.add('highlight');
            }
            populate_Memory_Table(memorydic, isHex)
            update_Register_Values(reg_value, isHex)
            update_FRegister_Values(f_reg_value, isHex)
            if (v_reg_value) update_VRegister_Values(v_reg_value, isHex)
        })
        .catch(error => {
            console.error(error);
        });
}
function populate_Stats(total_ins, alu_ins, jump_ins, data_transfer_ins, i_ins, m_ins, f_ins, c_ins, s_ins) {
    const tableBody = document.getElementById('statsTableBody');
    const tableHTML = `
              <tbody id="statsTableBody">
                <tr>
                  <td>Total instructions</td>
                  <td id="total_instructions">${total_ins}</td>
                </tr>
                <tr>
                  <td>Total cycles</td>
                  <td id="Total_cycles">${0}</td>
                </tr>
                <tr>
                  <td>ALU Instructions</td>
                  <td id="ALU_instructions">${alu_ins}</td>
                </tr>
                <tr>
                  <td>Jump Instructions</td>
                  <td id="Jump_instructions">${jump_ins}</td>
                </tr>
                <tr>
                  <td>Data Transfer Instructions</td>
                  <td id="Data_transfer">${data_transfer_ins}</td>
                </tr>
                <tr>
                  <td>I Extention instructions</td>
                  <td id="I_ins">${i_ins}</td>
                </tr>
                <tr>
                  <td>M Extention Instruction</td>
                  <td id="M_ins">${m_ins}</td>
                </tr>
                <tr>
                  <td>F Extention Instruction</td>
                  <td id="F_ins">${f_ins}</td>
                </tr>
                <tr>
                  <td>C Extention Instruction</td>
                  <td id="c_ins">${c_ins}</td>
                </tr>
                <tr>
                  <td>Supplementary Instruction</td>
                  <td id="s_ins">${s_ins}</td>
                </tr>
              </tbody>
            </table>
    `
    tableBody.innerHTML = tableHTML;
}
function copy_hex() {
    const hexDump = document.getElementById('dump-box').value;
    navigator.clipboard.writeText(hexDump).then(() => {
        alert("Hex dump copied to clipboard!");
    });
}
function download_hex() {
    const hexDump = document.getElementById('dump-box').value;
    const blob = new Blob([hexDump], { type: 'text/plain' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'hex_dump.txt';
    link.click();
}
function clear_hex() {
    document.getElementById('dump-box').value = '';
}
function reset_editor() {
    document.getElementById('editor-text-box').value = ''
}
function populate_Decoder_Table(code, hex, baseins) {
    let instructions = code.split('\n').filter(line => line.trim() !== '');
    instructions = instructions.filter((ins) => !ins.includes(':'));
    console.log(instructions)
    const tableBody = document.getElementById('decoderTableBody');
    console.log("table", tableBody);
    tableBody.innerHTML = '';
    let count = 0
    instructions.forEach((instruction, index) => {
        const pc = `0x${(index * 4).toString(16)}`;
        let hexdumparr = hex.split('\n').filter(line => line.trim() !== '')
        console.log((hexdumparr));
        const machineCode = hexdumparr[count];
        const basicCode = baseins[count];
        const originalCode = instruction;
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${pc}</td>
            <td>${machineCode}</td>
            <td>${basicCode}</td>
            <td>${originalCode}</td>
        `;
        tableBody.appendChild(row);
        count = count + 1;
    });
}
function update_Register_Values(data, isHex = 'true') {
    console.log(data);
    data.forEach((value, index) => {
        const formattedValue = isHex ? `0x${(value >>> 0).toString(16).padStart(8, '0')}` : value.toString(10);
        document.getElementById(`reg-${index}`).innerText = formattedValue;
    });
}
function update_FRegister_Values(data, isHex = 'true') {
    data.forEach((value, index) => {
        let formattedValue;
        if (isHex) {
            // Create a buffer to interpret float bits as int
            const buf = new ArrayBuffer(4);
            const view = new DataView(buf);
            view.setFloat32(0, value);
            const intVal = view.getUint32(0);
            formattedValue = `0x${intVal.toString(16).padStart(8, '0')}`;
        } else {
            formattedValue = value.toString(10);
        }
        document.getElementById(`freg-${index}`).innerText = formattedValue;
    });
}
function update_VRegister_Values(data, isHex = 'true') {
    data.forEach((value, index) => {
        const formattedValue0 = isHex ? `0x${(value[0] >>> 0).toString(16).padStart(8, '0')}` : value[0].toString(10);
        const formattedValue1 = isHex ? `0x${(value[1] >>> 0).toString(16).padStart(8, '0')}` : value[1].toString(10);
        document.getElementById(`vreg-l${index}`).innerText = formattedValue0;
        document.getElementById(`vreg-o${index}-1`).innerText = formattedValue1;
    });
}
function changeNotation(notation) {
    isHex = notation === 'hex';
    console.log("check reg", reg_value);
    populate_Memory_Table(memorydic, isHex);
    update_Register_Values(reg_value, isHex);
    update_FRegister_Values(f_reg_value, isHex);
}

function run_Code() {
    // const code = document.getElementById('editor-container').value;
    code = document.getElementById('editor-text-box').value

    // If custom, use 'run-code' (Itype). If spike, use 'gen-hex/run-code'?
    // Wait, hex_dump doesn't have run-code.
    // If user selects Spike, maybe 'Run' button should just step through everything or use a different endpoint?
    // User said: "currently the script_test.js calls the hex_dump views and uses spike"
    // But script_test.js calls 'run-code'.
    // If 'run-code' maps to Itype, then it was ALWAYS using custom simulator for Run?
    // Or maybe 'run-code' maps to something else?
    // Assuming 'run-code' is Itype, and user wants to switch.
    // If Spike is selected, what should Run do?
    // Maybe Spike doesn't support Run All in this UI?
    // Or maybe I should assume 'run-code' is the custom one and only use it when custom is selected?
    // But what if Spike is selected?
    // I'll assume for now that 'run-code' is for custom, and for Spike we might not have a run-all or it's not implemented yet in this context.
    // However, the user said "when custom interpreator is selected the Itype views are called".
    // This implies that when Spike is selected, Itype views are NOT called.
    // So if Spike is selected, 'run-code' (Itype) should NOT be called?
    // But what is called then?
    // Maybe the user only cares about Step/Assemble for Spike, and Run for Custom?
    // Or maybe I should leave Run as is (Itype) but only enable it for Custom?
    // "currently the script_test.js calls the hex_dump views and uses spike"
    // This statement contradicts the code calling 'run-code' (Itype).
    // Unless 'run-code' is mapped to hex_dump in some other way?
    // I checked urls.py, 'run-code' is in Itype.urls.
    // So 'run-code' IS Itype.
    // Maybe the user never clicked Run before, or thinks it uses Spike?
    // Or maybe the user WANTS the switch to control this.
    // I will update run_Code to respect the switch.
    // If Custom: call 'run-code'.
    // If Spike: maybe alert "Run All not supported for Spike in this mode" or try to find a Spike run endpoint?
    // hex_dump views has 'assemble' which starts spike.
    // Maybe 'assemble' IS the run for Spike?
    // But assemble just returns hex.
    // I'll stick to: Run button calls 'run-code' (Itype) if Custom.
    // If Spike, I'll keep it as is (calling 'run-code') BUT warn or maybe it just works?
    // Actually, if I change 'run-code' to be conditional, I need a target for Spike.
    // Since I don't have one, I'll default to 'run-code' (Itype) but maybe the user implies they want to use Itype for everything when Custom is selected.
    // So I will just leave Run as 'run-code' but maybe add a check?
    // Wait, the user said: "when custom interpreator is selected the Itype views are called... also the register file then starts from 0 not from 0x80000000"
    // This implies that for Spike, registers/memory start at 0x80000000.
    // My `populate_Memory_Table` handles the offset.

    // Let's just update run_Code to use the same logic:
    // If Custom: use 'run-code'.
    // If Spike: use 'run-code'? No, 'run-code' is Itype.
    // If the user wants to Run with Spike, they probably can't right now via 'run-code' endpoint.
    // I'll assume Run is a feature of the Custom Interpreter mainly.
    // But I'll leave it calling 'run-code' for now, as I don't have a replacement.

    const runUrl = 'run-code'; // Always Itype for now?
    // Or maybe I should use 'gen-hex/run-code' if it existed?
    // I'll just leave run_Code as is, but update the callback to handle vreg and memory offset.

    axios.post(runUrl, { code: code })
        .then(response => {
            const hex = response.data.hex;
            const memory = response.data.memory
            memorydic = memory
            const baseins = response.data.is_sudo
            const reg = response.data.registers
            const freg = response.data.f_reg
            const vreg = response.data.vreg // Added in Itype view

            reg_value = reg
            f_reg_value = freg
            v_reg_value = vreg

            populate_Decoder_Table(code, hex, baseins);
            update_Register_Values(reg, isHex)
            update_FRegister_Values(freg, isHex)
            if (vreg) update_VRegister_Values(vreg, isHex)
            populate_Memory_Table(memory, isHex)
        })
        .catch(error => {
            console.error('There was an error!', error);
        });
    console.log(code)

}
document.getElementById('scrollUpBtn').addEventListener('click', () => {
    const scrollUpBtn = document.getElementById('scrollUpBtn');
    if (memoryAddress <= 0) {
        scrollUpBtn.disabled = true; // Disable scroll up button
        scrollUpBtn.classList.add('disabled');
    } else {
        memoryAddress -= 16; // Decrement memory address by 16
        populate_Memory_Table(memorydic, isHex);
        scrollUpBtn.disabled = false; // Enable scroll up button
        scrollUpBtn.classList.remove('disabled');
    }
});


document.getElementById('scrollDownBtn').addEventListener('click', () => {
    memoryAddress += 16; // Increment memory address by 16
    populate_Memory_Table(memorydic, isHex);
    const scrollUpBtn = document.getElementById('scrollUpBtn');
    if (memoryAddress > 0) {
        scrollUpBtn.disabled = false; // Enable scroll up button
        scrollUpBtn.classList.remove('disabled');
    }
});
// Hide the splash screen after 3 seconds
window.onscroll = function () { myFunction() };

// Get the navbar
// var navbar = document.getElementById("navbar");

// // Get the offset position of the navbar
// var sticky = navbar.offsetTop;

// // Add the sticky class to the navbar when you reach its scroll position. Remove "sticky" when you leave the scroll position
// function myFunction() {
//   if (window.scrollY >= sticky) {
//     navbar.classList.add("sticky")
//   } else {
//     navbar.classList.remove("sticky");
//   }
// }

const openbtn = document.querySelector('.info-btn');
const closebtn = document.querySelector('#close-btn');
const modal = document.querySelector('.info-content');

openbtn.addEventListener('click', () => {
    modal.showModal();
})
closebtn.addEventListener('click', () => {
    modal.close();
})


