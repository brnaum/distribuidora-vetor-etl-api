from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from .models import Cliente, Vendedor


class VendedorAPITests(APITestCase):

    def test_nao_excluir_vendedor_com_clientes(self):
        usuario = get_user_model().objects.create_user(
            username='usuario_teste',
            password='senha_teste_123'
        )

        self.client.force_authenticate(user=usuario)

        vendedor = Vendedor.objects.create(
            nome='Vendedor Teste'
        )

        Cliente.objects.create(
            id_cliente='CLI001',
            razao_social='Cliente Teste',
            cidade='Brasília',
            uf='DF',
            vendedor_responsavel=vendedor
        )

        url = reverse('vendedor-detail', args=[vendedor.id])

        resposta = self.client.delete(url)

        self.assertEqual(
            resposta.status_code,
            status.HTTP_409_CONFLICT
        )

        self.assertTrue(
            Vendedor.objects.filter(id=vendedor.id).exists()
        )

class ClienteBairroAPITests(APITestCase):

    def test_buscar_clientes_por_bairro(self):
        vendedor = Vendedor.objects.create(
            nome='Vendedor Teste'
        )

        Cliente.objects.create(
            id_cliente='CLI001',
            razao_social='Cliente Asa Norte',
            bairro='Asa Norte',
            cidade='Brasília',
            uf='DF',
            vendedor_responsavel=vendedor
        )

        Cliente.objects.create(
            id_cliente='CLI002',
            razao_social='Cliente Asa Sul',
            bairro='Asa Sul',
            cidade='Brasília',
            uf='DF',
            vendedor_responsavel=vendedor
        )

        url = reverse(
            'cliente-buscar-por-bairro',
            kwargs={'nome': 'asa norte'}
        )

        resposta = self.client.get(url)

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.data['count'], 1)
        self.assertEqual(resposta.data['results'][0]['id_cliente'], 'CLI001')

class ClientePorVendedorAPITests(APITestCase):

    def test_listar_clientes_de_um_vendedor(self):
        vendedor1 = Vendedor.objects.create(
            nome='Vendedor Um'
        )

        vendedor2 = Vendedor.objects.create(
            nome='Vendedor Dois'
        )

        Cliente.objects.create(
            id_cliente='CLI001',
            razao_social='Cliente do Vendedor Um',
            cidade='Brasília',
            uf='DF',
            vendedor_responsavel=vendedor1
        )

        Cliente.objects.create(
            id_cliente='CLI002',
            razao_social='Cliente do Vendedor Dois',
            cidade='Brasília',
            uf='DF',
            vendedor_responsavel=vendedor2
        )

        url = reverse(
            'vendedor-listar-clientes',
            args=[vendedor1.id]
        )

        resposta = self.client.get(url)

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(len(resposta.data), 1)
        self.assertEqual(
            resposta.data[0]['id_cliente'],
            'CLI001'
        )

class ClienteCadastroAPITests(APITestCase):

    def setUp(self):
        self.url = reverse('cliente-list')

    def test_visitante_nao_pode_cadastrar_cliente(self):
        dados = {
            'id_cliente': 'CLI003',
            'razao_social': 'Cliente Teste'
        }

        resposta = self.client.post(
            self.url,
            dados,
            format='json'
        )

        self.assertEqual(
            resposta.status_code,
            status.HTTP_401_UNAUTHORIZED
        )

        self.assertFalse(
            Cliente.objects.filter(
                id_cliente='CLI003'
            ).exists()
        )

    def test_usuario_autenticado_pode_cadastrar_cliente(self):
        usuario = get_user_model().objects.create_user(
        username='usuario_cadastro',
        password='senha_teste_123'
    )

        self.client.force_authenticate(user=usuario)

        vendedor = Vendedor.objects.create(
        nome='Vendedor Teste'
    )

        dados = {
        'id_cliente': 'CLI004',
        'razao_social': 'Cliente Autenticado',
        'bairro': 'Asa Norte',
        'cidade': 'Brasília',
        'uf': 'DF',
        'vendedor_responsavel': vendedor.id
    }

        resposta = self.client.post(
        self.url,
        dados,
        format='json'
    )

        self.assertEqual(
        resposta.status_code,
        status.HTTP_201_CREATED,
        resposta.data
    )

        self.assertTrue(
        Cliente.objects.filter(
            id_cliente='CLI004'
        ).exists()
    )

    def test_visitante_pode_listar_clientes(self):
        resposta = self.client.get(self.url)

        self.assertEqual(
        resposta.status_code,
        status.HTTP_200_OK
    )

    def test_visitante_nao_pode_editar_cliente(self):
        vendedor = Vendedor.objects.create(
        nome='Vendedor Teste'
    )

        cliente = Cliente.objects.create(
        id_cliente='CLI005',
        razao_social='Cliente Original',
        bairro='Asa Norte',
        cidade='Brasília',
        uf='DF',
        vendedor_responsavel=vendedor
    )

        url = reverse(
        'cliente-detail',
        args=[cliente.pk]
    )

        resposta = self.client.patch(
        url,
        {'razao_social': 'Cliente Alterado'},
        format='json'
    )

        self.assertEqual(
        resposta.status_code,
        status.HTTP_401_UNAUTHORIZED
    )

        cliente.refresh_from_db()

        self.assertEqual(
        cliente.razao_social,
        'Cliente Original'
    )

    def test_usuario_autenticado_pode_editar_cliente(self):
        usuario = get_user_model().objects.create_user(
        username='usuario_edicao',
        password='senha_teste_123'
    )

        self.client.force_authenticate(user=usuario)

        vendedor = Vendedor.objects.create(
        nome='Vendedor Teste'
    )

        cliente = Cliente.objects.create(
        id_cliente='CLI006',
        razao_social='Cliente Original',
        bairro='Asa Norte',
        cidade='Brasília',
        uf='DF',
        vendedor_responsavel=vendedor
    )

        url = reverse('cliente-detail', args=[cliente.pk])

        resposta = self.client.patch(
        url,
        {'razao_social': 'Cliente Atualizado'},
        format='json'
    )

        self.assertEqual(
        resposta.status_code,
        status.HTTP_200_OK,
        resposta.data
    )

        cliente.refresh_from_db()

        self.assertEqual(
        cliente.razao_social,
        'Cliente Atualizado'
    )

    def test_visitante_nao_pode_excluir_cliente(self):
        vendedor = Vendedor.objects.create(
        nome='Vendedor Teste'
    )

        cliente = Cliente.objects.create(
        id_cliente='CLI007',
        razao_social='Cliente para Exclusão',
        bairro='Asa Norte',
        cidade='Brasília',
        uf='DF',
        vendedor_responsavel=vendedor
    )

        url = reverse('cliente-detail', args=[cliente.pk])

        resposta = self.client.delete(url)

        self.assertEqual(
        resposta.status_code,
        status.HTTP_401_UNAUTHORIZED
    )

        self.assertTrue(
        Cliente.objects.filter(pk=cliente.pk).exists()
    )

    def test_usuario_autenticado_pode_excluir_cliente(self):
        usuario = get_user_model().objects.create_user(
            username='usuario_exclusao',
            password='senha_teste_123'
        )
        self.client.force_authenticate(user=usuario)

        vendedor = Vendedor.objects.create(nome='Vendedor Teste')
        cliente = Cliente.objects.create(
            id_cliente='CLI005',
            razao_social='Cliente Para Excluir',
            bairro='Asa Norte',
            cidade='Brasília',
            uf='DF',
            vendedor_responsavel=vendedor
        )

        url = reverse('cliente-detail', args=[cliente.pk])
        resposta = self.client.delete(url)

        self.assertEqual(resposta.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Cliente.objects.filter(pk=cliente.pk).exists())

    def test_usuario_autenticado_pode_consultar_cliente(self):
        usuario = get_user_model().objects.create_user(
            username='usuario_consulta',
            password='senha_teste_123'
        )
        self.client.force_authenticate(user=usuario)

        vendedor = Vendedor.objects.create(nome='Vendedor Teste')
        cliente = Cliente.objects.create(
            id_cliente='CLI007',
            razao_social='Cliente Consulta',
            bairro='Asa Norte',
            cidade='Brasília',
            uf='DF',
            vendedor_responsavel=vendedor
        )

        url = reverse('cliente-detail', args=[cliente.pk])
        resposta = self.client.get(url)

        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta.data['id_cliente'], 'CLI007')

    def test_visitante_pode_consultar_cliente(self):
        vendedor = Vendedor.objects.create(nome='Vendedor Teste')
        cliente = Cliente.objects.create(
            id_cliente='CLI008',
            razao_social='Cliente Público',
            bairro='Asa Sul',
            cidade='Brasília',
            uf='DF',
            vendedor_responsavel=vendedor
        )

        url = reverse('cliente-detail', args=[cliente.pk])
        resposta = self.client.get(url)

        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta.data['id_cliente'], 'CLI008')

    def test_consultar_cliente_inexistente_retorna_404(self):
        url = reverse('cliente-detail', args=[999999])
        resposta = self.client.get(url)

        self.assertEqual(
            resposta.status_code,
            status.HTTP_404_NOT_FOUND
        )

    def test_usuario_autenticado_pode_editar_parcialmente_cliente(self):
        usuario = get_user_model().objects.create_user(
            username='usuario_patch',
            password='senha_teste_123'
        )
        self.client.force_authenticate(user=usuario)

        vendedor = Vendedor.objects.create(nome='Vendedor Teste')
        cliente = Cliente.objects.create(
            id_cliente='CLI009',
            razao_social='Cliente Original',
            bairro='Asa Norte',
            cidade='Brasília',
            uf='DF',
            vendedor_responsavel=vendedor
        )

        url = reverse('cliente-detail', args=[cliente.pk])
        resposta = self.client.patch(
            url,
            {'razao_social': 'Cliente Atualizado'},
            format='json'
        )

        self.assertEqual(resposta.status_code, status.HTTP_200_OK)

        cliente.refresh_from_db()
        self.assertEqual(cliente.razao_social, 'Cliente Atualizado')

    def test_visitante_nao_pode_editar_parcialmente_cliente(self):
        vendedor = Vendedor.objects.create(nome='Vendedor Teste')
        cliente = Cliente.objects.create(
            id_cliente='CLI010',
            razao_social='Cliente Original',
            bairro='Asa Norte',
            cidade='Brasília',
            uf='DF',
            vendedor_responsavel=vendedor
        )

        url = reverse('cliente-detail', args=[cliente.pk])
        resposta = self.client.patch(
            url,
            {'razao_social': 'Alteração Indevida'},
            format='json'
        )

        self.assertEqual(
            resposta.status_code,
            status.HTTP_401_UNAUTHORIZED
        )

        cliente.refresh_from_db()
        self.assertEqual(cliente.razao_social, 'Cliente Original')

    def test_usuario_autenticado_nao_pode_excluir_cliente_inexistente(self):
        usuario = get_user_model().objects.create_user(
            username='usuario_delete_404',
            password='senha_teste_123'
        )
        self.client.force_authenticate(user=usuario)

        url = reverse('cliente-detail', args=[999999])
        resposta = self.client.delete(url)

        self.assertEqual(
            resposta.status_code,
            status.HTTP_404_NOT_FOUND
        )


class ContratoAPITests(APITestCase):
    def setUp(self):
        self.vendedor = Vendedor.objects.create(nome='Vendedor Contrato')
        self.cliente = Cliente.objects.create(
            id_cliente='CLI100',
            razao_social='Cliente Contrato',
            cidade='Brasília',
            uf='DF',
            bairro='Asa Norte',
            vendedor_responsavel=self.vendedor,
            cnpj='11222333000181',
            telefone='61912345678',
            email='cliente@example.com',
        )

    def autenticar_com_token(self):
        usuario = get_user_model().objects.create_user(
            username='usuario_token', password='senha_teste_123',
        )
        resposta = self.client.post(
            reverse('api-token'),
            {'username': usuario.username, 'password': 'senha_teste_123'},
            format='json',
        )
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {resposta.data['token']}")

    def test_token_autoriza_escrita_e_leitura_de_contatos(self):
        self.autenticar_com_token()
        resposta = self.client.patch(
            reverse('cliente-detail', args=[self.cliente.pk]),
            {'uf': 'sp', 'cep': '01310-100', 'precisa_revisao': True},
            format='json',
        )
        self.assertEqual(resposta.status_code, status.HTTP_200_OK, resposta.data)
        self.assertEqual(resposta.data['email'], self.cliente.email)
        self.cliente.refresh_from_db()
        self.assertEqual((self.cliente.uf, self.cliente.cep), ('SP', '01310100'))
        self.assertFalse(self.cliente.precisa_revisao)

    def test_visitante_nao_recebe_dados_restritos(self):
        rotas = (
            (reverse('cliente-list'), 'pagina'),
            (reverse('cliente-detail', args=[self.cliente.pk]), 'objeto'),
            (reverse('cliente-buscar-por-bairro', kwargs={'nome': 'asa norte'}), 'pagina'),
            (reverse('vendedor-listar-clientes', args=[self.vendedor.pk]), 'lista'),
        )
        for url, formato in rotas:
            with self.subTest(url=url):
                resposta = self.client.get(url)
                self.assertEqual(resposta.status_code, status.HTTP_200_OK)
                dados = resposta.data
                if formato == 'pagina':
                    dados = dados['results'][0]
                elif formato == 'lista':
                    dados = dados[0]
                self.assertEqual(dados['id_cliente'], self.cliente.id_cliente)
                for campo in ('cnpj', 'telefone', 'email'):
                    self.assertNotIn(campo, dados)

    def test_visitante_nao_pode_escrever_vendedores(self):
        detalhe = reverse('vendedor-detail', args=[self.vendedor.pk])
        for metodo, url in (
            (self.client.post, reverse('vendedor-list')),
            (self.client.put, detalhe),
            (self.client.patch, detalhe),
            (self.client.delete, detalhe),
        ):
            with self.subTest(metodo=metodo.__name__):
                resposta = metodo(url, {'nome': 'Outro nome'}, format='json')
                self.assertEqual(resposta.status_code, status.HTTP_401_UNAUTHORIZED)
        self.vendedor.refresh_from_db()
        self.assertEqual(self.vendedor.nome, 'Vendedor Contrato')
        self.assertEqual(Vendedor.objects.count(), 1)

    def test_dados_invalidos_retornam_400(self):
        self.autenticar_com_token()
        resposta = self.client.patch(
            reverse('cliente-detail', args=[self.cliente.pk]),
            {'uf': 'XX', 'cnpj': '123', 'cep': '12', 'telefone': 'abc'},
            format='json',
        )
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(set(resposta.data), {'uf', 'cnpj', 'cep', 'telefone'})

    def test_lista_de_clientes_pagina_em_ordem_estavel(self):
        Cliente.objects.bulk_create([
            Cliente(
                id_cliente=f'EXTRA{i}', razao_social='Cliente adicional',
                cidade='Brasília', uf='DF', vendedor_responsavel=self.vendedor,
            )
            for i in range(20)
        ])
        url = reverse('cliente-list')
        primeira = self.client.get(url)
        segunda = self.client.get(url, {'page': 2})
        self.assertEqual(primeira.data['count'], 21)
        self.assertEqual(len(primeira.data['results']), 20)
        self.assertIsNotNone(primeira.data['next'])
        self.assertEqual([item['id_cliente'] for item in segunda.data['results']], ['EXTRA19'])
        self.assertIsNone(segunda.data['next'])
