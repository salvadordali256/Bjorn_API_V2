// Main application JavaScript for Bjorn HVAC Abbreviation Tool

document.addEventListener('DOMContentLoaded', function() {
    // Text form submission
    const textForm = document.getElementById('text-form');
    textForm.addEventListener('submit', handleTextFormSubmit);
    
    // File form submission
    const fileForm = document.getElementById('file-form');
    fileForm.addEventListener('submit', handleFileFormSubmit);
    
    // Download button
    const downloadBtn = document.getElementById('download-results');
    downloadBtn.addEventListener('click', handleDownload);
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

// Handle text form submission
async function handleTextFormSubmit(event) {
    event.preventDefault();
    
    // Get form data
    const text = document.getElementById('text-input').value;
    const targetLength = document.getElementById('target-length').value;
    const useML = document.getElementById('use-ml').checked;
    
    // Validate input
    if (!text) {
        alert('Please enter text to abbreviate');
        return;
    }
    
    try {
        // Show loading state
        const submitBtn = textForm.querySelector('button[type="submit"]');
        const originalBtnText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...';
        submitBtn.disabled = true;
        
        // Prepare form data
        const formData = new FormData();
        formData.append('text', text);
        formData.append('target_length', targetLength);
        formData.append('use_ml', useML);
        
        // Send to API
        const response = await fetch('/api/abbreviate', {
            method: 'POST',
            body: formData
        });
        
        // Process response
        if (response.ok) {
            const data = await response.json();
            
            if (data.success) {
                displayTextResults(data);
            } else {
                alert('Error: ' + data.error);
            }
        } else {
            alert('Error: ' + response.statusText);
        }
        
        // Restore button state
        submitBtn.innerHTML = originalBtnText;
        submitBtn.disabled = false;
        
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred. Please try again.');
    }
}

// Display text abbreviation results
function displayTextResults(data) {
    // Show results section
    const resultsSection = document.getElementById('text-results');
    resultsSection.classList.remove('d-none');
    
    // Set original text
    document.getElementById('original-text').textContent = data.original;
    document.getElementById('original-length').textContent = data.original_length;
    
    // Set abbreviated text
    document.getElementById('abbreviated-text').textContent = data.abbreviated;
    document.getElementById('abbreviated-length').textContent = data.abbreviated_length;
    
    // Set reduction percentage
    document.getElementById('reduction-percentage').textContent = 
        data.reduction_percentage.toFixed(1) + '%';
    
    // Set method used
    let methodText = 'Rule-based';
    if (data.method_used === 'ml_hybrid') {
        methodText = 'AI Hybrid Model';
    } else if (data.method_used === 'ml_basic') {
        methodText = 'AI Basic Model';
    } else if (data.method_used === 'no_change') {
        methodText = 'No change needed (already short)';
    }
    document.getElementById('method-used').textContent = methodText;
    
    // Set rules applied
    const rulesList = document.getElementById('rules-applied');
    rulesList.innerHTML = '';
    
    if (data.rules_applied && data.rules_applied.length > 0) {
        data.rules_applied.forEach(rule => {
            const li = document.createElement('li');
            li.textContent = rule;
            rulesList.appendChild(li);
        });
    } else {
        const li = document.createElement('li');
        li.textContent = 'No rules applied';
        rulesList.appendChild(li);
    }
    
    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

// Handle file form submission
async function handleFileFormSubmit(event) {
    event.preventDefault();
    
    // Get form data
    const fileInput = document.getElementById('file-input');
    const targetLength = document.getElementById('file-target-length').value;
    const useML = document.getElementById('file-use-ml').checked;
    
    // Validate input
    if (!fileInput.files || fileInput.files.length === 0) {
        alert('Please select a file to upload');
        return;
    }
    
    try {
        // Show loading state
        const submitBtn = fileForm.querySelector('button[type="submit"]');
        const originalBtnText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...';
        submitBtn.disabled = true;
        
        // Prepare form data
        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        formData.append('target_length', targetLength);
        formData.append('use_ml', useML);
        
        // Send to API
        const response = await fetch('/api/abbreviate', {
            method: 'POST',
            body: formData
        });
        
        // Process response
        if (response.ok) {
            const data = await response.json();
            
            if (data.success) {
                displayFileResults(data);
                // Store CSV data for download
                window.csvData = data.csv_data;
                window.csvFilename = 'abbreviated_' + data.filename;
            } else {
                alert('Error: ' + data.error);
            }
        } else {
            alert('Error: ' + response.statusText);
        }
        
        // Restore button state
        submitBtn.innerHTML = originalBtnText;
        submitBtn.disabled = false;
        
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred. Please try again.');
    }
}

// Display file processing results
function displayFileResults(data) {
    // Show results section
    const resultsSection = document.getElementById('file-results');
    resultsSection.classList.remove('d-none');
    
    // Set stats text
    const stats = data.stats;
    document.getElementById('file-stats').innerHTML = 
        `<strong>Processed:</strong> ${stats.processed_count} records<br>` +
        `<strong>Success Rate:</strong> ${stats.success_rate}<br>` +
        `<strong>Average Reduction:</strong> ${stats.avg_reduction}<br>` +
        `<strong>Processing Time:</strong> ${stats.processing_time}<br>` +
        `<strong>Method Used:</strong> ${stats.method_used}`;
    
    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

// Handle download button click
function handleDownload() {
    if (!window.csvData) {
        alert('No data available for download');
        return;
    }
    
    // Create blob from CSV data
    const blob = new Blob([window.csvData], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    
    // Create download link
    const a = document.createElement('a');
    a.href = url;
    a.download = window.csvFilename || 'abbreviated_data.csv';
    document.body.appendChild(a);
    a.click();
    
    // Clean up
    setTimeout(() => {
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }, 100);
}