document.addEventListener('DOMContentLoaded', function() {
    // Initialize formset counters
    const educationFormCount = document.querySelectorAll('#education-forms .formset-item').length;
    const experienceFormCount = document.querySelectorAll('#experience-forms .formset-item').length;
    const skillFormCount = document.querySelectorAll('#skill-forms .formset-item').length;

    // Add education form
    const addEducationBtn = document.getElementById('add-education');
    if (addEducationBtn) {
        addEducationBtn.addEventListener('click', function() {
            const formIdx = document.getElementById('id_education-TOTAL_FORMS').value;
            const template = document.getElementById('education-template').innerHTML
                .replace(/__prefix__/g, formIdx);
            
            const container = document.getElementById('education-forms');
            container.insertAdjacentHTML('beforeend', template);
            
            // Update total form count
            document.getElementById('id_education-TOTAL_FORMS').value = parseInt(formIdx) + 1;
            
            // Add event listener to the new delete button
            initializeDeleteButtons('education');
        });
    }

    // Add experience form
    const addExperienceBtn = document.getElementById('add-experience');
    if (addExperienceBtn) {
        addExperienceBtn.addEventListener('click', function() {
            const formIdx = document.getElementById('id_experience-TOTAL_FORMS').value;
            const template = document.getElementById('experience-template').innerHTML
                .replace(/__prefix__/g, formIdx);
            
            const container = document.getElementById('experience-forms');
            container.insertAdjacentHTML('beforeend', template);
            
            // Update total form count
            document.getElementById('id_experience-TOTAL_FORMS').value = parseInt(formIdx) + 1;
            
            // Add event listener to the new delete button
            initializeDeleteButtons('experience');
        });
    }

    // Add skill form
    const addSkillBtn = document.getElementById('add-skill');
    if (addSkillBtn) {
        addSkillBtn.addEventListener('click', function() {
            const formIdx = document.getElementById('id_skills-TOTAL_FORMS').value;
            const template = document.getElementById('skill-template').innerHTML
                .replace(/__prefix__/g, formIdx);
            
            const container = document.getElementById('skill-forms');
            container.insertAdjacentHTML('beforeend', template);
            
            // Update total form count
            document.getElementById('id_skills-TOTAL_FORMS').value = parseInt(formIdx) + 1;
            
            // Add event listener to the new delete button
            initializeDeleteButtons('skills');
        });
    }

    // Initialize delete buttons for existing forms
    initializeDeleteButtons('education');
    initializeDeleteButtons('experience');
    initializeDeleteButtons('skills');

    // Profile picture preview
    const profilePictureInput = document.querySelector('input[type="file"][name="profile_picture"]');
    if (profilePictureInput) {
        profilePictureInput.addEventListener('change', previewImage);
    }

    // Remove profile picture button
    const removeProfilePictureBtn = document.querySelector('button[onclick="removeProfilePicture()"]');
    if (removeProfilePictureBtn) {
        removeProfilePictureBtn.addEventListener('click', removeProfilePicture);
    }
});

// Initialize delete buttons for a specific form type
function initializeDeleteButtons(formType) {
    const container = document.getElementById(`${formType}-forms`);
    if (!container) return;
    
    container.querySelectorAll('.delete-formset').forEach(button => {
        if (!button.hasAttribute('data-initialized')) {
            button.addEventListener('click', function() {
                const formItem = this.closest('.formset-item');
                formItem.remove();
                updateFormIndices(formType);
            });
            button.setAttribute('data-initialized', 'true');
        }
    });
}

// Update form indices after form deletion
function updateFormIndices(formType) {
    const container = document.getElementById(`${formType}-forms`);
    if (!container) return;
    
    const totalForms = document.getElementById(`id_${formType}-TOTAL_FORMS`);
    if (!totalForms) return;
    
    const formCount = container.querySelectorAll('.formset-item').length;
    totalForms.value = formCount;
    
    // Update all form indices
    container.querySelectorAll('.formset-item').forEach((item, index) => {
        // Update all input, select, and textarea elements
        item.querySelectorAll('input, select, textarea, label').forEach(element => {
            if (element.htmlFor) {
                element.htmlFor = element.htmlFor.replace(/\d+/g, index);
            }
            if (element.id) {
                element.id = element.id.replace(/\d+/g, index);
            }
            if (element.name) {
                element.name = element.name.replace(/\d+/g, index);
            }
        });
    });
}

// Preview selected image
function previewImage(input) {
    const preview = document.getElementById('profile-preview');
    const emptyAvatar = document.getElementById('empty-avatar');
    
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        
        reader.onload = function(e) {
            if (preview) {
                preview.src = e.target.result;
                preview.style.display = 'block';
            } else {
                const img = document.createElement('img');
                img.id = 'profile-preview';
                img.className = 'profile-picture-preview';
                img.src = e.target.result;
                img.alt = 'Profile Preview';
                
                const container = input.closest('.flex').querySelector('.shrink-0');
                if (container) {
                    container.innerHTML = '';
                    container.appendChild(img);
                }
            }
            
            if (emptyAvatar) {
                emptyAvatar.style.display = 'none';
            }
        };
        
        reader.readAsDataURL(input.files[0]);
    }
}

// Remove profile picture
function removeProfilePicture() {
    const preview = document.getElementById('profile-preview');
    const emptyAvatar = document.getElementById('empty-avatar');
    const fileInput = document.querySelector('input[type="file"][name="profile_picture"]');
    
    if (preview) {
        preview.remove();
    }
    
    if (emptyAvatar) {
        emptyAvatar.style.display = 'flex';
    }
    
    if (fileInput) {
        fileInput.value = '';
    }
    
    // Add a hidden input to indicate the picture should be cleared
    let clearPictureInput = document.querySelector('input[name="profile_picture-clear"]');
    if (!clearPictureInput) {
        clearPictureInput = document.createElement('input');
        clearPictureInput.type = 'hidden';
        clearPictureInput.name = 'profile_picture-clear';
        clearPictureInput.value = 'on';
        document.getElementById('resume-form').appendChild(clearPictureInput);
    }
}
