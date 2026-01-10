  @Engine("mssql");

  Parent(parent: "Alice", child: "Bob");
  Parent(parent: "Bob", child: "Carol");

  Grandparent(grandparent:, grandchild:) :-
    Parent(parent: grandparent, child: x),
    Parent(parent: x, child: grandchild);
