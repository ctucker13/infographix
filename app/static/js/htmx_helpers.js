document.addEventListener('htmx:send', function (evt) {
  const target = evt.detail.target;
  if (target) {
    target.classList.add('loading');
  }
});

document.addEventListener('htmx:afterSwap', function (evt) {
  const target = evt.detail.target;
  if (target) {
    target.classList.remove('loading');
  }
});

document.addEventListener('DOMContentLoaded', function () {
  const builder = document.querySelector('[data-section-builder]');
  if (!builder) {
    return;
  }

  const form = builder.closest('form');
  const sectionsContainer = builder.querySelector('[data-section-list]');
  const hiddenField = builder.querySelector('#sections-json');
  const addSectionBtn = builder.querySelector('[data-add-section]');
  const sectionTemplate = document.getElementById('section-template');
  const blockTemplate = document.getElementById('text-block-template');
  const templateSelect = builder.querySelector('[data-template-select]');
  const templateSummary = builder.querySelector('[data-template-summary]');
  const templateGuidance = builder.querySelector('[data-template-guidance]');
  const applyTemplateBtn = builder.querySelector('[data-apply-template]');
  let templateOptions = [];
  try {
    templateOptions = JSON.parse(builder.dataset.templates || '[]');
  } catch (err) {
    console.warn('Unable to parse section templates', err);
    templateOptions = [];
  }

  if (!sectionTemplate || !blockTemplate) {
    return;
  }

  function addSection(data) {
    const fragment = sectionTemplate.content.cloneNode(true);
    const card = fragment.querySelector('.section-card');
    sectionsContainer.appendChild(fragment);
    const inserted = sectionsContainer.lastElementChild;
    const blockList = inserted.querySelector('[data-block-list]');
    const removeBtn = inserted.querySelector('[data-remove-section]');
    const addBlockBtn = inserted.querySelector('[data-add-block]');

    const blocks = (data && data.text_blocks && data.text_blocks.length ? data.text_blocks : [null]);
    blocks.forEach(function (block) {
      addBlock(blockList, block);
    });

    if (data) {
      inserted.querySelector('[data-field="title"]').value = data.title || '';
      inserted.querySelector('[data-field="icon_hint"]').value = data.icon_hint || '';
      inserted.querySelector('[data-field="chart_hint"]').value = data.chart_hint || '';
    }

    addBlockBtn.addEventListener('click', function () {
      addBlock(blockList, null);
      serializeSections();
    });

    removeBtn.addEventListener('click', function () {
      inserted.remove();
      renumberSections();
      serializeSections();
    });

    inserted.addEventListener('input', serializeSections);
    inserted.addEventListener('change', serializeSections);
    renumberSections();
    serializeSections();
  }

  function addBlock(listEl, data) {
    const fragment = blockTemplate.content.cloneNode(true);
    const block = fragment.querySelector('.text-block');
    listEl.appendChild(fragment);
    const inserted = listEl.lastElementChild;
    inserted.querySelector('[data-field="label"]').value = (data && data.label) || '';
    inserted.querySelector('[data-field="body"]').value = (data && data.body) || '';
    inserted.querySelector('[data-field="exact_text"]').checked = Boolean(data && data.exact_text);
    const removeBtn = inserted.querySelector('[data-remove-block]');
    removeBtn.addEventListener('click', function () {
      inserted.remove();
      serializeSections();
    });
  }

  function slugify(value, fallback) {
    if (!value) {
      return fallback;
    }
    const slug = value
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/(^-|-$)/g, '')
      .slice(0, 40);
    return slug || fallback;
  }

  function collectSections() {
    const sections = [];
    const cards = sectionsContainer.querySelectorAll('.section-card');
    cards.forEach(function (card, index) {
      const title = card.querySelector('[data-field="title"]').value.trim();
      const iconHint = card.querySelector('[data-field="icon_hint"]').value.trim();
      const chartHint = card.querySelector('[data-field="chart_hint"]').value.trim();
      const blocks = [];
      card.querySelectorAll('.text-block').forEach(function (block) {
        const labelInput = block.querySelector('[data-field="label"]');
        const bodyInput = block.querySelector('[data-field="body"]');
        const exactInput = block.querySelector('[data-field="exact_text"]');
        const label = labelInput.value.trim();
        const body = bodyInput.value.trim();
        if (!label && !body) {
          return;
        }
        blocks.push({
          label: label || 'Block',
          body,
          exact_text: exactInput.checked,
          summarizable: !exactInput.checked,
          decorative_only: false,
        });
      });

      if (!title && !iconHint && !chartHint && blocks.length === 0) {
        return;
      }

      const sectionId = slugify(title, `section-${index + 1}`);
      const sectionData = {
        id: sectionId,
        title: title || null,
        text_blocks: blocks,
      };
      if (iconHint) {
        sectionData.icon_hint = iconHint;
      }
      if (chartHint) {
        sectionData.chart_hint = chartHint;
      }
      sections.push(sectionData);
    });
    return sections;
  }

  function templateById(identifier) {
    if (!identifier) {
      return null;
    }
    return templateOptions.find(function (tpl) {
      return tpl.id === identifier;
    }) || null;
  }

  function describeTemplate(template) {
    if (!templateSummary) {
      return;
    }
    if (!template) {
      templateSummary.textContent = 'Pick a template to auto-fill sections.';
      if (templateGuidance) {
        templateGuidance.textContent = '';
      }
      return;
    }
    templateSummary.textContent = template.summary;
    if (templateGuidance) {
      const details = [];
      if (template.guidance && template.guidance.length) {
        details.push(template.guidance.join(' • '));
      }
      if (template.default_aspect_ratio || template.default_image_size) {
        const hints = [];
        if (template.default_aspect_ratio) {
          hints.push(`Aspect ${template.default_aspect_ratio}`);
        }
        if (template.default_image_size) {
          hints.push(`Size ${template.default_image_size}`);
        }
        details.push(hints.join(' · '));
      }
      templateGuidance.textContent = details.join('  ');
    }
  }

  function serializeSections() {
    const sections = collectSections();
    hiddenField.value = JSON.stringify(sections);
  }

  function renumberSections() {
    const cards = sectionsContainer.querySelectorAll('.section-card');
    cards.forEach(function (card, index) {
      const badge = card.querySelector('[data-section-number]');
      if (badge) {
        badge.textContent = index + 1;
      }
    });
  }

  function hydrateFromHidden() {
    let initial = [];
    try {
      initial = JSON.parse(hiddenField.value || '[]');
    } catch (err) {
      initial = [];
    }
    if (!initial.length) {
      addSection();
    } else {
      initial.forEach(function (section) {
        addSection(section);
      });
    }
    serializeSections();
  }

  addSectionBtn.addEventListener('click', function () {
    addSection();
  });

  if (templateSelect) {
    templateSelect.addEventListener('change', function () {
      const tpl = templateById(templateSelect.value);
      describeTemplate(tpl);
      if (applyTemplateBtn) {
        applyTemplateBtn.disabled = !tpl;
      }
    });
  }

  if (applyTemplateBtn) {
    applyTemplateBtn.addEventListener('click', function () {
      const tpl = templateById(templateSelect && templateSelect.value);
      if (!tpl) {
        return;
      }
      const hasContent = collectSections().length > 0;
      if (hasContent && !window.confirm('Applying a template will replace existing sections. Continue?')) {
        return;
      }
      sectionsContainer.innerHTML = '';
      tpl.sections.forEach(function (section) {
        addSection(section);
      });
      serializeSections();
    });
  }

  if (form) {
    form.addEventListener('submit', serializeSections);
  }

  document.addEventListener('htmx:configRequest', serializeSections);

  builder.addEventListener('sectionPreset:apply', function (event) {
    const payload = (event.detail && event.detail.sections) || [];
    sectionsContainer.innerHTML = '';
    if (!payload.length) {
      addSection();
    } else {
      payload.forEach(function (section) {
        addSection(section);
      });
    }
    serializeSections();
  });

  hydrateFromHidden();
  describeTemplate(null);
});

document.addEventListener('DOMContentLoaded', function () {
  const form = document.querySelector('[data-meta-prompt-form]');
  const root = form ? form.querySelector('[data-meta-prompt-root]') : null;
  if (!form || !root) {
    return;
  }

  const textarea = root.querySelector('[data-meta-prompt-input]');
  const applyBtn = root.querySelector('[data-meta-prompt-apply]');
  const clearBtn = root.querySelector('[data-meta-prompt-clear]');
  const status = root.querySelector('[data-meta-status]');
  const builder = document.querySelector('[data-section-builder]');
  const ratioSelect = document.querySelector('[data-aspect-select]');
  const ratioCustom = document.querySelector('[data-aspect-custom]');
  const ratioHidden = document.querySelector('[data-aspect-hidden]');
  const sizeSelect = document.querySelector('[data-size-select]');
  const sizeCustom = document.querySelector('[data-size-custom]');
  const sizeHidden = document.querySelector('[data-size-hidden]');

  function stripFences(value) {
    if (!value) {
      return '';
    }
    let raw = value.trim();
    if (raw.startsWith('```')) {
      const parts = raw.split('```');
      if (parts.length >= 3) {
        raw = parts.slice(1, -1).join('```');
      } else {
        raw = parts[parts.length - 1];
      }
    }
    return raw.trim();
  }

  function showStatus(message, isError) {
    if (!status) {
      return;
    }
    status.textContent = message || '';
    status.classList.toggle('error', Boolean(isError));
    status.classList.toggle('success', Boolean(message && !isError));
  }

  function parseMetaPrompt() {
    if (!textarea) {
      throw new Error('Meta prompt field not found.');
    }
    const raw = stripFences(textarea.value);
    if (!raw) {
      throw new Error('Paste the JSON output from Image Generation Chat first.');
    }
    try {
      return JSON.parse(raw);
    } catch (err) {
      throw new Error('Unable to parse meta prompt JSON.');
    }
  }

  function setValue(name, value) {
    const field = form.querySelector('[name="' + name + '"]');
    if (!field) {
      return;
    }
    if (field.tagName === 'SELECT') {
      const normalized = value == null ? '' : String(value);
      const exists = Array.from(field.options).some(function (opt) {
        return opt.value === normalized;
      });
      field.value = exists ? normalized : '';
    } else {
      field.value = value == null ? '' : value;
    }
    field.dispatchEvent(new Event('change', { bubbles: true }));
  }

  function applyAspect(value) {
    if (!ratioSelect || !ratioHidden) {
      return;
    }
    const normalized = (value || '').trim();
    if (!normalized) {
      ratioSelect.value = '';
      ratioSelect.dispatchEvent(new Event('change', { bubbles: true }));
      return;
    }
    const option = Array.from(ratioSelect.options).find(function (opt) {
      return opt.value === normalized;
    });
    if (option) {
      ratioSelect.value = normalized;
      ratioSelect.dispatchEvent(new Event('change', { bubbles: true }));
    } else {
      ratioSelect.value = 'custom';
      ratioSelect.dispatchEvent(new Event('change', { bubbles: true }));
      if (ratioCustom) {
        ratioCustom.value = normalized;
        ratioCustom.dispatchEvent(new Event('input', { bubbles: true }));
      }
    }
  }

  function applySize(value) {
    if (!sizeSelect || !sizeHidden) {
      return;
    }
    const normalized = (value || '').trim();
    if (!normalized) {
      sizeSelect.value = '';
      sizeSelect.dispatchEvent(new Event('change', { bubbles: true }));
      return;
    }
    const option = Array.from(sizeSelect.options).find(function (opt) {
      return opt.value === normalized;
    });
    if (option) {
      sizeSelect.value = normalized;
      sizeSelect.dispatchEvent(new Event('change', { bubbles: true }));
    } else {
      sizeSelect.value = 'custom';
      sizeSelect.dispatchEvent(new Event('change', { bubbles: true }));
      if (sizeCustom) {
        sizeCustom.value = normalized;
        sizeCustom.dispatchEvent(new Event('input', { bubbles: true }));
      }
    }
  }

  function applySections(sections) {
    if (!builder) {
      return;
    }
    builder.dispatchEvent(
      new CustomEvent('sectionPreset:apply', {
        detail: { sections: Array.isArray(sections) ? sections : [] },
      })
    );
  }

  function applyMetaPayload(payload) {
    setValue('topic', payload.topic || '');
    setValue('audience', payload.audience || '');
    setValue('desired_model', payload.desired_model || '');
    setValue('infographic_type', payload.infographic_type || '');
    setValue('visual_style', payload.visual_style || '');
    setValue('title', payload.title || '');
    setValue('subtitle', payload.subtitle || '');
    setValue('footer_text', payload.footer_text || '');
    setValue('text_preference', payload.text_preference || '');
    setValue('render_mode', payload.render_mode || '');
    if (Object.prototype.hasOwnProperty.call(payload, 'exact_text_required')) {
      setValue('exact_text_required', String(Boolean(payload.exact_text_required)));
    }
    applyAspect(payload.aspect_ratio);
    applySize(payload.image_size);
    applySections(payload.sections || []);
    return Array.isArray(payload.reference_image_hints) ? payload.reference_image_hints : [];
  }

  if (applyBtn) {
    applyBtn.addEventListener('click', function () {
      try {
        const payload = parseMetaPrompt();
        const hints = applyMetaPayload(payload);
        const message = Array.isArray(hints) && hints.length
          ? `Meta prompt applied. Remember to upload ${hints.length} reference asset${hints.length > 1 ? 's' : ''}.`
          : 'Meta prompt applied. Review the fields before previewing.';
        showStatus(message, false);
      } catch (err) {
        showStatus(err.message, true);
      }
    });
  }

  if (clearBtn && textarea) {
    clearBtn.addEventListener('click', function () {
      textarea.value = '';
      showStatus('', false);
    });
  }
});

document.addEventListener('DOMContentLoaded', function () {
  const controller = document.querySelector('[data-aspect-controller]');
  if (!controller) {
    return;
  }

  const ratioSelect = controller.querySelector('[data-aspect-select]');
  const ratioCustomInput = controller.querySelector('[data-aspect-custom]');
  const ratioHidden = controller.querySelector('[data-aspect-hidden]');
  const sizeSelect = controller.querySelector('[data-size-select]');
  const sizeCustomInput = controller.querySelector('[data-size-custom]');
  const sizeHidden = controller.querySelector('[data-size-hidden]');
  const infographicSelect = document.querySelector('select[name="infographic_type"]');
  const modelSelect = document.querySelector('select[name="desired_model"]');

  if (!ratioSelect || !ratioHidden || !sizeSelect || !sizeHidden) {
    return;
  }

  let defaultSizes = [];
  let presetDefaults = [];
  let modelDefaults = [];
  try {
    defaultSizes = controller.dataset.sizeDefaults ? JSON.parse(controller.dataset.sizeDefaults) : [];
  } catch (err) {
    defaultSizes = [];
  }
  try {
    presetDefaults = controller.dataset.presetDefaults ? JSON.parse(controller.dataset.presetDefaults) : [];
  } catch (err) {
    presetDefaults = [];
  }
  try {
    modelDefaults = controller.dataset.modelDefaults ? JSON.parse(controller.dataset.modelDefaults) : [];
  } catch (err) {
    modelDefaults = [];
  }

  const presetDefaultMap = new Map(
    presetDefaults.map(function (entry) {
      return [entry.id, entry.default_aspect || ''];
    })
  );
  const modelDefaultMap = new Map(
    modelDefaults.map(function (entry) {
      return [entry.id, entry.size || ''];
    })
  );

  const sizeLookup = new Map();
  Array.from(ratioSelect.options).forEach(function (option) {
    const sizesAttr = option.dataset.sizes;
    if (!sizesAttr || !option.value) {
      return;
    }
    sizesAttr
      .split(/\s+/)
      .map(function (size) {
        return size.trim();
      })
      .filter(Boolean)
      .forEach(function (size) {
        if (!sizeLookup.has(size)) {
          sizeLookup.set(size, option.value);
        }
      });
  });

  function sizesForRatio(value) {
    if (!value || value === 'custom') {
      return defaultSizes;
    }
    const selectedOption = Array.from(ratioSelect.options).find(function (opt) {
      return opt.value === value;
    });
    if (!selectedOption || !selectedOption.dataset.sizes) {
      return defaultSizes;
    }
    return selectedOption.dataset.sizes
      .split(/\s+/)
      .map(function (size) {
        return size.trim();
      })
      .filter(Boolean);
  }

  let suppressSync = false;

  function show(element, shouldShow) {
    if (!element) {
      return;
    }
    element.style.display = shouldShow ? '' : 'none';
  }

  function populateSizeOptions(ratioValue) {
    const preservedValue = sizeSelect.value;
    const sizes = sizesForRatio(ratioValue);

    sizeSelect.innerHTML = '';

    const autoOption = document.createElement('option');
    autoOption.value = '';
    autoOption.textContent = sizeAutoLabel();
    sizeSelect.appendChild(autoOption);

    const seen = new Set();
    sizes.forEach(function (size) {
      if (seen.has(size)) {
        return;
      }
      seen.add(size);
      const opt = document.createElement('option');
      opt.value = size;
      opt.textContent = size;
      sizeSelect.appendChild(opt);
    });

    const customOption = document.createElement('option');
    customOption.value = 'custom';
    customOption.textContent = 'Custom size…';
    sizeSelect.appendChild(customOption);

    if (sizes.includes(preservedValue) || preservedValue === 'custom') {
      sizeSelect.value = preservedValue;
    } else {
      sizeSelect.value = '';
      sizeHidden.value = '';
      show(sizeCustomInput, false);
      if (sizeCustomInput) {
        sizeCustomInput.value = '';
      }
    }
  }

  function handleRatioChange() {
    const value = ratioSelect.value;
    if (value === 'custom') {
      show(ratioCustomInput, true);
      ratioHidden.value = ratioCustomInput ? ratioCustomInput.value.trim() : '';
      populateSizeOptions(null);
    } else {
      show(ratioCustomInput, false);
      if (ratioCustomInput) {
        ratioCustomInput.value = '';
      }
      ratioHidden.value = value;
      populateSizeOptions(value);
    }
  }

  function handleRatioCustomInput() {
    if (ratioSelect.value === 'custom') {
      ratioHidden.value = ratioCustomInput.value.trim();
    }
  }

  function handleSizeChange() {
    const value = sizeSelect.value;
    if (value === 'custom') {
      show(sizeCustomInput, true);
      sizeHidden.value = sizeCustomInput ? sizeCustomInput.value.trim() : '';
      return;
    }

    show(sizeCustomInput, false);
    if (sizeCustomInput) {
      sizeCustomInput.value = '';
    }
    sizeHidden.value = value;

    if (value && sizeLookup.has(value) && !suppressSync) {
      const ratioForSize = sizeLookup.get(value);
      if (ratioForSize) {
        suppressSync = true;
        ratioSelect.value = ratioForSize;
        show(ratioCustomInput, false);
        if (ratioCustomInput) {
          ratioCustomInput.value = '';
        }
        ratioHidden.value = ratioForSize;
        populateSizeOptions(ratioForSize);
        sizeSelect.value = value;
        sizeHidden.value = value;
        suppressSync = false;
      }
    }
  }

  function handleSizeCustomInput() {
    if (sizeSelect.value === 'custom') {
      sizeHidden.value = sizeCustomInput.value.trim();
    }
  }

  function currentPresetDefault() {
    const presetId = infographicSelect ? infographicSelect.value : null;
    return (presetId && presetDefaultMap.get(presetId)) || '';
  }

  function currentModelDefault() {
    const modelId = modelSelect ? modelSelect.value : null;
    return (modelId && modelDefaultMap.get(modelId)) || '';
  }

  function updateRatioAutoLabel() {
    const autoOption = ratioSelect.querySelector('option[value=""]');
    if (!autoOption) {
      return;
    }
    const defaultRatio = currentPresetDefault();
    autoOption.textContent = defaultRatio ? `Auto (preset – ${defaultRatio})` : 'Auto (preset)';
  }

  function sizeAutoLabel() {
    const modelDefault = currentModelDefault();
    return modelDefault ? `Auto (model default – ${modelDefault})` : 'Auto (model default)';
  }

  ratioSelect.addEventListener('change', handleRatioChange);
  if (ratioCustomInput) {
    ratioCustomInput.addEventListener('input', handleRatioCustomInput);
  }
  sizeSelect.addEventListener('change', handleSizeChange);
  if (sizeCustomInput) {
    sizeCustomInput.addEventListener('input', handleSizeCustomInput);
  }

  if (infographicSelect) {
    infographicSelect.addEventListener('change', function () {
      updateRatioAutoLabel();
    });
  }

  if (modelSelect) {
    modelSelect.addEventListener('change', function () {
      populateSizeOptions(ratioSelect.value || '');
    });
  }

  updateRatioAutoLabel();
  populateSizeOptions(ratioSelect.value || '');
  ratioHidden.value = '';
  sizeHidden.value = '';
});

document.addEventListener('DOMContentLoaded', function () {
  const viewers = document.querySelectorAll('[data-zoom-viewer]');
  viewers.forEach(function (viewer) {
    const slider = viewer.querySelector('[data-zoom-slider]');
    const label = viewer.querySelector('[data-zoom-label]');
    const target = viewer.querySelector('[data-zoom-target]');
    const btnIn = viewer.querySelector('[data-zoom-in]');
    const btnOut = viewer.querySelector('[data-zoom-out]');
    const defaultValue = Number(viewer.dataset.zoomDefault || slider?.value || 75);

    if (!slider || !label || !target) {
      return;
    }

    function applyZoom(value) {
      const clamped = Math.min(Number(slider.max), Math.max(Number(slider.min), value));
      slider.value = clamped;
      const scale = clamped / 100;
      target.style.transform = `scale(${scale})`;
      label.textContent = `${clamped}%`;
    }

    slider.addEventListener('input', function () {
      applyZoom(Number(slider.value));
    });

    if (btnIn) {
      btnIn.addEventListener('click', function () {
        applyZoom(Number(slider.value) + Number(slider.step || 5));
      });
    }

    if (btnOut) {
      btnOut.addEventListener('click', function () {
        applyZoom(Number(slider.value) - Number(slider.step || 5));
      });
    }

    applyZoom(defaultValue);
  });
});

document.addEventListener('click', function (event) {
  const iterateBtn = event.target.closest('[data-iterate]');
  if (iterateBtn) {
    const field = document.querySelector('[data-parent-field]');
    const indicator = document.querySelector('[data-parent-indicator]');
    if (field) {
      field.value = iterateBtn.getAttribute('data-message-id') || '';
    }
    if (indicator) {
      indicator.classList.add('active');
    }
  }

  const clearBtn = event.target.closest('[data-parent-clear]');
  if (clearBtn) {
    const field = document.querySelector('[data-parent-field]');
    const indicator = document.querySelector('[data-parent-indicator]');
    if (field) {
      field.value = '';
    }
    if (indicator) {
      indicator.classList.remove('active');
    }
  }
});

document.addEventListener('DOMContentLoaded', function () {
  const composer = document.querySelector('[data-chat-composer]');
  if (!composer) {
    return;
  }

  const form = composer.querySelector('form');
  const textarea = composer.querySelector('textarea');
  const modeField = composer.querySelector('[data-mode-field]');
  const modeChips = composer.querySelectorAll('[data-mode-chip]');
  const statusLabel = composer.querySelector('[data-mode-status]');
  const sendIcon = composer.querySelector('[data-send-icon]');
  const modelPicker = document.querySelector('[data-model-picker]');
  const modelSelect = modelPicker ? modelPicker.querySelector('[data-model-select]') : null;
  let textModels = [];
  let imageModels = [];
  let defaultModelId = '';
  if (modelPicker) {
    try {
      textModels = JSON.parse(modelPicker.dataset.textModels || '[]');
      imageModels = JSON.parse(modelPicker.dataset.imageModels || '[]');
    } catch (err) {
      textModels = [];
      imageModels = [];
    }
    defaultModelId = modelPicker.dataset.defaultModel || '';
  }

  const MODE_STATUS = {
    auto: 'Let Gemini pick text or image',
    text: 'Natural conversation',
    image: 'Imagination mode',
    meta_prompt: 'Design Infographix-ready prompts',
  };
  let stickyMode = modeField ? modeField.value || 'auto' : 'auto';
  let predictedMode = 'text';

  function resolveModeFromText(value) {
    if (!value) {
      return 'text';
    }
    const imagePattern =
      /(\bdraw|\billustrat|\bgenerate|\bcreate|\bvisual|\bposter|\binfographic|\bdiagram|\bsketch|\bscene)/i;
    return imagePattern.test(value) ? 'image' : 'text';
  }

  function updateModelSelect(scope) {
    if (!modelSelect) {
      return;
    }
    const groups = [];
    if (scope === 'image') {
      groups.push({ label: 'Image models', items: imageModels });
    } else if (scope === 'text') {
      groups.push({ label: 'Chat models', items: textModels });
    } else if (scope === 'meta_prompt') {
      groups.push({ label: 'Chat models', items: textModels });
    } else {
      groups.push({ label: 'Chat models', items: textModels });
      groups.push({ label: 'Image models', items: imageModels });
    }
    const currentValue = modelSelect.value;
    const fragment = document.createDocumentFragment();
    const availableValues = [];
    groups.forEach(function (group) {
      if (!group.items || !group.items.length) {
        return;
      }
      const optgroup = document.createElement('optgroup');
      optgroup.label = group.label;
      group.items.forEach(function (item) {
        const option = document.createElement('option');
        option.value = item.id;
        option.textContent = item.label;
        optgroup.appendChild(option);
        availableValues.push(item.id);
      });
      fragment.appendChild(optgroup);
    });
    if (!fragment.childNodes.length) {
      return;
    }
    modelSelect.innerHTML = '';
    modelSelect.appendChild(fragment);
    const fallbacks = [currentValue, defaultModelId];
    groups.forEach(function (group) {
      if (group.items && group.items[0]) {
        fallbacks.push(group.items[0].id);
      }
    });
    const picked = fallbacks.find(function (value) {
      return value && availableValues.includes(value);
    });
    if (picked) {
      modelSelect.value = picked;
    }
  }

  function repaintMode() {
    const visualMode = stickyMode === 'auto' ? predictedMode : stickyMode;
    composer.classList.toggle('imagine-mode', visualMode === 'image');
    composer.classList.toggle('meta-mode', stickyMode === 'meta_prompt');
    if (sendIcon) {
      sendIcon.classList.toggle('paint', visualMode === 'image');
    }
    if (statusLabel) {
      statusLabel.textContent = MODE_STATUS[stickyMode] || MODE_STATUS.auto;
    }
    modeChips.forEach(function (chip) {
      chip.classList.toggle('active', chip.dataset.modeChip === stickyMode);
    });
  }

  function setMode(mode) {
    stickyMode = mode || 'auto';
    if (modeField) {
      modeField.value = stickyMode;
    }
    updateModelSelect(stickyMode);
    repaintMode();
  }

  if (textarea) {
    textarea.addEventListener('input', function () {
      const detected = resolveModeFromText(textarea.value);
      predictedMode = detected;
      if (stickyMode === 'auto') {
        repaintMode();
      }
    });
  }

  modeChips.forEach(function (chip) {
    chip.addEventListener('click', function () {
      const targetMode = chip.dataset.modeChip;
      setMode(targetMode);
    });
  });

  setMode(stickyMode);
});

document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('[data-test-prompt-root]').forEach(function (root) {
    let prompts = {};
    try {
      prompts = JSON.parse(root.dataset.testPrompts || '{}');
    } catch (err) {
      prompts = {};
    }
    const toggle = root.querySelector('[data-test-prompt-toggle]');
    const typeSelect = root.querySelector('select[name="infographic_type"]');
    if (!toggle || !typeSelect) {
      return;
    }
    const form = root.matches('form') ? root : root.closest('form');
    if (!form) {
      return;
    }
    const builder = document.querySelector('[data-section-builder]');
    const aspectController = document.querySelector('[data-aspect-controller]');
    const ratioSelect = aspectController ? aspectController.querySelector('[data-aspect-select]') : null;
    const ratioCustom = aspectController ? aspectController.querySelector('[data-aspect-custom]') : null;
    const sizeSelect = aspectController ? aspectController.querySelector('[data-size-select]') : null;
    const sizeCustom = aspectController ? aspectController.querySelector('[data-size-custom]') : null;

    function cloneSections(sections) {
      try {
        return JSON.parse(JSON.stringify(sections || []));
      } catch (err) {
        return [];
      }
    }

    function setTextField(name, value) {
      const input = form.querySelector('[name="' + name + '"]');
      if (input) {
        input.value = value || '';
      }
    }

    function normalizeBool(value) {
      if (typeof value === 'boolean') {
        return value ? 'true' : 'false';
      }
      return value || '';
    }

    function setSelectField(name, value) {
      const select = form.querySelector('select[name="' + name + '"]');
      if (!select) {
        return;
      }
      const normalized = value || '';
      const hasOption = Array.from(select.options).some(function (opt) {
        return opt.value === normalized;
      });
      select.value = hasOption ? normalized : '';
      select.dispatchEvent(new Event('change', { bubbles: true }));
    }

    function applyAspect(value) {
      if (!ratioSelect) {
        return;
      }
      const normalized = (value || '').trim();
      if (!normalized) {
        ratioSelect.value = '';
        ratioSelect.dispatchEvent(new Event('change', { bubbles: true }));
        return;
      }
      const hasOption = Array.from(ratioSelect.options).some(function (opt) {
        return opt.value === normalized;
      });
      if (hasOption) {
        ratioSelect.value = normalized;
        ratioSelect.dispatchEvent(new Event('change', { bubbles: true }));
      } else {
        ratioSelect.value = 'custom';
        ratioSelect.dispatchEvent(new Event('change', { bubbles: true }));
        if (ratioCustom) {
          ratioCustom.value = normalized;
          ratioCustom.dispatchEvent(new Event('input', { bubbles: true }));
        }
      }
    }

    function applyImageSize(value) {
      if (!sizeSelect) {
        return;
      }
      const normalized = (value || '').trim();
      if (!normalized) {
        sizeSelect.value = '';
        sizeSelect.dispatchEvent(new Event('change', { bubbles: true }));
        return;
      }
      const hasOption = Array.from(sizeSelect.options).some(function (opt) {
        return opt.value === normalized;
      });
      if (hasOption) {
        sizeSelect.value = normalized;
        sizeSelect.dispatchEvent(new Event('change', { bubbles: true }));
      } else {
        sizeSelect.value = 'custom';
        sizeSelect.dispatchEvent(new Event('change', { bubbles: true }));
        if (sizeCustom) {
          sizeCustom.value = normalized;
          sizeCustom.dispatchEvent(new Event('input', { bubbles: true }));
        }
      }
    }

    function applySections(sections) {
      if (!builder) {
        return;
      }
      builder.dispatchEvent(
        new CustomEvent('sectionPreset:apply', {
          detail: { sections: cloneSections(sections) },
        })
      );
    }

    function applySample() {
      const sample = prompts[typeSelect.value];
      if (!sample) {
        return;
      }
      setTextField('topic', sample.topic || '');
      setSelectField('audience', sample.audience || '');
      setSelectField('desired_model', sample.desired_model || '');
      setSelectField('visual_style', sample.visual_style || '');
      setTextField('title', sample.title || '');
      setTextField('subtitle', sample.subtitle || '');
      setTextField('footer_text', sample.footer_text || '');
      setSelectField('exact_text_required', normalizeBool(sample.exact_text_required));
      setSelectField('text_preference', sample.text_preference || '');
      setSelectField('render_mode', sample.render_mode || '');
      applyAspect(sample.aspect_ratio || '');
      applyImageSize(sample.image_size || '');
      applySections(sample.sections || []);
      toggle.checked = true;
    }

    function updateToggleState() {
      const sample = prompts[typeSelect.value];
      const wrapper = toggle.closest('.sample-toggle');
      const disabled = !sample;
      toggle.disabled = disabled;
      if (disabled) {
        toggle.checked = false;
        if (wrapper) {
          wrapper.classList.add('disabled');
        }
      } else if (wrapper) {
        wrapper.classList.remove('disabled');
      }
    }

    updateToggleState();

    toggle.addEventListener('change', function () {
      if (toggle.checked) {
        applySample();
      }
    });

    typeSelect.addEventListener('change', function () {
      updateToggleState();
      if (toggle.checked) {
        applySample();
      }
    });
  });
});

document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('[data-attachment-zone]').forEach(function (zone) {
    const input = zone.querySelector('[data-attachment-input]');
    const list = zone.querySelector('[data-attachment-list]');
    const clearBtn = zone.querySelector('[data-attachment-clear]');
    if (!input || !list) {
      return;
    }
    function renderFiles() {
      const files = Array.from(input.files || []);
      list.innerHTML = '';
      files.forEach(function (file) {
        const item = document.createElement('li');
        item.className = 'attachment-chip';
        const size = file.size > 1024 ? Math.round(file.size / 1024) + ' KB' : file.size + ' B';
        item.textContent = file.name + ' · ' + size;
        list.appendChild(item);
      });
      zone.dataset.hasFiles = files.length ? 'true' : 'false';
    }
    input.addEventListener('change', renderFiles);
    if (clearBtn) {
      clearBtn.addEventListener('click', function () {
        input.value = '';
        renderFiles();
      });
    }
    renderFiles();
  });
});

document.addEventListener('DOMContentLoaded', function () {
  const images = document.querySelectorAll('[data-image-card]');
  images.forEach(function (img) {
    function clearLoading() {
      const wrapper = img.closest('.image-card');
      if (wrapper) {
        wrapper.classList.remove('is-loading');
      }
    }
    if (img.complete) {
      clearLoading();
    } else {
      img.addEventListener('load', clearLoading);
      img.addEventListener('error', clearLoading);
    }
  });
});
