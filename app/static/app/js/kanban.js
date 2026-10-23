/* Focal Point — Kanban drag-and-drop, task creation, filters, mobile menu */

(function () {
    let draggedTaskId = null;

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

    function updateTaskUrl(taskId) {
        const board = document.querySelector('.kanban');
        if (!board) return null;
        const base = board.dataset.taskUpdateUrl || '/boards/tasks/0/update/';
        // base looks like /boards/tasks/0/update/; swap the 0 for the real task id
        return base.replace('/0/', `/${taskId}/`);
    }

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

        // Persist via AJAX
        const updateUrl = updateTaskUrl(taskId);
        if (!updateUrl) return;
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

    function attachDragDrop() {
        // Column drop zones
        document.querySelectorAll('.column').forEach((column) => {
            column.addEventListener('dragover', onDragOver);
            column.addEventListener('dragenter', onDragEnter);
            column.addEventListener('dragleave', onDragLeave);
            column.addEventListener('drop', onDrop);
        });
        // Task cards
        document.querySelectorAll('.task-card.draggable').forEach((card) => {
            card.setAttribute('draggable', 'true');
            card.addEventListener('dragstart', onDragStart);
        });
    }

    function setTaskModal(mode, ticket) {
        const editing = mode === 'edit';
        document.getElementById('task-modal-title').textContent = editing ? `Edit ${ticket}` : 'Create task';
        document.getElementById('task-submit').textContent = editing ? 'Save changes' : 'Create task';
    }

    function showTaskModal() {
        document.getElementById('task-modal').style.display = 'flex';
        document.getElementById('modal-title').focus();
    }

    function openTaskModal(columnId) {
        const form = document.getElementById('task-form');
        form.reset();
        form.action = form.dataset.createAction;
        const select = document.getElementById('modal-column');
        const firstColumn = document.querySelector('.column');
        select.value = columnId || (firstColumn ? firstColumn.dataset.columnId : '');
        setTaskModal('create');
        showTaskModal();
    }

    function openTaskEdit(card) {
        const board = document.querySelector('.kanban');
        const form = document.getElementById('task-form');
        form.reset();
        form.action = board.dataset.taskEditUrl.replace('/0/', `/${card.dataset.taskId}/`);
        document.getElementById('modal-title').value = card.dataset.title;
        document.getElementById('modal-desc').value = card.dataset.description;
        document.getElementById('modal-priority').value = card.dataset.priority;
        document.getElementById('modal-assignee').value = card.dataset.assignee;
        document.getElementById('modal-column').value = card.closest('.column').dataset.columnId;
        document.getElementById('modal-category').value = card.dataset.category;
        setTaskModal('edit', card.dataset.ticket);
        showTaskModal();
    }

    function closeTaskModal() {
        const modal = document.getElementById('task-modal');
        if (modal) modal.style.display = 'none';
    }

    // ----- Categories -----
    function resetCategoryForm() {
        const form = document.getElementById('category-form');
        form.reset();
        form.querySelectorAll('.swatch--custom').forEach((el) => el.remove());
        form.action = form.dataset.createAction;
        document.getElementById('category-form-title').textContent = 'New category';
        document.getElementById('category-submit').textContent = 'Add category';
        document.getElementById('category-cancel-edit').hidden = true;
    }

    function openCategoryModal() {
        resetCategoryForm();
        document.getElementById('category-modal').style.display = 'flex';
        document.getElementById('category-name').focus();
    }

    function closeCategoryModal() {
        const modal = document.getElementById('category-modal');
        if (modal) modal.style.display = 'none';
    }

    function editCategory(row) {
        const modal = document.getElementById('category-modal');
        const form = document.getElementById('category-form');
        resetCategoryForm();
        form.action = modal.dataset.editUrl.replace('/0/', `/${row.dataset.categoryId}/`);
        document.getElementById('category-name').value = row.dataset.name;

        const color = row.dataset.color;
        let radio = Array.from(form.querySelectorAll('input[name="color"]')).find(
            (r) => r.value.toLowerCase() === color.toLowerCase()
        );
        if (!radio) {
            const label = document.createElement('label');
            label.className = 'swatch swatch--custom';
            label.title = 'Current color';
            label.innerHTML = '<input type="radio" name="color"><span></span>';
            radio = label.querySelector('input');
            radio.value = color;
            label.querySelector('span').style.backgroundColor = color;
            form.querySelector('.swatches').prepend(label);
        }
        radio.checked = true;

        document.getElementById('category-form-title').textContent = 'Edit category';
        document.getElementById('category-submit').textContent = 'Save changes';
        document.getElementById('category-cancel-edit').hidden = false;
        document.getElementById('category-name').focus();
    }

    function openColumnModal(columnId) {
        const form = document.getElementById('column-form');
        const del = document.getElementById('column-delete');
        const delForm = document.getElementById('column-delete-form');
        form.reset();
        // Drop a stray swatch added for a previous column's custom colour
        form.querySelectorAll('.swatch--custom').forEach((el) => el.remove());

        if (columnId) {
            const board = document.querySelector('.kanban');
            const column = document.querySelector(`.column[data-column-id="${columnId}"]`);
            form.action = board.dataset.columnEditUrl.replace('/0/', `/${columnId}/`);
            document.getElementById('column-name').value = column.dataset.columnName;

            // Columns made before colour swatches existed may use a colour not in the palette
            const color = column.dataset.columnColor;
            let radio = Array.from(form.querySelectorAll('input[name="color"]')).find(
                (r) => r.value.toLowerCase() === color.toLowerCase()
            );
            if (!radio) {
                const label = document.createElement('label');
                label.className = 'swatch swatch--custom';
                label.title = 'Current color';
                label.innerHTML = '<input type="radio" name="color"><span></span>';
                radio = label.querySelector('input');
                radio.value = color;
                label.querySelector('span').style.backgroundColor = color;
                form.querySelector('.swatches').prepend(label);
            }
            radio.checked = true;

            delForm.action = board.dataset.columnDeleteUrl.replace('/0/', `/${columnId}/`);
            const count = parseInt(column.dataset.taskCount, 10) || 0;
            delForm.dataset.confirm = count
                ? `Delete "${column.dataset.columnName}" and its ${count} task${count === 1 ? '' : 's'}?`
                : `Delete "${column.dataset.columnName}"?`;
            del.hidden = false;
            document.getElementById('column-modal-title').textContent = 'Edit column';
            document.getElementById('column-submit').textContent = 'Save changes';
        } else {
            form.action = form.dataset.createAction;
            del.hidden = true;
            document.getElementById('column-modal-title').textContent = 'Add column';
            document.getElementById('column-submit').textContent = 'Add column';
        }
        document.getElementById('column-modal').style.display = 'flex';
        document.getElementById('column-name').focus();
    }

    function closeColumnModal() {
        const modal = document.getElementById('column-modal');
        if (modal) modal.style.display = 'none';
    }

    // Confirm before a column (and its tasks) is deleted
    const columnDeleteForm = document.getElementById('column-delete-form');
    if (columnDeleteForm) {
        columnDeleteForm.addEventListener('submit', (e) => {
            if (!confirm(columnDeleteForm.dataset.confirm || 'Delete this column?')) e.preventDefault();
        });
    }

    // ----- Task view (read-only) -----
    let viewedCard = null;

    function openTaskView(card) {
        viewedCard = card;
        const column = card.closest('.column');
        const d = card.dataset;

        document.getElementById('view-ticket').textContent = d.ticket;
        document.getElementById('view-title').textContent = d.title;

        const status = document.getElementById('view-status');
        status.textContent = '';
        const badge = document.createElement('span');
        badge.className = 'stage-badge';
        badge.textContent = column.dataset.columnName;
        badge.style.backgroundColor = column.dataset.columnColor;
        status.appendChild(badge);

        const priority = document.getElementById('view-priority');
        priority.textContent = '';
        const tag = document.createElement('span');
        tag.className = `tag tag--${d.priority}`;
        tag.innerHTML = '<span class="bars" aria-hidden="true"><i></i><i></i><i></i><i></i></span>';
        tag.appendChild(document.createTextNode(d.priorityLabel));
        priority.appendChild(tag);

        const category = document.getElementById('view-category');
        category.textContent = '';
        if (d.categoryName) {
            const chip = document.createElement('span');
            chip.className = 'chip';
            chip.textContent = d.categoryName;
            chip.style.backgroundColor = d.categoryColor;
            category.appendChild(chip);
        } else {
            category.textContent = 'None';
            category.classList.add('is-empty');
        }
        category.classList.toggle('is-empty', !d.categoryName);

        const assignee = document.getElementById('view-assignee');
        assignee.textContent = '';
        assignee.classList.toggle('is-empty', !d.assigneeName);
        if (d.assigneeName) {
            const avatar = document.createElement('span');
            avatar.className = 'avatar avatar--sm';
            avatar.textContent = d.assigneeName.charAt(0).toUpperCase();
            assignee.appendChild(avatar);
            assignee.appendChild(document.createTextNode(d.assigneeName));
        } else {
            assignee.textContent = 'Unassigned';
        }

        document.getElementById('view-created').textContent = d.created;

        const desc = document.getElementById('view-desc');
        desc.textContent = d.description || 'No description';
        desc.classList.toggle('is-empty', !d.description);

        document.getElementById('view-modal').style.display = 'flex';
        document.getElementById('view-edit').focus();
    }

    function closeTaskView() {
        const modal = document.getElementById('view-modal');
        if (modal) modal.style.display = 'none';
        viewedCard = null;
    }

    const viewEdit = document.getElementById('view-edit');
    if (viewEdit) {
        viewEdit.addEventListener('click', () => {
            const card = viewedCard;
            closeTaskView();
            if (card) openTaskEdit(card);
        });
    }

    // Clicking a card (not its buttons) opens the read-only view
    document.addEventListener('click', (e) => {
        const card = e.target.closest('.task-card');
        if (!card || e.target.closest('button, form, a')) return;
        openTaskView(card);
    });

    // Expose for inline onclick handlers in templates
    window.openTaskModal = openTaskModal;
    window.openTaskEdit = openTaskEdit;
    window.openTaskView = openTaskView;
    window.closeTaskView = closeTaskView;
    window.closeTaskModal = closeTaskModal;
    window.openCategoryModal = openCategoryModal;
    window.closeCategoryModal = closeCategoryModal;
    window.editCategory = editCategory;
    window.resetCategoryForm = resetCategoryForm;
    window.openColumnModal = openColumnModal;
    window.closeColumnModal = closeColumnModal;

    // Clicking outside the panel closes the modal
    const modal = document.getElementById('task-modal');
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target.id === 'task-modal') closeTaskModal();
        });
    }

    // Client-side search + priority filter
    function setupFilters() {
        const search = document.getElementById('task-search');
        const priority = document.getElementById('priority-filter');
        const category = document.getElementById('category-filter');
        if (!search || !priority) return;

        function apply() {
            const q = search.value.trim().toLowerCase();
            const p = priority.value;
            const c = category ? category.value : '';
            document.querySelectorAll('.task-card').forEach((card) => {
                const matchesText = !q || card.textContent.toLowerCase().includes(q);
                const matchesPriority = !p || card.dataset.priority === p;
                const matchesCategory = !c || card.dataset.category === c;
                card.hidden = !(matchesText && matchesPriority && matchesCategory);
            });
        }
        search.addEventListener('input', apply);
        priority.addEventListener('change', apply);
        if (category) category.addEventListener('change', apply);
    }

    // Sidebar toggle on narrow screens
    function setupMenu() {
        const app = document.getElementById('app');
        const btn = document.getElementById('menu-btn');
        const scrim = document.getElementById('scrim');
        if (!app || !btn) return;
        btn.addEventListener('click', () => app.classList.toggle('sidebar-open'));
        if (scrim) scrim.addEventListener('click', () => app.classList.remove('sidebar-open'));
    }

    // Escape closes whichever dialog is open
    document.addEventListener('keydown', (e) => {
        if (e.key !== 'Escape') return;
        closeTaskView();
        closeTaskModal();
        closeColumnModal();
        closeCategoryModal();
    });

    // Wire up drag-and-drop once the DOM is ready
    function init() {
        attachDragDrop();
        setupFilters();
        setupMenu();
    }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    // Re-wire after any dynamic re-render (e.g. new task added)
    window.__focalpointAttachDragDrop = attachDragDrop;
})();
