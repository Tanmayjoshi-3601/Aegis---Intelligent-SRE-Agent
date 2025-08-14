/**
 * SRE Agent Dashboard - Utilities
 * Helper functions and utilities for the dashboard
 */

class DashboardUtils {
    constructor() {
        this.debounceTimers = new Map();
        this.throttleTimers = new Map();
    }

    // Debounce function calls
    debounce(func, delay, key = 'default') {
        if (this.debounceTimers.has(key)) {
            clearTimeout(this.debounceTimers.get(key));
        }
        
        const timer = setTimeout(() => {
            func();
            this.debounceTimers.delete(key);
        }, delay);
        
        this.debounceTimers.set(key, timer);
    }

    // Throttle function calls
    throttle(func, delay, key = 'default') {
        if (this.throttleTimers.has(key)) {
            return;
        }
        
        func();
        this.throttleTimers.set(key, true);
        
        setTimeout(() => {
            this.throttleTimers.delete(key);
        }, delay);
    }

    // Format numbers with appropriate suffixes
    formatNumber(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        }
        if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toString();
    }

    // Format percentages
    formatPercentage(value, total) {
        if (total === 0) return '0%';
        return Math.round((value / total) * 100) + '%';
    }

    // Format time durations
    formatDuration(ms) {
        const seconds = Math.floor(ms / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        const days = Math.floor(hours / 24);

        if (days > 0) return `${days}d ${hours % 24}h ${minutes % 60}m`;
        if (hours > 0) return `${hours}h ${minutes % 60}m`;
        if (minutes > 0) return `${minutes}m ${seconds % 60}s`;
        return `${seconds}s`;
    }

    // Format relative time
    formatRelativeTime(timestamp) {
        const now = new Date();
        const time = new Date(timestamp);
        const diffMs = now - time;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;
        return time.toLocaleDateString();
    }

    // Format file sizes
    formatFileSize(bytes) {
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        if (bytes === 0) return '0 Bytes';
        const i = Math.floor(Math.log(bytes) / Math.log(1024));
        return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
    }

    // Generate random color
    getRandomColor() {
        const colors = [
            '#00d4ff', '#7c3aed', '#10b981', '#f59e0b', '#ef4444', '#3b82f6',
            '#8b5cf6', '#06b6d4', '#84cc16', '#f97316', '#ec4899', '#6366f1'
        ];
        return colors[Math.floor(Math.random() * colors.length)];
    }

    // Get color based on severity
    getSeverityColor(severity) {
        const colors = {
            critical: '#ef4444',
            high: '#f59e0b',
            medium: '#3b82f6',
            low: '#10b981'
        };
        return colors[severity] || '#64748b';
    }

    // Get color based on status
    getStatusColor(status) {
        const colors = {
            online: '#10b981',
            offline: '#ef4444',
            warning: '#f59e0b',
            active: '#3b82f6',
            resolved: '#10b981',
            acknowledged: '#8b5cf6'
        };
        return colors[status] || '#64748b';
    }

    // Copy text to clipboard
    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            return true;
        } catch (error) {
            console.error('Failed to copy to clipboard:', error);
            return false;
        }
    }

    // Download data as JSON
    downloadJSON(data, filename) {
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    // Download data as CSV
    downloadCSV(data, filename) {
        if (!Array.isArray(data) || data.length === 0) return;

        const headers = Object.keys(data[0]);
        const csvContent = [
            headers.join(','),
            ...data.map(row => headers.map(header => `"${row[header]}"`).join(','))
        ].join('\n');

        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    // Validate email format
    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    // Validate URL format
    isValidURL(url) {
        try {
            new URL(url);
            return true;
        } catch {
            return false;
        }
    }

    // Sanitize HTML content
    sanitizeHTML(html) {
        const div = document.createElement('div');
        div.textContent = html;
        return div.innerHTML;
    }

    // Generate unique ID
    generateId() {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    }

    // Deep clone object
    deepClone(obj) {
        if (obj === null || typeof obj !== 'object') return obj;
        if (obj instanceof Date) return new Date(obj.getTime());
        if (obj instanceof Array) return obj.map(item => this.deepClone(item));
        if (typeof obj === 'object') {
            const clonedObj = {};
            for (const key in obj) {
                if (obj.hasOwnProperty(key)) {
                    clonedObj[key] = this.deepClone(obj[key]);
                }
            }
            return clonedObj;
        }
    }

    // Merge objects deeply
    deepMerge(target, source) {
        const result = { ...target };
        
        for (const key in source) {
            if (source.hasOwnProperty(key)) {
                if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
                    result[key] = this.deepMerge(result[key] || {}, source[key]);
                } else {
                    result[key] = source[key];
                }
            }
        }
        
        return result;
    }

    // Get query parameters from URL
    getQueryParams() {
        const params = new URLSearchParams(window.location.search);
        const result = {};
        for (const [key, value] of params) {
            result[key] = value;
        }
        return result;
    }

    // Set query parameters in URL
    setQueryParams(params) {
        const url = new URL(window.location);
        for (const [key, value] of Object.entries(params)) {
            if (value !== null && value !== undefined) {
                url.searchParams.set(key, value);
            } else {
                url.searchParams.delete(key);
            }
        }
        window.history.replaceState({}, '', url);
    }

    // Local storage utilities
    setLocalStorage(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (error) {
            console.error('Failed to save to localStorage:', error);
            return false;
        }
    }

    getLocalStorage(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (error) {
            console.error('Failed to read from localStorage:', error);
            return defaultValue;
        }
    }

    removeLocalStorage(key) {
        try {
            localStorage.removeItem(key);
            return true;
        } catch (error) {
            console.error('Failed to remove from localStorage:', error);
            return false;
        }
    }

    // Session storage utilities
    setSessionStorage(key, value) {
        try {
            sessionStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (error) {
            console.error('Failed to save to sessionStorage:', error);
            return false;
        }
    }

    getSessionStorage(key, defaultValue = null) {
        try {
            const item = sessionStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (error) {
            console.error('Failed to read from sessionStorage:', error);
            return defaultValue;
        }
    }

    removeSessionStorage(key) {
        try {
            sessionStorage.removeItem(key);
            return true;
        } catch (error) {
            console.error('Failed to remove from sessionStorage:', error);
            return false;
        }
    }

    // Cookie utilities
    setCookie(name, value, days = 7) {
        const expires = new Date();
        expires.setTime(expires.getTime() + (days * 24 * 60 * 60 * 1000));
        document.cookie = `${name}=${value};expires=${expires.toUTCString()};path=/`;
    }

    getCookie(name) {
        const nameEQ = name + "=";
        const ca = document.cookie.split(';');
        for (let i = 0; i < ca.length; i++) {
            let c = ca[i];
            while (c.charAt(0) === ' ') c = c.substring(1, c.length);
            if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length, c.length);
        }
        return null;
    }

    removeCookie(name) {
        document.cookie = `${name}=;expires=Thu, 01 Jan 1970 00:00:00 UTC;path=/;`;
    }

    // Date utilities
    formatDate(date, format = 'YYYY-MM-DD') {
        const d = new Date(date);
        const year = d.getFullYear();
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        const hours = String(d.getHours()).padStart(2, '0');
        const minutes = String(d.getMinutes()).padStart(2, '0');
        const seconds = String(d.getSeconds()).padStart(2, '0');

        return format
            .replace('YYYY', year)
            .replace('MM', month)
            .replace('DD', day)
            .replace('HH', hours)
            .replace('mm', minutes)
            .replace('ss', seconds);
    }

    // Array utilities
    chunk(array, size) {
        const chunks = [];
        for (let i = 0; i < array.length; i += size) {
            chunks.push(array.slice(i, i + size));
        }
        return chunks;
    }

    unique(array, key = null) {
        if (key) {
            const seen = new Set();
            return array.filter(item => {
                const value = item[key];
                if (seen.has(value)) {
                    return false;
                }
                seen.add(value);
                return true;
            });
        }
        return [...new Set(array)];
    }

    groupBy(array, key) {
        return array.reduce((groups, item) => {
            const group = item[key];
            if (!groups[group]) {
                groups[group] = [];
            }
            groups[group].push(item);
            return groups;
        }, {});
    }

    // String utilities
    truncate(str, length = 100, suffix = '...') {
        if (str.length <= length) return str;
        return str.substring(0, length) + suffix;
    }

    capitalize(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
    }

    camelCase(str) {
        return str.replace(/-([a-z])/g, (g) => g[1].toUpperCase());
    }

    kebabCase(str) {
        return str.replace(/([a-z])([A-Z])/g, '$1-$2').toLowerCase();
    }

    // Math utilities
    roundToDecimal(num, decimals = 2) {
        return Math.round(num * Math.pow(10, decimals)) / Math.pow(10, decimals);
    }

    clamp(value, min, max) {
        return Math.min(Math.max(value, min), max);
    }

    lerp(start, end, factor) {
        return start + (end - start) * factor;
    }

    // DOM utilities
    createElement(tag, attributes = {}, children = []) {
        const element = document.createElement(tag);
        
        for (const [key, value] of Object.entries(attributes)) {
            if (key === 'className') {
                element.className = value;
            } else if (key === 'textContent') {
                element.textContent = value;
            } else if (key === 'innerHTML') {
                element.innerHTML = value;
            } else {
                element.setAttribute(key, value);
            }
        }
        
        children.forEach(child => {
            if (typeof child === 'string') {
                element.appendChild(document.createTextNode(child));
            } else {
                element.appendChild(child);
            }
        });
        
        return element;
    }

    // Event utilities
    addEventListeners(element, events) {
        for (const [event, handler] of Object.entries(events)) {
            element.addEventListener(event, handler);
        }
    }

    removeEventListeners(element, events) {
        for (const [event, handler] of Object.entries(events)) {
            element.removeEventListener(event, handler);
        }
    }

    // Animation utilities
    animate(element, properties, duration = 300, easing = 'ease') {
        return new Promise(resolve => {
            const startTime = performance.now();
            const startValues = {};
            
            // Get starting values
            for (const [property, endValue] of Object.entries(properties)) {
                startValues[property] = parseFloat(getComputedStyle(element)[property]) || 0;
            }
            
            function animate(currentTime) {
                const elapsed = currentTime - startTime;
                const progress = Math.min(elapsed / duration, 1);
                
                // Apply easing
                const easedProgress = easing === 'ease' ? 
                    1 - Math.pow(1 - progress, 3) : progress;
                
                // Update properties
                for (const [property, endValue] of Object.entries(properties)) {
                    const startValue = startValues[property];
                    const currentValue = startValue + (endValue - startValue) * easedProgress;
                    element.style[property] = currentValue + (property.includes('color') ? '' : 'px');
                }
                
                if (progress < 1) {
                    requestAnimationFrame(animate);
                } else {
                    resolve();
                }
            }
            
            requestAnimationFrame(animate);
        });
    }
}

// Initialize utilities
window.utils = new DashboardUtils(); 