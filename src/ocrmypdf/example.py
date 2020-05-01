import ocrmypdf


@ocrmypdf.hookimpl
def prepare(options):
    raise ValueError('foo')
