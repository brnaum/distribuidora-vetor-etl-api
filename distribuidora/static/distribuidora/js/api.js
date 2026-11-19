const main = document.querySelector('main');

export const endpoints = {
  clientes: main.dataset.clientesUrl,
  vendedores: main.dataset.vendedoresUrl,
  token: main.dataset.tokenUrl,
};

let token = null;
export const hasToken = () => Boolean(token);
export function setToken(value) {
  token = value;
}

export async function request(path, { method = 'GET', data, signal } = {}) {
  const url = new URL(path, location.origin);
  if (url.origin !== location.origin) throw new Error('Endereço da API inválido.');

  const headers = { Accept: 'application/json' };
  const activeToken = url.pathname === endpoints.token ? null : token;
  if (activeToken) headers.Authorization = `Token ${activeToken}`;
  if (data !== undefined) headers['Content-Type'] = 'application/json';

  let response;
  try {
    response = await fetch(url, {
      method, headers, signal, credentials: 'omit', cache: 'no-store',
      body: data === undefined ? undefined : JSON.stringify(data),
    });
  } catch (error) {
    if (error.name === 'AbortError') throw error;
    throw new Error('Falha de conexão. Verifique o servidor e tente novamente.');
  }

  if (response.status === 204) return null;
  const payload = await response.json().catch(() => null);
  if (response.ok && payload !== null) return payload;

  if (response.status === 401 && activeToken && activeToken === token && !signal?.aborted) {
    window.dispatchEvent(new Event('vetor:session-expired'));
  }

  const messages = {
    400: 'Confira os dados informados.',
    401: 'Entre para continuar.',
    403: 'Sua conta não tem permissão para esta operação.',
    404: 'Registro ou página não encontrada.',
    409: 'O registro possui vínculos que impedem esta operação.',
  };
  const error = new Error(messages[response.status] ?? 'O servidor não concluiu a operação.');
  error.status = response.status;
  if (response.status < 500 && payload && typeof payload === 'object') error.payload = payload;
  throw error;
}

export const recordPath = (collection, id) => `${collection}${encodeURIComponent(id)}/`;
