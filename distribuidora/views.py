from django.db.models.deletion import RestrictedError
from django.shortcuts import get_object_or_404

from rest_framework import serializers, viewsets
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .models import Cliente, Vendedor
from .serializers import (
    ClientePublicoSerializer,
    ClienteSerializer,
    ResumoBairroSerializer,
    VendedorSerializer,
)
from .services import clientes_por_bairro, clientes_por_vendedor, resumo_por_bairro
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiResponse,
    inline_serializer,
)

class VendedorComClientesError(APIException):
    status_code = 409
    default_detail = (
        'Não é possível excluir um vendedor '
        'que possui clientes vinculados.'
    )
    default_code = 'vendedor_com_clientes'


class ClientePagination(PageNumberPagination):
    page_size = 20


filtro_revisao = OpenApiParameter(
    name='precisa_revisao',
    type=bool,
    description='Filtra clientes marcados (true) ou não marcados (false) para revisão.',
)


@extend_schema_view(list=extend_schema(parameters=[filtro_revisao]))
class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.order_by('pk')
    serializer_class = ClienteSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = ClientePagination

    def filtrar_revisao(self, clientes):
        valor = self.request.query_params.get('precisa_revisao')
        if valor is None:
            return clientes
        valor = valor.casefold()
        if valor not in ('true', 'false'):
            raise ValidationError({'precisa_revisao': 'Use true ou false.'})
        return clientes.filter(precisa_revisao=valor == 'true')

    def list(self, request, *args, **kwargs):
        return self.resposta_clientes(self.get_queryset())

    def resposta_clientes(self, clientes):
        clientes = self.filtrar_revisao(self.filter_queryset(clientes))
        page = self.paginate_queryset(clientes)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        return Response(self.get_serializer(clientes, many=True).data)

    @extend_schema(
        parameters=[
            filtro_revisao,
            OpenApiParameter(
                name='nome',
                type=str,
                location=OpenApiParameter.PATH,
                description='Nome do bairro para filtrar os clientes.'
            )
        ],
        responses=ClienteSerializer(many=True),
    )
    @action(
        detail=False,
        methods=['get'],
        url_path=r'bairro/(?P<nome>[^/]+)'
    )
    def buscar_por_bairro(self, request, nome):
        return self.resposta_clientes(clientes_por_bairro(self.get_queryset(), nome))

    @extend_schema(
        parameters=[OpenApiParameter('id', int, OpenApiParameter.PATH), filtro_revisao],
        responses=ClienteSerializer(many=True),
    )
    @action(detail=False, methods=['get'], url_path=r'vendedor/(?P<id>[0-9]+)')
    def buscar_por_vendedor(self, request, id):
        vendedor = get_object_or_404(Vendedor, pk=id)
        return self.resposta_clientes(clientes_por_vendedor(vendedor))

    @extend_schema(responses=ResumoBairroSerializer(many=True))
    @action(detail=False, methods=['get'], url_path='bairros', pagination_class=None)
    def listar_bairros(self, request):
        resumo = resumo_por_bairro(self.get_queryset())
        return Response(self.get_serializer(resumo, many=True).data)

    def get_serializer_class(self):
        if self.action == 'listar_bairros':
            return ResumoBairroSerializer
        if getattr(self, 'swagger_fake_view', False) or self.request.user.is_authenticated:
            return ClienteSerializer
        return ClientePublicoSerializer


class VendedorViewSet(viewsets.ModelViewSet):
    queryset = Vendedor.objects.all()
    serializer_class = VendedorSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    @extend_schema(responses={
        204: None,
        409: OpenApiResponse(
            response=inline_serializer(
                name='VendedorComClientes',
                fields={'detail': serializers.CharField()},
            ),
            description='O vendedor possui clientes vinculados.',
        ),
    })
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    def perform_destroy(self, instance):
        try:
            instance.delete()
        except RestrictedError:
            raise VendedorComClientesError()

    @extend_schema(
        responses=ClienteSerializer(many=True),
        description='Lista de clientes do vendedor. CNPJ, telefone e e-mail exigem autenticação.',
    )
    @action(
        detail=True,
        methods=['get'],
        url_path='clientes'
    )
    def listar_clientes(self, request, pk=None):
        vendedor = self.get_object()

        clientes = clientes_por_vendedor(vendedor)

        serializer_class = (
            ClienteSerializer if request.user.is_authenticated else ClientePublicoSerializer
        )
        serializer = serializer_class(clientes, many=True, context=self.get_serializer_context())

        return Response(serializer.data)