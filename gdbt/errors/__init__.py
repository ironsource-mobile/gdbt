class Error(Exception):
    message = "Unknown error"
    code = "ERR_UNKNOWN"

    def __init__(self, details: str = ""):
        message = self.message
        if details:
            message += f": {details}"
        super().__init__(message)


class ProviderError(Error):
    message = "Provider error"
    code = "ERR_PROVIDER"


class ProviderNotFound(ProviderError):
    message = "Provider not found"
    code = "ERR_PROVIDER_NOT_FOUND"


class GrafanaError(ProviderError):
    message = "Grafana API error"
    code = "ERR_GRAFANA"


class ConsulError(ProviderError):
    message = "Consul error"
    code = "ERR_CONSUL"


class ConsulKeyNotFoundError(ConsulError):
    message = "Consul key not found"
    code = "ERR_CONSUL_KEY_NOT_FOUND"


class VariableError(Error):
    message = "Variable error"
    code = "ERR_VARIABLE"


class VariableNotFound(VariableError):
    message = "Variable not found"
    code = "ERR_VARIABLE_NOT_FOUND"


class VariableNotIterable(VariableError):
    message = "Variable is not iterable"
    code = "ERR_VARIABLE_NOT_ITERABLE"


class DataError(Error):
    variable = "Invalid data"
    code = "ERR_DATA"


class ConfigError(Error):
    message = "Configuration error"
    code = "ERR_CONFIG"


class EvaluationKindNotFound(ConfigError):
    message = "Invalid kind of evaluation"
    code = "ERR_CONFIG_EVALUATION_KIND_INVALID"
