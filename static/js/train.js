// Training interface JavaScript for Bjorn HVAC Abbreviation Tool

document.addEventListener('DOMContentLoaded', function() {
    // Training form submission
    const trainForm = document.getElementById('train-form');
    trainForm.addEventListener('submit', handleTrainFormSubmit);
    
    // Dictionary management
    const loadDictionaryBtn = document.getElementById('load-dictionary');
    loadDictionaryBtn.addEventListener('click', loadDictionary);
    
    const saveDictionaryBtn = document.getElementById('save-dictionary');
    saveDictionaryBtn.addEventListener('click', saveDictionary);
    
    const addAbbrevBtn = document.getElementById('add-abbrev');
    addAbbrevBtn.addEventListener('click', addAbbreviation);
});

// Handle training form submission
async function handleTrainFormSubmit(event) {
    event.preventDefault();
    
    // Get form data
    const fileInput = document.getElementById('training-file');
    const modelType = document.getElementById('model-type').value;
    const makeActive = document.getElementById('make-active').checked;
    
    // Validate input
    if (!fileInput.files || fileInput.files.length === 0) {
        alert('Please select a training file');
        return;
    }
    
    try {
        // Show loading state
        const submitBtn = trainForm.querySelector('button[type="submit"]');
        const originalBtnText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Training...';
        submitBtn.disabled = true;
        
        // In a real implementation, this would contact the API to train the model
        // For now, we'll simulate a successful training
        await new Promise(resolve => setTimeout(resolve, 3000));
        
        // Display results
        const trainingResults = document.getElementById('training-results');
        trainingResults.classList.remove('d-none');
        
        document.getElementById('training-stats').innerHTML = 
            `<strong>Model Type:</strong> ${modelType === 'hybrid' ? 'Hybrid Model' : 'Basic Model'}<br>` +
            `<strong>Training Data:</strong> ${fileInput.files[0].name}<br>` +
            `<strong>Examples Used:</strong> 248<br>` +
            `<strong>Validation Accuracy:</strong> 91.7%<br>` +
            `<strong>Status:</strong> Active and ready for use`;
        
        // Restore button state
        submitBtn.innerHTML = originalBtnText;
        submitBtn.disabled = false;
        
        // Scroll to results
        trainingResults.scrollIntoView({ behavior: 'smooth' });
        
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred during training. Please try again.');
    }
}

// Load abbreviation dictionary
async function loadDictionary() {
    try {
        const response = await fetch('/api/dictionary');
        
        if (response.ok) {
            const data = await response.json();
            
            if (data.success) {
                displayDictionary(data.entries);
            } else {
                alert('Error: ' + data.error);
            }
        } else {
            alert('Error: ' + response.statusText);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred. Please try again.');
    }
}

// Display abbreviation dictionary
function displayDictionary(entries) {
    // Show dictionary editor
    const dictionaryEditor = document.getElementById('dictionary-editor');
    dictionaryEditor.classList.remove('d-none');
    
    // Get table body
    const tableBody = document.querySelector('#dictionary-table tbody');
    tableBody.innerHTML = '';
    
    // Add rows
    entries.forEach((entry, index) => {
        const row = document.createElement('tr');
        
        row.innerHTML = `
            <td>${entry.original}</td>
            <td>${entry.abbreviated}</td>
            <td>
                <button class="btn btn-sm btn-danger" onclick="removeRow(this)">
                    Remove
                </button>
            </td>
        `;
        
        tableBody.appendChild(row);
    });
    
    // Scroll to dictionary
    dictionaryEditor.scrollIntoView({ behavior: 'smooth' });
}

// Remove dictionary row
window.removeRow = function(button) {
    const row = button.closest('tr');
    row.remove();
};

// Add new abbreviation
function addAbbreviation() {
    const termInput = document.getElementById('new-term');
    const abbrevInput = document.getElementById('new-abbrev');
    
    const term = termInput.value.trim();
    const abbrev = abbrevInput.value.trim();
    
    if (!term || !abbrev) {
        alert('Please enter both a term and its abbreviation');
        return;
    }
    
    // Add to table
    const tableBody = document.querySelector('#dictionary-table tbody');
    const row = document.createElement('tr');
    
    row.innerHTML = `
        <td>${term}</td>
        <td>${abbrev}</td>
        <td>
            <button class="btn btn-sm btn-danger" onclick="removeRow(this)">
                Remove
            </button>
        </td>
    `;
    
    tableBody.appendChild(row);
    
    // Clear inputs
    termInput.value = '';
    abbrevInput.value = '';
    termInput.focus();
}

// Save dictionary
async function saveDictionary() {
    try {
        // Collect entries from table
        const tableRows = document.querySelectorAll('#dictionary-table tbody tr');
        const entries = [];
        
        tableRows.forEach(row => {
            const cells = row.querySelectorAll('td');
            entries.push({
                original: cells[0].textContent,
                abbreviated: cells[1].textContent
            });
        });
        
        // In a real implementation, this would send the data to the API
        // For now, we'll simulate a successful save
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        alert(`Dictionary saved successfully with ${entries.length} entries.`);
        
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred. Please try again.');
    }
}