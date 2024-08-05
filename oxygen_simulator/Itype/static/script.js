
let variantEnabled = false;

function updateConfig(type, isChecked) {
    switch (type) {
        case 'variant':
            variantEnabled = isChecked;
            break;
    }
}
let reg_value = []
let memorydic = {}
let pc = 0
function updateRegisterValues(data) {
    data.forEach((value, index) => {
        document.getElementById(`reg-${index}`).innerText = `0x${value.toString(16).padStart(8, '0')}`;
    });
}

function runCode() {
    // const code = document.getElementById('editor-container').value;
    code = document.getElementsByClassName('codeEditor')[0].value
    console.log(typeof(code))

    axios.post('run-code', { code: code })
            .then(response => {
                const hex = response.data.hex;
                const memory = response.data.memory
                memorydic = memory
                const baseins = response.data.is_sudo
                const reg = response.data.registers
                reg_value = reg
                populateDecoderTable(code,hex,baseins);
                updateRegisterValues(reg)
                populateMemoryTable(memory)
            })
            .catch(error => {
                console.error('There was an error!', error);
            });
    console.log(code)
    
}

function dumpHex() {
    code = document.getElementsByClassName('codeEditor')[0].value
    axios.post('dump-code', { code: code })
            .then(response => {
                const hex = response.data.hex;
                document.getElementById('hexDump').value = hex;
            })
            .catch(error => {
                console.error('There was an error!', error);
            })

}

function assembleCode(){
    code = document.getElementsByClassName('codeEditor')[0].value
    axios.post('assemble-code', { code: code })
            .then(response => {
                const hex = response.data.hex;
                const baseins = response.data.is_sudo
                populateDecoderTable(code,hex,baseins);
            })
            .catch(error => {
                console.error('There was an error!', error);
            })
}

function copyHex() {
    const hexDump = document.getElementById('hexDump').value;
    navigator.clipboard.writeText(hexDump).then(() => {
        alert("Hex dump copied to clipboard!");
    });
}

function downloadHex() {
    const hexDump = document.getElementById('hexDump').value;
    const blob = new Blob([hexDump], { type: 'text/plain' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'hex_dump.txt';
    link.click();
}

function clearHex() {
    document.getElementById('hexDump').value = '';

}

function populateDecoderTable(code,hex_dump,baseins) {
    let instructions = code.split('\n').filter(line => line.trim() !== '');
    
    instructions = instructions.filter((ins) => !ins.includes(':'));
    console.log(instructions)
    const tableBody = document.getElementById('decoderTableBody');
    const tableBody2 = document.getElementById('adecoderTableBody');
    console.log("table" , tableBody);
    console.log("table 2 " , tableBody2);
    tableBody.innerHTML = '';
    tableBody2.innerHTML = '';
    let count = 0

    instructions.forEach((instruction, index) => {
        const pc = `0x${(index * 4).toString(16)}`;
        let hexdumparr = hex_dump.split('\n').filter(line => line.trim() !== '')
        
        console.log((hexdumparr));
        const machineCode = hexdumparr[count];
        const basicCode = baseins[count]; 
        const originalCode = instruction;

        const row = document.createElement('tr');
        const row2 = document.createElement('tr');
        row.innerHTML = `
            <td>${pc}</td>
            <td>${machineCode}</td>
            <td>${basicCode}</td>
            <td>${originalCode}</td>
        `;
        row2.innerHTML = `
            <td>${pc}</td>
            <td>${machineCode}</td>
            <td>${basicCode}</td>
            <td>${originalCode}</td>
        `;
        tableBody.appendChild(row);
        tableBody2.appendChild(row2);
        
        count = count +1
    });
}

function stepInstruction() {
    const currentInstruction = document.getElementById('decoderTableBody').rows[pc/4].cells[1].textContent;
    console.log(currentInstruction)
    const currentInstructionRow = document.getElementById('decoderTableBody').rows[pc/4];
    if (currentInstructionRow) {
        currentInstructionRow.classList.add('highlight'); // Add highlight class
    }


    axios.post('step', {
      instruction: currentInstruction,
      pc: pc,
      memory:memorydic,
      register : reg_value
    })
    .then(response => {
      const newPc = response.data.pc;
      memorydic = response.data.memory
      reg_value = response.data.register
      pc = newPc;
      console.log(pc)
      // Remove highlight from previous row
        if (currentInstructionRow) {
        currentInstructionRow.classList.remove('highlight');
        }

    // Highlight new row
    const newInstructionRow = document.getElementById('decoderTableBody').rows[pc/4];
        if (newInstructionRow) {
            newInstructionRow.classList.add('highlight');
        }


      populateMemoryTable(memorydic)
      updateRegisterValues(reg_value)
    })
    .catch(error => {
      console.error(error);
    });
  }
function reset(){

    axios.post('reset', {
      })
      .then(response => {
        const newPc = response.data.pc;
        memorydic = response.data.memory
        console.log(memorydic)
        reg_value = response.data.register
        console.log(reg_value)
        pc = newPc;
        console.log(pc)

        populateMemoryTable(memorydic)
        updateRegisterValues(reg_value)
      })

}

// function highlightInstruction(pc) {
// const rows = document.getElementById('decoderTableBody').rows;
// for (let i = 0; i < rows.length; i++) {
//     rows[i].classList.remove('highlight');
// }
// rows[pc].classList.add('highlight');
// }
  

// Function to populate memory table
let memoryAddress = 0; // Initial memory address
let memoryValues = {}; // Dictionary of memory values

// Function to populate memory table
function populateMemoryTable(data) {
    const tableBody = document.getElementById('memoryTableBody');
    tableBody.innerHTML = ''; // Clear existing rows

    
            memoryValues = data; 
            for (let i = 0; i < 10; i++) { 
                const addr1 = memoryAddress + (i * 4);
                const addr2 = memoryAddress + (i);
                const value = memoryValues[addr2] || 0; 
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>0x${addr1.toString(16)}</td>
                    <td>0x${(memoryValues[addr1] || 0).toString(16)}</td>
                    <td>0x${(memoryValues[addr1+1] || 0).toString(16)}</td>
                    <td>0x${(memoryValues[addr1+2] || 0).toString(16)}</td>
                    <td>0x${(memoryValues[addr1+3] || 0).toString(16)}</td>
                `;
                tableBody.appendChild(row);
                
            }
        ;
}

// Scroll up button click handler
document.getElementById('scrollUpBtn').addEventListener('click', () => {
    const scrollUpBtn = document.getElementById('scrollUpBtn');
    if (memoryAddress <= 0) {
        scrollUpBtn.disabled = true; // Disable scroll up button
        scrollUpBtn.classList.add('disabled');
    } else {
        memoryAddress -= 16; // Decrement memory address by 16
        populateMemoryTable(memorydic);
        scrollUpBtn.disabled = false; // Enable scroll up button
        scrollUpBtn.classList.remove('disabled');
    }
});

// Scroll down button click handler
document.getElementById('scrollDownBtn').addEventListener('click', () => {
    memoryAddress += 16; // Increment memory address by 16
    populateMemoryTable(memorydic);
    const scrollUpBtn = document.getElementById('scrollUpBtn');
    if (memoryAddress > 0) {
        scrollUpBtn.disabled = false; // Enable scroll up button
        scrollUpBtn.classList.remove('disabled');
    }
});

// function stepInstruction() {
//     const code = document.getElementsByClassName('codeEditor')[0].value;
//     const pc = document.getElementById('pc').value;
//     const registers = JSON.parse(document.getElementById('registers').value);
//     const memory = JSON.parse(document.getElementById('memory').value);

//     axios.post('step-instruction', {
//         code: code,
//         pc: pc,
//         registers: registers,
//         memory: memory
//     })
//     .then(response => {
//         const updatedPc = response.data.pc;
//         const updatedRegisters = response.data.registers;
//         const updatedMemory = response.data.memory;

//         // Update the frontend with the new values
//         document.getElementById('pc').value = updatedPc;
//         document.getElementById('registers').value = JSON.stringify(updatedRegisters);
//         document.getElementById('memory').value = JSON.stringify(updatedMemory);

//         // Update the decoder table
//         populateDecoderTable(code, updatedPc);
//     })
//     .catch(error => {
//         console.error('There was an error!', error);
//     });
// }

// Initialize memory table