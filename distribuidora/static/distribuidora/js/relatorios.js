import { endpoints, request } from './api.js';
import { showClient } from './clientes.js';
import { byId, button, element, errorText, row } from './ui.js';

const collator = new Intl.Collator('pt-BR');
const missingNeighborhood = 'Sem bairro informado';

async function collectReport(signal) {
  const neighborhoods = new Map();
  const pendingReview = [];
  const visited = new Set();
  let total = 0;
  let page = '1';

  while (page) {
    if (visited.has(page)) throw new Error('A API retornou uma página repetida.');
    visited.add(page);
    const result = await request(`${endpoints.clientes}?page=${encodeURIComponent(page)}`, { signal });
    for (const client of result.results) {
      const bairro = client.bairro?.trim() || '';
      const key = bairro.toLocaleLowerCase('pt-BR');
      const group = neighborhoods.get(key) ?? { label: bairro || missingNeighborhood, count: 0 };
      group.count += 1;
      neighborhoods.set(key, group);
      total += 1;

      if (client.precisa_revisao === true) {
        const { id, id_cliente, razao_social, cidade, uf, vendedor_responsavel } = client;
        pendingReview.push({ id, id_cliente, razao_social, bairro, cidade, uf, vendedor_responsavel });
      }
    }

    if (!result.next) break;
    page = new URL(result.next, location.origin).searchParams.get('page');
    if (!page) throw new Error('A API retornou um link de paginação inválido.');
  }

  return { neighborhoods: [...neighborhoods.values()], pendingReview, total };
}

export function setupReports(refresh) {
  const status = byId('reports-status');
  const content = byId('reports-content');
  const reload = byId('refresh-reports');
  const neighborhoodRows = byId('neighborhood-rows');
  const reviewRows = byId('review-rows');
  reload.addEventListener('click', () => refresh('relatorios'));

  return async (signal) => {
    content.hidden = true;
    neighborhoodRows.replaceChildren();
    reviewRows.replaceChildren();
    reload.disabled = true;
    status.textContent = 'Carregando relatórios…';
    try {
      const { neighborhoods, pendingReview, total } = await collectReport(signal);
      if (signal.aborted) return;

      neighborhoods.sort((a, b) => b.count - a.count || collator.compare(a.label, b.label));
      for (const group of neighborhoods) {
        const item = element('tr');
        const label = element('th', group.label);
        label.scope = 'row';
        item.append(label, element('td', group.count));
        neighborhoodRows.append(item);
      }
      byId('neighborhood-total').textContent = total;
      byId('review-table').hidden = !pendingReview.length;
      byId('review-status').textContent = pendingReview.length
        ? `${pendingReview.length} ${pendingReview.length === 1 ? 'cliente pendente' : 'clientes pendentes'}`
        : 'Nenhum cliente precisa de revisão.';

      for (const client of pendingReview) {
        const open = button('Visualizar', () => showClient(client.id, (id) => `Vendedor #${id}`));
        reviewRows.append(row([
          client.id_cliente, client.razao_social, client.bairro || '—', client.cidade, client.uf,
        ], [open]));
      }
      status.textContent = total ? '' : 'Nenhum cliente cadastrado.';
      content.hidden = false;
    } catch (error) {
      if (!signal.aborted) status.textContent = errorText(error);
    } finally {
      if (!signal.aborted) reload.disabled = false;
    }
  };
}
