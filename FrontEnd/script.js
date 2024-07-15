function openTab(event, tabName) {
    // Hide all tab content
    const tabContents = document.querySelectorAll(".tab-content");
    tabContents.forEach(content => content.style.display = "none");

    // Remove active class from all tab links
    const tabLinks = document.querySelectorAll(".tab-link");
    tabLinks.forEach(link => link.classList.remove("active"));

    // Show the current tab content and add active class to the clicked tab link
    document.getElementById(tabName).style.display = "block";
    event.currentTarget.classList.add("active");
}

// Show the first tab by default
document.addEventListener("DOMContentLoaded", function() {
    document.querySelector(".tab-link").click();
});

function downloadHexDump() {
    const hexDumpContent = document.getElementById('hex-dump-content').innerText;
    const blob = new Blob([hexDumpContent], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = url;
    a.download = 'hex_dump.txt';
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
}

function copyHexDump() {
    const hexDumpContent = document.getElementById('hex-dump-content').innerText;
    navigator.clipboard.writeText(hexDumpContent).then(() => {
        alert('Hex dump copied to clipboard!');
    });
}

function clearHexDump() {
    document.getElementById('hex-dump-content').innerText = '';
}

function dumpHex() {
    const instructionInput = document.getElementById('instruction-input').value;
    const hexDump = generateHexDump(instructionInput);
    document.getElementById('hex-dump-content').innerText = hexDump;
}

function generateHexDump(instructions) {
    // Placeholder function, replace with actual instruction to hex conversion logic
    return instructions.split('\n').map(instruction => {
        // Assuming each instruction is already in hex form or can be converted
        // Replace the following line with actual conversion logic
        return instruction.trim() ? `0x${parseInt(instruction, 16).toString(16).padStart(8, '0')}` : '';
    }).join('\n');
}
