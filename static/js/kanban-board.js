// static/js/kanban-board.js
document.addEventListener('DOMContentLoaded', function() {
    const tasks = document.querySelectorAll('.task-card');
    const columns = document.querySelectorAll('.kanban-column');

    tasks.forEach(task => {
        task.addEventListener('dragstart', (e) => {
            e.dataTransfer.setData('text/plain', task.dataset.taskId);
            task.classList.add('dragging');
        });
        task.addEventListener('dragend', (e) => {
            task.classList.remove('dragging');
        });
    });

    columns.forEach(column => {
        column.addEventListener('dragover', (e) => {
            e.preventDefault();
        });
        column.addEventListener('drop', (e) => {
            e.preventDefault();
            const taskId = e.dataTransfer.getData('text/plain');
            const newStatus = column.dataset.status;
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value
                || document.cookie.match(/csrftoken=([^;]+)/)?.[1];

            fetch(`/tasks/${taskId}/update-status/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({ status: newStatus })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    location.reload();
                } else {
                    alert('Ошибка: ' + (data.error || 'неизвестная ошибка'));
                }
            })
            .catch(err => alert('Ошибка сети: ' + err));
        });
    });
});
