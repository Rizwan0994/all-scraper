// Universal Product Scraper - Main JavaScript
// Handles all frontend functionality

// Initialize WebSocket connection
const socket = io();

// Global variables for filtering and pagination
let allProducts = [];
let filteredProducts = [];

// Pagination variables
let currentPage = 1;
let productsPerPage = 50; // Default products per page
let totalPages = 0;
let totalProducts = 0;
let isLoading = false;

// Chunk-based pagination state
let paginationState = {
    currentPage: 1,
    perPage: 50,
    totalProducts: 0,
    totalPages: 0,
    hasMore: false,
    isLoading: false
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Universal Product Scraper initialized');
    
    // Initialize form submission
    initializeFormSubmission();
    
    // Initialize button handlers
    initializeButtonHandlers();
    
    // Load initial products
    setTimeout(loadProducts, 1000);
    
    // Load product count for database insertion
    setTimeout(loadProductCount, 1500);
    
    // Auto-fill database credentials
    setTimeout(autoFillDatabaseCredentials, 2000);
});

function initializeFormSubmission() {
    const scrapeForm = document.getElementById('scrapeForm');
    if (scrapeForm) {
        scrapeForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            console.log('Form submitted');
            
            const keywords = document.getElementById('keywords').value;
            const maxProducts = document.getElementById('maxProducts').value;
            
            console.log('Keywords:', keywords);
            console.log('Max Products:', maxProducts);
            
            // Get selected websites
            const selectedSites = [];
            const siteCheckboxes = ['amazon', 'ebay', 'daraz', 'aliexpress', 'etsy', 'valuebox'];
            siteCheckboxes.forEach(site => {
                const checkbox = document.getElementById(site);
                if (checkbox && checkbox.checked) {
                    selectedSites.push(site);
                }
            });
            
            console.log('Selected sites:', selectedSites);
            
            if (selectedSites.length === 0) {
                alert('Please select at least one website to scrape.');
                return;
            }
            
            if (!keywords.trim()) {
                alert('Please enter keywords to scrape.');
                return;
            }
            
            const progressDiv = document.getElementById('progress');
            const resultsDiv = document.getElementById('results');
            
            progressDiv.style.display = 'block';
            resultsDiv.innerHTML = '';
            
            // Update status
            const statusElement = document.getElementById('current-status');
            if (statusElement) {
                statusElement.innerHTML = '<span class="status-indicator status-scraping"></span> Scraping...';
            }
            
            // Clear live products feed
            clearLiveFeed();
            
            try {
                console.log('Sending request to /scrape');
                const response = await fetch('/scrape', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        keywords: keywords,
                        max_products: parseInt(maxProducts),
                        selected_sites: selectedSites
                    })
                });
                
                console.log('Response received:', response.status);
                const data = await response.json();
                console.log('Response data:', data);
                
                if (data.status === 'started') {
                    resultsDiv.innerHTML = '<div class="alert alert-success">Scraping started successfully!</div>';
                    
                    // Show stop button and hide start button
                    const startBtn = document.getElementById('start-btn');
                    const stopBtn = document.getElementById('stop-btn');
                    
                    console.log('Start button found:', !!startBtn);
                    console.log('Stop button found:', !!stopBtn);
                    
                    if (startBtn) {
                        startBtn.style.display = 'none';
                        console.log('Start button hidden');
                    }
                    if (stopBtn) {
                        stopBtn.style.display = 'block';
                        console.log('Stop button shown');
                    }
                    
                    startStatusPolling();
                } else {
                    throw new Error(data.error || 'Unknown error');
                }
                
            } catch (error) {
                console.error('Scraping error:', error);
                progressDiv.style.display = 'none';
                resultsDiv.innerHTML = `<div class="alert alert-danger">Error: ${error.message}</div>`;
                
                // Show start button and hide stop button on error
                const startBtn = document.getElementById('start-btn');
                const stopBtn = document.getElementById('stop-btn');
                if (startBtn) startBtn.style.display = 'block';
                if (stopBtn) stopBtn.style.display = 'none';
                
                // Update status
                const statusElement = document.getElementById('current-status');
                if (statusElement) {
                    statusElement.innerHTML = '<span class="status-indicator status-error"></span> Error';
                }
            }
        });
    } else {
        console.error('Scrape form not found!');
    }
}

function initializeButtonHandlers() {
    // Fallback button click handler for scraping
    const scrapeButton = document.querySelector('.btn-scrape');
    if (scrapeButton) {
        scrapeButton.addEventListener('click', function(e) {
            console.log('Scrape button clicked');
        });
    }
    
    // Stop scraping button handler
    const stopButton = document.getElementById('stop-btn');
    if (stopButton) {
        stopButton.addEventListener('click', async function(e) {
            e.preventDefault();
            console.log('Stop button clicked');
            
            try {
                const response = await fetch('/api/scraping/stop', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'}
                });
                
                const result = await response.json();
                
                if (result.status === 'success') {
                    showAlert('Scraping will stop gracefully...', 'warning');
                    // Hide stop button and show start button
                    stopButton.style.display = 'none';
                    document.getElementById('start-btn').style.display = 'block';
                } else {
                    showAlert('Error stopping scraping: ' + result.error, 'danger');
                }
            } catch (error) {
                console.error('Error stopping scraping:', error);
                showAlert('Error stopping scraping. Please try again.', 'danger');
            }
        });
    }
    
    // Delete all products button handler
    const deleteAllButton = document.getElementById('delete-all-btn');
    if (deleteAllButton) {
        deleteAllButton.addEventListener('click', async function(e) {
            e.preventDefault();
            console.log('Delete all button clicked');
            
            // Show confirmation dialog
            if (!confirm('Are you sure you want to delete all scraped products? This will remove both JSON and CSV files and cannot be undone.')) {
                return;
            }
            
            try {
                const response = await fetch('/api/products/delete-all', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'}
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showAlert(result.message, 'success');
                    // Clear the products display
                    const productsContainer = document.getElementById('liveProducts');
                    if (productsContainer) {
                        productsContainer.innerHTML = '<div class="text-center text-muted p-4">No products available. Start scraping to see results.</div>';
                    }
                    // Update product count
                    updateProductCount(0);
                } else {
                    showAlert('Error deleting products: ' + result.error, 'danger');
                }
            } catch (error) {
                console.error('Error deleting products:', error);
                showAlert('Error deleting products. Please try again.', 'danger');
            }
        });
    }
}

// Database manager function
function openDatabaseManager() {
    try {
        console.log('Opening database manager');
        // Show database settings inline instead of popup
        const dbSection = document.getElementById('databaseSection');
        if (dbSection) {
            dbSection.style.display = 'block';
            // Scroll to database section
            dbSection.scrollIntoView({ behavior: 'smooth' });
        } else {
            console.error('Database section not found');
            alert('Database manager not available');
        }
    } catch (error) {
        console.error('Error opening database manager:', error);
        alert('Error opening database manager. Please try again.');
    }
}

// Database management functions
async function testDatabaseConnection() {
    const dbType = document.getElementById('dbType').value;
    const host = document.getElementById('dbHost').value;
    const port = document.getElementById('dbPort').value;
    const database = document.getElementById('dbName').value;
    const username = document.getElementById('dbUsername').value;
    const password = document.getElementById('dbPassword').value;
    
    try {
        const response = await fetch('/api/db/connect', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                db_type: dbType,
                host: host,
                port: port,
                database: database,
                username: username,
                password: password
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('Database connection successful!');
        } else {
            alert('Connection failed: ' + data.error);
        }
    } catch (error) {
        alert('Error testing connection: ' + error.message);
    }
}

async function insertProductsToDatabase() {
    const tableName = document.getElementById('tableName').value;
    
    // Get field mappings
    const mapping = {
        'product_name': document.getElementById('custom_product_name').value,
        'unit_price': document.getElementById('custom_unit_price').value,
        'category': document.getElementById('custom_category').value,
        'source_site': document.getElementById('custom_source_site').value
    };
    
    try {
        const response = await fetch('/api/db/insert', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                table_name: tableName,
                mapping: mapping
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert(`Successfully inserted ${data.inserted_count} products out of ${data.total_count} total products.`);
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        alert('Error inserting products: ' + error.message);
    }
}

function updateStatus(type, status) {
    const statusElement = document.getElementById('current-status');
    if (statusElement) {
        statusElement.innerHTML = `<span class="status-indicator status-${type}"></span> ${status}`;
    }
}

function updateCurrentSite(site) {
    if (site) {
        document.getElementById('current-site').textContent = site;
    }
}

function updateSiteProgress(site, count) {
    console.log(`${site} completed: ${count} products`);
}

function addProductToLiveFeed(product) {
    const liveProductsDiv = document.getElementById('live-products');
    if (!liveProductsDiv) return;
    
    // Remove the "no products" message if it exists
    const noProductsMsg = liveProductsDiv.querySelector('.text-center.text-muted');
    if (noProductsMsg) {
        noProductsMsg.remove();
    }
    
    const productHtml = `
        <div class="product-item">
            <div class="row">
                <div class="col-md-8">
                    <h6 class="mb-1">${product.name}</h6>
                    <div class="small text-muted">
                        <span class="badge bg-primary me-2">${product.site}</span>
                        <span class="badge bg-secondary me-2">${product.category || 'N/A'}</span>
                        <span class="text-success fw-bold">$${product.price > 0 ? product.price.toFixed(2) : '0.00'}</span>
                    </div>
                </div>
                <div class="col-md-4 text-end">
                    <small class="text-muted">${new Date().toLocaleTimeString()}</small>
                </div>
            </div>
        </div>
    `;
    
    // Add to the top of the feed
    liveProductsDiv.insertAdjacentHTML('afterbegin', productHtml);
    
    // Keep only the last 20 products in the feed
    const products = liveProductsDiv.querySelectorAll('.product-item');
    if (products.length > 20) {
        products[products.length - 1].remove();
    }
}

function updateLiveTotal(count) {
    const liveTotalElement = document.getElementById('live-total');
    if (liveTotalElement) {
        if (count !== undefined) {
            liveTotalElement.textContent = count;
        } else {
            // Increment the current count
            const currentCount = parseInt(liveTotalElement.textContent) || 0;
            liveTotalElement.textContent = currentCount + 1;
        }
    }
}

function clearLiveFeed() {
    const liveProductsDiv = document.getElementById('live-products');
    if (liveProductsDiv) {
        liveProductsDiv.innerHTML = `
            <div class="text-center text-muted py-4">
                <i class="fas fa-stream fa-3x mb-3"></i>
                <p>Products will appear here as they are scraped...</p>
            </div>
        `;
    }
    
    // Reset live total
    const liveTotalElement = document.getElementById('live-total');
    if (liveTotalElement) {
        liveTotalElement.textContent = '0';
    }
}

function showCompletionSummary(data) {
    const resultsDiv = document.getElementById('results');
    resultsDiv.innerHTML = `
        <div class="alert alert-success">
            <h5><i class="fas fa-check-circle"></i> Scraping Complete!</h5>
            <p><strong>Total Products:</strong> ${data.total_products}</p>
            <p><strong>Sites:</strong> ${Object.keys(data.site_breakdown).join(', ')}</p>
        </div>
    `;
}

function startStatusPolling() {
    const pollStatus = async () => {
        try {
            const response = await fetch('/status');
            const stats = await response.json();
            
            if (stats.total_products > 0) {
                updateStatus('ready', 'Complete');
                document.getElementById('progress').style.display = 'none';
                loadProducts();
                return;
            }
            
            setTimeout(pollStatus, 3000);
        } catch (error) {
            console.error('Status polling error:', error);
        }
    };
    
    setTimeout(pollStatus, 3000);
}

function applyFilters() {
    const categoryFilter = document.getElementById('categoryFilter').value;
    const subcategoryFilter = document.getElementById('subcategoryFilter').value;
    const siteFilter = document.getElementById('siteFilter').value;
    const minPrice = parseFloat(document.getElementById('minPrice').value) || 0;
    const maxPrice = parseFloat(document.getElementById('maxPrice').value) || Infinity;
    
    filteredProducts = allProducts.filter(product => {
        const categoryMatch = !categoryFilter || product.category === categoryFilter;
        const subcategoryMatch = !subcategoryFilter || product.sub_category === subcategoryFilter;
        const siteMatch = !siteFilter || product.source_site === siteFilter;
        const priceMatch = product.unit_price >= minPrice && product.unit_price <= maxPrice;
        
        return categoryMatch && subcategoryMatch && siteMatch && priceMatch;
    });
    
    // Reset to first page when applying filters
    currentPage = 1;
    displayProducts(filteredProducts);
}

function populateFilters(products) {
    const categories = [...new Set(products.map(p => p.category).filter(Boolean))];
    const subcategories = [...new Set(products.map(p => p.sub_category).filter(Boolean))];
    const sites = [...new Set(products.map(p => p.source_site).filter(Boolean))];
    
    // Populate category filter
    const categorySelect = document.getElementById('categoryFilter');
    categorySelect.innerHTML = '<option value="">All Categories</option>';
    categories.forEach(cat => {
        categorySelect.innerHTML += `<option value="${cat}">${cat}</option>`;
    });
    
    // Populate subcategory filter
    const subcategorySelect = document.getElementById('subcategoryFilter');
    subcategorySelect.innerHTML = '<option value="">All Subcategories</option>';
    subcategories.forEach(subcat => {
        subcategorySelect.innerHTML += `<option value="${subcat}">${subcat}</option>`;
    });
    
    // Populate site filter
    const siteSelect = document.getElementById('siteFilter');
    siteSelect.innerHTML = '<option value="">All Sites</option>';
    sites.forEach(site => {
        siteSelect.innerHTML += `<option value="${site}">${site}</option>`;
    });
}

function displayProducts(products) {
    // Update total pages based on filtered products
    totalPages = Math.ceil(products.length / productsPerPage);
    
    if (products.length === 0) {
        document.getElementById('products-table').innerHTML = '<p>No products found matching the filters.</p>';
        hidePaginationControls();
        return;
    }
    
    // Calculate pagination
    const startIndex = (currentPage - 1) * productsPerPage;
    const endIndex = Math.min(startIndex + productsPerPage, products.length);
    const paginatedProducts = products.slice(startIndex, endIndex);
    
    const tableHtml = `
        <div class="table-responsive">
            <table class="table table-striped">
                <thead>
                    <tr>
                        <th>Title</th>
                        <th>Category</th>
                        <th>Subcategory</th>
                        <th>Price</th>
                        <th>Site</th>
                        <th>Rating</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${paginatedProducts.map((p, index) => {
                        const globalIndex = (currentPage - 1) * productsPerPage + index;
                        return `
                        <tr>
                            <td>${p.title.substring(0, 60)}...</td>
                            <td><span class="badge bg-secondary">${p.category || 'N/A'}</span></td>
                            <td><span class="badge bg-light text-dark">${p.sub_category || 'N/A'}</span></td>
                            <td>$${p.price > 0 ? p.price.toFixed(2) : '0.00'}</td>
                            <td><span class="badge bg-primary">${p.source_site}</span></td>
                            <td>${p.rating ? p.rating.toFixed(1) : 'N/A'}</td>
                            <td>
                                <button class="btn btn-sm btn-outline-info" onclick="showProductDetails(${globalIndex})" title="View Details">
                                    <i class="fas fa-eye"></i>
                                </button>
                            </td>
                        </tr>
                    `}).join('')}
                </tbody>
            </table>
        </div>
    `;
    
    document.getElementById('products-table').innerHTML = tableHtml;
    
    // Update pagination controls
    updatePaginationControls(products.length, startIndex + 1, endIndex);
    showPaginationControls();
}

function exportFilteredProducts() {
    if (filteredProducts.length === 0) {
        alert('No filtered products to export. Please apply filters first.');
        return;
    }
    
    const csvContent = "data:text/csv;charset=utf-8," 
        + "Title,Category,Subcategory,Price,Site,Rating\n"
        + filteredProducts.map(p => 
            `"${p.title}","${p.category || ''}","${p.sub_category || ''}",${p.price},"${p.source_site}",${p.rating || ''}`
        ).join("\n");
    
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "filtered_products.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Enhanced loadProducts function with filtering
async function loadProducts() {
    try {
        const response = await fetch('/products');
        const products = await response.json();
        
        allProducts = products;
        filteredProducts = products;
        
        if (products.length === 0) {
            document.getElementById('products-table').innerHTML = '<p>No products available yet.</p>';
            return;
        }
        
        populateFilters(products);
        displayProducts(products);
        
    } catch (error) {
        console.error('Error loading products:', error);
    }
}

// WebSocket event handlers
socket.on('connect', function() {
    console.log('Connected to server');
    updateStatus('ready', 'Connected');
});

socket.on('disconnect', function() {
    console.log('Disconnected from server');
    updateStatus('error', 'Disconnected');
});

socket.on('new_product', function(data) {
    console.log('New product received:', data);
    addProductToLiveFeed(data);
    updateLiveTotal();
});

socket.on('stats_update', function(data) {
    console.log('Stats update:', data);
    updateLiveTotal(data.total_products);
    updateCurrentSite(data.current_site);
});

socket.on('status_update', function(data) {
    console.log('Status update:', data);
    if (data.current_status) {
        updateStatus('scraping', data.current_status);
    }
    if (data.current_site) {
        updateCurrentSite(data.current_site);
    }
});

socket.on('scraping_update', function(data) {
    console.log('Scraping update:', data);
    updateCurrentSite(data.site);
    updateSiteProgress(data.site, data.count);
});

socket.on('scraping_complete', function(data) {
    console.log('Scraping complete:', data);
    showCompletionSummary(data);
    updateStatus('ready', 'Complete');
    
    // Show start button and hide stop button when scraping completes
    const startBtn = document.getElementById('start-btn');
    const stopBtn = document.getElementById('stop-btn');
    if (startBtn) startBtn.style.display = 'block';
    if (stopBtn) stopBtn.style.display = 'none';
    
    loadProducts();
    // Reload product count after scraping
    loadProductCount();
});

// Database insertion functions
async function loadProductCount() {
    try {
        const response = await fetch('/api/db/product-count');
        const data = await response.json();
        
        if (data.success) {
            const countElement = document.getElementById('productCount');
            if (countElement) {
                countElement.textContent = data.count;
            }
        }
    } catch (error) {
        console.error('Error loading product count:', error);
    }
}

async function insertAllProducts() {
    const button = document.getElementById('insertAllBtn');
    const statusDiv = document.getElementById('insertStatus');
    
    // Disable button and show loading
    button.disabled = true;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Inserting...';
    statusDiv.style.display = 'block';
    statusDiv.innerHTML = '<div class="alert alert-info"><i class="fas fa-spinner fa-spin"></i> Inserting all products to database...</div>';
    
    try {
        // Get connection parameters from UI form
        const connectionParams = {
            host: document.getElementById('dbHost').value,
            user: document.getElementById('dbUsername').value,
            password: document.getElementById('dbPassword').value,
            database: document.getElementById('dbName').value,
            port: parseInt(document.getElementById('dbPort').value)
        };
        
        const response = await fetch('/api/db/insert-all', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(connectionParams)
        });
        
        const data = await response.json();
        
        if (data.success) {
            let message = `<div class="alert alert-success"><i class="fas fa-check-circle"></i> ${data.message}</div>`;
            if (data.inserted > 0 || data.updated > 0) {
                message += `<div class="mt-2">
                    <small class="text-muted">
                        <i class="fas fa-plus-circle text-success"></i> ${data.inserted} inserted | 
                        <i class="fas fa-edit text-warning"></i> ${data.updated} updated
                    </small>
                </div>`;
            }
            statusDiv.innerHTML = message;
        } else {
            statusDiv.innerHTML = `<div class="alert alert-danger"><i class="fas fa-exclamation-triangle"></i> ${data.message}</div>`;
        }
        
    } catch (error) {
        statusDiv.innerHTML = `<div class="alert alert-danger"><i class="fas fa-exclamation-triangle"></i> Error: ${error.message}</div>`;
    } finally {
        // Re-enable button
        button.disabled = false;
        button.innerHTML = '<i class="fas fa-upload"></i> Insert All Products (<span id="productCount">0</span>)';
        // Reload product count
        loadProductCount();
    }
}

async function insertTestProduct() {
    const button = document.getElementById('insertTestBtn');
    const statusDiv = document.getElementById('insertStatus');
    
    // Disable button and show loading
    button.disabled = true;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Testing...';
    statusDiv.style.display = 'block';
    statusDiv.innerHTML = '<div class="alert alert-info"><i class="fas fa-spinner fa-spin"></i> Testing insertion with 1 product...</div>';
    
    try {
        // Get connection parameters from UI form
        const connectionParams = {
            host: document.getElementById('dbHost').value,
            user: document.getElementById('dbUsername').value,
            password: document.getElementById('dbPassword').value,
            database: document.getElementById('dbName').value,
            port: parseInt(document.getElementById('dbPort').value)
        };
        
        const response = await fetch('/api/db/insert-test', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(connectionParams)
        });
        
        const data = await response.json();
        
        if (data.success) {
            let message = `<div class="alert alert-success"><i class="fas fa-check-circle"></i> ${data.message}</div>`;
            if (data.inserted > 0 || data.updated > 0) {
                message += `<div class="mt-2">
                    <small class="text-muted">
                        <i class="fas fa-plus-circle text-success"></i> ${data.inserted} inserted | 
                        <i class="fas fa-edit text-warning"></i> ${data.updated} updated
                    </small>
                </div>`;
            }
            statusDiv.innerHTML = message;
        } else {
            statusDiv.innerHTML = `<div class="alert alert-danger"><i class="fas fa-exclamation-triangle"></i> ${data.message}</div>`;
        }
        
    } catch (error) {
        statusDiv.innerHTML = `<div class="alert alert-danger"><i class="fas fa-exclamation-triangle"></i> Error: ${error.message}</div>`;
    } finally {
        // Re-enable button
        button.disabled = false;
        button.innerHTML = '<i class="fas fa-flask"></i> Test Insert (1 Product)';
    }
}

// Auto-fill database credentials from file
async function autoFillDatabaseCredentials() {
    try {
        // Auto-fill the database connection form with credentials from file
        const dbType = document.getElementById('dbType');
        const dbHost = document.getElementById('dbHost');
        const dbPort = document.getElementById('dbPort');
        const dbName = document.getElementById('dbName');
        const dbUsername = document.getElementById('dbUsername');
        const dbPassword = document.getElementById('dbPassword');
        
        if (dbType && dbHost && dbPort && dbName && dbUsername && dbPassword) {
            // Set MySQL as default
            dbType.value = 'mysql';
            
            // Auto-fill with credentials from file
            dbHost.value = '153.92.208.43';
            dbPort.value = '3306';
            dbName.value = 'scrapping';
            dbUsername.value = 'scrapping';
            dbPassword.value = 'el6xBRHruZ5BWqGhgvGA';
            
            console.log('Database credentials auto-filled from file');
        }
    } catch (error) {
        console.error('Error auto-filling database credentials:', error);
    }
}

// Helper function to show alerts
function showAlert(message, type = 'info') {
    const alertTypes = {
        'success': 'alert-success',
        'error': 'alert-danger',
        'danger': 'alert-danger',
        'warning': 'alert-warning',
        'info': 'alert-info'
    };
    
    const alertClass = alertTypes[type] || 'alert-info';
    const alertHtml = `<div class="alert ${alertClass}">${message}</div>`;
    
    // Try to find a results div to show the alert
    const resultsDiv = document.getElementById('results');
    if (resultsDiv) {
        resultsDiv.innerHTML = alertHtml;
    } else {
        // Fallback to browser alert
        alert(message);
    }
}

// Helper function to update product count
function updateProductCount(count) {
    const countElements = document.querySelectorAll('#productCount');
    countElements.forEach(element => {
        element.textContent = count;
    });
}

// ==================== PAGINATION FUNCTIONS ====================

function updatePaginationControls(totalItems, startItem, endItem) {
    // Update pagination info
    document.getElementById('start-item').textContent = startItem;
    document.getElementById('end-item').textContent = endItem;
    document.getElementById('total-items').textContent = totalItems;
    
    // Update page jump input max value
    document.getElementById('page-jump').max = totalPages;
    
    // Generate pagination buttons
    generatePaginationButtons();
}

function generatePaginationButtons() {
    const paginationNav = document.getElementById('pagination-nav');
    if (!paginationNav) return;
    
    let buttonsHtml = '';
    
    // Previous button
    const prevDisabled = currentPage <= 1 ? 'disabled' : '';
    buttonsHtml += `
        <li class="page-item ${prevDisabled}">
            <a class="page-link" href="javascript:void(0)" onclick="goToPreviousPage()">
                <i class="fas fa-chevron-left"></i> Previous
            </a>
        </li>
    `;
    
    // Page numbers
    const maxVisiblePages = 5;
    let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
    let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);
    
    // Adjust start page if we're near the end
    if (endPage - startPage < maxVisiblePages - 1) {
        startPage = Math.max(1, endPage - maxVisiblePages + 1);
    }
    
    // First page button
    if (startPage > 1) {
        buttonsHtml += `
            <li class="page-item">
                <a class="page-link" href="javascript:void(0)" onclick="goToPage(1)">1</a>
            </li>
        `;
        if (startPage > 2) {
            buttonsHtml += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
    }
    
    // Page number buttons
    for (let i = startPage; i <= endPage; i++) {
        const activeClass = i === currentPage ? 'active' : '';
        buttonsHtml += `
            <li class="page-item ${activeClass}">
                <a class="page-link" href="javascript:void(0)" onclick="goToPage(${i})">${i}</a>
            </li>
        `;
    }
    
    // Last page button
    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            buttonsHtml += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
        buttonsHtml += `
            <li class="page-item">
                <a class="page-link" href="javascript:void(0)" onclick="goToPage(${totalPages})">${totalPages}</a>
            </li>
        `;
    }
    
    // Next button
    const nextDisabled = currentPage >= totalPages ? 'disabled' : '';
    buttonsHtml += `
        <li class="page-item ${nextDisabled}">
            <a class="page-link" href="javascript:void(0)" onclick="goToNextPage()">
                Next <i class="fas fa-chevron-right"></i>
            </a>
        </li>
    `;
    
    paginationNav.innerHTML = buttonsHtml;
}

function goToPage(page) {
    if (page < 1 || page > totalPages) return;
    currentPage = page;
    displayProducts(filteredProducts);
}

function goToNextPage() {
    if (currentPage < totalPages) {
        currentPage++;
        displayProducts(filteredProducts);
    }
}

function goToPreviousPage() {
    if (currentPage > 1) {
        currentPage--;
        displayProducts(filteredProducts);
    }
}

function jumpToPage() {
    const pageInput = document.getElementById('page-jump');
    const page = parseInt(pageInput.value);
    
    if (page && page >= 1 && page <= totalPages) {
        goToPage(page);
        pageInput.value = ''; // Clear input after jump
    } else {
        alert(`Please enter a valid page number between 1 and ${totalPages}`);
    }
}

function changeProductsPerPage() {
    const newProductsPerPage = parseInt(document.getElementById('productsPerPageSelect').value);
    if (newProductsPerPage !== productsPerPage) {
        productsPerPage = newProductsPerPage;
        currentPage = 1; // Reset to first page when changing page size
        displayProducts(filteredProducts);
    }
}

function showPaginationControls() {
    const controls = document.getElementById('pagination-controls');
    if (controls && totalPages > 1) {
        controls.style.display = 'flex';
    }
}

function hidePaginationControls() {
    const controls = document.getElementById('pagination-controls');
    if (controls) {
        controls.style.display = 'none';
    }
}

// ==================== PRODUCT DETAIL FUNCTIONS ====================

let currentProductDetail = null;

function ensureModalExists() {
    // Check if modal exists, if not, create it dynamically
    let modal = document.getElementById('productDetailModal');
    if (!modal) {
        console.log('Creating product detail modal dynamically...');
        const modalHTML = `
            <div class="modal fade" id="productDetailModal" tabindex="-1" aria-labelledby="productDetailModalLabel" aria-hidden="true">
                <div class="modal-dialog modal-lg modal-dialog-scrollable">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="productDetailModalLabel">Product Details</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <div class="row mb-3">
                                <div class="col-md-4">
                                    <img id="productDetailImage" src="" alt="Product Image" class="img-fluid rounded" style="max-width: 100%; height: auto;">
                                </div>
                                <div class="col-md-8">
                                    <h6 id="productDetailTitle" class="fw-bold mb-2"></h6>
                                    <p class="mb-1"><strong>Price:</strong> <span id="productDetailPrice"></span></p>
                                    <p class="mb-1"><strong>Site:</strong> <span id="productDetailSite"></span></p>
                                    <p class="mb-1"><strong>Rating:</strong> <span id="productDetailRating"></span></p>
                                    <p class="mb-1"><strong>Category:</strong> <span id="productDetailCategory"></span></p>
                                    <p class="mb-1"><strong>Stock:</strong> <span id="productDetailStock"></span></p>
                                </div>
                            </div>
                            
                            <div id="productVariantsSection" style="display: none;">
                                <h6 class="fw-bold mb-2">Product Variants</h6>
                                <div id="productVariants" class="mb-3"></div>
                            </div>
                            
                            <div id="productImagesSection" style="display: none;">
                                <h6 class="fw-bold mb-2">Additional Images</h6>
                                <div id="productImages" class="row mb-3"></div>
                            </div>
                            
                            <div class="mt-3">
                                <h6 class="fw-bold mb-2">Raw JSON Data</h6>
                                <div class="bg-light p-3 rounded">
                                    <pre id="productDetailJSON" class="mb-0" style="font-size: 12px; max-height: 400px; overflow-y: auto;"></pre>
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" onclick="copyProductJSON()">
                                <i class="fas fa-copy"></i> Copy JSON
                            </button>
                            <button type="button" class="btn btn-primary" onclick="downloadProductJSON()">
                                <i class="fas fa-download"></i> Download JSON
                            </button>
                            <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">Close</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Add modal to body
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        modal = document.getElementById('productDetailModal');
    }
    return modal;
}

function showProductDetails(productIndex) {
    console.log('showProductDetails called with index:', productIndex);
    
    // Ensure DOM is ready
    if (document.readyState !== 'complete') {
        console.log('DOM not ready, waiting...');
        setTimeout(() => showProductDetails(productIndex), 100);
        return;
    }
    
    // Ensure modal exists
    ensureModalExists();
    
    // Get the product from filteredProducts array using the global index
    const product = filteredProducts[productIndex];
    if (!product) {
        alert('Product not found!');
        console.error('Product not found at index:', productIndex);
        return;
    }
    
    console.log('Product found:', product.title);
    currentProductDetail = product;
    
    // Get modal elements (they should exist now)
    const elements = {
        title: document.getElementById('productDetailTitle'),
        price: document.getElementById('productDetailPrice'),
        site: document.getElementById('productDetailSite'),
        rating: document.getElementById('productDetailRating'),
        category: document.getElementById('productDetailCategory'),
        stock: document.getElementById('productDetailStock')
    };
    
    // Double-check for missing elements
    for (const [key, element] of Object.entries(elements)) {
        if (!element) {
            console.error(`Element still not found after ensuring modal exists: productDetail${key.charAt(0).toUpperCase() + key.slice(1)}`);
            alert('Modal elements could not be created. Please refresh the page and try again.');
            return;
        }
    }
    
    // Populate modal with product data
    elements.title.textContent = product.title || 'N/A';
    elements.price.textContent = product.price > 0 ? `$${product.price.toFixed(2)}` : 'N/A';
    elements.site.textContent = product.source_site || 'N/A';
    elements.rating.textContent = product.rating ? `${product.rating}/5` : 'N/A';
    elements.category.textContent = `${product.category || 'N/A'} > ${product.sub_category || 'N/A'}`;
    elements.stock.textContent = product.current_stock || 'N/A';
    
    // Set main product image
    const imageElement = document.getElementById('productDetailImage');
    if (imageElement) {
        const mainImage = product.main_image_url || (product.additional_images && product.additional_images[0]) || '/static/images/placeholder.jpg';
        imageElement.src = mainImage;
        imageElement.onerror = function() {
            this.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZGRkIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtc2l6ZT0iMTQiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIiBmaWxsPSIjOTk5Ij5ObyBJbWFnZTwvdGV4dD48L3N2Zz4=';
        };
    }
    
    // Show/hide variants section
    const variantsSection = document.getElementById('productVariantsSection');
    if (variantsSection) {
        if (product.variants && product.variants.length > 0) {
            populateVariants(product.variants);
            variantsSection.style.display = 'block';
        } else {
            variantsSection.style.display = 'none';
        }
    }
    
    // Show/hide additional images section
    const imagesSection = document.getElementById('productImagesSection');
    if (imagesSection) {
        if (product.additional_images && product.additional_images.length > 0) {
            populateAdditionalImages(product.additional_images);
            imagesSection.style.display = 'block';
        } else {
            imagesSection.style.display = 'none';
        }
    }
    
    // Show raw JSON data
    const jsonElement = document.getElementById('productDetailJSON');
    if (jsonElement) {
        jsonElement.textContent = JSON.stringify(product, null, 2);
    }
    
    // Show the modal
    const modalElement = document.getElementById('productDetailModal');
    if (modalElement) {
        const modal = new bootstrap.Modal(modalElement);
        modal.show();
    } else {
        console.error('Modal element not found');
        alert('Product detail modal not found. Please refresh the page and try again.');
    }
}

function populateVariants(variants) {
    const variantsContainer = document.getElementById('productVariants');
    if (!variantsContainer) {
        console.error('Variants container not found');
        return;
    }
    
    const variantsHtml = variants.map((variant, index) => {
        const variantKeys = Object.keys(variant).filter(key => 
            !['price', 'stock', 'sku', 'images', 'attributes'].includes(key)
        );
        
        const variantType = variantKeys[0] || 'variant';
        const variantValue = variant[variantType] || 'N/A';
        
        return `
            <div class="variant-card variant-item mb-2">
                <div class="card-body p-3">
                    <div class="row align-items-center">
                        <div class="col-md-3">
                            <strong class="text-primary">${variantType.charAt(0).toUpperCase() + variantType.slice(1)}:</strong><br>
                            <span class="text-dark">${variantValue}</span>
                        </div>
                        <div class="col-md-2">
                            <small><strong>Price:</strong><br>$${variant.price ? variant.price.toFixed(2) : '0.00'}</small>
                        </div>
                        <div class="col-md-2">
                            <small><strong>Stock:</strong><br>${variant.stock || 'N/A'}</small>
                        </div>
                        <div class="col-md-2">
                            <small><strong>SKU:</strong><br><code style="font-size: 10px;">${variant.sku || 'N/A'}</code></small>
                        </div>
                        <div class="col-md-3 text-center">
                            ${variant.images && variant.images.length > 0 ? 
                                `<img src="${variant.images[0]}" alt="Variant Image" class="img-thumbnail" 
                                     style="width: 50px; height: 50px; object-fit: cover; cursor: pointer;" 
                                     onclick="showImageModal('${variant.images[0]}')">` : 
                                '<div class="text-muted" style="font-size: 12px;"><i class="fas fa-image"></i><br>No image</div>'
                            }
                        </div>
                    </div>
                </div>
            </div>
        `;
    }).join('');
    
    variantsContainer.innerHTML = variantsHtml;
}

function populateAdditionalImages(images) {
    const imagesContainer = document.getElementById('productImages');
    if (!imagesContainer) {
        console.error('Images container not found');
        return;
    }
    
    const imagesHtml = images.map((imageUrl, index) => `
        <div class="col-md-3 col-sm-4 col-6 mb-2">
            <img src="${imageUrl}" alt="Product Image ${index + 1}" class="img-thumbnail w-100" 
                 style="height: 120px; object-fit: cover; cursor: pointer;" 
                 onclick="showImageModal('${imageUrl}')">
        </div>
    `).join('');
    
    imagesContainer.innerHTML = imagesHtml;
}

function showImageModal(imageUrl) {
    // Create a simple image modal
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.innerHTML = `
        <div class="modal-dialog modal-lg modal-dialog-centered">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Product Image</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body text-center">
                    <img src="${imageUrl}" alt="Product Image" class="img-fluid">
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    const imageModal = new bootstrap.Modal(modal);
    imageModal.show();
    
    // Remove modal from DOM when hidden
    modal.addEventListener('hidden.bs.modal', function() {
        document.body.removeChild(modal);
    });
}

function copyProductJSON() {
    if (!currentProductDetail) return;
    
    const jsonText = JSON.stringify(currentProductDetail, null, 2);
    
    // Create a temporary textarea to copy the text
    const textarea = document.createElement('textarea');
    textarea.value = jsonText;
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);
    
    // Show success message
    showAlert('Product JSON copied to clipboard!', 'success');
}

function downloadProductJSON() {
    if (!currentProductDetail) return;
    
    const jsonText = JSON.stringify(currentProductDetail, null, 2);
    const blob = new Blob([jsonText], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = `product_${currentProductDetail.title ? currentProductDetail.title.replace(/[^a-zA-Z0-9]/g, '_') : 'unknown'}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    URL.revokeObjectURL(url);
    
    // Show success message
    showAlert('Product JSON downloaded successfully!', 'success');
}
