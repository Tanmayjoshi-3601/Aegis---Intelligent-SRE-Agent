/**
 * SRE Agent Dashboard - Controls Management
 * Handles system controls, settings, and configuration
 */

class ControlsManager {
    constructor() {
        this.settings = {
            anomalyThreshold: 70,
            autoResolution: true,
            pagingLevel: 'high',
            processingRate: 'medium'
        };
        this.initializeControls();
    }

    initializeControls() {
        // Initialize slider value display
        this.initializeSlider();
        
        // Initialize toggle switches
        this.initializeToggles();
        
        // Initialize select controls
        this.initializeSelects();
        
        // Load saved settings
        this.loadSettings();
        
        // Set up event listeners
        this.setupEventListeners();
    }

    initializeSlider() {
        const anomalyThreshold = document.getElementById('anomalyThreshold');
        const anomalyThresholdValue = document.getElementById('anomalyThresholdValue');
        
        if (anomalyThreshold && anomalyThresholdValue) {
            anomalyThreshold.addEventListener('input', (e) => {
                anomalyThresholdValue.textContent = `${e.target.value}%`;
                this.settings.anomalyThreshold = parseInt(e.target.value);
            });
        }
    }

    initializeToggles() {
        const autoResolution = document.getElementById('autoResolution');
        if (autoResolution) {
            autoResolution.addEventListener('change', (e) => {
                this.settings.autoResolution = e.target.checked;
            });
        }
    }

    initializeSelects() {
        const pagingLevel = document.getElementById('pagingLevel');
        const processingRate = document.getElementById('processingRate');
        
        if (pagingLevel) {
            pagingLevel.addEventListener('change', (e) => {
                this.settings.pagingLevel = e.target.value;
            });
        }
        
        if (processingRate) {
            processingRate.addEventListener('change', (e) => {
                this.settings.processingRate = e.target.value;
            });
        }
    }

    setupEventListeners() {
        // Apply settings button
        const applyButton = document.querySelector('button[onclick="applySettings()"]');
        if (applyButton) {
            applyButton.addEventListener('click', () => this.applySettings());
        }
        
        // Reset settings button
        const resetButton = document.querySelector('button[onclick="resetSettings()"]');
        if (resetButton) {
            resetButton.addEventListener('click', () => this.resetSettings());
        }
    }

    loadSettings() {
        try {
            const savedSettings = JSON.parse(localStorage.getItem('sreDashboardSettings') || '{}');
            
            // Load anomaly threshold
            if (savedSettings.anomalyThreshold) {
                this.settings.anomalyThreshold = savedSettings.anomalyThreshold;
                const slider = document.getElementById('anomalyThreshold');
                const value = document.getElementById('anomalyThresholdValue');
                if (slider) slider.value = savedSettings.anomalyThreshold;
                if (value) value.textContent = `${savedSettings.anomalyThreshold}%`;
            }
            
            // Load auto resolution setting
            if (savedSettings.autoResolution !== undefined) {
                this.settings.autoResolution = savedSettings.autoResolution;
                const toggle = document.getElementById('autoResolution');
                if (toggle) toggle.checked = savedSettings.autoResolution;
            }
            
            // Load paging level
            if (savedSettings.pagingLevel) {
                this.settings.pagingLevel = savedSettings.pagingLevel;
                const select = document.getElementById('pagingLevel');
                if (select) select.value = savedSettings.pagingLevel;
            }
            
            // Load processing rate
            if (savedSettings.processingRate) {
                this.settings.processingRate = savedSettings.processingRate;
                const select = document.getElementById('processingRate');
                if (select) select.value = savedSettings.processingRate;
            }
            
        } catch (error) {
            console.error('Failed to load settings:', error);
        }
    }

    saveSettings() {
        try {
            localStorage.setItem('sreDashboardSettings', JSON.stringify(this.settings));
            return true;
        } catch (error) {
            console.error('Failed to save settings:', error);
            return false;
        }
    }

    async applySettings() {
        try {
            // Save to localStorage
            this.saveSettings();
            
            // Send to backend API
            const response = await fetch('/api/settings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(this.settings)
            });
            
            if (response.ok) {
                this.showNotification('success', 'Settings Applied', 'System settings have been updated successfully.');
            } else {
                throw new Error('Failed to apply settings');
            }
            
        } catch (error) {
            console.error('Failed to apply settings:', error);
            this.showNotification('error', 'Settings Failed', 'Failed to apply settings. Please try again.');
        }
    }

    resetSettings() {
        try {
            // Clear localStorage
            localStorage.removeItem('sreDashboardSettings');
            
            // Reset to defaults
            this.settings = {
                anomalyThreshold: 70,
                autoResolution: true,
                pagingLevel: 'high',
                processingRate: 'medium'
            };
            
            // Update UI
            this.updateUI();
            
            this.showNotification('info', 'Settings Reset', 'Settings have been reset to defaults.');
            
        } catch (error) {
            console.error('Failed to reset settings:', error);
            this.showNotification('error', 'Reset Failed', 'Failed to reset settings. Please try again.');
        }
    }

    updateUI() {
        // Update slider
        const slider = document.getElementById('anomalyThreshold');
        const value = document.getElementById('anomalyThresholdValue');
        if (slider) slider.value = this.settings.anomalyThreshold;
        if (value) value.textContent = `${this.settings.anomalyThreshold}%`;
        
        // Update toggle
        const toggle = document.getElementById('autoResolution');
        if (toggle) toggle.checked = this.settings.autoResolution;
        
        // Update selects
        const pagingLevel = document.getElementById('pagingLevel');
        const processingRate = document.getElementById('processingRate');
        if (pagingLevel) pagingLevel.value = this.settings.pagingLevel;
        if (processingRate) processingRate.value = this.settings.processingRate;
    }

    getSettings() {
        return { ...this.settings };
    }

    updateSetting(key, value) {
        this.settings[key] = value;
    }

    showNotification(type, title, message) {
        if (window.dashboard && window.dashboard.showNotification) {
            window.dashboard.showNotification(type, title, message);
        } else {
            // Fallback notification
            console.log(`${type.toUpperCase()}: ${title} - ${message}`);
        }
    }

    // Validation methods
    validateAnomalyThreshold(value) {
        return value >= 0 && value <= 100;
    }

    validatePagingLevel(level) {
        return ['critical', 'high', 'medium', 'all'].includes(level);
    }

    validateProcessingRate(rate) {
        return ['low', 'medium', 'high', 'max'].includes(rate);
    }

    // Get processing rate limits
    getProcessingRateLimits() {
        const limits = {
            low: 100,
            medium: 500,
            high: 1000,
            max: 2000
        };
        return limits[this.settings.processingRate] || 500;
    }

    // Get paging level description
    getPagingLevelDescription() {
        const descriptions = {
            critical: 'Only critical incidents will page humans',
            high: 'High and critical incidents will page humans',
            medium: 'Medium, high, and critical incidents will page humans',
            all: 'All incidents will page humans'
        };
        return descriptions[this.settings.pagingLevel] || descriptions.high;
    }

    // Export settings for backup
    exportSettings() {
        return {
            settings: this.settings,
            timestamp: new Date().toISOString(),
            version: '1.0.0'
        };
    }

    // Import settings from backup
    importSettings(data) {
        try {
            if (data.settings && typeof data.settings === 'object') {
                this.settings = { ...this.settings, ...data.settings };
                this.updateUI();
                this.saveSettings();
                return true;
            }
            return false;
        } catch (error) {
            console.error('Failed to import settings:', error);
            return false;
        }
    }
}

// Initialize controls manager
window.controlsManager = new ControlsManager();

// Global functions for HTML onclick handlers
function applySettings() {
    if (window.controlsManager) {
        window.controlsManager.applySettings();
    }
}

function resetSettings() {
    if (window.controlsManager) {
        window.controlsManager.resetSettings();
    }
} 