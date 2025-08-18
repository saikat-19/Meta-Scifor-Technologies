document.addEventListener('DOMContentLoaded', function() {
    // Image gallery functionality
    const thumbnailButtons = document.querySelectorAll('.thumbnail-btn');
    const mainImage = document.querySelector('.aspect-w-1.aspect-h-1 img');
    
    if (thumbnailButtons.length > 0 && mainImage) {
        thumbnailButtons.forEach(button => {
            button.addEventListener('click', function() {
                // Remove active state from all thumbnails
                thumbnailButtons.forEach(btn => btn.classList.remove('ring-2', 'ring-indigo-500'));
                
                // Add active state to clicked thumbnail
                this.classList.add('ring-2', 'ring-indigo-500');
                
                // Update main image
                const newImageSrc = this.querySelector('img').getAttribute('data-full-src');
                if (newImageSrc) {
                    mainImage.src = newImageSrc;
                }
            });
        });
    }

    // Quantity controls
    const quantityInput = document.getElementById('quantity');
    const decrementBtn = document.querySelector('.decrement-btn');
    const incrementBtn = document.querySelector('.increment-btn');
    const maxQuantity = quantityInput ? parseInt(quantityInput.max) || 10 : 10;
    
    if (quantityInput && decrementBtn && incrementBtn) {
        // Decrease quantity
        decrementBtn.addEventListener('click', function() {
            let value = parseInt(quantityInput.value) || 1;
            if (value > 1) {
                quantityInput.value = value - 1;
            }
        });
        
        // Increase quantity
        incrementBtn.addEventListener('click', function() {
            let value = parseInt(quantityInput.value) || 1;
            if (value < maxQuantity) {
                quantityInput.value = value + 1;
            }
        });
        
        // Validate input
        quantityInput.addEventListener('change', function() {
            let value = parseInt(this.value) || 1;
            if (value < 1) value = 1;
            if (value > maxQuantity) value = maxQuantity;
            this.value = value;
        });
    }

    // Form submission with AJAX
    const addToCartForm = document.getElementById('add-to-cart-form');
    if (addToCartForm) {
        addToCartForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const submitButton = this.querySelector('button[type="submit"]');
            const originalButtonText = submitButton.innerHTML;
            
            // Show loading state
            submitButton.disabled = true;
            submitButton.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Adding...';
            
            fetch(this.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': formData.get('csrfmiddlewaretoken')
                }
            })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(err => {
                        throw err;
                    });
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    // Update cart count in header if the element exists
                    const cartCount = document.querySelector('.cart-count');
                    if (cartCount) {
                        cartCount.textContent = data.cart_count || data.cart_total_items;
                        cartCount.classList.remove('hidden');
                    }
                    
                    // Show success message
                    showNotification(data.message || 'Item added to cart!', 'success');
                    
                    // Update max quantity based on server response
                    const quantityInput = document.getElementById('quantity');
                    if (data.stock_available !== undefined) {
                        const maxAvailable = data.stock_available - (data.in_cart || 0);
                        quantityInput.max = maxAvailable > 0 ? maxAvailable : 1;
                        
                        // Update the current quantity if it exceeds the new max
                        if (parseInt(quantityInput.value) > maxAvailable) {
                            quantityInput.value = maxAvailable > 0 ? maxAvailable : 1;
                        }
                        
                        // Disable increment button if no more items can be added
                        const incrementBtn = document.querySelector('.increment-btn');
                        if (incrementBtn) {
                            if (maxAvailable <= 0) {
                                incrementBtn.disabled = true;
                                incrementBtn.classList.add('opacity-50', 'cursor-not-allowed');
                            } else {
                                incrementBtn.disabled = false;
                                incrementBtn.classList.remove('opacity-50', 'cursor-not-allowed');
                            }
                        }
                    }
                } else {
                    showNotification(data.message || 'Error adding item to cart', 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showNotification('An error occurred. Please try again.', 'error');
            })
            .finally(() => {
                // Reset button state
                submitButton.disabled = false;
                submitButton.innerHTML = originalButtonText;
            });
        });
    }
    
    // Helper function to show notifications
    function showNotification(message, type = 'info') {
        // You can implement a proper notification system here
        // For now, we'll just use alert
        alert(message);
    }
});
