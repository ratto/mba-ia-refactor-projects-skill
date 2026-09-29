"""Regra de negócio de pedidos. Não conhece HTTP nem SQL."""

from src.exceptions import DadosInvalidos, NaoEncontrado
from src.repositories.pedido_repository import EstoqueIndisponivel
from src.services import validators

STATUS_VALIDOS = ["pendente", "aprovado", "enviado", "entregue", "cancelado"]
STATUS_INICIAL = "pendente"
QUANTIDADE_MINIMA_POR_ITEM = 1


class PedidoService:
    def __init__(self, pedido_repository, produto_repository, notificador):
        self._pedidos = pedido_repository
        self._produtos = produto_repository
        self._notificador = notificador

    def listar_todos(self):
        return self._pedidos.listar()

    def listar_por_usuario(self, usuario_id):
        return self._pedidos.listar_por_usuario(usuario_id)

    def criar(self, dados):
        validators.exigir_dicionario(dados)

        usuario_id = dados.get("usuario_id")
        if not usuario_id:
            raise DadosInvalidos("Usuario ID é obrigatório")

        itens_informados = dados.get("itens") or []
        if not isinstance(itens_informados, list) or not itens_informados:
            raise DadosInvalidos("Pedido deve ter pelo menos 1 item")

        itens, total = self._precificar(itens_informados)

        try:
            pedido_id = self._pedidos.criar_com_itens(usuario_id, total, itens)
        except EstoqueIndisponivel as erro:
            # Corrida com outro pedido entre a validação e a gravação.
            raise DadosInvalidos(str(erro)) from erro

        self._notificador.pedido_criado(pedido_id, usuario_id)
        return {"pedido_id": pedido_id, "total": total}

    def atualizar_status(self, pedido_id, dados):
        validators.exigir_dicionario(dados)
        novo_status = validators.exigir_valor_permitido(
            dados.get("status", ""), STATUS_VALIDOS, "Status"
        )

        if not self._pedidos.buscar_por_id(pedido_id):
            raise NaoEncontrado("Pedido não encontrado")

        self._pedidos.atualizar_status(pedido_id, novo_status)
        self._notificador.status_alterado(pedido_id, novo_status)

    def _precificar(self, itens_informados):
        """Valida cada item, confere estoque e calcula o total do pedido.

        Os produtos são carregados uma única vez — o código legado consultava o
        mesmo produto duas vezes (validação e gravação).
        """
        itens = []
        total = 0

        for posicao, item in enumerate(itens_informados, start=1):
            rotulo = f"Item {posicao}"
            validators.exigir_dicionario(item, f"{rotulo} inválido")
            produto_id = validators.exigir_campo(
                item, "produto_id", f"{rotulo}: produto_id é obrigatório"
            )
            quantidade = validators.exigir_inteiro(
                validators.exigir_campo(
                    item, "quantidade", f"{rotulo}: quantidade é obrigatória"
                ),
                f"{rotulo}: quantidade",
                minimo=QUANTIDADE_MINIMA_POR_ITEM,
            )

            produto = self._produtos.buscar_por_id(produto_id)
            if produto is None:
                raise DadosInvalidos(f"Produto {produto_id} não encontrado")
            if produto["estoque"] < quantidade:
                raise DadosInvalidos(f"Estoque insuficiente para {produto['nome']}")

            total += produto["preco"] * quantidade
            itens.append({
                "produto_id": produto_id,
                "quantidade": quantidade,
                "preco_unitario": produto["preco"],
            })

        return itens, total
