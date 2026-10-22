"""Credenciais no cofre seguro do SO ou apenas memória; nunca configuração textual."""


class Credentials:
    """OS credential vault, otherwise process memory only. No plaintext fallback."""
    SERVICE = "ConversorDeBases"

    def __init__(self):
        self.memory = {}

    def get(self, provider):
        if provider in self.memory:
            return self.memory[provider]
        try:
            import keyring
            backend = keyring.get_keyring()
            if not self.secure(backend):
                return ""
            return keyring.get_password(self.SERVICE, provider) or ""
        except Exception:
            return ""

    @staticmethod
    def secure(backend):
        name = type(backend).__module__.lower()
        return any(s in name for s in ("secretservice", "windows", "macos", "kwallet")) and "plaintext" not in name

    def set(self, provider, secret, persist=False):
        if not secret.strip():
            return
        self.memory[provider] = secret.strip()
        if persist:
            try:
                import keyring
                if not self.secure(keyring.get_keyring()):
                    raise RuntimeError()
                keyring.set_password(self.SERVICE, provider, secret.strip())
            except Exception:
                raise ValueError("Cofre seguro indisponível. Chave mantida somente na memória desta sessão.") from None

    def delete(self, provider):
        self.memory.pop(provider, None)
        try:
            import keyring
            if self.secure(keyring.get_keyring()):
                keyring.delete_password(self.SERVICE, provider)
        except Exception:
            pass


credentials = Credentials()
