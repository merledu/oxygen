let pipelineEnabled = false;
let dataForwardingEnabled = false;
let variantEnabled = false;

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
    const code = document.getElementById('codeEditor').value;
    // Perform the assembly operation and generate hex dump
    const hexDump = "Generated Hex Dump";
    document.getElementById('hexDump').value = hexDump;
    // Populate the decoder table
    populateDecoderTable(code);
}

function dumpHex() {
    // Logic to dump hex code
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
