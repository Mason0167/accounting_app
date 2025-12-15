function openModal({type, text, formAction=null}) {
    const modal = document.getElementById('flexModal');
    const modalText = document.getElementById('modal-text');
    const modalForm = document.getElementById('modalForm');
    const modalConfirmBtn = document.getElementById('modalConfirmBtn');
    const modalOkBtn = document.getElementById('modalOkBtn');

    modalText.innerHTML = text;

    if(type === 'delete') {
        modalForm.style.display = 'block';
        modalOkBtn.style.display = 'none';
        modalForm.action = formAction;
        modalConfirmBtn.textContent = 'Yes, Delete';
    } else if(type === 'error') {
        modalForm.style.display = 'none';
        modalOkBtn.style.display = 'inline-block';
    }

    modal.style.display = 'flex';
}

function closeModal() {
    document.getElementById('flexModal').style.display = 'none';
}

// Attach Delete Button Events
document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.btn-delete').forEach(btn => {
        btn.addEventListener('click', () => {
            const tripId = btn.dataset.id;
            const tripName = btn.dataset.name;
            openModal({
                type: 'delete',
                text: `Are you sure you want to delete "${tripName}"?`,
                formAction: `/deleteTrip/${tripId}`
            });
        });
    });
});
