/**
 * Reusable review modal for pipeline wizard steps.
 *
 * Public API:
 *   openModal(config)  – open the modal with a config object
 *   closeModal()       – close the modal
 *   getSelectedItems() – return currently selected items
 *   Modal.filterItems(q) – re-filter list by query string
 *   Modal.toggleSelectAll() – toggle all items
 *   Modal.save()       – persist selection via config.onSave callback
 *
 * Config shape:
 *   { title: string,
 *     items: Array<{ id: string, text: string, selected?: boolean, relevant?: boolean }>,
 *     onSave: (selectedItems) => void | Promise<void>,
 *     onOpen?: () => void }
 */
const Modal = {
    /** @type {Array<{id:string,text:string,selected:boolean,relevant?:boolean}>} */
    items: [],

    /** @type {Object|null} */
    config: null,

    /** Last focused element before modal opened, to restore on close */
    _previousFocus: null,

    /** Bound keydown handler reference so we can remove it */
    _boundKeyHandler: null,

    // ─── Open ───────────────────────────────────────────────────────
    open(config) {
        this.config = config;
        this.items = config.items.map(item => ({
            ...item,
            selected: !!item.selected,
            relevant: item.relevant,
        }));

        // Set title
        const titleEl = document.getElementById('modal-title');
        if (titleEl) titleEl.textContent = config.title || 'Tinjau Item';

        // Reset search
        const searchEl = document.getElementById('modal-search');
        if (searchEl) searchEl.value = '';

        // Render list
        this.render();

        // Show modal
        const modal = document.getElementById('review-modal');
        if (!modal) return;
        modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';

        // Remember focus for restoration
        this._previousFocus = document.activeElement;

        // Bind keyboard handler
        this._boundKeyHandler = e => this._handleKeydown(e);
        document.addEventListener('keydown', this._boundKeyHandler, true);

        // Focus the search input for quick filtering
        if (searchEl) {
            searchEl.focus();
        }

        // Notify consumer
        if (typeof config.onOpen === 'function') config.onOpen();
    },

    // ─── Close ──────────────────────────────────────────────────────
    close() {
        const modal = document.getElementById('review-modal');
        if (!modal) return;
        modal.classList.add('hidden');
        document.body.style.overflow = '';

        // Remove keyboard handler
        if (this._boundKeyHandler) {
            document.removeEventListener('keydown', this._boundKeyHandler, true);
            this._boundKeyHandler = null;
        }

        // Restore focus
        if (this._previousFocus && typeof this._previousFocus.focus === 'function') {
            this._previousFocus.focus();
        }
        this._previousFocus = null;

        this.config = null;
    },

    // ─── Render item list ───────────────────────────────────────────
    render() {
        const container = document.getElementById('modal-items');
        const emptyEl = document.getElementById('modal-empty');
        if (!container) return;

        const searchEl = document.getElementById('modal-search');
        const search = (searchEl ? searchEl.value : '').toLowerCase();

        const filtered = this.items.filter(item =>
            item.text.toLowerCase().includes(search)
        );

        // Show/hide empty state
        if (emptyEl) {
            emptyEl.classList.toggle('hidden', filtered.length > 0);
        }
        container.classList.toggle('hidden', filtered.length === 0);

        if (filtered.length === 0) {
            this.updateCount();
            return;
        }

        container.innerHTML = filtered.map(item => `
            <label role="option"
                   aria-selected="${item.selected}"
                   tabindex="-1"
                   class="flex items-center gap-3 p-3 rounded-lg hover:bg-slate-700/30 transition-colors cursor-pointer border border-transparent hover:border-slate-700/50 group"
                   data-item-id="${this._escapeHtml(item.id)}">
                <input type="checkbox"
                       ${item.selected ? 'checked' : ''}
                       data-checkbox-id="${this._escapeHtml(item.id)}"
                       class="rounded border-slate-600 bg-slate-700 text-blue-600 focus:ring-blue-500 shrink-0"
                       tabindex="-1"
                       aria-label="${this._escapeHtml(item.text)}">
                <span class="text-slate-200 text-sm flex-1 min-w-0 break-words">${this._escapeHtml(item.text)}</span>
                ${item.relevant !== undefined ? `
                    <button type="button"
                            data-relevant-btn="${this._escapeHtml(item.id)}"
                            aria-label="${item.relevant ? 'Tandai tidak relevan' : 'Tandai relevan'}"
                            class="px-2 py-1 text-xs rounded shrink-0 transition-colors
                                   ${item.relevant
                                       ? 'bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30'
                                       : 'bg-slate-600 text-slate-400 hover:bg-slate-500'}">
                        ${item.relevant ? 'Relevan' : 'Tandai'}
                    </button>
                ` : ''}
            </label>
        `).join('');

        this.updateCount();
    },

    // ─── Filter ─────────────────────────────────────────────────────
    filterItems(_query) {
        this.render();
    },

    // ─── Toggle single item ─────────────────────────────────────────
    toggleItem(id) {
        const item = this.items.find(i => i.id === id);
        if (!item) return;
        item.selected = !item.selected;

        // Sync aria-selected
        const row = document.querySelector(`[data-item-id="${id}"]`);
        if (row) row.setAttribute('aria-selected', String(item.selected));

        this.updateCount();
        this._announce(`Item ${item.selected ? 'dipilih' : 'dibatalkan'}: ${item.text}`);
    },

    // ─── Toggle relevant flag ───────────────────────────────────────
    toggleRelevant(id) {
        const item = this.items.find(i => i.id === id);
        if (!item) return;
        item.relevant = !item.relevant;
        this.render();
        this._announce(`Item ditandai ${item.relevant ? 'relevan' : 'tidak relevan'}: ${item.text}`);
    },

    // ─── Select / Deselect all ──────────────────────────────────────
    toggleSelectAll() {
        const allSelected = this.items.every(i => i.selected);
        this.items.forEach(i => (i.selected = !allSelected));
        this.render();
        this._announce(allSelected ? 'Semua item dibatalkan' : 'Semua item dipilih');
    },

    // ─── Count badge ────────────────────────────────────────────────
    updateCount() {
        const el = document.getElementById('modal-count');
        if (!el) return;
        const selected = this.items.filter(i => i.selected).length;
        el.textContent = `Dipilih: ${selected} / ${this.items.length}`;
    },

    // ─── Get selected items ─────────────────────────────────────────
    getSelected() {
        return this.items.filter(i => i.selected);
    },

    // ─── Save ───────────────────────────────────────────────────────
    async save() {
        const selected = this.getSelected();
        if (this.config && typeof this.config.onSave === 'function') {
            await this.config.onSave(selected);
        }
        this.close();
    },

    // ─── Keyboard handler ───────────────────────────────────────────
    _handleKeydown(e) {
        if (e.key === 'Escape') {
            e.preventDefault();
            e.stopPropagation();
            this.close();
            return;
        }

        // Tab trap: keep focus inside the modal
        if (e.key === 'Tab') {
            const modal = document.getElementById('review-modal');
            if (!modal) return;
            const focusable = modal.querySelectorAll(
                'button, input, [tabindex]:not([tabindex="-1"])'
            );
            if (focusable.length === 0) return;
            const first = focusable[0];
            const last = focusable[focusable.length - 1];

            if (e.shiftKey) {
                if (document.activeElement === first) {
                    e.preventDefault();
                    last.focus();
                }
            } else {
                if (document.activeElement === last) {
                    e.preventDefault();
                    first.focus();
                }
            }
        }
    },

    // ─── Accessibility announcement ─────────────────────────────────
    _announce(message) {
        const region = document.getElementById('modal-live-region');
        if (region) {
            region.textContent = '';
            // Small timeout to ensure screen readers pick up the change
            requestAnimationFrame(() => {
                region.textContent = message;
            });
        }
    },

    // ─── HTML escape helper ─────────────────────────────────────────
    _escapeHtml(str) {
        const div = document.createElement('div');
        div.appendChild(document.createTextNode(str));
        return div.innerHTML;
    },
};

// ─── Event delegation ──────────────────────────────────────────────
// Handles clicks/changes inside the modal without inline handlers in HTML.
document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('review-modal');
    if (!modal) return;

    // Close button clicks
    modal.addEventListener('click', e => {
        const closeBtn = e.target.closest('[data-modal-close]');
        if (closeBtn) {
            Modal.close();
            return;
        }

        // Backdrop click
        if (e.target.hasAttribute('data-modal-backdrop-click')) {
            Modal.close();
            return;
        }

        // Select-all button
        if (e.target.closest('[data-modal-select-all]')) {
            Modal.toggleSelectAll();
            return;
        }

        // Save button
        if (e.target.closest('[data-modal-save]')) {
            Modal.save();
            return;
        }

        // Relevant toggle button
        const relevantBtn = e.target.closest('[data-relevant-btn]');
        if (relevantBtn) {
            Modal.toggleRelevant(relevantBtn.dataset.relevantBtn);
            return;
        }
    });

    // Checkbox change events (delegated)
    modal.addEventListener('change', e => {
        if (e.target.hasAttribute('data-checkbox-id')) {
            Modal.toggleItem(e.target.dataset.checkboxId);
        }
    });

    // Search input (debounced via input event)
    const searchEl = document.getElementById('modal-search');
    if (searchEl) {
        searchEl.addEventListener('input', () => {
            Modal.filterItems(searchEl.value);
        });
    }
});

// ─── Public API surface ────────────────────────────────────────────
window.Modal = Modal;
window.openModal = config => Modal.open(config);
window.closeModal = () => Modal.close();
window.getSelectedItems = () => Modal.getSelected();
