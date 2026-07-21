// Wizard state management
const Wizard = {
    updateContinueButton(stepId) {
        const step = document.getElementById(`step-${stepId}`);
        if (!step) return;
        const checkboxes = step.querySelectorAll('.step-item-checkbox');
        const checked = step.querySelectorAll('.step-item-checkbox:checked').length;
        const continueBtn = step.querySelector('.continue-btn');
        if (continueBtn) {
            continueBtn.disabled = checked === 0;
            continueBtn.classList.toggle('opacity-50', checked === 0);
            continueBtn.classList.toggle('cursor-not-allowed', checked === 0);
        }
    },

    initStep(stepId) {
        const step = document.getElementById(`step-${stepId}`);
        if (!step) return;
        const checkboxes = step.querySelectorAll('.step-item-checkbox');
        checkboxes.forEach(cb => {
            cb.addEventListener('change', () => this.updateContinueButton(stepId));
        });
        this.updateContinueButton(stepId);
    },

    async saveKeep(stepId, itemIds) {
        try {
            const response = await fetch(`/api/pipeline/step/${stepId}/keep`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ keep_ids: itemIds })
            });
            return response.ok;
        } catch (e) {
            console.error('Failed to save keep:', e);
            return false;
        }
    },

    async regenerate(stepId, itemIds) {
        try {
            const response = await fetch(`/api/pipeline/step/${stepId}/regenerate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ regenerate_ids: itemIds })
            });
            if (response.ok) {
                location.reload(); // Reload to show new data
            }
        } catch (e) {
            console.error('Failed to regenerate:', e);
        }
    },

    continueToNext(currentStepId) {
        // Save keep state
        const step = document.getElementById(`step-${currentStepId}`);
        if (!step) return;
        const checkedIds = Array.from(step.querySelectorAll('.step-item-checkbox:checked'))
            .map(cb => cb.dataset.itemId);
        
        this.saveKeep(currentStepId, checkedIds).then(success => {
            if (success) {
                const nextStepId = this.getNextStep(currentStepId);
                if (nextStepId) {
                    const nextStep = document.getElementById(`step-${nextStepId}`);
                    if (nextStep) {
                        nextStep.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    }
                }
            }
        });
    },

    getNextStep(currentStepId) {
        const order = ['research', 'discover', 'generate', 'score', 'export'];
        const idx = order.indexOf(currentStepId);
        return idx >= 0 && idx < order.length - 1 ? order[idx + 1] : null;
    }
};

// Initialize all steps on page load
document.addEventListener('DOMContentLoaded', () => {
    ['research', 'discover', 'generate', 'score', 'export'].forEach(stepId => {
        Wizard.initStep(stepId);
    });
});

// Expose to global scope for onclick handlers
window.Wizard = Wizard;
