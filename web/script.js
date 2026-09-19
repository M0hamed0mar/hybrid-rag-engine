// Additional JavaScript beyond inline scripts
// This file is for complex functionality if needed

// Export utilities for use in main.html
window.RAGSystem = {
    API_BASE: '/api/v1',

    async request(endpoint, options = {}) {
        const response = await fetch(`${this.API_BASE}${endpoint}`, {
            headers: { 'Content-Type': 'application/json' },
            ...options
        });
        return response.json();
    },

    formatBytes(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },

    formatTime(ms) {
        if (ms < 1000) return `${ms.toFixed(0)}ms`;
        return `${(ms / 1000).toFixed(2)}s`;
    }
};