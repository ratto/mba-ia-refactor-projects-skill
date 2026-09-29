"""Primitivas de segurança: hash de senha e emissão/verificação de token.

Usa `werkzeug.security` e `itsdangerous`, que já são dependências transitivas do
Flask — nenhuma dependência nova é introduzida.
"""

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from werkzeug.security import check_password_hash, generate_password_hash

_PREFIXOS_DE_HASH = ("pbkdf2:", "scrypt:", "argon2", "$")

SALT_DE_TOKEN = "auth-token"


def gerar_hash_senha(senha):
    return generate_password_hash(senha)


def senha_confere(hash_armazenado, senha_informada):
    if not hash_armazenado:
        return False
    return check_password_hash(hash_armazenado, senha_informada)


def parece_hash(valor):
    """Heurística para identificar senhas legadas ainda em texto puro."""
    return isinstance(valor, str) and valor.startswith(_PREFIXOS_DE_HASH)


class ServicoDeToken:
    """Emite e valida tokens de sessão assinados com a SECRET_KEY."""

    def __init__(self, secret_key, ttl_segundos):
        self._serializer = URLSafeTimedSerializer(secret_key, salt=SALT_DE_TOKEN)
        self.ttl_segundos = ttl_segundos

    def emitir(self, usuario_id, tipo):
        return self._serializer.dumps({"usuario_id": usuario_id, "tipo": tipo})

    def verificar(self, token):
        """Devolve o payload do token, ou None se inválido/expirado."""
        try:
            return self._serializer.loads(token, max_age=self.ttl_segundos)
        except (BadSignature, SignatureExpired):
            return None
