
let variantEnabled = false;

function updateConfig(type, isChecked) {
    switch (type) {
        case 'variant':
            variantEnabled = isChecked;
            break;
    }
}


let reg_value = []
let f_reg_value = []
let memorydic = {}
let pc = 0
function update_Register_Values(data) {
    data.forEach((value, index) => {
        document.getElementById(`reg-${index}`).innerText = `0x${value.toString(16).padStart(8, '0')}`;
    });
}


function update_FRegister_Values(data){
    data.forEach((value, index) => {
        document.getElementById(`freg-${index}`).innerText = `0x${value.toString(16).padStart(8 , '0')}`
    });

}


function run_code() {
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
                const freg = response.data.f_reg
                reg_value = reg
                f_reg_value = freg
                populate_Decoder_Table(code,hex,baseins);
                update_Register_Values(reg)
                update_FRegister_Values(freg)
                populate_Memory_Table(memory)
            })
            .catch(error => {
                console.error('There was an error!', error);
            });
    console.log(code)
    
}


function dump_hex() {
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


function assemble_code(){
    code = document.getElementsByClassName('codeEditor')[0].value
    axios.post('assemble-code', { code: code })
            .then(response => {
                const hex = response.data.hex;
                const baseins = response.data.is_sudo
                populate_Decoder_Table(code,hex,baseins);
            })
            .catch(error => {
                console.error('There was an error!', error);
            })
}


function copy_hex() {
    const hexDump = document.getElementById('hexDump').value;
    navigator.clipboard.writeText(hexDump).then(() => {
        alert("Hex dump copied to clipboard!");
    });
}


function download_hex() {
    const hexDump = document.getElementById('hexDump').value;
    const blob = new Blob([hexDump], { type: 'text/plain' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'hex_dump.txt';
    link.click();
}


function clear_hex() {
    document.getElementById('hexDump').value = '';
}


function populate_Decoder_Table(code,hex_dump,baseins) {
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
      register : reg_value,
      f_register : f_reg_value
    })
    .then(response => {
        const newPc = response.data.pc;
        memorydic = response.data.memory
        reg_value = response.data.register
        f_reg_value = response.data.f_reg
        console.log(typeof(f_reg_value))
        pc = newPc;
        console.log(pc)
        if (currentInstructionRow) {
        currentInstructionRow.classList.remove('highlight');
        }
        const newInstructionRow = document.getElementById('decoderTableBody').rows[pc/4];
        if (newInstructionRow) {
            newInstructionRow.classList.add('highlight');
        }
        populate_Memory_Table(memorydic)
        update_Register_Values(reg_value)
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
        f_reg_value = response.data.f_register
        console.log(reg_value)
        pc = newPc;
        console.log(pc)
        populate_Memory_Table(memorydic)
        update_Register_Values(reg_value)
        update_FRegister_Values(f_reg_value)
      })

}
  

let memoryAddress = 0; 
let memoryValues = {}; 

function populate_Memory_Table(data) {
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


document.getElementById('scrollUpBtn').addEventListener('click', () => {
    const scrollUpBtn = document.getElementById('scrollUpBtn');
    if (memoryAddress <= 0) {
        scrollUpBtn.disabled = true; // Disable scroll up button
        scrollUpBtn.classList.add('disabled');
    } else {
        memoryAddress -= 16; // Decrement memory address by 16
        populate_Memory_Table(memorydic);
        scrollUpBtn.disabled = false; // Enable scroll up button
        scrollUpBtn.classList.remove('disabled');
    }
});


document.getElementById('scrollDownBtn').addEventListener('click', () => {
    memoryAddress += 16; // Increment memory address by 16
    populate_Memory_Table(memorydic);
    const scrollUpBtn = document.getElementById('scrollUpBtn');
    if (memoryAddress > 0) {
        scrollUpBtn.disabled = false; // Enable scroll up button
        scrollUpBtn.classList.remove('disabled');
    }
});
