"""Regra de negócio do relatório de vendas. Não conhece HTTP nem SQL."""

CASAS_DECIMAIS = 2

# Faixas de desconto sobre o faturamento bruto, da maior para a menor.
# (faturamento mínimo, percentual aplicado)
FAIXAS_DE_DESCONTO = [
    (10000, 0.10),
    (5000, 0.05),
    (1000, 0.02),
]


class RelatorioService:
    def __init__(self, pedido_repository):
        self._pedidos = pedido_repository

    def vendas(self):
        resumo = self._pedidos.resumo_de_vendas()
        faturamento = resumo["faturamento"]
        total_pedidos = resumo["total_pedidos"]
        desconto = self.calcular_desconto(faturamento)

        return {
            "total_pedidos": total_pedidos,
            "faturamento_bruto": round(faturamento, CASAS_DECIMAIS),
            "desconto_aplicavel": round(desconto, CASAS_DECIMAIS),
            "faturamento_liquido": round(faturamento - desconto, CASAS_DECIMAIS),
            "pedidos_pendentes": resumo["pendentes"],
            "pedidos_aprovados": resumo["aprovados"],
            "pedidos_cancelados": resumo["cancelados"],
            "ticket_medio": (
                round(faturamento / total_pedidos, CASAS_DECIMAIS)
                if total_pedidos > 0 else 0
            ),
        }

    @staticmethod
    def calcular_desconto(faturamento):
        for minimo, percentual in FAIXAS_DE_DESCONTO:
            if faturamento > minimo:
                return faturamento * percentual
        return 0
