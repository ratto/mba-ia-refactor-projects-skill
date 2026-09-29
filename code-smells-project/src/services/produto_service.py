"""Regra de negócio de produtos. Não conhece HTTP nem SQL."""

from src.exceptions import DadosInvalidos, NaoEncontrado
from src.services import validators

CATEGORIAS_VALIDAS = [
    "informatica", "moveis", "vestuario", "geral", "eletronicos", "livros",
]
CATEGORIA_PADRAO = "geral"
TAMANHO_MINIMO_DO_NOME = 2
TAMANHO_MAXIMO_DO_NOME = 200


class ProdutoService:
    def __init__(self, produto_repository):
        self._repositorio = produto_repository

    def listar(self):
        return self._repositorio.listar()

    def buscar(self, produto_id):
        produto = self._repositorio.buscar_por_id(produto_id)
        if not produto:
            raise NaoEncontrado("Produto não encontrado")
        return produto

    def pesquisar(self, termo=None, categoria=None, preco_min=None, preco_max=None):
        return self._repositorio.pesquisar(
            termo=termo,
            categoria=categoria,
            preco_min=validators.converter_para_float(preco_min, "preco_min"),
            preco_max=validators.converter_para_float(preco_max, "preco_max"),
        )

    def criar(self, dados):
        atributos = self._validar(dados)
        return self._repositorio.criar(**atributos)

    def atualizar(self, produto_id, dados):
        # A ordem é preservada do comportamento original: a existência do produto
        # é verificada antes da validação do corpo.
        if not self._repositorio.buscar_por_id(produto_id):
            raise NaoEncontrado("Produto não encontrado")

        atributos = self._validar(dados, validar_categoria=False)
        self._repositorio.atualizar(produto_id, **atributos)

    def deletar(self, produto_id):
        if not self._repositorio.buscar_por_id(produto_id):
            raise NaoEncontrado("Produto não encontrado")
        self._repositorio.deletar(produto_id)

    def _validar(self, dados, validar_categoria=True):
        """Validação única de produto, compartilhada por criação e atualização.

        As mensagens de erro são idênticas às da versão anterior, para não
        quebrar clientes que dependem delas.
        """
        validators.exigir_dicionario(dados)
        nome = validators.exigir_campo(dados, "nome", "Nome é obrigatório")
        preco = validators.exigir_campo(dados, "preco", "Preço é obrigatório")
        estoque = validators.exigir_campo(dados, "estoque", "Estoque é obrigatório")

        validators.exigir_numero(preco, "Preço")
        validators.exigir_inteiro(estoque, "Estoque")
        if preco < 0:
            raise DadosInvalidos("Preço não pode ser negativo")
        if estoque < 0:
            raise DadosInvalidos("Estoque não pode ser negativo")

        nome = validators.exigir_texto(
            nome, "Nome",
            minimo=TAMANHO_MINIMO_DO_NOME,
            maximo=TAMANHO_MAXIMO_DO_NOME,
        )

        categoria = dados.get("categoria") or CATEGORIA_PADRAO
        if validar_categoria and categoria not in CATEGORIAS_VALIDAS:
            raise DadosInvalidos(
                "Categoria inválida. Válidas: " + str(CATEGORIAS_VALIDAS)
            )

        return {
            "nome": nome,
            "descricao": dados.get("descricao", ""),
            "preco": preco,
            "estoque": estoque,
            "categoria": categoria,
        }
