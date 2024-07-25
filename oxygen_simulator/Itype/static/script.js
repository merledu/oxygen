let pipelineEnabled = false;
let dataForwardingEnabled = false;
let variantEnabled = false;

const getRequest = async () => {
    const response = await axios.get('/request', {
    params: {
    'test' : "test"
    }
    })
    console.log(response.data)
    }
    getRequest();

function updateConfig(type, isChecked) {
    switch (type) {
        case 'pipeline':
            pipelineEnabled = isChecked;
            break;
        case 'dataForwarding':
            dataForwardingEnabled = isChecked;
            break;
        case 'variant':
            variantEnabled = isChecked;
            break;
    }
}

function assembleCode() {
    // const code = document.getElementById('editor-container').value;
    code = document.getElementsByClassName('codeEditor')[0].value
    let hehe
    let base
    axios.post('/assemble-code/', { code: code })
            .then(response => {
                const hex = response.data.hex;
                const baseins = response.data.is_sudo
                console.log(baseins)
                hehe = hex
                base = baseins
                document.getElementById('hexDump').value = hex;
                populateDecoderTable(code,hehe,base);
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
        // const pc = `0x${(index * 4).toString(16)}`;
        // // const machineCode = `0x${(index * 4 + 0x10000000).toString(16)}`; // Dummy machine code
        // const machineCode = hex_dump;
        // const basicCode = instruction; // Assuming basic code is the same as the original for now
        // const originalCode = instruction; // Placeholder

        // const row = document.createElement('tr');
        // row.innerHTML = `
        //     <td>${pc}</td>
        //     <td>${machineCode}</td>
        //     <td>${basicCode}</td>
        //     <td>${originalCode}</td>
        // `;
        // tableBody.appendChild(row);
            const pc = `0x${(index * 4).toString(16)}`;
            hexdumparr = hex_dump.split('\n').filter(line => line.trim() !== '')
            
            console.log((hexdumparr));
            const machineCode = hexdumparr[count];
            const basicCode = baseins[count]; // Assuming basic code is the same as the original for now
            const originalCode = instruction; // Placeholder
    
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

