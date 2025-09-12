document.addEventListener('DOMContentLoaded', function() {
    // Only select task items that have the task-item class (which we only add to tasks with details)
    const taskItems = document.querySelectorAll('.task-item');
    
    taskItems.forEach(item => {
        const header = item.querySelector('.task-header');
        const details = item.querySelector('.task-details-panel');
        
        // Only add click handler if both header and details exist
        if (!header || !details) return;
        
        header.addEventListener('click', function(e) {
            // Don't toggle if clicking on delete button or checkbox
            if (e.target.closest('button, a, [role="button"], [role="link"]')) {
                return;
            }
            
            const isActive = item.classList.contains('active');
            
            // Close all other open task details
            document.querySelectorAll('.task-item.active').forEach(activeItem => {
                if (activeItem !== item) {
                    activeItem.classList.remove('active');
                    activeItem.querySelector('.task-details-panel').style.maxHeight = '0';
                }
            });
            
            // Toggle current item
            if (!isActive) {
                item.classList.add('active');
                details.style.maxHeight = details.scrollHeight + 'px';
            } else {
                item.classList.remove('active');
                details.style.maxHeight = '0';
            }
        });
    });
});
