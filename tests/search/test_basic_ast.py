import pytest

from karp.search import basic_ast as ast


def test_AstException():
    e = ast.AstException('test')
    assert repr(e) == "AstException message='test'"


def test_AstNode():
    node = ast.AstNode('test')
    assert node.num_children() == 0
    assert not node.can_add_child()
    with pytest.raises(ast.TooManyChildren):
        node.add_child(ast.AstNode('child'))
    with pytest.raises(StopIteration):
        gen = node.children()
        next(gen)
    assert node.num_children() == sum(1 for i in node.children())


def test_NodeWithOneChild():
    node = ast.NodeWithOneChild('one', None)
    assert sum(1 for i in node.children()) == 0
    assert node.can_add_child()
    assert not node.has_child0()

    node.add_child(ast.AstNode('child0'))

    assert sum(1 for i in node.children()) == 1
    assert not node.can_add_child()
    assert node.has_child0()


def test_NodeWithTwoChildren():
    node = ast.NodeWithTwoChildren('two', None, None)
    assert sum(1 for i in node.children()) == 0
    assert node.can_add_child()
    assert not node.has_child0()
    assert not node.has_child1()

    node.add_child(ast.AstNode('child0'))

    assert sum(1 for i in node.children()) == 1
    assert node.can_add_child()
    assert node.has_child0()
    assert not node.has_child1()

    node.add_child(ast.AstNode('child1'))

    assert sum(1 for i in node.children()) == 2
    assert not node.can_add_child()
    assert node.has_child0()
    assert node.has_child1()


def test_NodeWithThreeChildren():
    node = ast.NodeWithThreeChildren('three', None, None, None)
    assert sum(1 for i in node.children()) == 0
    assert node.can_add_child()
    assert not node.has_child0()
    assert not node.has_child1()
    assert not node.has_child2()

    node.add_child(ast.AstNode('child0'))

    assert sum(1 for i in node.children()) == 1
    assert node.can_add_child()
    assert node.has_child0()
    assert not node.has_child1()
    assert not node.has_child2()

    node.add_child(ast.AstNode('child1'))

    assert sum(1 for i in node.children()) == 2
    assert node.can_add_child()
    assert node.has_child0()
    assert node.has_child1()
    assert not node.has_child2()

    node.add_child(ast.AstNode('child2'))

    assert sum(1 for i in node.children()) == 3
    assert not node.can_add_child()
    assert node.has_child0()
    assert node.has_child1()
    assert node.has_child2()


def test_UnaryOp_1():
    node = ast.UnaryOp('test')

    assert node.num_children() == 0
    assert node.can_add_child()
    assert node.num_children() == sum(1 for i in node.children())
    assert not node.has_child0()

    node.add_child(ast.AstNode('child'))

    assert not node.can_add_child()
    with pytest.raises(ast.TooManyChildren):
        node.add_child(ast.AstNode('child'))
    assert node.num_children() == sum(1 for i in node.children())
    assert node.has_child0()


def test_UnaryOp_2():
    node = ast.UnaryOp('test')

    assert node.num_children() == 0
    assert node.can_add_child()
    assert node.num_children() == sum(1 for i in node.children())
    assert not node.has_child0()

    node.child0 = ast.AstNode('child')

    assert not node.can_add_child()
    with pytest.raises(ast.TooManyChildren):
        node.add_child(ast.AstNode('child'))
    assert node.num_children() == sum(1 for i in node.children())
    assert node.has_child0()


def test_BinaryOp_1():
    node = ast.BinaryOp('test')

    assert node.num_children() == 0
    assert node.can_add_child()
    assert node.num_children() == sum(1 for i in node.children())
    assert not node.has_child0()
    assert not node.has_child1()

    node.add_child(ast.AstNode('child1'))

    assert node.num_children() == 1
    assert node.can_add_child()
    assert node.num_children() == sum(1 for i in node.children())
    assert node.has_child0()
    assert not node.has_child1()

    node.add_child(ast.AstNode('child2'))

    assert node.num_children() == 2
    assert not node.can_add_child()
    with pytest.raises(ast.TooManyChildren):
        node.add_child(ast.AstNode('child'))
    assert node.num_children() == sum(1 for i in node.children())
    assert node.has_child0()
    assert node.has_child1()


def test_BinaryOp_2():
    node = ast.BinaryOp('test')

    assert node.num_children() == 0
    assert node.can_add_child()
    assert node.num_children() == sum(1 for i in node.children())
    assert not node.has_child0()
    assert not node.has_child1()

    node.child0 = ast.AstNode('child1')

    assert node.num_children() == 1
    assert node.can_add_child()
    assert node.num_children() == sum(1 for i in node.children())
    assert node.has_child0()
    assert not node.has_child1()

    node.add_child(ast.AstNode('child2'))

    assert not node.can_add_child()
    with pytest.raises(ast.TooManyChildren):
        node.add_child(ast.AstNode('child'))
    assert node.num_children() == sum(1 for i in node.children())
    assert node.has_child0()
    assert node.has_child1()


def test_BinaryOp_3():
    node = ast.BinaryOp('test')

    assert node.num_children() == 0
    assert node.can_add_child()
    assert node.num_children() == sum(1 for i in node.children())
    assert not node.has_child0()
    assert not node.has_child1()

    node.add_child(ast.AstNode('child1'))

    assert node.num_children() == 1
    assert node.can_add_child()
    assert node.num_children() == sum(1 for i in node.children())
    assert node.has_child0()
    assert not node.has_child1()

    node.child1 = ast.AstNode('child2')

    assert not node.can_add_child()
    with pytest.raises(ast.TooManyChildren):
        node.add_child(ast.AstNode('child'))
    assert node.num_children() == sum(1 for i in node.children())
    assert node.has_child0()
    assert node.has_child1()


def test_BinaryOp_4():
    node = ast.BinaryOp('test')

    assert node.num_children() == 0
    assert node.can_add_child()
    assert node.num_children() == sum(1 for i in node.children())
    assert not node.has_child0()
    assert not node.has_child1()

    node.child0 = ast.AstNode('child1')

    assert node.num_children() == 1
    assert node.can_add_child()
    assert node.num_children() == sum(1 for i in node.children())
    assert node.has_child0()
    assert not node.has_child1()

    node.child1 = ast.AstNode('child2')

    assert not node.can_add_child()
    with pytest.raises(ast.TooManyChildren):
        node.add_child(ast.AstNode('child'))
    assert node.num_children() == sum(1 for i in node.children())
    assert node.has_child0()
    assert node.has_child1()


def test_TernaryOp_1():
    node = ast.TernaryOp('test')

    assert node.num_children() == 0
    assert node.can_add_child()
    assert node.num_children() == sum(1 for i in node.children())
    assert not node.has_child0()
    assert not node.has_child1()
    assert not node.has_child2()

    node.add_child(ast.AstNode('child1'))

    assert node.num_children() == 1
    assert node.can_add_child()
    assert node.num_children() == sum(1 for i in node.children())
    assert node.has_child0()
    assert not node.has_child1()
    assert not node.has_child2()

    node.add_child(ast.AstNode('child2'))

    assert node.num_children() == 2
    assert node.can_add_child()
    assert node.num_children() == sum(1 for i in node.children())
    assert node.has_child0()
    assert node.has_child1()
    assert not node.has_child2()

    node.add_child(ast.AstNode('child3'))

    assert node.num_children() == 3
    assert not node.can_add_child()
    with pytest.raises(ast.TooManyChildren):
        node.add_child(ast.AstNode('child'))
    assert node.num_children() == sum(1 for i in node.children())
    assert node.has_child0()
    assert node.has_child1()
    assert node.has_child2()


def test_TernaryOp_2():
    node = ast.TernaryOp('test')

    assert node.num_children() == 0
    assert node.can_add_child()
    assert node.num_children() == sum(1 for i in node.children())
    assert not node.has_child0()
    assert not node.has_child1()
    assert not node.has_child2()

    node.child0 = ast.AstNode('child1')

    assert node.num_children() == 1
    assert node.can_add_child()
    assert node.num_children() == sum(1 for i in node.children())
    assert node.has_child0()
    assert not node.has_child1()
    assert not node.has_child2()

    node.add_child(ast.AstNode('child2'))

    assert node.num_children() == 2
    assert node.can_add_child()
    assert node.num_children() == sum(1 for i in node.children())
    assert node.has_child0()
    assert node.has_child1()
    assert not node.has_child2()

    node.add_child(ast.AstNode('child3'))

    assert node.num_children() == 3
    assert not node.can_add_child()
    with pytest.raises(ast.TooManyChildren):
        node.add_child(ast.AstNode('child'))
    assert node.num_children() == sum(1 for i in node.children())
    assert node.has_child0()
    assert node.has_child1()
    assert node.has_child2()


def test_TernaryOp_3():
    node = ast.TernaryOp('test')

    assert node.num_children() == 0
    assert node.can_add_child()
    assert node.num_children() == sum(1 for i in node.children())
    assert not node.has_child0()
    assert not node.has_child1()
    assert not node.has_child2()

    node.add_child(ast.AstNode('child1'))

    assert node.num_children() == 1
    assert node.can_add_child()
    assert node.num_children() == sum(1 for i in node.children())
    assert node.has_child0()
    assert not node.has_child1()
    assert not node.has_child2()

    node.child1 = ast.AstNode('child2')

    assert node.num_children() == 2
    assert node.can_add_child()
    assert node.num_children() == sum(1 for i in node.children())
    assert node.has_child0()
    assert node.has_child1()
    assert not node.has_child2()

    node.add_child(ast.AstNode('child3'))

    assert node.num_children() == 3
    assert not node.can_add_child()
    with pytest.raises(ast.TooManyChildren):
        node.add_child(ast.AstNode('child'))
    assert node.num_children() == sum(1 for i in node.children())
    assert node.has_child0()
    assert node.has_child1()
    assert node.has_child2()


def test_TernaryOp_4():
    node = ast.TernaryOp('test')

    assert node.num_children() == 0
    assert node.can_add_child()
    assert node.num_children() == sum(1 for i in node.children())
    assert not node.has_child0()
    assert not node.has_child1()
    assert not node.has_child2()

    node.add_child(ast.AstNode('child1'))

    assert node.num_children() == 1
    assert node.can_add_child()
    assert node.num_children() == sum(1 for i in node.children())
    assert node.has_child0()
    assert not node.has_child1()
    assert not node.has_child2()

    node.add_child(ast.AstNode('child2'))

    assert node.num_children() == 2
    assert node.can_add_child()
    assert node.num_children() == sum(1 for i in node.children())
    assert node.has_child0()
    assert node.has_child1()
    assert not node.has_child2()

    node.child2 = ast.AstNode('child3')

    assert node.num_children() == 3
    assert not node.can_add_child()
    with pytest.raises(ast.TooManyChildren):
        node.add_child(ast.AstNode('child'))
    assert node.num_children() == sum(1 for i in node.children())
    assert node.has_child0()
    assert node.has_child1()
    assert node.has_child2()
