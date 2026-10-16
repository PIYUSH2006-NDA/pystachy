f"""An f-string is no docstring: the module's __doc__ is None."""
from .docmod import doc_of


def has_doc() -> bool:
    return __doc__ is not None and len(doc_of()) > 0
