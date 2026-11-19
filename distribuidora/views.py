from django.db.models.deletion import RestrictedError

from rest_framework import serializers, viewsets
from rest_framework.exceptions import APIException
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .models import Cliente, Vendedor
from .serializers import ClientePublicoSerializer, ClienteSerializer, VendedorSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import (
    extend_schema,
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


class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.order_by('pk')
    serializer_class = ClienteSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = ClientePagination

    def get_serializer_class(self):
        if getattr(self, 'swagger_fake_view', False) or self.request.user.is_authenticated:
            return ClienteSerializer
        return ClientePublicoSerializer

    @extend_schema(
        parameters=[
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
        url_path=r'bairro/(?P<nome>[^/.]+)'
    )
    def buscar_por_bairro(self, request, nome=None):
        clientes = self.get_queryset().filter(
            bairro__iexact=nome
        )

        page = self.paginate_queryset(clientes)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(clientes, many=True)

        return Response(serializer.data)


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

        clientes = Cliente.objects.filter(
            vendedor_responsavel=vendedor
        ).order_by('pk')

        serializer_class = (
            ClienteSerializer if request.user.is_authenticated else ClientePublicoSerializer
        )
        serializer = serializer_class(clientes, many=True, context=self.get_serializer_context())

        return Response(serializer.data)