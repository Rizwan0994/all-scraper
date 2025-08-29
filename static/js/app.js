// Universal Product Scraper - Main JavaScript
// Handles all frontend functionality

// Initialize WebSocket connection
const socket = io();

// Global variables for filtering
let allProducts = [];
let filteredProducts = [];

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Universal Product Scraper initialized');
    
    // Initialize form submission
    initializeFormSubmission();
    
    // Initialize button handlers
    initializeButtonHandlers();
    
    // Load initial products
    setTimeout(loadProducts, 1000);
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
                    startStatusPolling();
                } else {
                    throw new Error(data.error || 'Unknown error');
                }
                
            } catch (error) {
                console.error('Scraping error:', error);
                progressDiv.style.display = 'none';
                resultsDiv.innerHTML = `<div class="alert alert-danger">Error: ${error.message}</div>`;
                
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
    if (products.length === 0) {
        document.getElementById('products-table').innerHTML = '<p>No products found matching the filters.</p>';
        return;
    }
    
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
                    </tr>
                </thead>
                <tbody>
                    ${products.map(p => `
                        <tr>
                            <td>${p.title.substring(0, 60)}...</td>
                            <td><span class="badge bg-secondary">${p.category || 'N/A'}</span></td>
                            <td><span class="badge bg-light text-dark">${p.sub_category || 'N/A'}</span></td>
                            <td>$${p.price > 0 ? p.price.toFixed(2) : '0.00'}</td>
                            <td><span class="badge bg-primary">${p.source_site}</span></td>
                            <td>${p.rating ? p.rating.toFixed(1) : 'N/A'}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
            <p class="text-muted">Showing ${products.length} of ${allProducts.length} products</p>
        </div>
    `;
    
    document.getElementById('products-table').innerHTML = tableHtml;
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
    loadProducts();
});
