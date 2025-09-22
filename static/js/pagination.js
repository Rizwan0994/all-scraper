// ===== CHUNK-BASED PRODUCT PAGINATION =====
// Efficient product loading using chunk-based backend

class ProductPagination {
    constructor() {
        this.currentPage = 1;
        this.perPage = 50;
        this.totalProducts = 0;
        this.totalPages = 0;
        this.hasMore = false;
        this.isLoading = false;
        this.currentSearch = null;
    }
    
    async loadPage(page = 1, perPage = 50) {
        if (this.isLoading) {
            console.log('Already loading, skipping request');
            return;
        }
        
        this.isLoading = true;
        this.showLoadingIndicator();
        
        try {
            console.log(`🔄 Loading page ${page} with ${perPage} products per page`);
            
            const response = await fetch(`/api/products/page/${page}?per_page=${perPage}`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            // Update pagination state
            this.currentPage = data.page;
            this.perPage = data.per_page;
            this.totalProducts = data.total_products;
            this.totalPages = data.total_pages;
            this.hasMore = data.has_more;
            
            // Display products
            this.displayProducts(data.products);
            this.updatePaginationControls();
            
            console.log(`✅ Loaded page ${page}: ${data.products.length} products`);
            console.log(`📊 Total: ${this.totalProducts.toLocaleString()} products, ${this.totalPages} pages`);
            
        } catch (error) {
            console.error('❌ Error loading products:', error);
            this.showErrorMessage(`Failed to load products: ${error.message}`);
        } finally {
            this.isLoading = false;
            this.hideLoadingIndicator();
        }
    }
    
    async searchProducts(query, category = '', site = '', page = 1) {
        if (this.isLoading) return;
        
        this.isLoading = true;
        this.showLoadingIndicator();
        
        try {
            const params = new URLSearchParams({
                page: page,
                per_page: this.perPage
            });
            
            if (query) params.append('q', query);
            if (category) params.append('category', category);
            if (site) params.append('site', site);
            
            const response = await fetch(`/api/products/search?${params}`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            // Update search state
            this.currentSearch = { query, category, site };
            this.currentPage = data.page;
            this.totalProducts = data.total_results;
            this.totalPages = data.total_pages;
            this.hasMore = data.has_more;
            
            // Display results
            this.displayProducts(data.products);
            this.updatePaginationControls();
            this.showSearchInfo(data);
            
            console.log(`🔍 Search results: ${data.products.length} products found`);
            
        } catch (error) {
            console.error('❌ Error searching products:', error);
            this.showErrorMessage(`Search failed: ${error.message}`);
        } finally {
            this.isLoading = false;
            this.hideLoadingIndicator();
        }
    }
    
    displayProducts(products) {
        const container = this.getProductContainer();
        
        if (!products || products.length === 0) {
            container.innerHTML = `
                <div class="col-12">
                    <div class="text-center text-muted p-5">
                        <i class="fas fa-search fa-3x mb-3"></i>
                        <h4>No products found</h4>
                        <p>Try adjusting your search criteria or load a different page.</p>
                    </div>
                </div>
            `;
            return;
        }
        
        const productHTML = products.map(product => this.createProductCard(product)).join('');
        container.innerHTML = productHTML;
        
        // Scroll to top of products
        container.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
    
    createProductCard(product) {
        const imageUrl = product.image || '/static/images/no-image.png';
        const price = product.price ? `$${parseFloat(product.price).toFixed(2)}` : 'N/A';
        const rating = product.rating ? '★'.repeat(Math.floor(product.rating)) + '☆'.repeat(5 - Math.floor(product.rating)) : 'No rating';
        
        return `
            <div class="col-md-6 col-lg-4 col-xl-3 mb-4">
                <div class="card product-card h-100 shadow-sm">
                    <div class="position-relative">
                        <img src="${imageUrl}" class="card-img-top product-image" alt="${product.title}" 
                             style="height: 200px; object-fit: cover;" 
                             onerror="this.src='/static/images/no-image.png'">
                        ${product.stock > 0 ? '<span class="badge badge-success position-absolute" style="top: 10px; right: 10px;">In Stock</span>' : '<span class="badge badge-warning position-absolute" style="top: 10px; right: 10px;">Limited</span>'}
                    </div>
                    <div class="card-body d-flex flex-column">
                        <h6 class="card-title" style="height: 3rem; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;" title="${product.title}">
                            ${product.title}
                        </h6>
                        <div class="product-details flex-grow-1">
                            <div class="d-flex justify-content-between align-items-center mb-2">
                                <span class="text-success font-weight-bold h5 mb-0">${price}</span>
                                <small class="text-warning">${rating}</small>
                            </div>
                            <p class="text-muted small mb-1">
                                <i class="fas fa-tag text-primary"></i> ${product.category || 'N/A'}
                            </p>
                            <p class="text-muted small mb-1">
                                <i class="fas fa-store text-info"></i> ${product.source_site || 'N/A'}
                            </p>
                            ${product.stock ? `<p class="text-info small mb-1"><i class="fas fa-box"></i> Stock: ${product.stock}</p>` : ''}
                            ${product.sku ? `<p class="text-secondary small mb-0"><i class="fas fa-barcode"></i> ${product.sku}</p>` : ''}
                        </div>
                        <div class="mt-auto pt-2">
                            <button class="btn btn-outline-primary btn-sm btn-block" onclick="showProductDetails('${product.sku || product.title}')">
                                <i class="fas fa-eye"></i> View Details
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    updatePaginationControls() {
        const paginationContainer = document.getElementById('pagination-controls');
        if (!paginationContainer) {
            this.createPaginationContainer();
            return this.updatePaginationControls();
        }
        
        const prevButton = this.currentPage > 1 ? 
            `<button class="btn btn-outline-primary" onclick="productPagination.navigateToPage(${this.currentPage - 1})" ${this.isLoading ? 'disabled' : ''}>
                <i class="fas fa-chevron-left"></i> Previous
            </button>` : 
            `<button class="btn btn-outline-secondary" disabled>
                <i class="fas fa-chevron-left"></i> Previous
            </button>`;
        
        const nextButton = this.hasMore ? 
            `<button class="btn btn-outline-primary" onclick="productPagination.navigateToPage(${this.currentPage + 1})" ${this.isLoading ? 'disabled' : ''}>
                Next <i class="fas fa-chevron-right"></i>
            </button>` : 
            `<button class="btn btn-outline-secondary" disabled>
                Next <i class="fas fa-chevron-right"></i>
            </button>`;
        
        // Create page number buttons
        const pageButtons = this.createPageButtons();
        
        paginationContainer.innerHTML = `
            <div class="row align-items-center">
                <div class="col-md-4 mb-2 mb-md-0">
                    <span class="text-muted">
                        <i class="fas fa-info-circle"></i>
                        Page ${this.currentPage} of ${this.totalPages.toLocaleString()} 
                        <br><small>(${this.totalProducts.toLocaleString()} total products)</small>
                    </span>
                </div>
                <div class="col-md-4 mb-2 mb-md-0 text-center">
                    <div class="btn-group" role="group">
                        ${prevButton}
                        ${pageButtons}
                        ${nextButton}
                    </div>
                </div>
                <div class="col-md-4 text-md-right">
                    <div class="d-flex align-items-center justify-content-md-end">
                        <label for="page-size-select" class="mb-0 mr-2 text-muted">Show:</label>
                        <select class="form-control form-control-sm" id="page-size-select" style="width: auto;" onchange="productPagination.changePageSize(this.value)" ${this.isLoading ? 'disabled' : ''}>
                            <option value="25" ${this.perPage === 25 ? 'selected' : ''}>25</option>
                            <option value="50" ${this.perPage === 50 ? 'selected' : ''}>50</option>
                            <option value="100" ${this.perPage === 100 ? 'selected' : ''}>100</option>
                            <option value="200" ${this.perPage === 200 ? 'selected' : ''}>200</option>
                        </select>
                    </div>
                </div>
            </div>
        `;
    }
    
    createPageButtons() {
        if (this.totalPages <= 1) return '';
        
        const currentPage = this.currentPage;
        const totalPages = this.totalPages;
        const maxButtons = 3; // Reduced for mobile friendliness
        
        let startPage = Math.max(1, currentPage - Math.floor(maxButtons / 2));
        let endPage = Math.min(totalPages, startPage + maxButtons - 1);
        
        if (endPage - startPage + 1 < maxButtons) {
            startPage = Math.max(1, endPage - maxButtons + 1);
        }
        
        let buttons = '';
        
        // Page range
        for (let i = startPage; i <= endPage; i++) {
            const isActive = i === currentPage;
            buttons += `<button class="btn ${isActive ? 'btn-primary' : 'btn-outline-primary'}" 
                        onclick="productPagination.navigateToPage(${i})" ${this.isLoading ? 'disabled' : ''}>${i}</button>`;
        }
        
        return buttons;
    }
    
    navigateToPage(page) {
        if (page < 1 || page > this.totalPages || this.isLoading) return;
        
        if (this.currentSearch) {
            this.searchProducts(
                this.currentSearch.query,
                this.currentSearch.category,
                this.currentSearch.site,
                page
            );
        } else {
            this.loadPage(page, this.perPage);
        }
    }
    
    changePageSize(newPerPage) {
        if (this.isLoading) return;
        this.perPage = parseInt(newPerPage);
        this.navigateToPage(1); // Go to first page with new page size
    }
    
    getProductContainer() {
        let container = document.getElementById('products-container');
        if (!container) {
            // Create products container if it doesn't exist
            container = document.createElement('div');
            container.id = 'products-container';
            container.className = 'row';
            
            // Find a good place to insert it
            const mainContent = document.querySelector('.main-content') || 
                              document.querySelector('.container-fluid') || 
                              document.body;
            
            // Create a wrapper div for better layout
            const wrapper = document.createElement('div');
            wrapper.className = 'products-section my-4';
            wrapper.innerHTML = `
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <h4 class="mb-0"><i class="fas fa-boxes"></i> Products</h4>
                    <div class="search-controls">
                        <div class="input-group">
                            <input type="text" class="form-control" id="product-search" placeholder="Search products...">
                            <div class="input-group-append">
                                <button class="btn btn-primary" onclick="performSearch()">
                                    <i class="fas fa-search"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
                <div id="search-info"></div>
            `;
            wrapper.appendChild(container);
            mainContent.appendChild(wrapper);
        }
        return container;
    }
    
    createPaginationContainer() {
        let container = document.getElementById('pagination-controls');
        if (!container) {
            container = document.createElement('div');
            container.id = 'pagination-controls';
            container.className = 'pagination-container my-4 p-3 bg-light rounded';
            
            // Insert after products container
            const productsContainer = this.getProductContainer();
            productsContainer.parentNode.insertBefore(container, productsContainer.nextSibling);
        }
        return container;
    }
    
    showLoadingIndicator() {
        const container = this.getProductContainer();
        container.innerHTML = `
            <div class="col-12">
                <div class="text-center p-5">
                    <div class="spinner-border text-primary mb-3" role="status">
                        <span class="sr-only">Loading...</span>
                    </div>
                    <h5>Loading products...</h5>
                    <p class="text-muted">This should only take a moment with our optimized chunking system!</p>
                </div>
            </div>
        `;
    }
    
    hideLoadingIndicator() {
        // Loading indicator is automatically replaced by product content
    }
    
    showErrorMessage(message) {
        const container = this.getProductContainer();
        container.innerHTML = `
            <div class="col-12">
                <div class="alert alert-danger" role="alert">
                    <h5><i class="fas fa-exclamation-triangle"></i> Error Loading Products</h5>
                    <p><strong>Error:</strong> ${message}</p>
                    <div class="mt-3">
                        <button class="btn btn-outline-danger" onclick="productPagination.loadPage(1)">
                            <i class="fas fa-redo"></i> Try Again
                        </button>
                        <button class="btn btn-outline-secondary ml-2" onclick="location.reload()">
                            <i class="fas fa-refresh"></i> Reload Page
                        </button>
                    </div>
                </div>
            </div>
        `;
    }
    
    showSearchInfo(data) {
        const infoContainer = document.getElementById('search-info');
        if (!infoContainer) return;
        
        const searchTerms = [];
        if (data.query) searchTerms.push(`"${data.query}"`);
        if (data.category) searchTerms.push(`Category: ${data.category}`);
        if (data.site) searchTerms.push(`Site: ${data.site}`);
        
        infoContainer.innerHTML = `
            <div class="alert alert-info alert-dismissible">
                <button type="button" class="close" onclick="productPagination.clearSearch()">
                    <span>&times;</span>
                </button>
                <i class="fas fa-search"></i>
                <strong>Search Results:</strong> Found ${data.total_results.toLocaleString()} products for ${searchTerms.join(', ')}
                <small class="text-muted">(searched ${data.chunks_searched} chunks)</small>
            </div>
        `;
    }
    
    clearSearch() {
        this.currentSearch = null;
        const infoContainer = document.getElementById('search-info');
        if (infoContainer) {
            infoContainer.innerHTML = '';
        }
        const searchInput = document.getElementById('product-search');
        if (searchInput) {
            searchInput.value = '';
        }
        this.loadPage(1);
    }
    
    async loadStats() {
        try {
            const response = await fetch('/api/products/stats');
            if (response.ok) {
                const stats = await response.json();
                this.displayStats(stats);
                console.log('📊 Stats loaded:', stats);
            }
        } catch (error) {
            console.error('❌ Error loading stats:', error);
        }
    }
    
    displayStats(stats) {
        // Update dashboard stats if elements exist
        const totalElement = document.getElementById('total-products') || 
                           document.querySelector('[data-stat="total-products"]');
        if (totalElement && stats.total_products) {
            totalElement.textContent = stats.total_products.toLocaleString();
        }
        
        const chunksElement = document.getElementById('total-chunks') ||
                            document.querySelector('[data-stat="total-chunks"]');
        if (chunksElement && stats.total_chunks) {
            chunksElement.textContent = stats.total_chunks;
        }
        
        // Update any other stat elements
        if (stats.global_stats) {
            const globalStats = stats.global_stats;
            
            const categoriesElement = document.querySelector('[data-stat="categories"]');
            if (categoriesElement && globalStats.total_categories) {
                categoriesElement.textContent = globalStats.total_categories;
            }
            
            const sitesElement = document.querySelector('[data-stat="sites"]');
            if (sitesElement && globalStats.total_sites) {
                sitesElement.textContent = globalStats.total_sites;
            }
        }
    }
}

// Global search function
function performSearch() {
    const searchInput = document.getElementById('product-search');
    if (searchInput && searchInput.value.trim()) {
        productPagination.searchProducts(searchInput.value.trim());
    } else {
        productPagination.clearSearch();
    }
}

// Handle enter key in search
document.addEventListener('keydown', function(event) {
    if (event.key === 'Enter') {
        const activeElement = document.activeElement;
        if (activeElement && activeElement.id === 'product-search') {
            performSearch();
        }
    }
});

// Initialize global pagination instance
const productPagination = new ProductPagination();

// Auto-load when document is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Initializing chunk-based product pagination...');
    
    // Small delay to ensure all other scripts are loaded
    setTimeout(() => {
        productPagination.loadPage(1);
        productPagination.loadStats();
    }, 1000);
});

// Placeholder function for product details (you can implement this)
function showProductDetails(identifier) {
    console.log('Show details for:', identifier);
    // You can implement a modal or navigation to product detail page
    alert(`Product details for: ${identifier}\n\nThis feature can be implemented to show detailed product information.`);
}

