document.getElementById('query-form').addEventListener('submit', async function(event) {
    event.preventDefault(); // Prevent default form submission
    const queryInput = document.getElementById('query-input');
    const query = queryInput.value.trim();

    console.log('Form submitted, query:', query); // Debug log

    if (!query) {
        showAlert('Пожалуйста, введите ваш запрос', 'warning');
        return;
    }

    const conversation = document.getElementById('conversation');
    addMessage(conversation, 'user', query);
    const loadingId = addLoadingIndicator(conversation);

    try {
        const response = await fetch("{% url 'firstblog:result' %}", {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken(),
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest' // Signal AJAX request
            },
            body: JSON.stringify({ query: query })
        });

        console.log('Response status:', response.status); // Debug log
        const data = await response.json();
        console.log('Response data:', data); // Debug log

        if (!response.ok) {
            throw new Error(data.error || 'Ошибка сервера');
        }

        if (data.status === 'error') {
            throw new Error(data.error);
        }

        updateLoadingToMessage(
            conversation,
            loadingId,
            'ai',
            formatResponse(data.context || [], data.answer || '')
        );
    } catch (error) {
        console.error('Error:', error);
        updateLoadingToError(conversation, loadingId, error.message);
    } finally {
        queryInput.value = '';
    }
});

function getCSRFToken() {
    const name = 'csrftoken';
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    console.log('CSRF Token:', cookieValue); // Debug log
    return cookieValue;
}

function addMessage(conversation, role, content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role === 'user' ? 'text-end' : 'text-start'} mb-2`;
    messageDiv.innerHTML = `<strong>${role === 'user' ? 'Вы' : 'AI'}</strong>: ${content}`;
    conversation.appendChild(messageDiv);
    conversation.scrollTop = conversation.scrollHeight;
}

function addLoadingIndicator(conversation) {
    const loadingId = 'loading-' + Date.now();
    const loadingDiv = document.createElement('div');
    loadingDiv.id = loadingId;
    loadingDiv.className = 'message text-start mb-2';
    loadingDiv.innerHTML = '<strong>AI</strong>: <i>Загрузка...</i>';
    conversation.appendChild(loadingDiv);
    conversation.scrollTop = conversation.scrollHeight;
    return loadingId;
}

function updateLoadingToMessage(conversation, loadingId, role, content) {
    const loadingDiv = document.getElementById(loadingId);
    if (loadingDiv) {
        loadingDiv.innerHTML = `<strong>${role === 'user' ? 'Вы' : 'AI'}</strong>: ${content}`;
        loadingDiv.className = `message ${role === 'user' ? 'text-end' : 'text-start'} mb-2`;
        conversation.scrollTop = conversation.scrollHeight;
    }
}

function updateLoadingToError(conversation, loadingId, errorMessage) {
    const loadingDiv = document.getElementById(loadingId);
    if (loadingDiv) {
        loadingDiv.innerHTML = `<strong>AI</strong>: <span class="text-danger">Ошибка: ${errorMessage}</span>`;
        conversation.scrollTop = conversation.scrollHeight;
    }
}

function formatResponse(context, answer) {
    let formatted = answer;
    if (context && context.length > 0) {
        formatted = `<p><strong>Контекст:</strong></p><ul>`;
        context.forEach(item => {
            formatted += `<li>${item}</li>`;
        });
        formatted += `</ul><p><strong>Ответ:</strong> ${answer}</p>`;
    }
    return formatted;
}

function showAlert(message, type) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.role = 'alert';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    const conversation = document.getElementById('conversation');
    conversation.insertBefore(alertDiv, conversation.firstChild);
    conversation.scrollTop = conversation.scrollHeight;
    setTimeout(() => alertDiv.remove(), 5000);
}