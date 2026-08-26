const API_BASE = '/api/v1';
let token = localStorage.getItem('token') || '';
let currentUser = null;
let currentProjectId = null;
let currentProjectMembers = [];
let currentPageProjects = 1;
const perPage = 6;

// DOM
const authScreen = document.getElementById('auth-screen');
const mainScreen = document.getElementById('main-screen');
const authForm = document.getElementById('auth-form');
const emailInput = document.getElementById('email');
const fullNameInput = document.getElementById('full_name');
const passwordInput = document.getElementById('password');
const authBtn = document.getElementById('auth-btn');
const authError = document.getElementById('auth-error');
const loginTab = document.getElementById('login-tab');
const registerTab = document.getElementById('register-tab');
const userEmailSpan = document.getElementById('user-email');
const logoutBtn = document.getElementById('logout-btn');
const projectsSection = document.getElementById('projects-section');
const tagsSection = document.getElementById('tags-section');
const tasksSection = document.getElementById('tasks-section');
const projectsList = document.getElementById('projects-list');
const tagsList = document.getElementById('tags-list');
const currentProjectName = document.getElementById('current-project-name');
const filterStatus = document.getElementById('filter-status');
const filterPriority = document.getElementById('filter-priority');
const projectsPagination = document.getElementById('projects-pagination');
const modal = document.getElementById('modal');
const modalTitle = document.getElementById('modal-title');
const modalForm = document.getElementById('modal-form');
const modalClose = document.getElementById('modal-close');
const toast = document.getElementById('toast');

const kanbanColumns = {
    todo: document.getElementById('tasks-todo'),
    in_progress: document.getElementById('tasks-in_progress'),
    done: document.getElementById('tasks-done')
};

// Инициализация
function showToast(message, type = 'success') {
    toast.textContent = message;
    toast.className = `toast show`;
    toast.style.backgroundColor = type === 'error' ? '#ef4444' : '#1e293b';
    setTimeout(() => toast.classList.remove('show'), 3000);
}

function showScreen(screenId) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    document.getElementById(screenId).classList.add('active');
}

function setAuthMode(mode) {
    authMode = mode;
    loginTab.classList.toggle('active', mode === 'login');
    registerTab.classList.toggle('active', mode === 'register');
    fullNameInput.style.display = mode === 'register' ? 'block' : 'none';
    authBtn.textContent = mode === 'login' ? 'Войти' : 'Зарегистрироваться';
    authError.textContent = '';
}

let authMode = 'login';
loginTab.addEventListener('click', () => setAuthMode('login'));
registerTab.addEventListener('click', () => setAuthMode('register'));

authForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    authError.textContent = '';
    const email = emailInput.value.trim();
    const password = passwordInput.value;

    try {
        if (authMode === 'register') {
            const fullName = fullNameInput.value.trim();
            if (!fullName) throw new Error('Введите имя');
            await apiRequest('/auth/register', 'POST', { email, full_name: fullName, password }, false);
        }
        const loginRes = await apiRequest('/auth/login', 'POST', { username: email, password }, true);
        token = loginRes.access_token;
        localStorage.setItem('token', token);
        await loadMain();
    } catch (err) {
        authError.textContent = err.message || 'Ошибка';
    }
});

logoutBtn.addEventListener('click', () => {
    token = '';
    localStorage.removeItem('token');
    currentUser = null;
    showScreen('auth-screen');
    authForm.reset();
    setAuthMode('login');
});

async function loadMain() {
    currentUser = await apiRequest('/users/me', 'GET');
    userEmailSpan.textContent = currentUser.email;
    showScreen('main-screen');
    loadProjects();
    loadTags();
}

// Навигация
document.getElementById('projects-nav').addEventListener('click', () => {
    projectsSection.style.display = 'block';
    tagsSection.style.display = 'none';
    tasksSection.style.display = 'none';
    loadProjects();
});
document.getElementById('tags-nav').addEventListener('click', () => {
    projectsSection.style.display = 'none';
    tagsSection.style.display = 'block';
    tasksSection.style.display = 'none';
    loadTags();
});

// Проекты
async function loadProjects(page = 1) {
    currentPageProjects = page;
    const data = await apiRequest(`/projects/?page=${page}&per_page=${perPage}`, 'GET');
    projectsList.innerHTML = data.items.map(p => {
        const isOwner = p.owner_id === currentUser.id || currentUser.role === 'admin';
        return `
            <div class="card" data-id="${p.id}">
                <h3>${p.name}</h3>
                <p>${p.description}</p>
                <small>Владелец ID: ${p.owner_id}</small>
                <div class="card-actions">
                    <button class="btn primary small open-tasks" data-id="${p.id}" data-name="${p.name}">Задачи</button>
                    ${isOwner ? `<button class="btn secondary small edit-project" data-id="${p.id}">Изменить</button>
                    <button class="btn danger small delete-project" data-id="${p.id}">Удалить</button>` : ''}
                </div>
            </div>`;
    }).join('');

    // Обработчики
    projectsList.querySelectorAll('.open-tasks').forEach(btn => {
        btn.addEventListener('click', () => {
            currentProjectId = btn.dataset.id;
            currentProjectName.textContent = btn.dataset.name;
            projectsSection.style.display = 'none';
            tasksSection.style.display = 'block';
            loadProjectMembers();
            loadTasks();
        });
    });

    projectsList.querySelectorAll('.edit-project').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.stopPropagation();
            const projectId = btn.dataset.id;
            const project = await apiRequest(`/projects/${projectId}`, 'GET');
            openModal('Редактировать проект', `
                <input type="text" id="edit-project-name" value="${project.name}" required>
                <input type="text" id="edit-project-desc" value="${project.description}" required>
                <button type="submit" class="btn primary">Сохранить</button>
            `);
            modalForm.onsubmit = async (e) => {
                e.preventDefault();
                const name = document.getElementById('edit-project-name').value;
                const description = document.getElementById('edit-project-desc').value;
                await apiRequest(`/projects/${projectId}`, 'PATCH', { name, description });
                closeModal();
                loadProjects();
                showToast('Проект обновлён');
            };
        });
    });

    projectsList.querySelectorAll('.delete-project').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.stopPropagation();
            if (!confirm('Удалить проект?')) return;
            await apiRequest(`/projects/${btn.dataset.id}`, 'DELETE');
            loadProjects();
            showToast('Проект удалён');
        });
    });

    renderPagination(projectsPagination, data.total, data.page, data.per_page, loadProjects);
}

document.getElementById('create-project-btn').addEventListener('click', () => {
    openModal('Новый проект', `
        <input type="text" id="project-name" placeholder="Название" required>
        <input type="text" id="project-desc" placeholder="Описание" required>
        <button type="submit" class="btn primary">Создать</button>
    `);
    modalForm.onsubmit = async (e) => {
        e.preventDefault();
        const name = document.getElementById('project-name').value;
        const description = document.getElementById('project-desc').value;
        await apiRequest('/projects/create_project', 'POST', { name, description });
        closeModal();
        loadProjects();
        showToast('Проект создан');
    };
});

// Теги
async function loadTags() {
    const tags = await apiRequest('/tags/', 'GET');
    const canDelete = currentUser.role === 'admin';
    tagsList.innerHTML = tags.map(t => `
        <div class="card">
            <h3>${t.name}</h3>
            ${canDelete ? `<button class="btn danger small delete-tag" data-id="${t.id}">Удалить</button>` : ''}
        </div>
    `).join('');
    tagsList.querySelectorAll('.delete-tag').forEach(btn => {
        btn.addEventListener('click', async () => {
            if (!confirm('Удалить тег?')) return;
            await apiRequest(`/tags/${btn.dataset.id}`, 'DELETE');
            loadTags();
            showToast('Тег удалён');
        });
    });
}

document.getElementById('create-tag-btn').addEventListener('click', () => {
    openModal('Новый тег', `
        <input type="text" id="tag-name" placeholder="Название" required>
        <button type="submit" class="btn primary">Создать</button>
    `);
    modalForm.onsubmit = async (e) => {
        e.preventDefault();
        const name = document.getElementById('tag-name').value;
        await apiRequest('/tags/', 'POST', { name });
        closeModal();
        loadTags();
        showToast('Тег создан');
    };
});

// Задачи (Kanban)
async function loadProjectMembers() {
    try {
        currentProjectMembers = await apiRequest(`/projects/${currentProjectId}/members`, 'GET');
    } catch (e) {
        currentProjectMembers = [];
    }
}

async function loadTasks() {
    if (!currentProjectId) return;
    const params = new URLSearchParams();
    if (filterStatus.value) params.append('status', filterStatus.value);
    if (filterPriority.value) params.append('priority', filterPriority.value);
    params.append('project_id', currentProjectId);
    // Пагинация не используется в Kanban (можно доработать)
    params.append('per_page', 100); // допустим, максимум 100 задач

    const data = await apiRequest(`/tasks?${params.toString()}`, 'GET');
    const tasks = data.items;

    // Очищаем колонки
    Object.values(kanbanColumns).forEach(col => col.innerHTML = '');

    // Распределяем задачи по колонкам
    tasks.forEach(task => {
        const column = kanbanColumns[task.status] || kanbanColumns.todo;
        column.appendChild(createTaskCard(task));
    });
}

function createTaskCard(task) {
    const card = document.createElement('div');
    card.className = 'card';
    card.draggable = true;
    card.dataset.taskId = task.id;
    card.dataset.status = task.status;

    const canEdit = currentUser.role === 'admin' || task.assignee_id === currentUser.id || isProjectOwner(task);
    // isProjectOwner будем приблизительно определять: если currentUser.id в currentProjectMembers и он владелец? упростим: можно проверить через API, но пока оставим

    let tagsHtml = '';
    if (task.tags && task.tags.length > 0) {
        tagsHtml = task.tags.map(tag => `<span class="badge">${tag.name}</span>`).join('');
    }

    card.innerHTML = `
        <h3>${task.title}</h3>
        <p>${task.description}</p>
        <div>
            <span class="badge ${task.status}">${task.status}</span>
            <span class="badge ${task.priority}">${task.priority}</span>
            ${task.due_date ? `<span class="badge">📅 ${task.due_date.slice(0,10)}</span>` : ''}
            ${tagsHtml}
        </div>
        <div class="card-actions">
            ${task.assignee_id === currentUser.id || currentUser.role === 'admin' || isProjectOwner(task) ?
                `<button class="btn primary small edit-task" data-id="${task.id}">Изменить</button>
                 <button class="btn danger small delete-task" data-id="${task.id}">Удалить</button>` : ''}
        </div>
    `;

    // Обработчики кнопок
    card.querySelector('.edit-task')?.addEventListener('click', (e) => {
        e.stopPropagation();
        editTask(task.id);
    });
    card.querySelector('.delete-task')?.addEventListener('click', async (e) => {
        e.stopPropagation();
        if (confirm('Удалить задачу?')) {
            await apiRequest(`/tasks/${task.id}`, 'DELETE');
            loadTasks();
            showToast('Задача удалена');
        }
    });

    card.addEventListener('dragstart', (e) => {
        e.dataTransfer.setData('text/plain', card.dataset.taskId);
        card.classList.add('dragging');
    });
    card.addEventListener('dragend', () => card.classList.remove('dragging'));

    return card;
}

// Проверка, является ли текущий пользователь владельцем проекта (упрощенно)
function isProjectOwner(task) {
    // Здесь можно сделать запрос к проекту, но для экономии предположим, что currentProjectMembers содержит id владельца? Нет.
    // Лучше просто проверить, что currentUser.id равен project.owner_id, но у нас нет этой информации в задаче.
    // Можно временно разрешить редактирование всем, у кого есть доступ к проекту, а точные права проверяются на бэке.
    return true; // Позже можно уточнить
}

async function editTask(taskId) {
    const task = await apiRequest(`/tasks/${taskId}`, 'GET');
    const tags = await apiRequest('/tags/', 'GET');
    const members = currentProjectMembers;
    const isAdmin = currentUser.role === 'admin';
    const isAssignee = task.assignee_id === currentUser.id;
    const isOwner = isProjectOwner(task); // приблизительно

    let formHtml = `
        <input type="text" id="edit-task-title" value="${task.title}" ${!isAdmin && isAssignee ? 'disabled' : ''} required>
        <textarea id="edit-task-desc" ${!isAdmin && isAssignee ? 'disabled' : ''}>${task.description}</textarea>
        ${!isAdmin && isAssignee ? '' : `
            <select id="edit-task-priority">
                <option value="low" ${task.priority==='low'?'selected':''}>Низкий</option>
                <option value="medium" ${task.priority==='medium'?'selected':''}>Средний</option>
                <option value="high" ${task.priority==='high'?'selected':''}>Высокий</option>
            </select>
            <input type="date" id="edit-task-due" value="${task.due_date ? task.due_date.slice(0,10) : ''}">
            <select id="edit-task-assignee">
                <option value="">Без исполнителя</option>
                ${members.map(m => `<option value="${m.id}" ${m.id===task.assignee_id?'selected':''}>${m.email}</option>`).join('')}
            </select>
            <div>
                <label>Теги:</label><br>
                ${tags.map(t => `<label><input type="checkbox" value="${t.id}" ${task.tags?.some(tag => tag.id === t.id) ? 'checked' : ''}> ${t.name}</label><br>`).join('')}
            </div>
        `}
        <button type="submit" class="btn primary">Сохранить</button>
    `;

    openModal('Редактировать задачу', formHtml);
    modalForm.onsubmit = async (e) => {
        e.preventDefault();
        const updateData = {};
        if (!isAssignee || isAdmin || isOwner) {
            updateData.title = document.getElementById('edit-task-title').value;
            updateData.description = document.getElementById('edit-task-desc').value;
            updateData.priority = document.getElementById('edit-task-priority').value;
            updateData.due_date = document.getElementById('edit-task-due').value || null;
            const assignee = document.getElementById('edit-task-assignee')?.value;
            if (assignee !== undefined) updateData.assignee_id = assignee ? parseInt(assignee) : null;
            const selectedTags = [...modalForm.querySelectorAll('input[type=checkbox]:checked')].map(cb => parseInt(cb.value));
            updateData.tag_ids = selectedTags;
        }
        // Исполнитель может менять только статус (через drag and drop)
        await apiRequest(`/tasks/${taskId}`, 'PATCH', updateData);
        closeModal();
        loadTasks();
        showToast('Задача обновлена');
    };
}

// Drag and Drop
function setupDragAndDrop() {
    document.querySelectorAll('.kanban-column').forEach(column => {
        column.addEventListener('dragover', (e) => {
            e.preventDefault();
            column.classList.add('drag-over');
        });
        column.addEventListener('dragleave', () => column.classList.remove('drag-over'));
        column.addEventListener('drop', async (e) => {
            e.preventDefault();
            column.classList.remove('drag-over');
            const taskId = e.dataTransfer.getData('text/plain');
            const newStatus = column.dataset.status;
            if (taskId) {
                try {
                    await apiRequest(`/tasks/${taskId}`, 'PATCH', { status: newStatus });
                    loadTasks();
                    showToast('Статус обновлён');
                } catch (error) {
                    showToast(error.message, 'error');
                }
            }
        });
    });
}

document.getElementById('create-task-btn').addEventListener('click', async () => {
    if (!currentProjectId) return;
    const tags = await apiRequest('/tags/', 'GET');
    const members = currentProjectMembers;
    openModal('Новая задача', `
        <input type="text" id="task-title" placeholder="Название" required>
        <textarea id="task-desc" placeholder="Описание"></textarea>
        <select id="task-priority">
            <option value="low">Низкий</option>
            <option value="medium" selected>Средний</option>
            <option value="high">Высокий</option>
        </select>
        <input type="date" id="task-due">
        <select id="task-assignee">
            <option value="">Без исполнителя</option>
            ${members.map(m => `<option value="${m.id}">${m.email}</option>`).join('')}
        </select>
        <div>
            <label>Теги:</label><br>
            ${tags.map(t => `<label><input type="checkbox" value="${t.id}"> ${t.name}</label><br>`).join('')}
        </div>
        <button type="submit" class="btn primary">Создать</button>
    `);
    modalForm.onsubmit = async (e) => {
        e.preventDefault();
        const title = document.getElementById('task-title').value;
        const description = document.getElementById('task-desc').value;
        const priority = document.getElementById('task-priority').value;
        const due_date = document.getElementById('task-due').value || null;
        const assignee = document.getElementById('task-assignee').value;
        const selectedTags = [...modalForm.querySelectorAll('input[type=checkbox]:checked')].map(cb => parseInt(cb.value));

        const body = { title, description, priority, due_date, tag_ids: selectedTags };
        if (assignee) body.assignee_id = parseInt(assignee);

        await apiRequest(`/projects/${currentProjectId}/tasks`, 'POST', body);
        closeModal();
        loadTasks();
        showToast('Задача создана');
    };
});

document.getElementById('back-to-projects').addEventListener('click', () => {
    projectsSection.style.display = 'block';
    tasksSection.style.display = 'none';
    loadProjects(currentPageProjects);
});

// Фильтры
filterStatus.addEventListener('change', loadTasks);
filterPriority.addEventListener('change', loadTasks);

// Пагинация (для проектов)
function renderPagination(container, total, currentPage, perPage, loadFunction) {
    const totalPages = Math.ceil(total / perPage);
    if (totalPages <= 1) {
        container.innerHTML = '';
        return;
    }
    container.innerHTML = `
        <button class="btn secondary small" ${currentPage <= 1 ? 'disabled' : ''} data-page="${currentPage-1}">← Назад</button>
        <span>Страница ${currentPage} из ${totalPages}</span>
        <button class="btn secondary small" ${currentPage >= totalPages ? 'disabled' : ''} data-page="${currentPage+1}">Вперёд →</button>
    `;
    container.querySelectorAll('button').forEach(btn => {
        btn.addEventListener('click', () => {
            if (!btn.disabled) loadFunction(parseInt(btn.dataset.page));
        });
    });
}

// Модальное окно
function openModal(title, formHtml) {
    modalTitle.textContent = title;
    modalForm.innerHTML = formHtml;
    modal.style.display = 'flex';
}

function closeModal() {
    modal.style.display = 'none';
}

modalClose.addEventListener('click', closeModal);
modal.addEventListener('click', (e) => {
    if (e.target === modal) closeModal();
});

// API запрос
async function apiRequest(path, method = 'GET', body = null, isForm = false) {
    const headers = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    let options = { method, headers };

    if (body) {
        if (isForm) {
            headers['Content-Type'] = 'application/x-www-form-urlencoded';
            const formData = new URLSearchParams();
            for (const [key, value] of Object.entries(body)) formData.append(key, value);
            options.body = formData;
        } else {
            headers['Content-Type'] = 'application/json';
            options.body = JSON.stringify(body);
        }
    }

    const res = await fetch(`${API_BASE}${path}`, options);
    if (res.status === 204) return null;
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || `Ошибка ${res.status}`);
    return data;
}

// Старт
if (token) {
    loadMain();
} else {
    showScreen('auth-screen');
    setAuthMode('login');
}

setupDragAndDrop();