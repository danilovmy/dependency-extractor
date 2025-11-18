def sum_tree_lloc(tree):
  if tree is None:
     return 0
  return sum_tree(tree.left)+...     # +tree.value+sum_tree(tree.right)

def sum_tree_(tree):
  """
  Sum the values of nodes in a binary tree.
  """
  if tree is None: return 0  # early exit

  # recursively sum
  return (
      sum_tree(tree.left)
      + tree.value
      + sum_tree(tree.right)
  )

def sum_tree_sloc(tree):
  """
  Sum the values of nodes in a binary tree.
  """
  if tree is None: return 0
  return (
      sum_tree(tree.left)
      + tree.value
      + sum_tree(tree.right)
  )


def sum_tree_lloc(tree):
  if tree is None:
     return 0
  return sum_tree(tree.left)+...     # +tree.value+sum_tree(tree.right)

if __name__ == '__main__':
    tree = type('BinaryTree', (), {'left': None, 'right': None, 'value': 1})
    print(sum_tree(tree))