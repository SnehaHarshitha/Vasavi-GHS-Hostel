// PG Hostel Mess Main JavaScript File

document.addEventListener('DOMContentLoaded', function () {
    // Auto-dismiss alert toasts after 5 seconds safely
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            try {
                const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
                if (bsAlert) bsAlert.close();
            } catch (e) {
                // Ignore if alert already closed
            }
        }, 5000);
    });

    // Stable Live Date and Time Ticker (only mutates DOM when text changes)
    let lastDateStr = '';
    function updateLiveDateTime() {
        const liveElements = document.querySelectorAll('.live-date-ticker');
        if (liveElements.length > 0) {
            const now = new Date();
            const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit' };
            const dateStr = now.toLocaleDateString('en-US', options);
            if (dateStr !== lastDateStr) {
                lastDateStr = dateStr;
                liveElements.forEach(el => {
                    if (el.textContent !== dateStr) {
                        el.textContent = dateStr;
                    }
                });
            }
        }
    }

    updateLiveDateTime();
    setInterval(updateLiveDateTime, 1000);

    // Check unread notifications count via AJAX
    const notifBadge = document.getElementById('notif-badge-count');
    if (notifBadge) {
        fetch('/api/notifications/unread-count')
            .then(res => res.json())
            .then(data => {
                if (data && data.unread_count > 0) {
                    notifBadge.textContent = data.unread_count;
                    notifBadge.classList.remove('d-none');
                } else {
                    notifBadge.classList.add('d-none');
                }
            })
            .catch(err => console.log('Notification fetch error:', err));
    }
});

// Helper function to handle AJAX food selection
function quickSelectFood(choice) {
    const formData = new FormData();
    formData.append('choice', choice);

    fetch('/api/mess/select', {
        method: 'POST',
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            alert(data.message);
            window.location.reload();
        } else {
            alert('Selection failed: ' + data.message);
        }
    })
    .catch(err => console.error(err));
}

// Helper function to toggle password visibility
function togglePasswordVisibility(inputId, btn) {
    const input = document.getElementById(inputId);
    if (!input) return;
    const icon = btn.querySelector('i');
    if (input.type === 'password') {
        input.type = 'text';
        if (icon) {
            icon.classList.remove('fa-eye');
            icon.classList.add('fa-eye-slash');
        }
    } else {
        input.type = 'password';
        if (icon) {
            icon.classList.remove('fa-eye-slash');
            icon.classList.add('fa-eye');
        }
    }
}
