import { request, hasToken } from './api.js';

export const byId = (id) => document.getElementById(id);

export function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}

export function button(label, action, className) {
  const node = element('button', label, className);
  node.type = 'button';
  node.addEventListener('click', action);
  return node;
}

export function row(values, actions) {
  const tr = element('tr');
  for (const value of values) tr.append(element('td', value ?? '—'));
  const cell = element('td');
  const group = element('div', undefined, 'actions');
  group.append(...actions);
  cell.append(group);
  tr.append(cell);
  return tr;
}

export function message(node, text) {
  node.textContent = text;
  node.hidden = !text;
}

export function notice(text, isError = false) {
  const node = byId('notice');
  node.classList.toggle('error', isError);
  message(node, text);
}

export function errorText(error, form) {
  const payload = error.payload;
  if (!payload) return error.message;
  return Object.entries(payload).map(([field, value]) => {
    const control = form?.elements.namedItem(field);
    const label = control?.labels?.[0]?.textContent.trim();
    const detail = Array.isArray(value) ? value.join(' ') : value;
    return label ? `${label} — ${detail}` : String(detail);
  }).join('\n') || error.message;
}

const dialog = byId('dialog');
const body = byId('dialog-body');
const dialogError = byId('dialog-error');
let activeDialog;

export function closeDialog() {
  activeDialog?.abort();
  activeDialog = undefined;
  dialog.close();
  body.replaceChildren();
  message(dialogError, '');
}

byId('dialog-close').addEventListener('click', closeDialog);
dialog.addEventListener('cancel', (event) => {
  event.preventDefault();
  closeDialog();
});

export async function openDialog(title, render) {
  closeDialog();
  const controller = new AbortController();
  activeDialog = controller;
  byId('dialog-title').textContent = title;
  body.replaceChildren(element('p', 'Carregando…'));
  dialog.showModal();
  try {
    const content = await render(controller.signal);
    if (!controller.signal.aborted) {
      body.replaceChildren(content);
      body.querySelector('input, select')?.focus();
    }
  } catch (error) {
    if (!controller.signal.aborted) {
      body.replaceChildren();
      message(dialogError, errorText(error));
    }
  }
}

export function disableButton(control, pendingLabel) {
  const label = control.textContent;
  control.disabled = true;
  control.textContent = pendingLabel;
  return () => {
    control.textContent = label;
    control.disabled = false;
  };
}

export function formData(form) {
  return Object.fromEntries(
    [...new FormData(form)].map(([key, value]) => [key, value.trim()]),
  );
}

export function editor(template, path, original, signal, onSaved, prepare = () => {}) {
  const form = byId(template).content.firstElementChild.cloneNode(true);
  prepare(form);
  for (const control of form.elements) {
    if (control.name && original?.[control.name] != null) control.value = original[control.name];
  }

  const initial = formData(form);
  const submit = form.querySelector('button[type=submit]');
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    if (submit.disabled || !hasToken()) return;
    const data = formData(form);
    if (original) {
      for (const key of Object.keys(data)) {
        if (data[key] === initial[key]) delete data[key];
      }
    }
    if ('data_cadastro' in data && !data.data_cadastro) data.data_cadastro = null;
    if (!Object.keys(data).length) {
      closeDialog();
      notice('Nenhuma alteração para salvar.');
      return;
    }

    message(dialogError, '');
    const restore = disableButton(submit, 'Salvando…');
    try {
      await request(path, { method: original ? 'PATCH' : 'POST', data });
      if (!signal.aborted) closeDialog();
      onSaved();
    } catch (error) {
      if (!signal.aborted) message(dialogError, errorText(error, form));
    } finally {
      restore();
    }
  });
  return form;
}

export function confirmDelete(title, name, path, onDeleted) {
  if (!hasToken()) return;
  openDialog(title, (signal) => {
    const wrapper = element('div');
    const remove = button('Confirmar exclusão', async () => {
      if (remove.disabled || !hasToken()) return;
      message(dialogError, '');
      const restore = disableButton(remove, 'Excluindo…');
      try {
        await request(path, { method: 'DELETE' });
        if (!signal.aborted) closeDialog();
        onDeleted();
      } catch (error) {
        if (!signal.aborted) {
          message(dialogError, error.status === 409
            ? 'Este vendedor possui clientes vinculados. Transfira os vínculos antes de excluí-lo.'
            : errorText(error));
        }
      } finally {
        restore();
      }
    }, 'danger');
    wrapper.append(element('p', `Confirma a exclusão de “${name}”?`), remove);
    return wrapper;
  });
}
