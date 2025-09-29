
class TestClass:

    def visit(self, node):
        """Visit a node."""
        method = 'visit_' + node.__class__.__name__
        if hasattr(self, method):
            return getattr(self, method)(node)

    @property
    def name(self):
        return self.__class__.__name__