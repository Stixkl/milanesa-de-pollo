/**
 * TRACKADEMIC - JavaScript Principal
 * Sistema de Gestión Académica Profesional
 * v2.0
 */

// Utilidades globales - Disponibles inmediatamente
const TrackademicUtils = {
    /**
     * Formatear números
     */
    formatNumber(num, decimals = 2) {
        return new Intl.NumberFormat('es-ES', {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        }).format(num);
    },

    /**
     * Formatear fechas
     */
    formatDate(date, format = 'short') {
        const options = {
            short: { day: 'numeric', month: 'short', year: 'numeric' },
            long: { day: 'numeric', month: 'long', year: 'numeric' },
            time: { hour: '2-digit', minute: '2-digit' }
        };
        
        return new Intl.DateTimeFormat('es-ES', options[format]).format(new Date(date));
    },

    /**
     * Mostrar notificación
     */
    showNotification(message, type = 'info', duration = 5000) {
        // Remover notificaciones existentes
        const existingNotifications = document.querySelectorAll('.notification');
        existingNotifications.forEach(notification => notification.remove());

        const notification = document.createElement('div');
        notification.className = `notification notification-${type} show`;
        
        // Icono según el tipo
        const icons = {
            info: '<i class="fas fa-info-circle"></i>',
            success: '<i class="fas fa-check-circle"></i>',
            warning: '<i class="fas fa-exclamation-triangle"></i>',
            danger: '<i class="fas fa-times-circle"></i>'
        };
        
        notification.innerHTML = `
            <div class="notification-content">
                <div class="notification-icon">${icons[type] || icons.info}</div>
                <div class="notification-body">
                    <div class="notification-message">${message}</div>
                </div>
                <button class="notification-close">&times;</button>
            </div>
        `;

        document.body.appendChild(notification);

        // Auto-remove
        setTimeout(() => {
            notification.classList.add('fade-out');
            setTimeout(() => notification.remove(), 300);
        }, duration);

        // Manual close
        notification.querySelector('.notification-close').addEventListener('click', () => {
            notification.classList.add('fade-out');
            setTimeout(() => notification.remove(), 300);
        });
    },

    /**
     * Debounce function
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    /**
     * Throttle function
     */
    throttle(func, limit) {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }
};

class TrackademicApp {
    constructor() {
        this.sidebar = document.querySelector('.sidebar');
        this.mainContent = document.querySelector('.main-content');
        this.sidebarToggle = document.querySelector('.sidebar-toggle');
        this.mobileBreakpoint = 768;
        this.tabletBreakpoint = 1024;
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupResponsive();
        this.initializeComponents();
        this.setupAnimations();
    }

    /**
     * Configurar event listeners
     */
    setupEventListeners() {
        // Toggle del sidebar
        if (this.sidebarToggle) {
            this.sidebarToggle.addEventListener('click', () => this.toggleSidebar());
        }

        // Cerrar sidebar en mobile al hacer click fuera
        document.addEventListener('click', (e) => {
            if (window.innerWidth <= this.mobileBreakpoint) {
                if (!this.sidebar.contains(e.target) && !this.sidebarToggle.contains(e.target)) {
                    this.closeMobileSidebar();
                }
            }
        });

        // Navegación activa
        this.setupActiveNavigation();

        // Smooth scroll para enlaces internos
        this.setupSmoothScroll();

        // Auto-refresh para estadísticas
        this.setupAutoRefresh();
    }

    /**
     * Toggle del sidebar
     */
    toggleSidebar() {
        const width = window.innerWidth;
        
        if (width <= this.mobileBreakpoint) {
            // Mobile: slide in/out
            this.sidebar.classList.toggle('mobile-open');
        } else if (width <= this.tabletBreakpoint) {
            // Tablet: collapse/expand
            this.sidebar.classList.toggle('expanded');
            this.mainContent.classList.toggle('compressed');
        } else {
            // Desktop: collapse/expand
            this.sidebar.classList.toggle('collapsed');
            this.mainContent.classList.toggle('expanded');
        }
    }

    /**
     * Cerrar sidebar en mobile
     */
    closeMobileSidebar() {
        this.sidebar.classList.remove('mobile-open');
    }

    /**
     * Configurar responsive behavior
     */
    setupResponsive() {
        window.addEventListener('resize', () => {
            const width = window.innerWidth;
            
            // Reset classes al cambiar de breakpoint
            if (width > this.mobileBreakpoint) {
                this.sidebar.classList.remove('mobile-open');
            }
            
            if (width > this.tabletBreakpoint) {
                this.sidebar.classList.remove('expanded');
                this.mainContent.classList.remove('compressed');
            }
        });
    }

    /**
     * Configurar navegación activa
     */
    setupActiveNavigation() {
        const currentPath = window.location.pathname;
        const navLinks = document.querySelectorAll('.nav-link');
        
        navLinks.forEach(link => {
            const href = link.getAttribute('href');
            if (href && currentPath.includes(href) && href !== '/') {
                link.classList.add('active');
            } else if (href === '/' && currentPath === '/') {
                link.classList.add('active');
            }
        });
    }

    /**
     * Configurar smooth scroll
     */
    setupSmoothScroll() {
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
    }

    /**
     * Configurar auto-refresh para estadísticas
     */
    setupAutoRefresh() {
        if (window.location.pathname.includes('/informes/')) {
            setInterval(() => {
                this.refreshStats();
            }, 300000); // 5 minutos
        }
    }

    /**
     * Refrescar estadísticas via AJAX
     */
    async refreshStats() {
        try {
            const response = await fetch('/api/estadisticas/tiempo-real/');
            if (response.ok) {
                const data = await response.json();
                this.updateStatsUI(data);
            }
        } catch (error) {
            console.log('Auto-refresh no disponible:', error);
        }
    }

    /**
     * Actualizar UI con nuevos datos
     */
    updateStatsUI(data) {
        // Actualizar métricas principales
        const statsCards = document.querySelectorAll('.stats-value');
        if (data.metrics) {
            statsCards.forEach((card, index) => {
                if (data.metrics[index]) {
                    this.animateNumber(card, data.metrics[index]);
                }
            });
        }
    }

    /**
     * Animar números
     */
    animateNumber(element, target) {
        const current = parseFloat(element.textContent) || 0;
        const increment = (target - current) / 20;
        let value = current;
        
        const animation = setInterval(() => {
            value += increment;
            if ((increment > 0 && value >= target) || (increment < 0 && value <= target)) {
                value = target;
                clearInterval(animation);
            }
            element.textContent = value.toFixed(2);
        }, 50);
    }

    /**
     * Inicializar componentes
     */
    initializeComponents() {
        this.initTooltips();
        this.initModals();
        this.initFormValidation();
        this.initSearchBox();
    }

    /**
     * Inicializar tooltips
     */
    initTooltips() {
        document.querySelectorAll('[data-tooltip]').forEach(element => {
            element.addEventListener('mouseenter', (e) => {
                this.showTooltip(e.target, e.target.dataset.tooltip);
            });
            
            element.addEventListener('mouseleave', () => {
                this.hideTooltip();
            });
        });
    }

    /**
     * Mostrar tooltip
     */
    showTooltip(element, text) {
        const tooltip = document.createElement('div');
        tooltip.className = 'tooltip-modern';
        tooltip.textContent = text;
        
        document.body.appendChild(tooltip);
        
        const rect = element.getBoundingClientRect();
        tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
        tooltip.style.top = rect.top - tooltip.offsetHeight - 8 + 'px';
        
        setTimeout(() => tooltip.classList.add('show'), 10);
    }

    /**
     * Ocultar tooltip
     */
    hideTooltip() {
        const tooltip = document.querySelector('.tooltip-modern');
        if (tooltip) {
            tooltip.classList.remove('show');
            setTimeout(() => tooltip.remove(), 200);
        }
    }

    /**
     * Inicializar modales
     */
    initModals() {
        document.querySelectorAll('[data-modal-target]').forEach(trigger => {
            trigger.addEventListener('click', (e) => {
                e.preventDefault();
                const modalId = trigger.dataset.modalTarget;
                this.openModal(modalId);
            });
        });

        document.querySelectorAll('.modal-close').forEach(closeBtn => {
            closeBtn.addEventListener('click', () => {
                this.closeModal();
            });
        });

        // Cerrar modal con Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeModal();
            }
        });
    }

    /**
     * Abrir modal
     */
    openModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('show');
            document.body.classList.add('modal-open');
        }
    }

    /**
     * Cerrar modal
     */
    closeModal() {
        const modals = document.querySelectorAll('.modal.show');
        modals.forEach(modal => {
            modal.classList.remove('show');
        });
        document.body.classList.remove('modal-open');
    }

    /**
     * Validación de formularios
     */
    initFormValidation() {
        document.querySelectorAll('form[data-validate]').forEach(form => {
            form.addEventListener('submit', (e) => {
                if (!this.validateForm(form)) {
                    e.preventDefault();
                }
            });

            // Validación en tiempo real
            form.querySelectorAll('input, select, textarea').forEach(field => {
                field.addEventListener('blur', () => {
                    this.validateField(field);
                });
            });
        });
    }

    /**
     * Validar formulario
     */
    validateForm(form) {
        let isValid = true;
        const fields = form.querySelectorAll('input, select, textarea');
        
        fields.forEach(field => {
            if (!this.validateField(field)) {
                isValid = false;
            }
        });
        
        return isValid;
    }

    /**
     * Validar campo individual
     */
    validateField(field) {
        const value = field.value.trim();
        const type = field.type;
        const required = field.hasAttribute('required');
        let isValid = true;
        let message = '';

        // Limpiar errores previos
        this.clearFieldError(field);

        // Validar campo requerido
        if (required && !value) {
            isValid = false;
            message = 'Este campo es requerido';
        }

        // Validaciones específicas por tipo
        if (value && type === 'email') {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(value)) {
                isValid = false;
                message = 'Ingrese un email válido';
            }
        }

        if (value && field.hasAttribute('data-min-length')) {
            const minLength = parseInt(field.dataset.minLength);
            if (value.length < minLength) {
                isValid = false;
                message = `Mínimo ${minLength} caracteres`;
            }
        }

        // Mostrar error si es necesario
        if (!isValid) {
            this.showFieldError(field, message);
        }

        return isValid;
    }

    /**
     * Mostrar error en campo
     */
    showFieldError(field, message) {
        field.classList.add('error');
        const errorDiv = document.createElement('div');
        errorDiv.className = 'field-error';
        errorDiv.textContent = message;
        field.parentNode.appendChild(errorDiv);
    }

    /**
     * Limpiar error de campo
     */
    clearFieldError(field) {
        field.classList.remove('error');
        const error = field.parentNode.querySelector('.field-error');
        if (error) {
            error.remove();
        }
    }

    /**
     * Configurar caja de búsqueda
     */
    initSearchBox() {
        const searchInput = document.querySelector('.search-input');
        if (searchInput) {
            let searchTimeout;
            
            searchInput.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    this.performSearch(e.target.value);
                }, 300);
            });
        }
    }

    /**
     * Realizar búsqueda
     */
    async performSearch(query) {
        if (query.length < 2) return;
        
        try {
            const response = await fetch(`/api/buscar/?q=${encodeURIComponent(query)}`);
            if (response.ok) {
                const results = await response.json();
                this.showSearchResults(results);
            }
        } catch (error) {
            console.log('Búsqueda no disponible:', error);
        }
    }

    /**
     * Mostrar resultados de búsqueda
     */
    showSearchResults(results) {
        // Implementar dropdown de resultados
        console.log('Resultados de búsqueda:', results);
    }

    /**
     * Configurar animaciones
     */
    setupAnimations() {
        // Intersection Observer para animaciones
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-in');
                }
            });
        }, { threshold: 0.1 });

        // Observar elementos con clase animate-on-scroll
        document.querySelectorAll('.animate-on-scroll').forEach(el => {
            observer.observe(el);
        });
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    new TrackademicApp();
});

// Exportar para uso global
window.TrackademicApp = TrackademicApp;
window.TrackademicUtils = TrackademicUtils; 