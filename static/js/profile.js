// ========== DOM элементы ==========
const menuBtns = document.querySelectorAll('.menu-btn');
const panels = {
    edit: document.getElementById('editPanel'),
    activity: document.getElementById('activityPanel'),
    settings: document.getElementById('settingsPanel')
};

// Элементы шапки
const profileNameSpan = document.getElementById('profileName');
const profileEmailSpan = document.getElementById('profileEmail');
const profilePhoneSpan = document.getElementById('profilePhone');

// Поля редактирования
const editName = document.getElementById('editName');
const editEmail = document.getElementById('editEmail');
const editPhone = document.getElementById('editPhone');
const editBirth = document.getElementById('editBirth');
const editTelegram = document.getElementById('editTelegram');
const editLinkedin = document.getElementById('editLinkedin');

// Кнопки
const saveProfileBtn = document.getElementById('saveProfileBtn');
const addActivityBtn = document.getElementById('addActivityBtn');
const clearHistoryBtn = document.getElementById('clearHistoryBtn');
const changePasswordBtn = document.getElementById('changePasswordBtn');
const logoutBtn = document.getElementById('logoutBtn');
const themeSelect = document.getElementById('themeSelect');
const notificationsCheckbox = document.getElementById('notificationsCheckbox');

// Сообщения
const saveMessage = document.getElementById('saveMessage');
const settingsMessage = document.getElementById('settingsMessage');

// Список активности
const activityList = document.getElementById('activityList');

// ========== 1. Переключение вкладок ==========
function switchTab(tabId) {
    // Скрыть все панели
    Object.values(panels).forEach(panel => {
        if (panel) panel.classList.remove('active');
    });

    // Показать выбранную панель
    const activePanel = document.getElementById(`${tabId}Panel`);
    if (activePanel) activePanel.classList.add('active');

    // Обновить активную кнопку
    menuBtns.forEach(btn => {
        btn.classList.remove('active');
        if (btn.getAttribute('data-tab') === tabId) {
            btn.classList.add('active');
        }
    });
}

// Назначить обработчики кнопкам меню
menuBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        const tabId = btn.getAttribute('data-tab');
        switchTab(tabId);
    });
});

// ========== 2. Обновление шапки профиля ==========
function updateProfileHeader(name, email, phone) {
    if (profileNameSpan) profileNameSpan.textContent = name || 'Alena Alenova';
    if (profileEmailSpan) profileEmailSpan.textContent = email || 'alena@gmail.com';
    if (profilePhoneSpan) profilePhoneSpan.textContent = phone || '89179103339';
}

// ========== 3. Добавление записи в активность ==========
function addActivityLog(message) {
    if (!activityList) return;

    const now = new Date();
    const dateStr = now.toLocaleDateString('ru-RU');
    const timeStr = now.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });

    const li = document.createElement('li');
    li.innerHTML = `🕐 ${dateStr} ${timeStr} — ${message}`;
    activityList.prepend(li);

    // Ограничим количество записей (оставляем не более 20)
    while (activityList.children.length > 20) {
        activityList.removeChild(activityList.lastChild);
    }
}

// ========== 4. Сохранение профиля ==========
if (saveProfileBtn) {
    saveProfileBtn.addEventListener('click', () => {
        const newName = editName.value.trim();
        const newEmail = editEmail.value.trim();
        const newPhone = editPhone.value.trim();
        const newBirth = editBirth.value;
        const newTelegram = editTelegram.value.trim();
        const newLinkedin = editLinkedin.value.trim();

        // Валидация
        if (!newName) {
            saveMessage.textContent = '❌ Имя не может быть пустым';
            saveMessage.className = 'message error';
            setTimeout(() => {
                saveMessage.textContent = '';
                saveMessage.className = 'message';
            }, 3000);
            return;
        }

        if (!newEmail || !newEmail.includes('@')) {
            saveMessage.textContent = '❌ Введите корректный email';
            saveMessage.className = 'message error';
            setTimeout(() => {
                saveMessage.textContent = '';
                saveMessage.className = 'message';
            }, 3000);
            return;
        }

        // Обновляем шапку
        updateProfileHeader(newName, newEmail, newPhone);

        // Сохраняем в localStorage (имитация БД)
        const userData = {
            name: newName,
            email: newEmail,
            phone: newPhone,
            birth: newBirth,
            telegram: newTelegram,
            linkedin: newLinkedin
        };
        localStorage.setItem('crm_user_data', JSON.stringify(userData));

        // Добавляем запись в активность
        addActivityLog('Профиль обновлён');

        // Показываем сообщение об успехе
        saveMessage.textContent = '✅ Профиль успешно обновлён!';
        saveMessage.className = 'message success';
        setTimeout(() => {
            saveMessage.textContent = '';
            saveMessage.className = 'message';
        }, 3000);
    });
}

// ========== 5. Загрузка сохранённых данных профиля ==========
function loadSavedProfileData() {
    const savedData = localStorage.getItem('crm_user_data');
    if (savedData) {
        try {
            const data = JSON.parse(savedData);
            if (editName) editName.value = data.name || 'Alena Alenova';
            if (editEmail) editEmail.value = data.email || 'alena@gmail.com';
            if (editPhone) editPhone.value = data.phone || '89179103339';
            if (editBirth) editBirth.value = data.birth || '1990-01-01';
            if (editTelegram) editTelegram.value = data.telegram || '';
            if (editLinkedin) editLinkedin.value = data.linkedin || '';

            // Обновляем шапку
            updateProfileHeader(data.name, data.email, data.phone);
        } catch(e) {
            console.error('Ошибка загрузки данных:', e);
        }
    }
}

// ========== 6. Добавление тестовой активности ==========
if (addActivityBtn) {
    addActivityBtn.addEventListener('click', () => {
        addActivityLog('Просмотр раздела "Моя активность"');
    });
}

// ========== 7. Очистка истории активности ==========
if (clearHistoryBtn) {
    clearHistoryBtn.addEventListener('click', () => {
        if (activityList) {
            activityList.innerHTML = '<li>🗑️ История активности очищена</li>';
            addActivityLog('История активности очищена');

            if (settingsMessage) {
                settingsMessage.textContent = '✅ История активности очищена';
                settingsMessage.className = 'message success';
                setTimeout(() => {
                    settingsMessage.textContent = '';
                    settingsMessage.className = 'message';
                }, 2000);
            }
        }
    });
}

// ========== 8. Смена пароля ==========
if (changePasswordBtn) {
    changePasswordBtn.addEventListener('click', () => {
        const newPassword = document.getElementById('newPassword');
        if (!newPassword) return;

        const password = newPassword.value.trim();

        if (password.length < 4) {
            if (settingsMessage) {
                settingsMessage.textContent = '❌ Пароль должен быть минимум 4 символа';
                settingsMessage.className = 'message error';
                setTimeout(() => {
                    settingsMessage.textContent = '';
                    settingsMessage.className = 'message';
                }, 3000);
            }
            return;
        }

        // Сохраняем пароль (в реальном проекте - хешируем и отправляем на сервер)
        localStorage.setItem('crm_password', btoa(password));

        if (settingsMessage) {
            settingsMessage.textContent = '✅ Пароль успешно изменён';
            settingsMessage.className = 'message success';
            setTimeout(() => {
                settingsMessage.textContent = '';
                settingsMessage.className = 'message';
            }, 3000);
        }

        newPassword.value = '';
        addActivityLog('Пароль изменён');
    });
}

// ========== 9. Тема оформления ==========
function loadTheme() {
    const savedTheme = localStorage.getItem('crm_theme');
    if (savedTheme === 'dark') {
        document.body.classList.add('dark-theme');
        if (themeSelect) themeSelect.value = 'dark';
    } else {
        document.body.classList.remove('dark-theme');
        if (themeSelect) themeSelect.value = 'light';
    }
}

if (themeSelect) {
    themeSelect.addEventListener('change', (e) => {
        const theme = e.target.value;
        if (theme === 'dark') {
            document.body.classList.add('dark-theme');
            localStorage.setItem('crm_theme', 'dark');
        } else {
            document.body.classList.remove('dark-theme');
            localStorage.setItem('crm_theme', 'light');
        }
    });
}

// ========== 10. Уведомления ==========
function loadNotificationsSetting() {
    const savedSetting = localStorage.getItem('crm_notifications');
    if (savedSetting !== null && notificationsCheckbox) {
        notificationsCheckbox.checked = savedSetting === 'true';
    }
}

if (notificationsCheckbox) {
    notificationsCheckbox.addEventListener('change', (e) => {
        const isChecked = e.target.checked;
        localStorage.setItem('crm_notifications', isChecked);

        if (isChecked) {
            console.log('🔔 Уведомления включены');
        } else {
            console.log('🔕 Уведомления выключены');
        }
    });
}

// ========== 11. ВЫХОД НА ГЛАВНУЮ ==========
function logout() {
    // Очищаем сессионные данные
    localStorage.removeItem('crm_logged_in');
    sessionStorage.clear();

    // Добавляем запись в лог (опционально)
    console.log('Пользователь вышел из системы:', new Date().toLocaleString());

    // Показываем сообщение
    alert('Вы вышли из профиля. Перенаправление на главную страницу...');

    // Редирект на указанный адрес
    window.location.href = 'http://127.0.0.1:8000/';
}

if (logoutBtn) {
    logoutBtn.addEventListener('click', logout);
}

// ========== 12. Аватар (обработка выбора файла) ==========
const avatarInput = document.getElementById('editAvatar');
if (avatarInput) {
    avatarInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            if (file.size > 5 * 1024 * 1024) {
                alert('Файл слишком большой. Максимальный размер 5MB');
                avatarInput.value = '';
                return;
            }

            const reader = new FileReader();
            reader.onload = function(event) {
                localStorage.setItem('crm_avatar', event.target.result);
                addActivityLog('Аватар обновлён');
                alert('Аватар успешно загружен!');
            };
            reader.readAsDataURL(file);
        }
    });
}

// ========== 13. Загрузка сохранённого аватара ==========
function loadSavedAvatar() {
    const savedAvatar = localStorage.getItem('crm_avatar');
    if (savedAvatar) {
        // Можно отобразить аватар в шапке, если добавить элемент
        console.log('Сохранённый аватар загружен');
    }
}

// ========== 14. Инициализация при загрузке страницы ==========
document.addEventListener('DOMContentLoaded', () => {
    loadSavedProfileData();
    loadTheme();
    loadNotificationsSetting();
    loadSavedAvatar();

    // Добавляем запись о входе в активность
    addActivityLog('Вход в профиль');

    console.log('CRM Профиль загружен');
});