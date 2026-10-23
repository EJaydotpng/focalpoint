/* Focal Point — Kanban drag-and-drop + task creation */

(function () {
    let draggedTaskId = null;

    function onDragStart(e) {
        draggedTaskId = e.target.dataset.taskId;
        e.target.classList.add('dragging');
        e.dataTransfer.setData('text/plain', draggedTaskId);
        e.dataTransfer.effectAllowed = 'move';
    }

    function onDragOver(e) {
        e.preventDefault();
        e.currentTarget.classList.add('drag-over');
    }

    function onDragEnter(e) {
        e.preventDefault();
    }

    function onDragLeave(e) {
        e.currentTarget.classList.remove('drag-over');
    }

    function onDrop(e) {
        e.preventDefault();
        const column = e.currentTarget;
        column.classList.remove('drag-over');

        const taskId = e.dataTransfer.getData('text/plain');
        if (!taskId) return;

        const taskEl = document.querySelector(`[data-task-id="${taskId}"]`);
        if (!taskEl) return;
        taskEl.classList.remove('dragging');

        // Determine position by where the card was dropped among siblings
        const body = column.querySelector('.column-body');
        const cards = Array.from(body.querySelectorAll('.task-card')).filter(
            (c) => c.dataset.taskId !== taskId
        );
        const insertAt = cards.findIndex((c) => {
            const rect = c.getBoundingClientRect();
            return e.clientY < rect.top + rect.height / 2;
        });
        const position = insertAt === -1 ? cards.length : insertAt;

        // Move element visually right away for responsiveness
        if (insertAt === -1) {
            body.appendChild(taskEl);
        } else {
            cards[insertAt].parentNode.insertBefore(taskEl, cards[insertAt]);
        }

        // Persist via AJAX to task-update
        const updateUrl = `{% url 'task-update' 0 %}`.replace('/0/', `/${taskId}/`);
        fetch(updateUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            body: `column=${encodeURIComponent(column.dataset.columnId)}&position=${encodeURIComponent(position)}`,
            credentials: 'same-origin',
        })
            .then((r) => {
                if (!r.ok) {
                    alert('Failed to move task.');
                }
            })
            .catch(() => alert('Failed to move task.'));
    }

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === name + '=') {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    function openTaskModal(columnId) {
        const modal = document.getElementById('task-modal');
        const input = document.getElementById('modal-column');
        if (columnId) {
            input.value = columnId;
        } else {
            const firstColumn = document.querySelector('.column');
            input.value = firstColumn ? firstColumn.dataset.columnId : '';
        }
        modal.style.display = 'flex';
    }

    function closeTaskModal() {
        document.getElementById('task-modal').style.display = 'none';
    }

    // Expose inline handlers used by templates (kept minimal)
    window.onDragStart = onDragStart;
    window.onDragOver = onDragOver;
    window.onDragEnter = onDragEnter;
    window.onDragLeave = onDragLeave;
    window.onDrop = onDrop;
    window.openTaskModal = openTaskModal;
    window.closeTaskModal = closeTaskModal;

    // Clicking outside the panel closes the modal
    const modal = document.getElementById('task-modal');
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target.id === 'task-modal') closeTaskModal();
        });
    }
})();
