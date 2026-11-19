
import re

from rest_framework import serializers
from .models import Cliente, Vendedor, Auditoria
from .normalizadores import normalizar_cep

class ClientePublicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = (
            'id', 'id_cliente', 'razao_social', 'bairro', 'cep', 'cidade',
            'uf', 'data_cadastro', 'vendedor_responsavel', 'precisa_revisao',
        )
        read_only_fields = ('precisa_revisao',)


class ClienteSerializer(ClientePublicoSerializer):
    class Meta(ClientePublicoSerializer.Meta):
        fields = ClientePublicoSerializer.Meta.fields + ('cnpj', 'telefone', 'email')

    def validate_uf(self, value):
        estados = {
            'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
            'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
            'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO',
        }
        uf = value.upper()
        if uf not in estados:
            raise serializers.ValidationError('Informe uma UF brasileira válida.')
        return uf

    def validate_cnpj(self, value):
        if value in (None, ''):
            return value
        cnpj = value.upper()
        if not re.fullmatch(
            r'(?:[A-Z0-9]{12}[0-9]{2}|[A-Z0-9]{2}\.[A-Z0-9]{3}\.[A-Z0-9]{3}/[A-Z0-9]{4}-[0-9]{2})',
            cnpj,
        ):
            raise serializers.ValidationError('Informe um CNPJ em formato válido.')
        return re.sub(r'[./-]', '', cnpj)

    def validate_cep(self, value):
        if value in (None, ''):
            return value
        cep = normalizar_cep(value) if re.fullmatch(r'[0-9]{5}-?[0-9]{3}', value) else None
        if cep is None:
            raise serializers.ValidationError('Informe um CEP válido com oito dígitos.')
        return cep

    def validate_telefone(self, value):
        if value in (None, ''):
            return value
        if not re.fullmatch(r'(?:\+?55 ?)?(?:\([1-9][0-9]\)|[1-9][0-9]) ?[0-9]{4,5}-?[0-9]{4}', value):
            raise serializers.ValidationError('Informe um telefone brasileiro com DDD.')
        return re.sub(r'[^0-9]', '', value)


class ResumoBairroSerializer(serializers.Serializer):
    bairro = serializers.CharField(allow_null=True)
    total = serializers.IntegerField(min_value=0)


class VendedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendedor
        fields = '__all__'

class AuditoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Auditoria
        fields = '__all__'
