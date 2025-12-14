function openDeleteModal(tripId, tripName) {
    const modal = document.getElementById('deleteModal');
    const modalText = document.getElementById('modal-text');
    const deleteForm = document.getElementById('deleteForm');

    modalText.textContent = `Are you sure you want to delete "${tripName}"?`;
    deleteForm.action = `/deleteTrip/${tripId}`;
    modal.style.display = 'flex';
}

function closeDeleteModal() {
    document.getElementById('deleteModal').style.display = 'none';
}

// Attach click events to delete buttons dynamically
document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.btn-delete').forEach(btn => {
        btn.addEventListener('click', () => {
            const tripId = btn.dataset.id;
            const tripName = btn.dataset.name;
            openDeleteModal(tripId, tripName);
        });
    });

    // Optional: close modal when clicking the cancel button
    const cancelBtn = document.getElementById('cancelDelete');
    if (cancelBtn) {
        cancelBtn.addEventListener('click', closeDeleteModal);
    }
});
