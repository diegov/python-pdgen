from . import PdPatch, RenderVisitor


class PdFile(object):
    def __init__(self, filepath, patch=None):
        self.filepath = filepath
        self.patch = patch if patch is not None else PdPatch()

    def save(self):
        for abstr_file in self.patch.abstraction_files:
            abstr_file.save()

        with open(self.filepath, 'w') as f:
            self.patch.accept(RenderVisitor(f))
