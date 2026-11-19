from django.db.models import Count

from .normalizadores import chave_bairro


def clientes_por_bairro(clientes, nome):
    chave = chave_bairro(nome)
    bairros = clientes.order_by().values_list('bairro', flat=True).distinct()
    correspondentes = [bairro for bairro in bairros if chave_bairro(bairro) == chave]
    if not chave:
        return clientes.none()
    return clientes.filter(bairro__in=correspondentes)


def clientes_por_vendedor(vendedor):
    return vendedor.clientes.order_by('pk')


def resumo_por_bairro(clientes):
    variantes = clientes.order_by().values('bairro').annotate(total=Count('pk'))
    grupos = {}
    for variante in sorted(variantes, key=lambda item: (-item['total'], item['bairro'] or '')):
        nome = ' '.join((variante['bairro'] or '').split())
        chave = chave_bairro(nome)
        grupo = grupos.setdefault(chave, {'bairro': nome if chave else None, 'total': 0})
        grupo['total'] += variante['total']
    return [grupos[chave] for chave in sorted(grupos, key=lambda valor: (not valor, valor))]
