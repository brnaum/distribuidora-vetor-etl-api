import { endpoints, hasToken, recordPath, request } from './api.js';
import { showClient } from './clientes.js';
import { byId, button, confirmDelete, editor, element, errorText, notice, openDialog, row } from './ui.js';

export function setupSellers(refresh) {
  const status = byId('sellers-status');
  const rows = byId('seller-rows');
  const retry = byId('sellers-retry');

  function finish(text) {
    notice(text);
    refresh('vendedores');
  }

  function edit(seller) {
    if (!hasToken()) return;
    openDialog(seller ? 'Editar vendedor' : 'Novo vendedor', async (signal) => {
      const path = seller ? recordPath(endpoints.vendedores, seller.id) : endpoints.vendedores;
      const original = seller ? await request(path, { signal }) : null;
      return editor('seller-form-template', path, original, signal, () => {
        finish(seller ? 'Vendedor atualizado.' : 'Vendedor cadastrado.');
      });
    });
  }

  function linkedClients(seller) {
    openDialog(`Clientes de ${seller.nome}`, async (signal) => {
      const clients = await request(`${recordPath(endpoints.vendedores, seller.id)}clientes/`, { signal });
      if (!clients.length) return element('p', 'Nenhum cliente vinculado.');
      const list = element('ul');
      for (const client of clients) {
        const item = element('li');
        item.append(button(`${client.razao_social} · ${client.id_cliente}`, () => {
          showClient(client.id, () => seller.nome);
        }));
        list.append(item);
      }
      return list;
    });
  }

  byId('new-seller').addEventListener('click', () => edit(null));
  retry.addEventListener('click', () => refresh('vendedores'));

  return async (signal) => {
    rows.replaceChildren();
    retry.hidden = true;
    status.textContent = 'Carregando vendedores…';
    try {
      const sellers = await request(endpoints.vendedores, { signal });
      if (signal.aborted) return;
      status.textContent = sellers.length
        ? `${sellers.length} ${sellers.length === 1 ? 'vendedor encontrado' : 'vendedores encontrados'}`
        : 'Nenhum vendedor cadastrado.';
      for (const seller of sellers) {
        const actions = [button('Ver clientes', () => linkedClients(seller))];
        if (hasToken()) {
          actions.push(
            button('Editar', () => edit(seller)),
            button('Excluir', () => confirmDelete(
              'Excluir vendedor', seller.nome, recordPath(endpoints.vendedores, seller.id),
              () => finish('Vendedor excluído.'),
            ), 'danger'),
          );
        }
        rows.append(row([seller.id, seller.nome], actions));
      }
    } catch (error) {
      if (signal.aborted) return;
      status.textContent = errorText(error);
      retry.hidden = false;
    }
  };
}
