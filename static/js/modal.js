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
    } else if(type === 'error' || type === 'success') {
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
    // Trip delete buttons
    document.querySelectorAll('.btn-delete').forEach(btn => {
        btn.addEventListener('click', () => {
            const tripId = btn.dataset.id;
            const tripName = btn.dataset.name;
            openModal({
                type: 'delete',
                text: `Are you sure you want to delete trip "${tripName}"?`,
                formAction: `/deleteTrip/${tripId}`
            });
        });
    });

    // Expense delete buttons
    document.querySelectorAll('.btn-delete-expense').forEach(btn => {
        btn.addEventListener('click', () => {
            const expenseId = btn.dataset.id;
            const itemName = btn.dataset.item;
            openModal({
                type: 'delete',
                text: `Are you sure you want to delete expense "${itemName}"?`,
                formAction: `/deleteExpense/${expenseId}`
            });
        });
    });
});
