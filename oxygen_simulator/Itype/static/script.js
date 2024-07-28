
let variantEnabled = false;

function updateConfig(type, isChecked) {
    switch (type) {
        case 'variant':
            variantEnabled = isChecked;
            break;
    }
}
function updateRegisterValues(data) {
    data.forEach((value, index) => {
        document.getElementById(`reg-${index}`).innerText = `0x${value.toString(16).padStart(8, '0')}`;
    });
}

function assembleCode() {
    // const code = document.getElementById('editor-container').value;
    code = document.getElementsByClassName('codeEditor')[0].value
    let hehe
    let base
    let registers
    axios.post('/assemble-code/', { code: code })
            .then(response => {
                const hex = response.data.hex;
                const baseins = response.data.is_sudo
                const reg = response.data.registers
                console.log(baseins)
                hehe = hex
                base = baseins
                console.log(reg)
                registers = reg
                document.getElementById('hexDump').value = hex;
                populateDecoderTable(code,hehe,base);
                updateRegisterValues(registers)
            })
            .catch(error => {
                console.error('There was an error!', error);
            });
    console.log(code)
    
    const hexDump = "Generated Hex Dump";
    document.getElementById('hexDump').value = hexDump;
    
    
}

function dumpHex() {
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
    const instructions = code.split('\n').filter(line => line.trim() !== '');
    console.log(instructions)
    const tableBody = document.getElementById('decoderTableBody');
    tableBody.innerHTML = '';
    let count = 0

    instructions.forEach((instruction, index) => {
            const pc = `0x${(index * 4).toString(16)}`;
            hexdumparr = hex_dump.split('\n').filter(line => line.trim() !== '')
            
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
            count = count +1
        });
}

function stepInstruction() {
    // Logic to step through instructions
}

