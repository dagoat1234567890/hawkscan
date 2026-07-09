document.addEventListener('DOMContentLoaded', () => {
    const tableContainer = document.getElementById('history-table-container');
    const tbody = document.getElementById('history-tbody');
    const emptyState = document.getElementById('empty-state');
    const loadingState = document.getElementById('loading-state');

    let allHistory = [];

    async function loadHistory() {
        loadingState.style.display = 'block';
        tableContainer.style.display = 'none';
        emptyState.style.display = 'none';

        try {
            const res = await fetch('/api/history_global');
            allHistory = await res.json();

            loadingState.style.display = 'none';

            if (allHistory.length === 0) {
                emptyState.style.display = 'block';
            } else {
                renderTable(allHistory);
                tableContainer.style.display = 'block';
            }
        } catch (error) {
            console.error('Failed to load history:', error);
            loadingState.style.display = 'none';
            emptyState.style.display = 'block';
            emptyState.querySelector('h3').innerText = 'Error loading history';
        }
    }

    function renderTable(data) {
    tbody.innerHTML = '';
    if (data.length === 0) {
        // Updated padding and font size for the empty row match
        tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: var(--text-secondary); padding: 2rem; font-size: 1.1rem;">No matches found.</td></tr>';
        return;
    }

    data.forEach(item => {
        const row = document.createElement('tr');
        
        const dateStr = new Date(item.timestamp + 'Z').toLocaleString();
        const myPrice = (item.my_price !== null && !isNaN(item.my_price)) ? `AED ${item.my_price.toLocaleString()}` : '-';
        const avg = (item.market_avg !== null && !isNaN(item.market_avg)) ? `AED ${item.market_avg.toLocaleString()}` : '-';
        const high = (item.market_high !== null && !isNaN(item.market_high)) ? `AED ${item.market_high.toLocaleString()}` : '-';
        const low = (item.market_low !== null && !isNaN(item.market_low)) ? `AED ${item.market_low.toLocaleString()}` : '-';

        // Added padding: 1.5rem 2rem; and font-size: 1.1rem; to all cells (td)
        row.innerHTML = `
            <td style="color: var(--text-secondary); font-size: 1.1rem; padding: 1.5rem 2rem;">${dateStr}</td>
            <td style="font-weight: 500; color: var(--text-primary); font-size: 1.1rem; padding: 1.5rem 2rem;">${item.product_name}</td>
            <td style="padding: 1.5rem 2rem;"><span style="font-size: 0.9rem; padding: 0.4rem 0.7rem; border-radius: 4px; background: var(--border-color); color: var(--text-primary); text-transform: uppercase;">${item.platform}</span></td>
            <td style="color: var(--accent-secondary); font-weight: 600; font-size: 1.1rem; padding: 1.5rem 2rem;">${myPrice}</td>
            <td style="font-size: 1.1rem; padding: 1.5rem 2rem;">${avg}</td>
            <td style="color: #ef4444; font-weight: 600; font-size: 1.1rem; padding: 1.5rem 2rem;">${high}</td>
            <td style="color: #10b981; font-weight: 600; font-size: 1.1rem; padding: 1.5rem 2rem;">${low}</td>
        `;
        tbody.appendChild(row);
    });
}


    let currentSortColumn = null;
    let currentSortDirection = 1;

    window.sortHistory = (column) => {
        if (currentSortColumn === column) {
            currentSortDirection *= -1; // toggle
        } else {
            currentSortColumn = column;
            currentSortDirection = 1;
        }

        allHistory.sort((a, b) => {
            let valA, valB;
            if (column === 'date') {
                valA = new Date(a.timestamp + 'Z').getTime();
                valB = new Date(b.timestamp + 'Z').getTime();
            } else if (column === 'price') {
                valA = a.my_price || 0;
                valB = b.my_price || 0;
            } else if (column === 'market_avg') {
                valA = a.market_avg || 0;
                valB = b.market_avg || 0;
            } else if (column === 'market_high') {
                valA = a.market_high || 0;
                valB = b.market_high || 0;
            } else if (column === 'market_low') {
                valA = a.market_low || 0;
                valB = b.market_low || 0;
            }
            if (valA < valB) return -1 * currentSortDirection;
            if (valA > valB) return 1 * currentSortDirection;
            return 0;
        });

        // Update headers to show arrow indicator
        const dateIndicator = document.getElementById('sort-date-indicator');
        const priceIndicator = document.getElementById('sort-price-indicator');
        const avgIndicator = document.getElementById('sort-market-avg-indicator');
        const highIndicator = document.getElementById('sort-market-high-indicator');
        const lowIndicator = document.getElementById('sort-market-low-indicator');
        
        if (dateIndicator) dateIndicator.textContent = column === 'date' ? (currentSortDirection === 1 ? '▲' : '▼') : '↕';
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
        if (isNaN(targetNum)) return true; // fallback if invalid
        
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
        return queryWords.every(word => targetValue.includes(word));
    }

    function applyFilters() {
        const dateFilter = document.getElementById('filter-date')?.value || '';
        const nameFilter = document.getElementById('filter-name')?.value || '';
        const platformFilter = document.getElementById('filter-platform')?.value || '';
        const priceFilter = document.getElementById('filter-price')?.value || '';
        const avgFilter = document.getElementById('filter-avg')?.value || '';
        const highFilter = document.getElementById('filter-high')?.value || '';
        const lowFilter = document.getElementById('filter-low')?.value || '';

        const filtered = allHistory.filter(item => {
            const dateStr = new Date(item.timestamp + 'Z').toLocaleString();
            
            const matchesDate = checkSmartTextFilter(dateStr, dateFilter);
            const matchesName = checkSmartTextFilter(item.product_name, nameFilter);
            const matchesPlatform = checkSmartTextFilter(item.platform, platformFilter);
            
            const matchesPrice = checkNumericFilter(item.my_price, priceFilter);
            const matchesAvg = checkNumericFilter(item.market_avg, avgFilter);
            const matchesHigh = checkNumericFilter(item.market_high, highFilter);
            const matchesLow = checkNumericFilter(item.market_low, lowFilter);
            
            return matchesDate && matchesName && matchesPlatform && matchesPrice && matchesAvg && matchesHigh && matchesLow;
        });

        renderTable(filtered);
    }

    // Attach event listeners to filter inputs
    ['date', 'name', 'platform', 'price', 'avg', 'high', 'low'].forEach(col => {
        const input = document.getElementById(`filter-${col}`);
        if (input) {
            input.addEventListener('input', applyFilters);
        }
    });

    loadHistory();
});
