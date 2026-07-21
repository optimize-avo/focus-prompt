// Wizard state management
const Wizard = {
    currentStep: 'research',
    steps: ['research', 'discover', 'generate', 'score', 'export'],
    stepStatuses: {},

    async goToStep(stepId) {
        const currentIdx = this.steps.indexOf(this.currentStep);
        const targetIdx = this.steps.indexOf(stepId);

        // Allow going back or to completed steps
        if (targetIdx < currentIdx || this.isStepCompleted(stepId)) {
            window.location.href = `/pipeline/${stepId}`;
        }
    },

    isStepCompleted(stepId) {
        const status = this.stepStatuses[stepId];
        return status && status.completed === true;
    },

    prevStep() {
        const idx = this.steps.indexOf(this.currentStep);
        if (idx > 0) {
            window.location.href = `/pipeline/${this.steps[idx - 1]}`;
        }
    },

    nextStep() {
        const idx = this.steps.indexOf(this.currentStep);
        if (idx < this.steps.length - 1) {
            window.location.href = `/pipeline/${this.steps[idx + 1]}`;
        }
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
                location.reload();
            }
        } catch (e) {
            console.error('Failed to regenerate:', e);
        }
    },

    continueToNext(currentStepId) {
        const step = document.getElementById(`step-${currentStepId}`);
        if (!step) return;
        const checkedIds = Array.from(step.querySelectorAll('.step-item-checkbox:checked'))
            .map(cb => cb.dataset.itemId);

        this.saveKeep(currentStepId, checkedIds).then(success => {
            if (success) {
                const nextStepId = this.getNextStep(currentStepId);
                if (nextStepId) {
                    window.location.href = `/pipeline/${nextStepId}`;
                }
            }
        });
    },

    getNextStep(currentStepId) {
        const idx = this.steps.indexOf(currentStepId);
        return idx >= 0 && idx < this.steps.length - 1 ? this.steps[idx + 1] : null;
    }
};

window.Wizard = Wizard;
