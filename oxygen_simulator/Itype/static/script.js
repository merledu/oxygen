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
    axios.post('/assemble-code/', { code: code })
            .then(response => {
                const hex = response.data.hex;
                document.getElementById('hexDump').value = hex;
            })
            .catch(error => {
                console.error('There was an error!', error);
            });
    console.log(code)
    
    const hexDump = "Generated Hex Dump";
    document.getElementById('hexDump').value = hexDump;
    populateDecoderTable(code);
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

function populateDecoderTable(code) {
    const instructions = code.split('\n').filter(line => line.trim() !== '');
    const tableBody = document.getElementById('decoderTableBody');
    tableBody.innerHTML = '';

    instructions.forEach((instruction, index) => {
        const pc = `0x${(index * 4).toString(16)}`;
        const machineCode = `0x${(index * 4 + 0x10000000).toString(16)}`; // Dummy machine code
        const basicCode = instruction; // Assuming basic code is the same as the original for now
        const originalCode = instruction; // Placeholder

        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${pc}</td>
            <td>${machineCode}</td>
            <td>${basicCode}</td>
            <td>${originalCode}</td>
        `;
        tableBody.appendChild(row);
    });
}

function stepInstruction() {
    // Logic to step through instructions
}

