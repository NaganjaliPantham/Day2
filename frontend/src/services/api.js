import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    console.log(`Making ${config.method.toUpperCase()} request to ${config.url}`);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response.data;
  },
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    throw error;
  }
);

// API endpoints
export const apiService = {
  // Health check
  healthCheck: () => api.get('/'),

  // Entity management
  getEntities: () => api.get('/api/entities'),
  createEntity: (entityData) => api.post('/api/entities', entityData),
  getEntityProfile: (entityId) => api.get(`/api/entities/${entityId}`),

  // Risk assessment
  assessRisk: (entityIds, includeRecommendations = true) => 
    api.post('/api/assess-risk', {
      entity_ids: entityIds,
      include_recommendations: includeRecommendations
    }),

  // Model management
  trainModel: (useSimpleData = true, dataSize = 1000) =>
    api.post('/api/train-model', {
      use_sample_data: useSimpleData,
      data_size: dataSize
    }),
  getModelInfo: () => api.get('/api/model-info'),

  // Security rules
  getSecurityRules: () => api.get('/api/security-rules'),
  createSecurityRule: (ruleData) => api.post('/api/security-rules', ruleData),

  // Pattern detection
  detectPatterns: () => api.post('/api/detect-patterns'),

  // Dashboard and statistics
  getDashboardStats: () => api.get('/api/dashboard-stats'),

  // Recommendations
  implementRecommendation: (recommendationId, notes = '') =>
    api.post(`/api/recommendations/${recommendationId}/implement`, { notes }),

  // Sample data initialization
  initializeSampleData: () => api.post('/api/initialize-sample-data'),
};

// Risk scoring utilities
export const riskUtils = {
  getRiskColor: (riskScore) => {
    if (riskScore <= 15) return '#52c41a'; // Green - Low
    if (riskScore <= 25) return '#faad14'; // Orange - Medium  
    if (riskScore <= 35) return '#fa541c'; // Red - High
    return '#a8071a'; // Dark Red - Critical
  },

  getRiskLevel: (riskScore) => {
    if (riskScore <= 15) return 'Low';
    if (riskScore <= 25) return 'Medium';
    if (riskScore <= 35) return 'High';
    return 'Critical';
  },

  getRiskIcon: (riskLevel) => {
    switch (riskLevel) {
      case 'Low': return '🟢';
      case 'Medium': return '🟡';
      case 'High': return '🟠';
      case 'Critical': return '🔴';
      default: return '⚪';
    }
  },

  formatRiskScore: (score) => {
    return typeof score === 'number' ? score.toFixed(1) : '0.0';
  },

  getTrendIcon: (trend) => {
    switch (trend) {
      case 'increasing': return '📈';
      case 'decreasing': return '📉';
      case 'stable': return '➡️';
      default: return '❓';
    }
  }
};

// Chart configuration utilities
export const chartConfig = {
  riskDistributionColors: ['#52c41a', '#faad14', '#fa541c', '#a8071a'],
  
  defaultChartOptions: {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: 'top',
      },
    },
  },

  timeSeriesOptions: {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      x: {
        type: 'time',
        display: true,
        title: {
          display: true,
          text: 'Time'
        }
      },
      y: {
        display: true,
        title: {
          display: true,
          text: 'Risk Score'
        },
        min: 0,
        max: 50
      }
    },
    plugins: {
      legend: {
        display: true,
        position: 'top',
      },
    },
  },

  departmentStatsOptions: {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: 'right',
      },
    },
  }
};

// Notification utilities
export const notificationService = {
  success: (message, description = '') => {
    // Implementation depends on your notification library (antd notification, react-toastify, etc.)
    console.log('SUCCESS:', message, description);
  },

  error: (message, description = '') => {
    console.error('ERROR:', message, description);
  },

  info: (message, description = '') => {
    console.log('INFO:', message, description);
  },

  warning: (message, description = '') => {
    console.warn('WARNING:', message, description);
  }
};

// Error handling utilities
export const errorHandler = {
  handleApiError: (error, defaultMessage = 'An error occurred') => {
    let message = defaultMessage;
    let description = '';

    if (error.response) {
      // Server responded with error status
      message = error.response.data?.detail || error.response.data?.message || defaultMessage;
      description = `Status: ${error.response.status}`;
    } else if (error.request) {
      // Request was made but no response received
      message = 'Network error - please check your connection';
      description = 'The server may be unavailable';
    } else {
      // Something else happened
      message = error.message || defaultMessage;
    }

    notificationService.error(message, description);
    return { message, description };
  }
};

// Data formatting utilities
export const dataFormatter = {
  formatDate: (dateString) => {
    if (!dateString) return 'N/A';
    try {
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return 'Invalid Date';
    }
  },

  formatNumber: (number, decimals = 2) => {
    if (typeof number !== 'number') return 'N/A';
    return number.toFixed(decimals);
  },

  formatPercentage: (value, total) => {
    if (!total || total === 0) return '0%';
    return `${((value / total) * 100).toFixed(1)}%`;
  },

  truncateText: (text, maxLength = 50) => {
    if (!text || text.length <= maxLength) return text;
    return `${text.substring(0, maxLength)}...`;
  }
};

export default api;