// static/js/notifications.js

// Управление уведомлениями

// Проверка новых уведомлений
function checkNewNotifications() {
    fetch('/notifications/api/unread-count/')
        .then(response => response.json())
        .then(data => {
            updateNotificationBadge(data.count);
            if (data.count > 0) {
                showNotificationToast('У вас ' + data.count + ' новых уведомлений');
            }
        });
}

// Обновление бейджа уведомлений
function updateNotificationBadge(count) {
    const badge = document.getElementById('notification-badge');
    if (badge) {
        if (count > 0) {
            badge.textContent = count;
            badge.style.display = 'inline';
        } else {
            badge.style.display = 'none';
        }
    }
}

// Показ toast-уведомления
function showNotificationToast(message, type = 'info') {
    // Создание toast элемента
    const toastHtml = `
        <div class="toast" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header bg-${type} text-white">
                <strong class="me-auto">Уведомление</strong>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        </div>
    `;

    // Добавление toast в контейнер
    const toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(container);
    }

    document.getElementById('toast-container').insertAdjacentHTML('beforeend', toastHtml);

    // Показ toast
    const toastElement = document.querySelector('.toast:last-child');
    const toast = new bootstrap.Toast(toastElement, { autohide: true, delay: 5000 });
    toast.show();

    // Удаление после скрытия
    toastElement.addEventListener('hidden.bs.toast', function() {
        this.remove();
    });
}

// Периодическая проверка новых уведомлений (каждые 30 секунд)
setInterval(checkNewNotifications, 30000);

// Отметить все уведомления как прочитанные
function markAllAsRead() {
    fetch('/notifications/read-all/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateNotificationBadge(0);
            showNotificationToast('Все уведомления отмечены как прочитанные', 'success');
        }
    });
}

// Отметить одно уведомление как прочитанное
function markAsRead(notificationId) {
    fetch(`/notifications/${notificationId}/read/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const element = document.getElementById(`notification-${notificationId}`);
            if (element) {
                element.classList.remove('unread');
                element.classList.add('read');
            }
            checkNewNotifications();
        }
    });
}