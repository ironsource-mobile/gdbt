class Error(Exception):
    message = "Unknown error"
    code = "ERR_UNKNOWN"

    @property
    def text(self) -> str:
        text = f"[{self.code}]: {self.message}"
        if self.details:
            text += f": {self.details}"
        return text

    def __init__(self, details: str = ""):
        self.details = details
        super().__init__(self.message)


class ProviderError(Error):
    message = "Provider error"
    code = "ERR_PROVIDER"


class ProviderNotFound(ProviderError):
    message = "Provider not found"
    code = "ERR_PROVIDER_NOT_FOUND"


class GrafanaError(ProviderError):
    message = "Grafana API error"
    code = "ERR_GRAFANA"


class GrafanaServerError(GrafanaError):
    message = "Grafana server error"
    code = "ERR_GRAFANA_SERVER_ERROR"


class GrafanaResourceNotFound(GrafanaError):
    message = "Grafana resource not found"
    code = "ERR_GRAFANA_RESOURCE_NOT_FOUND"


class FileError(ProviderError):
    message = "File error"
    code = "ERR_FILE"


class FileNotFound(FileError):
    message = "File not found"
    code = "ERR_FILE_NOT_FOUND"


class FileAccessDenied(FileError):
    message = "Access denied to file"
    code = "ERR_FILE_ACCESS_DENIED"


class ConsulError(ProviderError):
    message = "Consul error"
    code = "ERR_CONSUL"


class ConsulKeyNotFound(ConsulError):
    message = "Consul key not found"
    code = "ERR_CONSUL_KEY_NOT_FOUND"


class S3Error(ProviderError):
    message = "S3 error"
    code = "ERR_S3"


class S3BucketNotFound(S3Error):
    message = "S3 bucket not found"
    code = "ERR_S3_BUCKET_NOT_FOUND"


class S3ObjectNotFound(S3Error):
    message = "S3 object not found"
    code = "ERR_S3_OBJECT_NOT_FOUND"


class S3AccessDenied(S3Error):
    message = "Access denied to S3 bucket"
    code = "ERR_S3_ACCESS_DENIED"


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


class ConfigFileNotFound(ConfigError):
    message = "Configuration file not found"
    code = "ERR_CONFIG_FILE_NOT_FOUND"


class ConfigEmpty(ConfigError):
    message = "Configuration is empty"
    code = "ERR_CONFIG_EMPTY"


class ConfigFormatInvalid(ConfigError):
    message = "Invalid configuration format"
    code = "ERR_CONFIG_FORMAT_INVALID"


class EvaluationKindNotFound(ConfigError):
    message = "Invalid kind of evaluation"
    code = "ERR_CONFIG_EVALUATION_KIND_INVALID"


class StateError(Error):
    message = "State error"
    code = "ERR_STATE"


class StateVersionIncompatible(StateError):
    message = "Incompatible state version"
    code = "ERR_STATE_VERSION_INCOMPATIBLE"


class StateCorrupted(StateError):
    message = "Invalid state format, it might be corrupted"
    code = "ERR_STATE_CORRUPTED"


class StateLockError(StateError):
    message = "State lock error"
    code = "ERR_STATE_LOCK"


class StateAlreadyLocked(StateError):
    message = "State already locked, is someone else modifying the same resource?"
    code = "ERR_STATE_ALREADY_LOCKED"


class StateUnlockError(StateError):
    message = "Unable to unlock state"
    code = "ERR_STATE_UNLOCK_FAIL"
