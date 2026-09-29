"""Validação de formato de entrada, compartilhada pelos Services.

Funções simples da stdlib — o projeto não tem uma lib de schema entre suas
dependências e não vale adicionar uma só para este escopo (KISS).
"""

from src.exceptions import DadosInvalidos


def exigir_dicionario(dados, mensagem="Dados inválidos"):
    if not isinstance(dados, dict) or not dados:
        raise DadosInvalidos(mensagem)
    return dados


def exigir_campo(dados, campo, mensagem):
    if campo not in dados or dados[campo] is None:
        raise DadosInvalidos(mensagem)
    return dados[campo]


def exigir_texto(valor, rotulo, minimo=1, maximo=None):
    if not isinstance(valor, str) or not valor.strip():
        raise DadosInvalidos(f"{rotulo} deve ser um texto não vazio")
    valor = valor.strip()
    if len(valor) < minimo:
        raise DadosInvalidos(f"{rotulo} muito curto")
    if maximo is not None and len(valor) > maximo:
        raise DadosInvalidos(f"{rotulo} muito longo")
    return valor


def exigir_numero(valor, rotulo, minimo=None):
    # bool é subclasse de int em Python — rejeitado explicitamente.
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise DadosInvalidos(f"{rotulo} deve ser numérico")
    if minimo is not None and valor < minimo:
        raise DadosInvalidos(f"{rotulo} não pode ser menor que {minimo}")
    return valor


def exigir_inteiro(valor, rotulo, minimo=None):
    if isinstance(valor, bool) or not isinstance(valor, int):
        raise DadosInvalidos(f"{rotulo} deve ser um número inteiro")
    if minimo is not None and valor < minimo:
        raise DadosInvalidos(f"{rotulo} não pode ser menor que {minimo}")
    return valor


def converter_para_float(valor, rotulo):
    """Converte um parâmetro de query string, devolvendo None quando ausente."""
    if valor is None or valor == "":
        return None
    try:
        return float(valor)
    except (TypeError, ValueError):
        raise DadosInvalidos(f"{rotulo} deve ser um número")


def exigir_valor_permitido(valor, permitidos, rotulo):
    if valor not in permitidos:
        raise DadosInvalidos(f"{rotulo} inválido. Válidos: {list(permitidos)}")
    return valor
