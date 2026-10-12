# error: import_kwargs_annotation.py:5: error: emods.kwanns.show() is not supported: parameter 'kwargs': unsupported type annotation
# A call of an imported function whose **kwargs annotation Pystachy does not support reports it
# where the program calls it, as for another parameter's annotation.
import emods.kwanns
print(emods.kwanns.count(), emods.kwanns.show(a=1))
