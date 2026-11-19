from django.contrib.staticfiles import finders
from django.test import SimpleTestCase
from django.urls import reverse


class FrontendPagesTests(SimpleTestCase):
    def test_inicio_abre_login_com_opcao_de_visitante(self):
        response = self.client.get(reverse('frontend:inicio'), follow=True)
        self.assertRedirects(response, reverse('frontend:login'))
        self.assertContains(response, 'Continuar como visitante')
        self.assertContains(response, f'href="{reverse("frontend:clientes")}"')

    def test_paginas_renderizam_o_painel_com_links_para_a_api(self):
        for page in ('clientes', 'vendedores', 'relatorios', 'login'):
            with self.subTest(page=page):
                response = self.client.get(reverse(f'frontend:{page}'))
                self.assertTemplateUsed(response, 'distribuidora/base.html')
                self.assertContains(response, f'id="{page}"')
                self.assertContains(response, f'data-clientes-url="{reverse("cliente-list")}"')
                self.assertContains(response, f'data-vendedores-url="{reverse("vendedor-list")}"')
                self.assertContains(response, f'data-token-url="{reverse("api-token")}"')
                self.assertNotContains(response, 'Authorization:')

    def test_arquivos_estaticos_do_painel_estao_disponiveis(self):
        response = self.client.get(reverse('frontend:clientes'))
        for path in ('css/style.css', 'js/app.js'):
            self.assertContains(response, f'/static/distribuidora/{path}')

        for filename in ('app', 'ui', 'api', 'auth', 'clientes', 'vendedores', 'relatorios'):
            with self.subTest(filename=filename):
                self.assertIsNotNone(finders.find(f'distribuidora/js/{filename}.js'))
        self.assertIsNotNone(finders.find('distribuidora/css/style.css'))
