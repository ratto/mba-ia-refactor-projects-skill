"""Regra de negócio de usuários e autenticação. Não conhece HTTP nem SQL."""

import logging

from src.exceptions import DadosInvalidos, NaoAutenticado, NaoEncontrado
from src.services import validators
from src.services.seguranca import gerar_hash_senha, senha_confere

logger = logging.getLogger(__name__)

TAMANHO_MINIMO_DA_SENHA = 6
TIPO_PADRAO = "cliente"


class UsuarioService:
    def __init__(self, usuario_repository, servico_de_token):
        self._repositorio = usuario_repository
        self._tokens = servico_de_token

    def listar(self):
        return self._repositorio.listar()

    def buscar(self, usuario_id):
        usuario = self._repositorio.buscar_por_id(usuario_id)
        if not usuario:
            raise NaoEncontrado("Usuário não encontrado")
        return usuario

    def criar(self, dados):
        validators.exigir_dicionario(dados)
        nome = dados.get("nome", "")
        email = dados.get("email", "")
        senha = dados.get("senha", "")

        if not nome or not email or not senha:
            raise DadosInvalidos("Nome, email e senha são obrigatórios")

        nome = validators.exigir_texto(nome, "Nome")
        email = validators.exigir_texto(email, "Email")
        senha = validators.exigir_texto(
            senha, "Senha", minimo=TAMANHO_MINIMO_DA_SENHA
        )

        if self._repositorio.email_existe(email):
            raise DadosInvalidos("Email já cadastrado")

        # O tipo do usuário nunca vem do corpo da requisição: aceitar `tipo` do
        # cliente permitiria que qualquer um se cadastrasse como admin.
        return self._repositorio.criar(nome, email, gerar_hash_senha(senha), TIPO_PADRAO)

    def autenticar(self, dados):
        """Valida credenciais e devolve (usuário público, token)."""
        validators.exigir_dicionario(dados)
        email = dados.get("email", "")
        senha = dados.get("senha", "")

        if not email or not senha:
            raise DadosInvalidos("Email e senha são obrigatórios")

        usuario = self._repositorio.buscar_por_email_com_senha(email)
        if not usuario or not senha_confere(usuario["senha"], senha):
            # Mensagem genérica: distinguir "email inexistente" de "senha errada"
            # entrega ao atacante uma lista de e-mails válidos.
            logger.info("Tentativa de login rejeitada")
            raise NaoAutenticado("Email ou senha inválidos")

        publico = {
            "id": usuario["id"],
            "nome": usuario["nome"],
            "email": usuario["email"],
            "tipo": usuario["tipo"],
        }
        logger.info("Login bem-sucedido para o usuário %s", usuario["id"])
        return publico, self._tokens.emitir(usuario["id"], usuario["tipo"])
