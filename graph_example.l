@Engine("sqlite");

Edge(1, 2);
Edge(1, 3);
Edge(3, 4);

@Recursive(Path, 5);
Path(x, y) distinct :- Edge(x, y);
Path(x, z) distinct :- Edge(x, y), Path(y, z);

LongPath() :- Path(1, 4);
