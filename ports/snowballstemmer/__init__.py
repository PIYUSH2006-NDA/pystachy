__all__ = ('language', 'stemmer')

try:
    import Stemmer
    algorithms = Stemmer.algorithms
    stemmer = Stemmer.Stemmer
except ImportError:
    # Pystachy port: only the English (Porter2) and Porter stemmers are ported, as
    # PORT.md says; the other 34 modules are left out
    from .english_stemmer import EnglishStemmer
    from .porter_stemmer import PorterStemmer

    # Pystachy port: no _languages and no stemmer(lang): the dict holds classes as
    # values, and stemmer() returns an object of whichever class lang names, which
    # needs one type for objects of different classes (#7, #9). Make the stemmer
    # itself, as in snowballstemmer.english_stemmer.EnglishStemmer().stemWord(word).
    def algorithms() -> list[str]:
        return ['english', 'porter']
