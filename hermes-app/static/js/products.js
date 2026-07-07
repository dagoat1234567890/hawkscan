document.addEventListener('DOMContentLoaded', () => {
    const tableContainer = document.getElementById('products-table-container');
    const emptyState = document.getElementById('empty-state');
    const loadingState = document.getElementById('loading-state');
    
    // Product Logic Below
    
    const addModal = document.getElementById('add-modal');
    const openModalBtn = document.getElementById('open-modal-btn');
    const closeModalBtn = document.getElementById('close-modal-btn');
    const addProductForm = document.getElementById('add-product-form');
    const submitBtn = document.getElementById('modal-submit-btn');
    const btnText = submitBtn.querySelector('.btn-text');
    const loader = submitBtn.querySelector('.loader');

    // Modal logic
    openModalBtn.addEventListener('click', () => {
        addModal.classList.add('active');
    });

    closeModalBtn.addEventListener('click', () => {
        addModal.classList.remove('active');
        addProductForm.reset();
    });

    // Close modals when clicking outside
    window.addEventListener('click', (e) => {
        if (e.target === addModal) {
            addModal.classList.remove('active');
            addProductForm.reset();
        }
        if (e.target === historyModal) {
            historyModal.classList.remove('active');
        }
    });


    // Form Submit
    addProductForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        btnText.style.display = 'none';
        loader.style.display = 'block';
        submitBtn.disabled = true;

        const productData = {
            product_name: document.getElementById('modal-product-name').value,
            company_name: document.getElementById('modal-company-name').value,
            platform: document.getElementById('modal-platform').value,
            catalog_url: document.getElementById('modal-catalog-url').value
        };

        try {
            const res = await fetch('/api/track', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(productData)
            });

            if (res.ok) {
                addModal.classList.remove('active');
                addProductForm.reset();
                loadProducts();
            } else {
                const data = await res.json();
                alert(data.error || 'Failed to add product.');
            }
        } catch (error) {
            console.error(error);
            alert('Connection failed.');
        } finally {
            btnText.style.display = 'block';
            loader.style.display = 'none';
            submitBtn.disabled = false;
        }
    });

    let allProducts = [];
    let currentSortColumn = null;
    let currentSortDirection = 1;

    // Fetch and render products
    async function loadProducts() {
        loadingState.style.display = 'block';
        if (tableContainer) tableContainer.style.display = 'none';
        emptyState.style.display = 'none';

        try {
            const res = await fetch('/api/trackers');
            allProducts = await res.json();

            loadingState.style.display = 'none';
            renderTable(allProducts);
        } catch (error) {
            console.error(error);
            loadingState.innerHTML = '<p style="color: #ef4444;">Failed to load products.</p>';
        }
    }

    function renderTable(data) {
        const tbody = document.getElementById('products-tbody');
        
        if (data.length === 0) {
            emptyState.style.display = 'block';
            if (tableContainer) tableContainer.style.display = 'none';
            return;
        }

        emptyState.style.display = 'none';
        tbody.innerHTML = '';
        data.forEach(product => {
            const row = document.createElement('tr');
            row.style.cursor = 'pointer';
            row.onclick = () => window.openHistoryModal(product.id);
            
            // Format prices
            const currentPrice = product.last_price || product.baseline_price;
            const baseline = currentPrice ? `AED ${parseFloat(currentPrice).toLocaleString()}` : '--';
            const marketAvg = product.last_market_avg ? `AED ${parseFloat(product.last_market_avg).toLocaleString()}` : '--';
            const marketHigh = product.last_market_high ? `AED ${parseFloat(product.last_market_high).toLocaleString()}` : '--';
            const marketLow = product.last_market_low ? `AED ${parseFloat(product.last_market_low).toLocaleString()}` : '--';

            row.innerHTML = `
                <td style="font-weight: 500; color: var(--text-primary);">
                    ${product.product_name}
                    <div style="font-size: 0.75rem; color: var(--text-secondary); margin-top: 0.25rem;">${product.company_name} • <span style="text-transform: uppercase; color: var(--accent-primary);">${product.platform}</span></div>
                </td>
                <td style="color: var(--accent-secondary); font-weight: 600;">${baseline}</td>
                <td>${marketAvg}</td>
                <td style="color: #ef4444;">${marketHigh}</td>
                <td style="color: #10b981;">${marketLow}</td>
                <td style="display: flex; gap: 1.5rem; align-items: center;">
                    <div class="toggle-container" style="display: flex; align-items: center; gap: 0.5rem;" onclick="event.stopPropagation();">
                        <label class="toggle-switch">
                            <input type="checkbox" onchange="window.toggleAnalysis(${product.id}, this)" ${product.is_active ? 'checked' : ''}>
                            <span class="toggle-slider"></span>
                        </label>
                        <div class="toggle-label ${product.is_active ? 'active' : ''}">
                            <span class="toggle-text" style="font-size: 0.8rem; color: var(--text-secondary); font-weight: 500;">${product.is_active ? 'Monitoring 24/7' : 'Analyze 24/7'}</span>
                        </div>
                    </div>
                    <button onclick="event.stopPropagation(); window.deleteProduct(${product.id})" style="background: none; border: none; color: #ef4444; cursor: pointer; padding: 0.5rem; display: flex; align-items: center;" title="Delete Product">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });
        if (tableContainer) tableContainer.style.display = 'block';
    }

    window.sortProducts = (column) => {
        if (currentSortColumn === column) {
            currentSortDirection *= -1; // toggle
        } else {
            currentSortColumn = column;
            currentSortDirection = 1;
        }

        allProducts.sort((a, b) => {
            let valA, valB;
            if (column === 'name') {
                valA = a.product_name.toLowerCase();
                valB = b.product_name.toLowerCase();
            } else if (column === 'price') {
                valA = a.last_price || a.baseline_price || 0;
                valB = b.last_price || b.baseline_price || 0;
            } else if (column === 'market_avg') {
                valA = a.last_market_avg || 0;
                valB = b.last_market_avg || 0;
            } else if (column === 'market_high') {
                valA = a.last_market_high || 0;
                valB = b.last_market_high || 0;
            } else if (column === 'market_low') {
                valA = a.last_market_low || 0;
                valB = b.last_market_low || 0;
            }
            if (valA < valB) return -1 * currentSortDirection;
            if (valA > valB) return 1 * currentSortDirection;
            return 0;
        });

        // Update headers to show arrow indicator
        const nameIndicator = document.getElementById('sort-name-indicator');
        const priceIndicator = document.getElementById('sort-price-indicator');
        const avgIndicator = document.getElementById('sort-market-avg-indicator');
        const highIndicator = document.getElementById('sort-market-high-indicator');
        const lowIndicator = document.getElementById('sort-market-low-indicator');

        if (nameIndicator) nameIndicator.textContent = column === 'name' ? (currentSortDirection === 1 ? '▲' : '▼') : '↕';
        if (priceIndicator) priceIndicator.textContent = column === 'price' ? (currentSortDirection === 1 ? '▲' : '▼') : '↕';
        if (avgIndicator) avgIndicator.textContent = column === 'market_avg' ? (currentSortDirection === 1 ? '▲' : '▼') : '↕';
        if (highIndicator) highIndicator.textContent = column === 'market_high' ? (currentSortDirection === 1 ? '▲' : '▼') : '↕';
        if (lowIndicator) lowIndicator.textContent = column === 'market_low' ? (currentSortDirection === 1 ? '▲' : '▼') : '↕';

        applyFilters();
    };

    function checkNumericFilter(value, filterStr) {
        if (!filterStr) return true;
        
        filterStr = filterStr.trim();
        let operator = '=';
        let numStr = filterStr;

        if (filterStr.startsWith('>=')) { operator = '>='; numStr = filterStr.substring(2); }
        else if (filterStr.startsWith('<=')) { operator = '<='; numStr = filterStr.substring(2); }
        else if (filterStr.startsWith('>')) { operator = '>'; numStr = filterStr.substring(1); }
        else if (filterStr.startsWith('<')) { operator = '<'; numStr = filterStr.substring(1); }
        
        numStr = numStr.trim();
        if (!numStr) return true;

        const targetNum = parseFloat(numStr);
        if (isNaN(targetNum)) return true; // fallback if user typed invalid number
        
        value = parseFloat(value) || 0;

        switch (operator) {
            case '>': return value > targetNum;
            case '<': return value < targetNum;
            case '>=': return value >= targetNum;
            case '<=': return value <= targetNum;
            case '=': return value === targetNum || value.toString().includes(numStr);
            default: return true;
        }
    }

    function checkSmartTextFilter(value, filterStr) {
        if (!filterStr) return true;
        const queryWords = filterStr.toLowerCase().trim().split(/\s+/);
        const targetValue = (value || '').toLowerCase();
        // Ensure ALL words in the query exist in the target string
        return queryWords.every(word => targetValue.includes(word));
    }

    function applyFilters() {
        const nameFilter = document.getElementById('filter-name')?.value || '';
        const priceFilter = document.getElementById('filter-price')?.value || '';
        const avgFilter = document.getElementById('filter-avg')?.value || '';
        const highFilter = document.getElementById('filter-high')?.value || '';
        const lowFilter = document.getElementById('filter-low')?.value || '';

        const filtered = allProducts.filter(item => {
            const matchesName = checkSmartTextFilter(item.product_name, nameFilter);
            const matchesPrice = checkNumericFilter(item.last_price || item.baseline_price, priceFilter);
            const matchesAvg = checkNumericFilter(item.last_market_avg, avgFilter);
            const matchesHigh = checkNumericFilter(item.last_market_high, highFilter);
            const matchesLow = checkNumericFilter(item.last_market_low, lowFilter);
            
            return matchesName && matchesPrice && matchesAvg && matchesHigh && matchesLow;
        });

        renderTable(filtered);
    }

    // Attach event listeners to filter inputs
    ['name', 'price', 'avg', 'high', 'low'].forEach(col => {
        const input = document.getElementById(`filter-${col}`);
        if (input) {
            input.addEventListener('input', applyFilters);
        }
    });

    window.toggleAnalysis = async (productId, checkbox) => {
        try {
            const res = await fetch(`/api/trackers/${productId}/toggle`, {
                method: 'POST'
            });
            const data = await res.json();
            
            if (res.ok) {
                const label = checkbox.closest('.toggle-container').querySelector('.toggle-label');
                const text = label.querySelector('.toggle-text');
                
                if (data.is_active) {
                    label.classList.add('active');
                    text.textContent = 'Monitoring 24/7';
                } else {
                    label.classList.remove('active');
                    text.textContent = 'Analyze 24/7';
                }
            } else {
                checkbox.checked = !checkbox.checked;
                alert('Failed to toggle status');
            }
        } catch (error) {
            checkbox.checked = !checkbox.checked;
            console.error('Error toggling tracker:', error);
        }
    };
    
    window.deleteProduct = async (productId) => {
        if (!confirm("Are you sure you want to delete this product?")) {
            return;
        }
        try {
            const res = await fetch(`/api/trackers/${productId}`, {
                method: 'DELETE'
            });
            const data = await res.json();
            
            if (res.ok) {
                loadProducts();
            } else {
                alert(data.error || 'Failed to delete product');
            }
        } catch (error) {
            console.error('Error deleting product:', error);
            alert('Failed to connect to the server');
        }
    };

    // History Modal Logic
    const historyModal = document.getElementById('history-modal');
    const closeHistoryBtn = document.getElementById('close-history-modal-btn');
    const historyTbody = document.getElementById('history-modal-tbody');
    const historyLoading = document.getElementById('history-loading');
    const historyCount = document.getElementById('history-modal-count');

    closeHistoryBtn.addEventListener('click', () => {
        historyModal.classList.remove('active');
    });

    window.openHistoryModal = async (productId) => {
        historyModal.classList.add('active');
        historyTbody.innerHTML = '';
        historyLoading.style.display = 'block';
        historyCount.textContent = '0';

        try {
            const res = await fetch(`/api/history/${productId}`);
            if (res.ok) {
                const data = await res.json();
                historyLoading.style.display = 'none';
                historyCount.textContent = data.length;
                
                const historyInfo = document.getElementById('history-modal-info');
                historyInfo.style.display = 'none'; // reset

                if (data.length > 0) {
                    const hasEmptyMarketData = data.some(item => item.market_avg === null || item.market_avg === 0 || item.market_avg === undefined);
                    if (hasEmptyMarketData) {
                        historyInfo.style.display = 'block';
                        historyInfo.innerHTML = "<strong>💡 Note:</strong> If some Market Price columns are empty or show '-', it means no competitors were found and <strong>you were the only seller</strong> of this product at that specific time!";
                    }
                }
                
                if (data.length === 0) {
                    historyTbody.innerHTML = '<tr><td colspan="5" style="padding: 1rem; text-align: center; color: var(--text-secondary);">No scan history available yet.</td></tr>';
                } else {
                    data.forEach(item => {
                        const row = document.createElement('tr');
                        const dateStr = new Date(item.timestamp + 'Z').toLocaleString();
                        const myPrice = item.my_price ? `AED ${parseFloat(item.my_price).toLocaleString()}` : '-';
                        const avg = item.market_avg ? `AED ${parseFloat(item.market_avg).toLocaleString()}` : '-';
                        const high = item.market_high ? `AED ${parseFloat(item.market_high).toLocaleString()}` : '-';
                        const low = item.market_low ? `AED ${parseFloat(item.market_low).toLocaleString()}` : '-';
                        
                        row.innerHTML = `
                            <td style="padding: 0.75rem; border-bottom: 1px solid var(--border-color);">${dateStr}</td>
                            <td style="padding: 0.75rem; border-bottom: 1px solid var(--border-color); color: var(--accent-secondary); font-weight: 600;">${myPrice}</td>
                            <td style="padding: 0.75rem; border-bottom: 1px solid var(--border-color);">${avg}</td>
                            <td style="padding: 0.75rem; border-bottom: 1px solid var(--border-color); color: #10b981;">${low}</td>
                            <td style="padding: 0.75rem; border-bottom: 1px solid var(--border-color); color: #ef4444;">${high}</td>
                        `;
                        historyTbody.appendChild(row);
                    });
                }
            } else {
                historyLoading.style.display = 'none';
                historyTbody.innerHTML = '<tr><td colspan="5" style="padding: 1rem; text-align: center; color: #ef4444;">Error loading history.</td></tr>';
            }
        } catch (e) {
            console.error('Failed to fetch history', e);
            historyLoading.style.display = 'none';
            historyTbody.innerHTML = '<tr><td colspan="5" style="padding: 1rem; text-align: center; color: #ef4444;">Failed to fetch history.</td></tr>';
        }
    };

    // Scan All Logic
    const scanAllBtn = document.getElementById('scan-all-btn');
    const scanAllProgress = document.getElementById('scan-all-progress');
    
    if (scanAllBtn) {
        scanAllBtn.addEventListener('click', async () => {
            try {
                // Fetch all trackers to scan
                const res = await fetch('/api/trackers');
                if (!res.ok) return;
                const products = await res.json();
                
                if (products.length === 0) {
                    alert("No products to scan!");
                    return;
                }
                
                scanAllBtn.disabled = true;
                scanAllBtn.style.opacity = '0.5';
                scanAllProgress.style.display = 'inline';
                
                let completed = 0;
                scanAllProgress.textContent = `Scanning 0/${products.length}...`;
                
                const delay = ms => new Promise(res => setTimeout(res, ms));

                for (const product of products) {
                    try {
                        await fetch('/api/analyze', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                product_name: product.product_name,
                                company_name: product.company_name,
                                platform: product.platform
                            })
                        });
                    } catch (e) {
                        console.error(`Failed to scan product ${product.product_name}`, e);
                    }
                    completed++;
                    scanAllProgress.textContent = `Scanning ${completed}/${products.length}...`;
                    
                    // Add a small delay between products to prevent AI rate limits
                    if (completed < products.length) {
                        await delay(2500);
                    }
                }
                
                scanAllProgress.textContent = `Scan Complete!`;
                
                // Reload dashboard data
                await loadProducts();
                
                setTimeout(() => {
                    scanAllProgress.style.display = 'none';
                    scanAllBtn.disabled = false;
                    scanAllBtn.style.opacity = '1';
                }, 2000);
                
            } catch (error) {
                console.error("Scan All error:", error);
                scanAllBtn.disabled = false;
                scanAllBtn.style.opacity = '1';
                scanAllProgress.style.display = 'none';
            }
        });
    }

    // Initial load
    loadProducts();
});
